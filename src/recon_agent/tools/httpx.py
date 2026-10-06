"""HTTP probing with scoped address constraints, fixed argv and no redirects."""

import os
import re
import shutil
from dataclasses import dataclass, field
from ipaddress import ip_address
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import urlsplit

from pydantic import InstanceOf

from recon_agent.core.config.models import ExecutionConfig
from recon_agent.core.errors import (
    ConfigurationError,
    ErrorCode,
    ErrorContext,
    ParserError,
    PlannerValidationError,
    ToolExecutionError,
    ToolTimeoutError,
    ToolUnavailableError,
)
from recon_agent.core.results import Failure, OperationResult, Success
from recon_agent.domain import (
    ActionRequest,
    Target,
)
from recon_agent.domain.budgets import ReservationOutcome
from recon_agent.domain.capabilities import (
    CapabilityDescriptor,
    CapabilityId,
    RiskClass,
)
from recon_agent.execution import (
    AsyncProcessRunner,
    ProcessExecution,
    ProcessRunner,
    ProcessSpec,
)
from recon_agent.policy.actions import ActionPolicyValidator
from recon_agent.policy.budgets import BudgetController
from recon_agent.tools.base import AdapterDefinition, ToolAdapter
from recon_agent.tools.httpx_models import HttpProbeOutput, HttpxContext, HttpxInput
from recon_agent.tools.httpx_parser import normalize, parse, probe_url

_VERSION = "1.9.0"
_FLAGS = (
    "-silent",
    "-nc",
    "-duc",
    "-json",
    "-stream",
    "-t",
    "1",
    "-rl",
    "1",
    "-retries",
    "0",
    "-timeout",
    "10",
    "-no-fallback-scheme",
    "-x",
    "GET",
    "-cdn",
    "false",
    "-random-agent=false",
    "-status-code",
    "-title",
    "-server",
    "-content-type",
    "-content-length",
    "-location",
    "-tech-detect",
    "-ip",
    "-response-size-to-read",
    "65536",
    "-response-size-to-save",
    "65536",
)


def _failure(
    error: ParserError
    | PlannerValidationError
    | ToolExecutionError
    | ToolTimeoutError
    | ToolUnavailableError,
) -> Failure:
    return Failure(error=error.to_error_info())


def _spec(
    executable: str, directory: str, args: tuple[str, ...], timeout: float
) -> ProcessSpec:
    # No inherited credentials, proxy/config variables or flag configuration.
    environment = tuple(
        (key, directory)
        for key in (
            "HOME",
            "USERPROFILE",
            "APPDATA",
            "LOCALAPPDATA",
            "XDG_CONFIG_HOME",
            "TMPDIR",
            "TMP",
            "TEMP",
        )
    )
    if "SystemRoot" in os.environ:
        environment += (("SystemRoot", os.environ["SystemRoot"]),)
    return ProcessSpec(
        executable=executable,
        args=("-config", os.devnull, "-auth", "false", *args),
        timeout_seconds=timeout,
        environment=environment,
    )


def _checked_process(
    result: OperationResult[ProcessExecution], limit: int
) -> OperationResult[ProcessExecution]:
    if isinstance(result, Failure):
        return result
    process = ProcessExecution.model_validate(result.value)
    if process.return_code != 0:
        return _failure(
            ToolExecutionError(
                "HTTPX exited unsuccessfully",
                context=ErrorContext(tool="httpx", exit_code=process.return_code),
            )
        )
    if (
        process.stdout_truncated
        or process.stderr_truncated
        or len(process.stdout) > limit
        or len(process.stderr) > limit
    ):
        return _failure(ParserError("HTTPX output is truncated or oversized"))
    return Success[ProcessExecution](value=process)


@dataclass(frozen=True, slots=True)
class HttpxAdapter(ToolAdapter):
    """Operator-only executable/resolver/contact addresses; detect before real AVAILABLE registration.

    The injected runner must honor the same or smaller configured stream bound.
    Every allowed contact IP and resolver needs independent scope membership.
    """

    executable: str = field(repr=False)
    nameserver: str = field(repr=False)
    contact_addresses: tuple[str, ...] = field(repr=False)
    config: ExecutionConfig = field(repr=False)
    runner: ProcessRunner | None = field(default=None, repr=False)
    _timeout: float = field(init=False, repr=False)
    _output_limit: int = field(init=False, repr=False)

    def __post_init__(self) -> None:
        try:
            snapshot = ExecutionConfig.model_validate(self.config.model_dump())
            if (
                not isinstance(self.executable, str)
                or not Path(self.executable).is_absolute()
            ):
                raise ValueError("absolute executable required")
            endpoint = ip_address(self.nameserver)
            if endpoint.version != 4 or str(endpoint) != self.nameserver:
                raise ValueError("canonical numeric IPv4 resolver required")
            if (
                not isinstance(self.contact_addresses, tuple)
                or not 1 <= len(self.contact_addresses) <= 64
                or any(
                    str(ip_address(address)) != address
                    for address in self.contact_addresses
                )
            ):
                raise ValueError("bounded canonical numeric contact addresses required")
            ProcessSpec(executable=self.executable)
        except (ValueError, TypeError, AttributeError) as cause:
            raise ConfigurationError(
                "Invalid trusted HTTPX adapter settings"
            ) from cause
        object.__setattr__(self, "_timeout", snapshot.default_timeout_seconds)
        object.__setattr__(self, "_output_limit", snapshot.max_output_bytes)
        if self.runner is None:
            object.__setattr__(self, "runner", AsyncProcessRunner(snapshot))

    @property
    def definition(self) -> AdapterDefinition:
        return AdapterDefinition(
            adapter_id="httpx",
            descriptor=CapabilityDescriptor(
                capability=CapabilityId.PROBE_HTTP,
                description="Probe authorized HTTP endpoints for bounded service metadata",
                risk_class=RiskClass.ACTIVE_SAFE,
            ),
            input_schema=HttpxInput,
            output_schema=HttpProbeOutput,
            parameter_target_fields=("candidates",),
        )

    @classmethod
    async def detect(
        cls,
        config: ExecutionConfig,
        *,
        nameserver: str,
        contact_addresses: tuple[str, ...],
        binary: str = "httpx",
        runner: ProcessRunner | None = None,
    ) -> OperationResult[InstanceOf["HttpxAdapter"]]:
        """Explicit isolated local version check; no target probing or DNS queries."""
        if not isinstance(binary, str) or not binary.strip() or "\x00" in binary:
            raise ConfigurationError("Invalid trusted HTTPX binary setting")
        executable = shutil.which(binary)
        if executable is None:
            return _failure(ToolUnavailableError("HTTPX executable unavailable"))
        adapter = cls(
            str(Path(executable).absolute()),
            nameserver,
            contact_addresses,
            config,
            runner,
        )
        assert adapter.runner is not None
        try:
            with TemporaryDirectory(prefix="recon-httpx-") as directory:
                result = _checked_process(
                    await adapter.runner.run(
                        _spec(
                            adapter.executable,
                            directory,
                            ("-version", "-nc", "-duc"),
                            min(adapter._timeout, 5.0),
                        )
                    ),
                    adapter._output_limit,
                )
                if isinstance(result, Failure):
                    return result
                text = (result.value.stdout + b"\n" + result.value.stderr).decode(
                    "utf-8"
                )
                versions = re.findall(
                    r"Current Version:[ \t]*v?([0-9]+\.[0-9]+\.[0-9]+)[ \t]*$",
                    text,
                    re.MULTILINE,
                )
                if versions != [_VERSION]:
                    return _failure(ToolUnavailableError("Unsupported HTTPX version"))
        except (OSError, UnicodeError, ValueError, TypeError, AttributeError):
            return _failure(ToolUnavailableError("HTTPX availability check failed"))
        return Success[InstanceOf[HttpxAdapter]](value=adapter)

    async def execute(
        self,
        request: ActionRequest,
        *,
        policy: ActionPolicyValidator,
        budgets: BudgetController,
        context: HttpxContext,
    ) -> OperationResult[HttpProbeOutput]:
        try:
            request = ActionRequest.model_validate(request)
            context = HttpxContext.model_validate(context)
        except (ValueError, TypeError):
            return _failure(
                PlannerValidationError("Malformed HTTPX request or context")
            )
        if (
            request.capability != CapabilityId.PROBE_HTTP
            or policy.budget_eligibility is not budgets
            or request.asset_id not in (None, context.asset_id)
            or self._output_limit > budgets.limits.max_output_bytes
        ):
            return _failure(
                PlannerValidationError(
                    "HTTPX execution composition does not match request"
                )
            )
        selected = policy.registry.resolve(request.capability)
        if isinstance(selected, Failure):
            return selected
        if selected.value is not self:
            return _failure(
                PlannerValidationError(
                    "HTTPX adapter is not the registered capability binding"
                )
            )
        approved = policy.validate(request)
        if isinstance(approved, Failure):
            return approved
        target = approved.value.scope_match.canonical_target
        # Policy validates every original member before conversion or input creation.
        matches = approved.value.parameter_scope_matches or (
            approved.value.scope_match,
        )
        try:
            probe_url(target)  # Primary subjects obey the same supported forms.
            candidates = tuple(
                sorted({probe_url(match.canonical_target) for match in matches})
            )
        except ValueError:
            return _failure(PlannerValidationError("Unsupported HTTP probe target"))
        addresses = tuple(sorted(set(self.contact_addresses)))
        infrastructure = []
        for address in (*addresses, self.nameserver):
            checked = policy.scope_validator.validate(
                Target(id="httpx-contact", kind="ip", value=address)
            )
            if isinstance(checked, Failure):
                return checked
            infrastructure.append(checked.value)
        # Reject numeric candidates outside this execution's finite contact set.
        for candidate in candidates:
            host = urlsplit(candidate).hostname
            assert host is not None
            try:
                numeric = str(ip_address(host))
            except ValueError:
                continue
            if numeric not in addresses:
                return _failure(
                    PlannerValidationError("HTTP address is not configured for contact")
                )
        reserved = budgets.reserve(
            approved.value.model_copy(
                update={
                    "parameter_scope_matches": (*matches, *infrastructure),
                }
            )
        )
        if isinstance(reserved, Failure):
            return reserved
        assert self.runner is not None
        with reserved.value as permit:
            timeout = min(self._timeout, budgets.state.remaining_seconds)
            if timeout <= 0:
                permit.release(ReservationOutcome.TIMEOUT)
                return _failure(ToolTimeoutError("HTTPX execution deadline reached"))
            try:
                with TemporaryDirectory(prefix="recon-httpx-") as directory:
                    # Final contact checks occur before writing ANY candidate to input.
                    for host in (*candidates, *addresses, self.nameserver):
                        checked = policy.scope_validator.validate_value(host)
                        if isinstance(checked, Failure):
                            permit.release(ReservationOutcome.ABORTED)
                            return checked
                    input_path = Path(directory) / "candidates.txt"
                    input_path.write_text(
                        "".join(host + "\n" for host in candidates), encoding="ascii"
                    )
                    result = _checked_process(
                        await self.runner.run(
                            _spec(
                                self.executable,
                                directory,
                                (
                                    *_FLAGS,
                                    "-allow",
                                    ",".join(addresses),
                                    "-r",
                                    "udp:" + self.nameserver + ":53",
                                    "-l",
                                    str(input_path),
                                ),
                                timeout,
                            )
                        ),
                        min(self._output_limit, budgets.limits.max_output_bytes),
                    )
                    if isinstance(result, Failure):
                        permit.release(
                            ReservationOutcome.TIMEOUT
                            if result.error.code == ErrorCode.TOOL_TIMEOUT
                            else ReservationOutcome.FAILED
                        )
                        return result
                    if budgets.state.remaining_seconds <= 0:
                        permit.release(ReservationOutcome.TIMEOUT)
                        return _failure(
                            ToolTimeoutError("HTTPX execution deadline reached")
                        )
                    facts, malformed = parse(
                        result.value.stdout,
                        candidates,
                        addresses,
                        policy.scope_validator,
                    )
                    output = normalize(
                        facts,
                        malformed,
                        candidates,
                        addresses,
                        self.nameserver,
                        target.value,
                        context,
                    )
                    if len(output.model_dump_json().encode()) > min(
                        self._output_limit, budgets.limits.max_output_bytes
                    ):
                        raise ValueError("normalized output exceeds bound")
                    permit.release(
                        ReservationOutcome.FAILED
                        if output.status == "partial"
                        else ReservationOutcome.COMPLETED
                    )
                    return Success[HttpProbeOutput](value=output)
            except OSError:
                permit.release(ReservationOutcome.FAILED)
                return _failure(
                    ToolExecutionError("HTTPX local execution setup failed")
                )
            except (ValueError, TypeError, AttributeError, RecursionError):
                permit.release(ReservationOutcome.FAILED)
                return _failure(ParserError("Malformed or oversized HTTPX output"))

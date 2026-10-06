"""Bulk DNS verification with trusted argv and independently scoped candidates."""

import os
import re
import shutil
from dataclasses import dataclass, field
from ipaddress import ip_address
from pathlib import Path
from tempfile import TemporaryDirectory

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
from recon_agent.tools.dnsx_models import DnsxContext, DnsxInput, DnsxOutput
from recon_agent.tools.dnsx_parser import normalize, parse

_VERSION = "1.2.2"
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
    "-retry",
    "1",
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
        args=("-auth", "false", *args),
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
                "DNSX exited unsuccessfully",
                context=ErrorContext(tool="dnsx", exit_code=process.return_code),
            )
        )
    if (
        process.stdout_truncated
        or process.stderr_truncated
        or len(process.stdout) > limit
        or len(process.stderr) > limit
    ):
        return _failure(ParserError("DNSX output is truncated or oversized"))
    return Success[ProcessExecution](value=process)


@dataclass(frozen=True, slots=True)
class DnsxAdapter(ToolAdapter):
    """Operator-only executable/resolver; detect before real AVAILABLE registration.

    The injected runner must honor the same or smaller configured stream bound.
    Resolver infrastructure needs independent numeric-IP scope membership.
    """

    executable: str = field(repr=False)
    nameserver: str = field(repr=False)
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
            ProcessSpec(executable=self.executable)
        except (ValueError, TypeError, AttributeError) as cause:
            raise ConfigurationError("Invalid trusted DNSX adapter settings") from cause
        object.__setattr__(self, "_timeout", snapshot.default_timeout_seconds)
        object.__setattr__(self, "_output_limit", snapshot.max_output_bytes)
        if self.runner is None:
            object.__setattr__(self, "runner", AsyncProcessRunner(snapshot))

    @property
    def definition(self) -> AdapterDefinition:
        return AdapterDefinition(
            adapter_id="dnsx",
            descriptor=CapabilityDescriptor(
                capability=CapabilityId.VERIFY_DNS,
                description="Verify bounded authorized hostname batches into DNS evidence",
                risk_class=RiskClass.ACTIVE_SAFE,
            ),
            input_schema=DnsxInput,
            output_schema=DnsxOutput,
            parameter_target_fields=("candidates",),
        )

    @classmethod
    async def detect(
        cls,
        config: ExecutionConfig,
        *,
        nameserver: str,
        binary: str = "dnsx",
        runner: ProcessRunner | None = None,
    ) -> OperationResult[InstanceOf["DnsxAdapter"]]:
        """Explicit local availability/version probe; no DNS queries."""
        if not isinstance(binary, str) or not binary.strip() or "\x00" in binary:
            raise ConfigurationError("Invalid trusted DNSX binary setting")
        executable = shutil.which(binary)
        if executable is None:
            return _failure(ToolUnavailableError("DNSX executable unavailable"))
        adapter = cls(str(Path(executable).absolute()), nameserver, config, runner)
        assert adapter.runner is not None
        try:
            with TemporaryDirectory(prefix="recon-dnsx-") as directory:
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
                    return _failure(ToolUnavailableError("Unsupported DNSX version"))
        except (OSError, UnicodeError, ValueError, TypeError, AttributeError):
            return _failure(ToolUnavailableError("DNSX availability check failed"))
        return Success[InstanceOf[DnsxAdapter]](value=adapter)

    async def execute(
        self,
        request: ActionRequest,
        *,
        policy: ActionPolicyValidator,
        budgets: BudgetController,
        context: DnsxContext,
    ) -> OperationResult[DnsxOutput]:
        try:
            request = ActionRequest.model_validate(request)
            context = DnsxContext.model_validate(context)
        except (ValueError, TypeError):
            return _failure(PlannerValidationError("Malformed DNSX request or context"))
        if (
            request.capability != CapabilityId.VERIFY_DNS
            or policy.budget_eligibility is not budgets
            or request.asset_id not in (None, context.asset_id)
            or self._output_limit > budgets.limits.max_output_bytes
        ):
            return _failure(
                PlannerValidationError(
                    "DNSX execution composition does not match request"
                )
            )
        selected = policy.registry.resolve(request.capability)
        if isinstance(selected, Failure):
            return selected
        if selected.value is not self:
            return _failure(
                PlannerValidationError(
                    "DNSX adapter is not the registered capability binding"
                )
            )
        approved = policy.validate(request)
        if isinstance(approved, Failure):
            return approved
        target = approved.value.scope_match.canonical_target
        if target.kind not in ("hostname", "domain"):
            return _failure(
                PlannerValidationError("DNS verification requires a hostname subject")
            )
        parameters = DnsxInput.model_validate(approved.value.parameters)
        # ActionPolicyValidator already independently validated EVERY candidate.
        # Canonicalize only these matches; never silently drop an unauthorized one.
        matches = approved.value.parameter_scope_matches
        if any(
            match.canonical_target.kind not in ("hostname", "domain")
            or "." not in match.canonical_target.value
            for match in matches
        ):
            return _failure(
                PlannerValidationError("DNSX candidates require dotted hostnames")
            )
        candidates = tuple(sorted({match.canonical_target.value for match in matches}))
        if not candidates:
            return _failure(PlannerValidationError("DNSX batch is empty"))
        endpoint = policy.scope_validator.validate(
            Target(id="dnsx-resolver", kind="ip", value=self.nameserver)
        )
        if isinstance(endpoint, Failure):
            return endpoint
        reserved = budgets.reserve(
            approved.value.model_copy(
                update={
                    "parameter_scope_matches": (*matches, endpoint.value),
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
                return _failure(ToolTimeoutError("DNSX execution deadline reached"))
            try:
                with TemporaryDirectory(prefix="recon-dnsx-") as directory:
                    # Final contact checks occur before writing ANY candidate to input.
                    for host in (*candidates, self.nameserver):
                        checked = policy.scope_validator.validate_value(host)
                        if isinstance(checked, Failure):
                            permit.release(ReservationOutcome.ABORTED)
                            return checked
                    input_path = Path(directory) / "candidates.txt"
                    input_path.write_text(
                        "".join(host + ".\n" for host in candidates), encoding="ascii"
                    )
                    result = _checked_process(
                        await self.runner.run(
                            _spec(
                                self.executable,
                                directory,
                                (
                                    *_FLAGS,
                                    "-" + parameters.record_type.lower(),
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
                            ToolTimeoutError("DNSX execution deadline reached")
                        )
                    queries, malformed = parse(
                        result.value.stdout,
                        candidates,
                        parameters.record_type,
                        self.nameserver,
                        policy.scope_validator,
                    )
                    output = normalize(
                        queries,
                        malformed,
                        candidates,
                        parameters.record_type,
                        target.value,
                        self.nameserver,
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
                    return Success[DnsxOutput](value=output)
            except OSError:
                permit.release(ReservationOutcome.FAILED)
                return _failure(ToolExecutionError("DNSX local execution setup failed"))
            except (ValueError, TypeError, AttributeError, RecursionError):
                permit.release(ReservationOutcome.FAILED)
                return _failure(ParserError("Malformed or oversized DNSX output"))

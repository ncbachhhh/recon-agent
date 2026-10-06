"""Bounded TCP CONNECT discovery over independently authorized numeric contacts."""

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
    Scope,
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
from recon_agent.execution.lifecycle import ExecutionStart, notify_execution_start
from recon_agent.policy.actions import ActionPolicyValidator
from recon_agent.policy.budgets import BudgetController
from recon_agent.policy.scope import ScopeValidator
from recon_agent.tools.base import AdapterDefinition, ToolAdapter
from recon_agent.tools.naabu_models import (
    ContactBinding,
    NaabuContext,
    NaabuInput,
    NaabuSettings,
    PortDiscoveryOutput,
)
from recon_agent.tools.naabu_parser import normalize, parse

_VERSION = "2.3.5"
_FLAGS = (
    "-silent",
    "-nc",
    "-duc",
    "-json",
    "-stream",
    "-no-stdin",
    "-s",
    "c",
    "-Pn",
    "-iv",
    "4,6",
    "-c",
    "1",
    "-rate",
    "1",
    "-retries",
    "1",
    "-timeout",
    "1s",
    "-warm-up-time",
    "0",
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
                "Naabu exited unsuccessfully",
                context=ErrorContext(tool="naabu", exit_code=process.return_code),
            )
        )
    if (
        process.stdout_truncated
        or process.stderr_truncated
        or len(process.stdout) > limit
        or len(process.stderr) > limit
    ):
        return _failure(ParserError("Naabu output is truncated or oversized"))
    return Success[ProcessExecution](value=process)


@dataclass(frozen=True, slots=True)
class NaabuAdapter(ToolAdapter):
    """Trusted immutable finite ranges/bindings; detect before AVAILABLE registration.

    Injected runners must honor the same or smaller configured stream bound.
    Names never enter Naabu input; operator address assertions do not grant scope.
    """

    executable: str = field(repr=False)
    config: ExecutionConfig = field(repr=False)
    settings: NaabuSettings = field(default_factory=NaabuSettings, repr=False)
    runner: ProcessRunner | None = field(default=None, repr=False)
    _timeout: float = field(init=False, repr=False)
    _output_limit: int = field(init=False, repr=False)

    def __post_init__(self) -> None:
        try:
            snapshot = ExecutionConfig.model_validate(self.config.model_dump())
            settings = NaabuSettings.model_validate(self.settings.model_dump())
            if (
                not isinstance(self.executable, str)
                or not Path(self.executable).is_absolute()
            ):
                raise ValueError("absolute executable required")
            for binding in settings.bindings:
                # Centralized syntax canonicalization only; execution uses REAL scope.
                root = Target(id="binding", kind="hostname", value=binding.hostname)
                checked = ScopeValidator(Scope(id="syntax", roots=(root,))).validate(
                    root
                )
                if (
                    isinstance(checked, Failure)
                    or checked.value.canonical_target.value != binding.hostname
                ):
                    raise ValueError("canonical hostname binding required")
                for address in binding.addresses:
                    numeric = ip_address(address)
                    if str(numeric) != address or "%" in address:
                        raise ValueError("canonical numeric binding required")
            ProcessSpec(executable=self.executable)
        except (ValueError, TypeError, AttributeError) as cause:
            raise ConfigurationError(
                "Invalid trusted Naabu adapter settings"
            ) from cause
        object.__setattr__(self, "settings", settings)
        object.__setattr__(self, "_timeout", snapshot.default_timeout_seconds)
        object.__setattr__(self, "_output_limit", snapshot.max_output_bytes)
        if self.runner is None:
            object.__setattr__(self, "runner", AsyncProcessRunner(snapshot))

    @property
    def definition(self) -> AdapterDefinition:
        return AdapterDefinition(
            adapter_id="naabu",
            descriptor=CapabilityDescriptor(
                capability=CapabilityId.DISCOVER_PORTS,
                description="Discover bounded open TCP ports on authorized numeric contacts",
                risk_class=RiskClass.ACTIVE_SAFE,
            ),
            input_schema=NaabuInput,
            output_schema=PortDiscoveryOutput,
            parameter_target_fields=("candidates",),
        )

    @classmethod
    async def detect(
        cls,
        config: ExecutionConfig,
        *,
        settings: NaabuSettings | None = None,
        binary: str = "naabu",
        runner: ProcessRunner | None = None,
    ) -> OperationResult[InstanceOf["NaabuAdapter"]]:
        """Explicit isolated local version check; no target probing or DNS queries."""
        if not isinstance(binary, str) or not binary.strip() or "\x00" in binary:
            raise ConfigurationError("Invalid trusted Naabu binary setting")
        executable = shutil.which(binary)
        if executable is None:
            return _failure(ToolUnavailableError("Naabu executable unavailable"))
        adapter = cls(
            str(Path(executable).absolute()),
            config,
            settings or NaabuSettings(),
            runner,
        )
        assert adapter.runner is not None
        try:
            with TemporaryDirectory(prefix="recon-naabu-") as directory:
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
                    return _failure(ToolUnavailableError("Unsupported Naabu version"))
        except (OSError, UnicodeError, ValueError, TypeError, AttributeError):
            return _failure(ToolUnavailableError("Naabu availability check failed"))
        return Success[InstanceOf[NaabuAdapter]](value=adapter)

    async def execute(
        self,
        request: ActionRequest,
        *,
        policy: ActionPolicyValidator,
        budgets: BudgetController,
        context: NaabuContext,
        on_started: ExecutionStart | None = None,
    ) -> OperationResult[PortDiscoveryOutput]:
        try:
            request = ActionRequest.model_validate(request)
            context = NaabuContext.model_validate(context)
        except (ValueError, TypeError):
            return _failure(
                PlannerValidationError("Malformed Naabu request or context")
            )
        if (
            request.capability != CapabilityId.DISCOVER_PORTS
            or policy.budget_eligibility is not budgets
            or request.asset_id not in (None, context.asset_id)
            or self._output_limit > budgets.limits.max_output_bytes
        ):
            return _failure(
                PlannerValidationError(
                    "Naabu execution composition does not match request"
                )
            )
        selected = policy.registry.resolve(request.capability)
        if isinstance(selected, Failure):
            return selected
        if selected.value is not self:
            return _failure(
                PlannerValidationError(
                    "Naabu adapter is not the registered capability binding"
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
        if target.kind not in ("hostname", "domain", "ip") or any(
            m.canonical_target.kind not in ("hostname", "domain", "ip") for m in matches
        ):
            return _failure(
                PlannerValidationError("Port discovery requires a hostname or IP")
            )
        candidates = tuple(sorted({m.canonical_target.value for m in matches}))
        configured = {b.hostname: b.addresses for b in self.settings.bindings}
        bindings = []
        infrastructure = []
        for candidate in candidates:
            try:
                numeric = str(ip_address(candidate))
                contact: tuple[str, ...] = (numeric,)
            except ValueError:
                contact = configured.get(candidate, ())
            if not contact:
                return _failure(
                    PlannerValidationError("Hostname has no operator contact binding")
                )
            contact = tuple(sorted(set(contact)))
            for address in contact:
                checked = policy.scope_validator.validate(
                    Target(id="naabu-contact", kind="ip", value=address)
                )
                if isinstance(checked, Failure):
                    return checked
                infrastructure.append(checked.value)
            bindings.append(ContactBinding(hostname=candidate, addresses=contact))
        addresses = tuple(sorted({a for b in bindings for a in b.addresses}))
        ports = self.settings.ports
        if len(addresses) > 64 or len(addresses) * len(ports) > 4096:
            return _failure(
                PlannerValidationError("Port discovery exceeds contact or probe bound")
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
            started = notify_execution_start(on_started)
            if isinstance(started, Failure):
                permit.release(ReservationOutcome.ABORTED)
                return started
            timeout = min(self._timeout, budgets.state.remaining_seconds)
            if timeout <= 0:
                permit.release(ReservationOutcome.TIMEOUT)
                return _failure(ToolTimeoutError("Naabu execution deadline reached"))
            try:
                with TemporaryDirectory(prefix="recon-naabu-") as directory:
                    # Final contact checks occur before writing ANY candidate to input.
                    for host in (target.value, *candidates, *addresses):
                        checked = policy.scope_validator.validate_value(host)
                        if isinstance(checked, Failure):
                            permit.release(ReservationOutcome.ABORTED)
                            return checked
                    input_path = Path(directory) / "candidates.txt"
                    input_path.write_text(
                        "".join(host + "\n" for host in addresses), encoding="ascii"
                    )
                    result = _checked_process(
                        await self.runner.run(
                            _spec(
                                self.executable,
                                directory,
                                (
                                    *_FLAGS,
                                    "-p",
                                    ",".join(str(port) for port in ports),
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
                            ToolTimeoutError("Naabu execution deadline reached")
                        )
                    facts, malformed = parse(
                        result.value.stdout,
                        addresses,
                        ports,
                    )
                    output = normalize(
                        facts,
                        malformed,
                        candidates,
                        tuple(bindings),
                        addresses,
                        ports,
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
                    return Success[PortDiscoveryOutput](value=output)
            except OSError:
                permit.release(ReservationOutcome.FAILED)
                return _failure(
                    ToolExecutionError("Naabu local execution setup failed")
                )
            except (ValueError, TypeError, AttributeError, RecursionError):
                permit.release(ReservationOutcome.FAILED)
                return _failure(ParserError("Malformed or oversized Naabu output"))

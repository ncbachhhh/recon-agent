"""Bounded TLS inspection with pinned numeric contacts and authorized SNI only."""

import os
import re
import shutil
import sys
from dataclasses import dataclass, field
from ipaddress import ip_address
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import urlsplit

from pydantic import InstanceOf, JsonValue

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
from recon_agent.domain import ActionRequest, Scope, Target
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
from recon_agent.tools.tlsx_models import (
    TlsInspectionOutput,
    TlsxContact,
    TlsxContext,
    TlsxInput,
    TlsxSettings,
)
from recon_agent.tools.tlsx_parser import normalize, parse

_VERSION = "1.4.0"
_FLAGS = (
    "-silent",
    "-nc",
    "-duc",
    "-json",
    "-sm",
    "ctls",
    "-c",
    "1",
    "-retry",
    "1",
    "-timeout",
    "5",
    "-delay",
    "1s",
    "-tps",
    "-san",
    "-cn",
    "-so",
    "-tv",
    "-cipher",
    "-se",
    "-hash",
    "sha256",
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
            "PATH",
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
        args=("-config", os.devnull, *args),
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
                "TLSX exited unsuccessfully",
                context=ErrorContext(tool="tlsx", exit_code=process.return_code),
            )
        )
    if (
        process.stdout_truncated
        or process.stderr_truncated
        or len(process.stdout) > limit
        or len(process.stderr) > limit
    ):
        return _failure(ParserError("TLSX output is truncated or oversized"))
    return Success[ProcessExecution](value=process)


def _endpoint(target: Target, port: int | None) -> tuple[str, int]:
    if target.kind in ("hostname", "domain", "ip"):
        return target.value, port or 443
    if target.kind == "url":
        parts = urlsplit(target.value)
        if (
            parts.scheme != "https"
            or parts.path not in ("", "/")
            or parts.query
            or parts.fragment
            or parts.hostname is None
            or (port is not None and port != (parts.port or 443))
        ):
            raise ValueError("TLS endpoint requires unambiguous HTTPS authority")
        return parts.hostname, parts.port or 443
    raise ValueError("TLS inspection requires hostname, IP or HTTPS authority")


@dataclass(frozen=True, slots=True)
class TlsxAdapter(ToolAdapter):
    """Only successful explicit 1.4.0 detection enables bounded execution.

    Operator bindings authorize nothing. Injected runners must enforce configured
    capture/deadline/cancellation limits. Caller owns lifecycle and state ingestion.
    """

    executable: str = field(repr=False)
    config: ExecutionConfig = field(repr=False)
    settings: TlsxSettings = field(default_factory=TlsxSettings, repr=False)
    runner: ProcessRunner | None = field(default=None, repr=False)
    _verified: bool = field(init=False, default=False, repr=False)
    _timeout: float = field(init=False, repr=False)
    _output_limit: int = field(init=False, repr=False)

    def __post_init__(self) -> None:
        try:
            snapshot = ExecutionConfig.model_validate(self.config.model_dump())
            settings = TlsxSettings.model_validate(self.settings.model_dump())
            if (
                not isinstance(self.executable, str)
                or not Path(self.executable).is_absolute()
            ):
                raise ValueError("absolute executable required")
            ProcessSpec(executable=self.executable)
            for binding in settings.bindings:
                root = Target(id="binding", kind="hostname", value=binding.hostname)
                checked = ScopeValidator(Scope(id="syntax", roots=(root,))).validate(
                    root
                )
                if (
                    isinstance(checked, Failure)
                    or checked.value.canonical_target.value != binding.hostname
                ):
                    raise ValueError("canonical hostname required")
                for address in binding.addresses:
                    if str(ip_address(address)) != address or "%" in address:
                        raise ValueError("canonical numeric binding required")
        except (ValueError, TypeError, AttributeError) as cause:
            raise ConfigurationError("Invalid trusted TLSX adapter settings") from cause
        object.__setattr__(self, "settings", settings)
        object.__setattr__(self, "_timeout", snapshot.default_timeout_seconds)
        object.__setattr__(self, "_output_limit", snapshot.max_output_bytes)
        if self.runner is None:
            object.__setattr__(self, "runner", AsyncProcessRunner(snapshot))

    @property
    def definition(self) -> AdapterDefinition:
        return AdapterDefinition(
            adapter_id="tlsx",
            descriptor=CapabilityDescriptor(
                capability=CapabilityId.INSPECT_TLS,
                description="Inspect bounded TLS/certificate metadata on authorized endpoints",
                risk_class=RiskClass.ACTIVE_SAFE,
            ),
            input_schema=TlsxInput,
            output_schema=TlsInspectionOutput,
            parameter_target_fields=("candidates",),
        )

    @classmethod
    async def detect(
        cls,
        config: ExecutionConfig,
        *,
        settings: TlsxSettings | None = None,
        binary: str = "tlsx",
        runner: ProcessRunner | None = None,
    ) -> OperationResult[InstanceOf["TlsxAdapter"]]:
        """Bounded isolated local version probe; never installs or contacts targets."""
        if not isinstance(binary, str) or not binary.strip() or "\x00" in binary:
            raise ConfigurationError("Invalid trusted TLSX binary setting")
        if sys.platform != "linux":
            return _failure(
                ToolUnavailableError("TLSX containment profile requires Linux")
            )
        executable = shutil.which(binary)
        if executable is None:
            return _failure(ToolUnavailableError("TLSX executable unavailable"))
        adapter = cls(
            str(Path(executable).absolute()), config, settings or TlsxSettings(), runner
        )
        assert adapter.runner is not None
        try:
            with TemporaryDirectory(prefix="recon-tlsx-") as directory:
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
                    r"Current version:[ \t]*v?([0-9]+\.[0-9]+\.[0-9]+)[ \t]*$",
                    text,
                    re.MULTILINE,
                )
                if versions != [_VERSION]:
                    return _failure(ToolUnavailableError("Unsupported TLSX version"))
        except (OSError, UnicodeError, ValueError, TypeError, AttributeError):
            return _failure(ToolUnavailableError("TLSX availability check failed"))
        object.__setattr__(adapter, "_verified", True)
        return Success[InstanceOf[TlsxAdapter]](value=adapter)

    async def execute(
        self,
        request: ActionRequest,
        *,
        policy: ActionPolicyValidator,
        budgets: BudgetController,
        context: TlsxContext,
        on_started: ExecutionStart | None = None,
    ) -> OperationResult[TlsInspectionOutput]:
        try:
            request = ActionRequest.model_validate(request)
            context = TlsxContext.model_validate(context)
        except (ValueError, TypeError):
            return _failure(PlannerValidationError("Malformed TLSX request or context"))
        if (
            request.capability != CapabilityId.INSPECT_TLS
            or policy.budget_eligibility is not budgets
            or request.asset_id not in (None, context.asset_id)
            or self._output_limit > budgets.limits.max_output_bytes
        ):
            return _failure(
                PlannerValidationError(
                    "TLSX execution composition does not match request"
                )
            )
        selected = policy.registry.resolve(request.capability)
        if isinstance(selected, Failure):
            return selected
        if selected.value is not self:
            return _failure(
                PlannerValidationError(
                    "TLSX adapter is not the registered capability binding"
                )
            )
        if not self._verified:
            return _failure(ToolUnavailableError("TLSX version has not been verified"))
        approved = policy.validate(request)
        if isinstance(approved, Failure):
            return approved
        target = approved.value.scope_match.canonical_target
        matches = approved.value.parameter_scope_matches or (
            approved.value.scope_match,
        )
        parameters = TlsxInput.model_validate(approved.value.parameters)
        candidates = tuple(sorted({m.canonical_target.value for m in matches}))
        configured = {b.hostname: b.addresses for b in self.settings.bindings}
        contacts: set[tuple[str, str, int]] = set()
        infrastructure = []
        try:
            # Validate the primary authority even when a batch supplies contacts.
            _endpoint(target, parameters.port)
            for match in matches:
                host, port = _endpoint(match.canonical_target, parameters.port)
                if port not in self.settings.ports:
                    raise ValueError("TLS port is not operator-approved")
                try:
                    addresses: tuple[str, ...] = (str(ip_address(host)),)
                except ValueError:
                    addresses = configured.get(host, ())
                if not addresses:
                    raise ValueError("hostname has no operator numeric binding")
                for address in sorted(set(addresses)):
                    checked = policy.scope_validator.validate(
                        Target(id="tlsx-contact", kind="ip", value=address)
                    )
                    if isinstance(checked, Failure):
                        return checked
                    infrastructure.append(checked.value)
                    contacts.add((host, address, port))
            if len(contacts) > 64:
                raise ValueError("TLS contact count bound")
        except (ValueError, TypeError, AttributeError):
            return _failure(
                PlannerValidationError("Unsupported or unbound TLS endpoint/port")
            )
        ordered = tuple(
            TlsxContact(host=h, address=a, port=p) for h, a, p in sorted(contacts)
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
            remaining = budgets.state.remaining_seconds
            deadline = min(self._timeout, remaining)
            if deadline <= 0:
                permit.release(ReservationOutcome.TIMEOUT)
                return _failure(ToolTimeoutError("TLSX execution deadline reached"))
            facts: list[dict[str, JsonValue]] = []
            malformed = 0
            stdout_size = stderr_size = 0
            try:
                with TemporaryDirectory(prefix="recon-tlsx-") as directory:
                    # Complete batch checks precede ALL files and executions.
                    for value in (
                        target.value,
                        *candidates,
                        *(c.address for c in ordered),
                    ):
                        checked = policy.scope_validator.validate_value(value)
                        if isinstance(checked, Failure):
                            permit.release(ReservationOutcome.ABORTED)
                            return checked
                    groups: dict[str, list[TlsxContact]] = {}
                    for contact in ordered:
                        sni = "" if contact.host == contact.address else contact.host
                        groups.setdefault(sni, []).append(contact)
                    for index, (sni, group) in enumerate(sorted(groups.items())):
                        elapsed = remaining - budgets.state.remaining_seconds
                        timeout = min(
                            deadline - elapsed, budgets.state.remaining_seconds
                        )
                        if timeout <= 0:
                            permit.release(ReservationOutcome.TIMEOUT)
                            return _failure(
                                ToolTimeoutError("TLSX execution deadline reached")
                            )
                        # Revalidate before each process, not merely before a prior group.
                        for value in (
                            target.value,
                            *candidates,
                            *(c.address for c in group),
                        ):
                            checked = policy.scope_validator.validate_value(value)
                            if isinstance(checked, Failure):
                                permit.release(ReservationOutcome.ABORTED)
                                return checked
                        input_path = Path(directory) / f"contacts-{index}.txt"
                        input_path.write_text(
                            "".join(
                                f"{'[' + c.address + ']' if ':' in c.address else c.address}:{c.port}\n"
                                for c in group
                            ),
                            encoding="ascii",
                        )
                        args: tuple[str, ...] = (*_FLAGS, "-l", str(input_path))
                        if sni:
                            sni_path = Path(directory) / f"sni-{index}.txt"
                            sni_path.write_text(sni + "\n", encoding="ascii")
                            args += ("-sni", str(sni_path))
                        result = _checked_process(
                            await self.runner.run(
                                _spec(
                                    self.executable,
                                    directory,
                                    args,
                                    timeout,
                                )
                            ),
                            self._output_limit,
                        )
                        if isinstance(result, Failure):
                            permit.release(
                                ReservationOutcome.TIMEOUT
                                if result.error.code == ErrorCode.TOOL_TIMEOUT
                                else ReservationOutcome.FAILED
                            )
                            return result
                        stdout_size += len(result.value.stdout)
                        stderr_size += len(result.value.stderr)
                        if max(stdout_size, stderr_size) > self._output_limit:
                            raise ValueError("aggregate capture bound")
                        if remaining - budgets.state.remaining_seconds >= deadline:
                            permit.release(ReservationOutcome.TIMEOUT)
                            return _failure(
                                ToolTimeoutError("TLSX execution deadline reached")
                            )
                        parsed, invalid = parse(
                            result.value.stdout, tuple(group), context
                        )
                        facts.extend(parsed)
                        malformed += invalid
                    output = normalize(
                        tuple(facts),
                        malformed,
                        ordered,
                        candidates,
                        target.value,
                        context,
                    )
                    if len(output.model_dump_json().encode()) > self._output_limit:
                        raise ValueError("normalized output bound")
                    if remaining - budgets.state.remaining_seconds >= deadline:
                        permit.release(ReservationOutcome.TIMEOUT)
                        return _failure(
                            ToolTimeoutError("TLSX execution deadline reached")
                        )
                    permit.release(
                        ReservationOutcome.FAILED
                        if output.status == "partial"
                        else ReservationOutcome.COMPLETED
                    )
                    return Success[TlsInspectionOutput](value=output)
            except OSError:
                permit.release(ReservationOutcome.FAILED)
                return _failure(ToolExecutionError("TLSX local execution setup failed"))
            except (ValueError, TypeError, AttributeError, RecursionError):
                permit.release(ReservationOutcome.FAILED)
                return _failure(ParserError("Malformed or oversized TLSX output"))

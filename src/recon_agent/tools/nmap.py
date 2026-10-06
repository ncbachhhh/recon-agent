"""Bounded native Nmap service detection; supported binary must exclude NSE."""

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
    ScopeRejectedError,
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
from recon_agent.tools.nmap_models import (
    DiscoveredPortSelection,
    NmapContext,
    NmapInput,
    NmapSettings,
    ServiceFingerprintOutput,
)
from recon_agent.tools.nmap_parser import normalize, parse

_VERSION = "7.95"
_FLAGS = (
    "--unprivileged",
    "-sT",
    "-sV",
    "--version-intensity",
    "2",
    "-Pn",
    "-n",
    "--disable-arp-ping",
    "--max-parallelism",
    "1",
    "--scan-delay",
    "1s",
    "--max-rate",
    "1",
    "--max-retries",
    "0",
    "-oX",
    "-",
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
        args=args,
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
                "Nmap exited unsuccessfully",
                context=ErrorContext(tool="nmap", exit_code=process.return_code),
            )
        )
    if (
        process.stdout_truncated
        or process.stderr_truncated
        or len(process.stdout) > limit
        or len(process.stderr) > limit
    ):
        return _failure(ParserError("Nmap output is truncated or oversized"))
    return Success[ProcessExecution](value=process)


@dataclass(frozen=True, slots=True)
class NmapAdapter(ToolAdapter):
    """Trusted discovery selections; detect a no-Lua build before AVAILABLE registration.

    Direct construction is inert; only successful detection enables execution.
    Injected runners must honor configured capture/deadline/cancellation limits.
    """

    executable: str = field(repr=False)
    config: ExecutionConfig = field(repr=False)
    settings: NmapSettings = field(repr=False)
    runner: ProcessRunner | None = field(default=None, repr=False)
    _verified: bool = field(init=False, default=False, repr=False)
    _timeout: float = field(init=False, repr=False)
    _output_limit: int = field(init=False, repr=False)

    def __post_init__(self) -> None:
        try:
            snapshot = ExecutionConfig.model_validate(self.config.model_dump())
            settings = NmapSettings.model_validate(self.settings.model_dump())
            if (
                not isinstance(self.executable, str)
                or not Path(self.executable).is_absolute()
            ):
                raise ValueError("absolute executable required")
            if not Path(settings.data_directory).is_absolute():
                raise ValueError("absolute data directory required")
            for selection in settings.selections:
                checked = ScopeValidator(
                    Scope(
                        id="syntax",
                        allow_private_ips=True,
                        roots=(
                            Target(id="selection", kind="ip", value=selection.address),
                        ),
                    )
                ).validate_value(selection.address)
                if (
                    isinstance(checked, Failure)
                    or checked.value.canonical_target.value != selection.address
                ):
                    raise ValueError("canonical numeric discovery selection required")
                if selection.hostname is not None:
                    root = Target(
                        id="binding", kind="hostname", value=selection.hostname
                    )
                    checked = ScopeValidator(
                        Scope(id="syntax", roots=(root,))
                    ).validate(root)
                    if (
                        isinstance(checked, Failure)
                        or checked.value.canonical_target.value != selection.hostname
                    ):
                        raise ValueError("canonical hostname binding required")
            ProcessSpec(executable=self.executable)
        except (ValueError, TypeError, AttributeError, ScopeRejectedError) as cause:
            raise ConfigurationError("Invalid trusted Nmap adapter settings") from cause
        object.__setattr__(self, "settings", settings)
        object.__setattr__(self, "_timeout", snapshot.default_timeout_seconds)
        object.__setattr__(self, "_output_limit", snapshot.max_output_bytes)
        if self.runner is None:
            object.__setattr__(self, "runner", AsyncProcessRunner(snapshot))

    def with_selections(
        self, selections: tuple[DiscoveredPortSelection, ...]
    ) -> "NmapAdapter":
        """Trusted workflow snapshot; retain detection for the same installation.

        Does not authorize selections, alter this adapter, or probe the binary.
        Execution still checks policy, independent scope and selected port subsets.
        """
        adapter = NmapAdapter(
            self.executable,
            self.config.model_copy(
                update={
                    "default_timeout_seconds": self._timeout,
                    "max_output_bytes": self._output_limit,
                }
            ),
            NmapSettings(
                data_directory=self.settings.data_directory, selections=selections
            ),
            self.runner,
        )
        object.__setattr__(adapter, "_verified", self._verified)
        return adapter

    @property
    def definition(self) -> AdapterDefinition:
        return AdapterDefinition(
            adapter_id="nmap",
            descriptor=CapabilityDescriptor(
                capability=CapabilityId.FINGERPRINT_SERVICES,
                description="Fingerprint selected approved TCP services on authorized contacts",
                risk_class=RiskClass.ACTIVE_SAFE,
            ),
            input_schema=NmapInput,
            output_schema=ServiceFingerprintOutput,
            parameter_target_fields=(),
        )

    @classmethod
    async def detect(
        cls,
        config: ExecutionConfig,
        *,
        settings: NmapSettings,
        binary: str = "nmap",
        runner: ProcessRunner | None = None,
    ) -> OperationResult[InstanceOf["NmapAdapter"]]:
        """Explicit isolated local version check; no target probing or DNS queries."""
        if not isinstance(binary, str) or not binary.strip() or "\x00" in binary:
            raise ConfigurationError("Invalid trusted Nmap binary setting")
        executable = shutil.which(binary)
        if executable is None:
            return _failure(ToolUnavailableError("Nmap executable unavailable"))
        adapter = cls(
            str(Path(executable).absolute()),
            config,
            settings,
            runner,
        )
        assert adapter.runner is not None
        try:
            with TemporaryDirectory(prefix="recon-nmap-") as directory:
                result = _checked_process(
                    await adapter.runner.run(
                        _spec(
                            adapter.executable,
                            directory,
                            ("--version",),
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
                    r"^Nmap version ([0-9]+\.[0-9]+) \( https://nmap.org \)$",
                    text,
                    re.MULTILINE,
                )
                without = re.findall(r"^Compiled without:(.*)$", text, re.MULTILINE)
                with_features = re.findall(r"^Compiled with:(.*)$", text, re.MULTILINE)
                if (
                    versions != [_VERSION]
                    or len(without) != 1
                    or "liblua" not in without[0].split()
                    or len(with_features) != 1
                    or "lua" in with_features[0].lower()
                ):
                    return _failure(
                        ToolUnavailableError(
                            "Unsupported Nmap version or NSE-enabled build"
                        )
                    )
        except (OSError, UnicodeError, ValueError, TypeError, AttributeError):
            return _failure(ToolUnavailableError("Nmap availability check failed"))
        object.__setattr__(adapter, "_verified", True)
        return Success[InstanceOf[NmapAdapter]](value=adapter)

    async def execute(
        self,
        request: ActionRequest,
        *,
        policy: ActionPolicyValidator,
        budgets: BudgetController,
        context: NmapContext,
        on_started: ExecutionStart | None = None,
    ) -> OperationResult[ServiceFingerprintOutput]:
        if not self._verified:
            return _failure(
                ToolUnavailableError("Nmap no-NSE availability is not verified")
            )
        try:
            request = ActionRequest.model_validate(request)
            context = NmapContext.model_validate(context)
        except (ValueError, TypeError):
            return _failure(PlannerValidationError("Malformed Nmap request or context"))
        if (
            request.capability != CapabilityId.FINGERPRINT_SERVICES
            or policy.budget_eligibility is not budgets
            or request.asset_id not in (None, context.asset_id)
            or self._output_limit > budgets.limits.max_output_bytes
        ):
            return _failure(
                PlannerValidationError(
                    "Nmap execution composition does not match request"
                )
            )
        selected = policy.registry.resolve(request.capability)
        if isinstance(selected, Failure):
            return selected
        if selected.value is not self:
            return _failure(
                PlannerValidationError(
                    "Nmap adapter is not the registered capability binding"
                )
            )
        approved = policy.validate(request)
        if isinstance(approved, Failure):
            return approved
        target = approved.value.scope_match.canonical_target
        if target.kind not in ("hostname", "domain", "ip"):
            return _failure(
                PlannerValidationError("Fingerprinting requires a hostname or IP")
            )
        parameters = NmapInput.model_validate(approved.value.parameters)
        ports = tuple(sorted(set(parameters.ports)))
        selections = tuple(
            s
            for s in self.settings.selections
            if target.value == (s.hostname if s.hostname is not None else s.address)
        )
        if len(selections) != 1 or not set(ports) <= set(selections[0].ports):
            return _failure(
                PlannerValidationError("Ports lack a trusted discovery selection")
            )
        address = selections[0].address
        contact = policy.scope_validator.validate(
            Target(id="nmap-contact", kind="ip", value=address)
        )
        if isinstance(contact, Failure):
            return contact
        reserved = budgets.reserve(
            approved.value.model_copy(
                update={
                    "parameter_scope_matches": (contact.value,),
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
                return _failure(ToolTimeoutError("Nmap execution deadline reached"))
            try:
                with TemporaryDirectory(prefix="recon-nmap-") as directory:
                    # Revalidate both the logical subject and exact numeric contact.
                    for host in (target.value, address):
                        checked = policy.scope_validator.validate_value(host)
                        if isinstance(checked, Failure):
                            permit.release(ReservationOutcome.ABORTED)
                            return checked
                    result = _checked_process(
                        await self.runner.run(
                            _spec(
                                self.executable,
                                directory,
                                (
                                    *_FLAGS,
                                    "-p",
                                    ",".join(str(port) for port in ports),
                                    "--datadir",
                                    self.settings.data_directory,
                                    "--versiondb",
                                    str(
                                        Path(self.settings.data_directory)
                                        / "nmap-service-probes"
                                    ),
                                    "--servicedb",
                                    str(
                                        Path(self.settings.data_directory)
                                        / "nmap-services"
                                    ),
                                    *(
                                        ("-6",)
                                        if ip_address(address).version == 6
                                        else ()
                                    ),
                                    address,
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
                            ToolTimeoutError("Nmap execution deadline reached")
                        )
                    facts, unreported = parse(result.value.stdout, address, ports)
                    output = normalize(
                        facts,
                        unreported,
                        address,
                        ports,
                        target.value,
                        context,
                        selections[0].evidence_ids,
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
                    return Success[ServiceFingerprintOutput](value=output)
            except OSError:
                permit.release(ReservationOutcome.FAILED)
                return _failure(ToolExecutionError("Nmap local execution setup failed"))
            except (ValueError, TypeError, AttributeError, RecursionError):
                permit.release(ReservationOutcome.FAILED)
                return _failure(ParserError("Malformed or oversized Nmap output"))

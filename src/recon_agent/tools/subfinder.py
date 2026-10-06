"""Passive enumeration with trusted argv, isolated settings and current policy."""

import json
import os
import re
import shutil
from dataclasses import dataclass, field
from hashlib import sha256
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
    Asset,
    Evidence,
    Observation,
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
from recon_agent.policy.actions import ActionPolicyValidator
from recon_agent.policy.budgets import BudgetController
from recon_agent.policy.scope import ScopeValidator
from recon_agent.tools.base import AdapterDefinition, ToolAdapter
from recon_agent.tools.subfinder_models import (
    SubdomainOutput,
    SubfinderContext,
    SubfinderInput,
    SubfinderLine,
)

_VERSION = "2.9.0"
# Reviewed upstream flags/JSONL/source behavior. No source selection by planner.
_FLAGS = (
    "-silent",
    "-nc",
    "-duc",
    "-json",
    "-cs",
    "-s",
    "hackertarget",
    "-rl",
    "1",
    "-rls",
    "hackertarget=1/s",
    "-t",
    "1",
    "-timeout",
    "10",
    "-max-time",
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
        for key in ("HOME", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "XDG_CONFIG_HOME")
    )
    if "SystemRoot" in os.environ:
        environment += (("SystemRoot", os.environ["SystemRoot"]),)
    return ProcessSpec(
        executable=executable,
        args=("-config", os.devnull, "-pc", os.devnull, *args),
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
                "Subfinder exited unsuccessfully",
                context=ErrorContext(tool="subfinder", exit_code=process.return_code),
            )
        )
    if (
        process.stdout_truncated
        or process.stderr_truncated
        or len(process.stdout) > limit
        or len(process.stderr) > limit
    ):
        return _failure(ParserError("Subfinder output is truncated or oversized"))
    return Success[ProcessExecution](value=process)


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _hosts(raw: bytes, root: str) -> tuple[str, ...]:
    # Reuse centralized syntax/canonicalization and label membership. This local
    # parser-only declaration is NEVER the operational scope or future authority.
    syntax = ScopeValidator(
        Scope(
            id="subfinder-parser",
            roots=(Target(id="query", kind="domain", value=root),),
            allow_subdomains=True,
        )
    )
    hosts: set[str] = set()
    lines = raw.decode("utf-8").splitlines()
    if len(lines) > 4096:
        raise ValueError("too many output lines")
    for line in lines:
        if not line.strip():
            continue
        if len(line) > 2048:
            raise ValueError("oversized output line")
        record = SubfinderLine.model_validate(
            json.loads(line, object_pairs_hook=_unique_object)
        )
        original = syntax.validate_value(record.input)
        candidate = syntax.validate_value(record.host)
        if (
            isinstance(original, Failure)
            or isinstance(candidate, Failure)
            or original.value.canonical_target.kind != "hostname"
            or candidate.value.canonical_target.kind != "hostname"
            or original.value.canonical_target.value != root
        ):
            raise ValueError("invalid output name or input")
        host = candidate.value.canonical_target.value
        if host == root:
            raise ValueError("root is not a discovered subdomain")
        hosts.add(host)
        if len(hosts) > 1024:
            raise ValueError("too many discovered hosts")
    return tuple(sorted(hosts))


def _normalize(
    hosts: tuple[str, ...], root: str, context: SubfinderContext
) -> SubdomainOutput:
    # Snapshot is returned alongside its memory reference. No raw output/credentials
    # or decorative diagnostics escape into observations or error messages.
    snapshot = json.dumps(
        {
            "query_target": root,
            "source_version": _VERSION,
            "provider_sources": ["hackertarget"],
            "hosts": list(hosts),
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    evidence_id = f"{context.execution_id}:subfinder:evidence"
    evidence = Evidence(
        id=evidence_id,
        source="subfinder",
        capability="enumerate_subdomains",
        origin=root,
        artifact_reference=f"memory:{context.execution_id}",
        locator="discovery",
        collected_at=context.collected_at,
        execution_id=context.execution_id,
        sha256=sha256(snapshot.encode()).hexdigest(),
    )
    observations = tuple(
        Observation(
            id=f"{context.execution_id}:subfinder:observation:{index}",
            kind="metadata",
            asset_id=context.asset_id,
            source="subfinder",
            observed_at=context.collected_at,
            execution_id=context.execution_id,
            evidence_ids=(evidence_id,),
            data={
                "query_target": root,
                "hostname": host,
                "status": "discovered",
                "capability": "enumerate_subdomains",
                "source_version": _VERSION,
                "provider_sources": ["hackertarget"],
            },
        )
        for index, host in enumerate(hosts)
    )
    return SubdomainOutput(
        query_target=root,
        hosts=hosts,
        asset=Asset(
            id=context.asset_id,
            kind="host",
            value=root,
            observation_ids=tuple(item.id for item in observations),
        ),
        observations=observations,
        evidence=(evidence,),
    )


@dataclass(frozen=True, slots=True)
class SubfinderAdapter(ToolAdapter):
    """Trusted operator composition. Call detect before AVAILABLE registration.

    Explicit composition opts into sending authorized roots to HackerTarget's
    passive hostsearch API. No active resolution, default/all sources or secrets.
    An injected runner must enforce the supplied config's same/smaller stream cap.
    """

    executable: str = field(repr=False)
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
            ProcessSpec(executable=self.executable)
        except (ValueError, TypeError, AttributeError) as cause:
            raise ConfigurationError(
                "Invalid trusted Subfinder adapter settings"
            ) from cause
        object.__setattr__(self, "_timeout", snapshot.default_timeout_seconds)
        object.__setattr__(self, "_output_limit", snapshot.max_output_bytes)
        if self.runner is None:
            object.__setattr__(self, "runner", AsyncProcessRunner(snapshot))

    @property
    def definition(self) -> AdapterDefinition:
        return AdapterDefinition(
            adapter_id="subfinder",
            descriptor=CapabilityDescriptor(
                capability=CapabilityId.ENUMERATE_SUBDOMAINS,
                description="Collect passive subdomain discovery evidence for authorized roots",
                risk_class=RiskClass.PASSIVE,
            ),
            input_schema=SubfinderInput,
            output_schema=SubdomainOutput,
            parameter_target_fields=(),
        )

    @classmethod
    async def detect(
        cls,
        config: ExecutionConfig,
        *,
        binary: str = "subfinder",
        runner: ProcessRunner | None = None,
    ) -> OperationResult[InstanceOf["SubfinderAdapter"]]:
        """Explicit local availability/version probe; no root or enumeration."""
        if not isinstance(binary, str) or not binary.strip() or "\x00" in binary:
            raise ConfigurationError("Invalid trusted Subfinder binary setting")
        executable = shutil.which(binary)
        if executable is None:
            return _failure(ToolUnavailableError("Subfinder executable unavailable"))
        adapter = cls(str(Path(executable).absolute()), config, runner)
        assert adapter.runner is not None
        try:
            with TemporaryDirectory(prefix="recon-subfinder-") as directory:
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
                    return _failure(
                        ToolUnavailableError("Unsupported Subfinder version")
                    )
        except (OSError, UnicodeError, ValueError, TypeError, AttributeError):
            return _failure(ToolUnavailableError("Subfinder availability check failed"))
        return Success[InstanceOf[SubfinderAdapter]](value=adapter)

    async def execute(
        self,
        request: ActionRequest,
        *,
        policy: ActionPolicyValidator,
        budgets: BudgetController,
        context: SubfinderContext,
    ) -> OperationResult[SubdomainOutput]:
        try:
            request = ActionRequest.model_validate(request)
            context = SubfinderContext.model_validate(context)
        except (ValueError, TypeError):
            return _failure(
                PlannerValidationError("Malformed Subfinder request or context")
            )
        if (
            request.capability != CapabilityId.ENUMERATE_SUBDOMAINS
            or policy.budget_eligibility is not budgets
            or request.asset_id not in (None, context.asset_id)
            or self._output_limit > budgets.limits.max_output_bytes
        ):
            return _failure(
                PlannerValidationError(
                    "Subfinder execution composition does not match request"
                )
            )
        selected = policy.registry.resolve(request.capability)
        if isinstance(selected, Failure):
            return selected
        if selected.value is not self:
            return _failure(
                PlannerValidationError(
                    "Subfinder adapter is not the registered capability binding"
                )
            )
        approved = policy.validate(request)
        if isinstance(approved, Failure):
            return approved
        target = approved.value.scope_match.canonical_target
        if target.kind not in ("hostname", "domain"):
            return _failure(
                PlannerValidationError("Subdomain enumeration requires a hostname root")
            )
        reserved = budgets.reserve(approved.value)
        if isinstance(reserved, Failure):
            return reserved
        assert self.runner is not None
        with reserved.value as permit:
            timeout = min(self._timeout, budgets.state.remaining_seconds)
            if timeout <= 0:
                permit.release(ReservationOutcome.TIMEOUT)
                return _failure(
                    ToolTimeoutError("Subfinder execution deadline reached")
                )
            try:
                with TemporaryDirectory(prefix="recon-subfinder-") as directory:
                    result = _checked_process(
                        await self.runner.run(
                            _spec(
                                self.executable,
                                directory,
                                (*_FLAGS, "-d", target.value),
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
                            ToolTimeoutError("Subfinder execution deadline reached")
                        )
                    output = _normalize(
                        _hosts(result.value.stdout, target.value), target.value, context
                    )
                    if len(output.model_dump_json().encode()) > min(
                        self._output_limit, budgets.limits.max_output_bytes
                    ):
                        raise ValueError("normalized output exceeds bound")
                    permit.release(ReservationOutcome.COMPLETED)
                    return Success[SubdomainOutput](value=output)
            except OSError:
                permit.release(ReservationOutcome.FAILED)
                return _failure(
                    ToolExecutionError("Subfinder local execution setup failed")
                )
            except (ValueError, TypeError, AttributeError, RecursionError):
                permit.release(ReservationOutcome.FAILED)
                return _failure(ParserError("Malformed or oversized Subfinder output"))

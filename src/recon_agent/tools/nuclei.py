"""Nuclei foundation: explicit availability and a permanently denied scan gate."""

import os
import re
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory

from pydantic import InstanceOf

from recon_agent.core.config.models import ExecutionConfig
from recon_agent.core.errors import (
    ConfigurationError,
    ErrorContext,
    ParserError,
    PlannerValidationError,
    ToolExecutionError,
    ToolUnavailableError,
)
from recon_agent.core.results import Failure, OperationResult, Success
from recon_agent.domain import ActionRequest
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
from recon_agent.tools.nuclei_models import NucleiContext, NucleiInput, NucleiOutput
from recon_agent.tools.nuclei_parser import ingest


@dataclass(frozen=True, slots=True)
class NucleiProfilePolicy:
    """Restrictive interface stub. No approved catalog or override exists in T01."""

    def resolve(self, parameters: NucleiInput) -> OperationResult[ProcessSpec]:
        try:
            NucleiInput.model_validate(parameters)
        except (ValueError, TypeError):
            return Failure(
                error=PlannerValidationError(
                    "Invalid Nuclei profile input"
                ).to_error_info()
            )
        return Failure(
            error=PlannerValidationError(
                "Nuclei scanning requires an approved enforced profile; none exist"
            ).to_error_info()
        )


@dataclass(frozen=True, slots=True)
class NucleiAdapter(ToolAdapter):
    """No scan subprocess can be constructed or run, including with fake runners.

    Availability detection is a separate explicit local version probe. Captured
    fixture output can be ingested without detection or any binary installed.
    """

    executable: str = field(repr=False)
    config: ExecutionConfig = field(repr=False)
    runner: ProcessRunner | None = field(default=None, repr=False)
    _timeout: float = field(init=False, repr=False)
    _output_limit: int = field(init=False, repr=False)

    def __post_init__(self) -> None:
        try:
            config = ExecutionConfig.model_validate(self.config.model_dump())
            if (
                not isinstance(self.executable, str)
                or not Path(self.executable).is_absolute()
            ):
                raise ValueError("absolute trusted executable required")
            ProcessSpec(executable=self.executable)
        except (ValueError, TypeError, AttributeError) as cause:
            raise ConfigurationError("Invalid trusted Nuclei settings") from cause
        object.__setattr__(self, "_timeout", config.default_timeout_seconds)
        object.__setattr__(self, "_output_limit", config.max_output_bytes)
        if self.runner is None:
            object.__setattr__(self, "runner", AsyncProcessRunner(config))

    @property
    def definition(self) -> AdapterDefinition:
        return AdapterDefinition(
            adapter_id="nuclei",
            descriptor=CapabilityDescriptor(
                capability=CapabilityId.SCAN_TEMPLATES,
                description="Template detection foundation; all scan profiles disabled",
                risk_class=RiskClass.ACTIVE_SAFE,
            ),
            input_schema=NucleiInput,
            output_schema=NucleiOutput,
            parameter_target_fields=(),
        )

    def scan_spec(self, parameters: NucleiInput) -> OperationResult[ProcessSpec]:
        """No raw-argv/path overload or executable profile can bypass this stub."""
        return NucleiProfilePolicy().resolve(parameters)

    @classmethod
    async def detect(
        cls,
        config: ExecutionConfig,
        *,
        binary: str = "nuclei",
        runner: ProcessRunner | None = None,
    ) -> OperationResult[InstanceOf["NucleiAdapter"]]:
        """Opt-in local 3.4.10 probe; never registers or enables scans/templates."""
        if not isinstance(binary, str) or not binary.strip() or "\x00" in binary:
            raise ConfigurationError("Invalid trusted Nuclei binary setting")
        if sys.platform != "linux":
            return Failure(
                error=ToolUnavailableError(
                    "Nuclei probe requires Linux"
                ).to_error_info()
            )
        executable = shutil.which(binary)
        if executable is None:
            return Failure(
                error=ToolUnavailableError(
                    "Nuclei executable unavailable"
                ).to_error_info()
            )
        adapter = cls(str(Path(executable).absolute()), config, runner)
        assert adapter.runner is not None
        try:
            with TemporaryDirectory(prefix="recon-nuclei-") as directory:
                environment = tuple(
                    (key, directory)
                    for key in (
                        "PATH",
                        "HOME",
                        "XDG_CONFIG_HOME",
                        "XDG_CACHE_HOME",
                        "TMPDIR",
                    )
                )
                result = await adapter.runner.run(
                    ProcessSpec(
                        executable=adapter.executable,
                        args=("-duc", "-nc", "-config", os.devnull, "-version"),
                        timeout_seconds=min(adapter._timeout, 5.0),
                        environment=environment,
                        working_directory=directory,
                    )
                )
                if isinstance(result, Failure):
                    return result
                process = ProcessExecution.model_validate(result.value)
                if process.return_code != 0:
                    return Failure(
                        error=ToolExecutionError(
                            "Nuclei version probe failed",
                            context=ErrorContext(
                                tool="nuclei", exit_code=process.return_code
                            ),
                        ).to_error_info()
                    )
                if (
                    process.stdout_truncated
                    or process.stderr_truncated
                    or len(process.stdout) > adapter._output_limit
                    or len(process.stderr) > adapter._output_limit
                ):
                    return Failure(
                        error=ParserError(
                            "Incomplete Nuclei version output"
                        ).to_error_info()
                    )
                text = (process.stdout + b"\n" + process.stderr).decode("utf-8")
                versions = re.findall(
                    r"Nuclei Engine Version:[ \t]*v?([0-9]+\.[0-9]+\.[0-9]+)[ \t]*$",
                    text,
                    re.MULTILINE,
                )
                if versions != ["3.4.10"]:
                    return Failure(
                        error=ToolUnavailableError(
                            "Unsupported Nuclei version"
                        ).to_error_info()
                    )
        except (OSError, ValueError, TypeError, AttributeError):
            return Failure(
                error=ToolUnavailableError(
                    "Nuclei availability check failed"
                ).to_error_info()
            )
        return Success[InstanceOf[NucleiAdapter]](value=adapter)

    async def execute(
        self,
        request: ActionRequest,
        *,
        policy: ActionPolicyValidator,
        budgets: BudgetController,
        context: NucleiContext,
    ) -> OperationResult[NucleiOutput]:
        """Current registry/policy/scope checks, then denial before spending/contact."""
        try:
            request = ActionRequest.model_validate(request)
            context = NucleiContext.model_validate(context)
        except (ValueError, TypeError):
            return Failure(
                error=PlannerValidationError(
                    "Malformed Nuclei request/context"
                ).to_error_info()
            )
        if (
            request.capability != CapabilityId.SCAN_TEMPLATES
            or policy.budget_eligibility is not budgets
            or request.asset_id not in (None, context.asset_id)
        ):
            return Failure(
                error=PlannerValidationError(
                    "Nuclei composition mismatch"
                ).to_error_info()
            )
        selected = policy.registry.resolve(request.capability)
        if isinstance(selected, Failure):
            return selected
        if selected.value is not self:
            return Failure(
                error=PlannerValidationError(
                    "Nuclei adapter binding mismatch"
                ).to_error_info()
            )
        approved = policy.validate(request)
        if isinstance(approved, Failure):
            return approved
        subject = policy.scope_validator.validate_value(context.query_target)
        if isinstance(subject, Failure):
            return subject
        if (
            subject.value.canonical_target
            != approved.value.scope_match.canonical_target
        ):
            return Failure(
                error=PlannerValidationError("Nuclei subject mismatch").to_error_info()
            )
        # Even a valid policy result and declared availability cannot enable scans.
        denied = self.scan_spec(NucleiInput.model_validate(approved.value.parameters))
        if isinstance(denied, Failure):
            return denied
        return Failure(
            error=PlannerValidationError("Nuclei dispatch is disabled").to_error_info()
        )

    def ingest(
        self,
        result: OperationResult[ProcessExecution],
        *,
        context: NucleiContext,
        scope: ScopeValidator,
    ) -> OperationResult[NucleiOutput]:
        """Offline parsing only; does not call a runner, reserve or mutate state."""
        return ingest(
            result, context=context, scope=scope, output_limit=self._output_limit
        )

"""Trusted specialized FFUF virtual-host discovery on a numeric contact endpoint."""

import asyncio
import os
import re
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory
from time import monotonic
from urllib.parse import urljoin, urlsplit

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
from recon_agent.domain import ActionRequest, Target
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
from recon_agent.tools.base import AdapterDefinition, ToolAdapter
from recon_agent.tools.ffuf_models import (
    FfufContext,
    FfufInput,
    FfufSettings,
    FuzzDiscoveryOutput,
)
from recon_agent.tools.ffuf_parser import endpoint_url, normalize, parse

# Exactly one HEAD / Host test per child; no recursion, calibration, replay or body.
_FLAGS = (
    "-noninteractive",
    "-s",
    "-json",
    "-X",
    "HEAD",
    "-mc",
    "all",
    "-r=false",
    "-recursion=false",
    "-ac=false",
    "-ach=false",
    "-http2=false",
    "-ignore-body",
    "-timeout",
    "10",
    "-t",
    "1",
    "-scrapers",
    "",
)


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
        args=args,
        timeout_seconds=timeout,
        environment=environment,
        working_directory=directory,
    )


def _checked_process(
    result: OperationResult[ProcessExecution], limit: int
) -> OperationResult[ProcessExecution]:
    if isinstance(result, Failure):
        return result
    process = ProcessExecution.model_validate(result.value)
    if process.return_code != 0:
        return Failure(
            error=ToolExecutionError(
                "FFUF exited unsuccessfully",
                context=ErrorContext(tool="ffuf", exit_code=process.return_code),
            ).to_error_info()
        )
    if (
        process.stdout_truncated
        or process.stderr_truncated
        or len(process.stdout) > limit
        or len(process.stderr) > limit
    ):
        return Failure(
            error=ParserError("FFUF output is truncated or oversized").to_error_info()
        )
    return Success[ProcessExecution](value=process)


@dataclass(frozen=True, slots=True)
class FfufAdapter(ToolAdapter):
    executable: str
    config: ExecutionConfig
    settings: FfufSettings
    runner: ProcessRunner | None = field(default=None, repr=False, compare=False)
    _verified: bool = field(default=False, init=False, repr=False)

    def __post_init__(self) -> None:
        try:
            config = ExecutionConfig.model_validate(self.config)
            settings = FfufSettings.model_validate(self.settings)
            if not Path(self.executable).is_absolute() or "\x00" in self.executable:
                raise ValueError("absolute trusted executable required")
        except (ValueError, TypeError):
            raise ConfigurationError("Invalid trusted FFUF composition") from None
        object.__setattr__(self, "config", config)
        object.__setattr__(self, "settings", settings)
        if self.runner is None:
            object.__setattr__(self, "runner", AsyncProcessRunner(config))

    @property
    def definition(self) -> AdapterDefinition:
        return AdapterDefinition(
            adapter_id="ffuf",
            descriptor=CapabilityDescriptor(
                capability=CapabilityId.DISCOVER_CONTENT,
                description="Specialized vhost_names HEAD discovery on authorized numeric HTTP endpoints",
                risk_class=RiskClass.ACTIVE_SAFE,
            ),
            input_schema=FfufInput,
            output_schema=FuzzDiscoveryOutput,
            parameter_target_fields=(),
        )

    @classmethod
    async def detect(
        cls,
        config: ExecutionConfig,
        *,
        settings: FfufSettings,
        binary: str = "ffuf",
        runner: ProcessRunner | None = None,
    ) -> OperationResult[InstanceOf["FfufAdapter"]]:
        if not isinstance(binary, str) or not binary.strip() or "\x00" in binary:
            raise ConfigurationError("Invalid trusted FFUF binary setting")
        if sys.platform != "linux":
            return Failure(
                error=ToolUnavailableError(
                    "FFUF profile requires Linux"
                ).to_error_info()
            )
        executable = shutil.which(binary)
        if executable is None:
            return Failure(
                error=ToolUnavailableError(
                    "FFUF executable unavailable"
                ).to_error_info()
            )
        adapter = cls(
            str(Path(executable).absolute()),
            config,
            settings,
            runner,
        )
        assert adapter.runner is not None
        try:
            with TemporaryDirectory(prefix="recon-ffuf-") as directory:
                result = _checked_process(
                    await adapter.runner.run(
                        _spec(
                            adapter.executable,
                            directory,
                            ("-V",),
                            min(config.default_timeout_seconds, 5.0),
                        )
                    ),
                    config.max_output_bytes,
                )
                if isinstance(result, Failure):
                    return result
                text = (result.value.stdout + b"\n" + result.value.stderr).decode(
                    "utf-8"
                )
                if re.findall(
                    r"^ffuf version: ([0-9]+\.[0-9]+\.[0-9]+)[ \t]*$",
                    text,
                    re.MULTILINE,
                ) != ["2.1.0"]:
                    return Failure(
                        error=ToolUnavailableError(
                            "Unsupported FFUF version"
                        ).to_error_info()
                    )
        except (OSError, ValueError, TypeError, AttributeError, ToolUnavailableError):
            return Failure(
                error=ToolUnavailableError(
                    "FFUF availability check failed"
                ).to_error_info()
            )
        object.__setattr__(adapter, "_verified", True)
        return Success[InstanceOf[FfufAdapter]](value=adapter)

    async def execute(
        self,
        request: ActionRequest,
        *,
        policy: ActionPolicyValidator,
        budgets: BudgetController,
        context: FfufContext,
        on_started: ExecutionStart | None = None,
    ) -> OperationResult[FuzzDiscoveryOutput]:
        try:
            request = ActionRequest.model_validate(request)
            context = FfufContext.model_validate(context)
        except (ValueError, TypeError):
            return Failure(
                error=PlannerValidationError(
                    "Malformed fuzz request/context"
                ).to_error_info()
            )
        if (
            request.capability != CapabilityId.DISCOVER_CONTENT
            or policy.budget_eligibility is not budgets
            or request.asset_id not in (None, context.asset_id)
            or self.config.max_output_bytes > budgets.limits.max_output_bytes
        ):
            return Failure(
                error=PlannerValidationError(
                    "FFUF composition mismatch"
                ).to_error_info()
            )
        selected = policy.registry.resolve(request.capability)
        if isinstance(selected, Failure):
            return selected
        if selected.value is not self:
            return Failure(
                error=PlannerValidationError(
                    "FFUF registry binding mismatch"
                ).to_error_info()
            )
        if not self._verified:
            return Failure(
                error=ToolUnavailableError(
                    "FFUF version has not been verified"
                ).to_error_info()
            )
        approved = policy.validate(request)
        if isinstance(approved, Failure):
            return approved
        try:
            endpoint_url(Target(id="ffuf-input", kind="url", value=request.target))
            root = endpoint_url(approved.value.scope_match.canonical_target)
        except (ValueError, TypeError):
            return Failure(
                error=PlannerValidationError(
                    "FFUF requires a numeric HTTP(S) endpoint"
                ).to_error_info()
            )
        address = urlsplit(root).hostname
        assert address is not None
        contact = policy.scope_validator.validate_value(address)
        if isinstance(contact, Failure):
            return contact
        suffix = policy.scope_validator.validate_value(self.settings.vhost_suffix)
        if isinstance(suffix, Failure):
            return suffix
        reserved = budgets.reserve(
            approved.value.model_copy(
                update={"parameter_scope_matches": (contact.value, suffix.value)}
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
            duration = min(
                self.config.default_timeout_seconds, budgets.state.remaining_seconds
            )
            if duration <= 0:
                permit.release(ReservationOutcome.TIMEOUT)
                return Failure(
                    error=ToolTimeoutError("FFUF deadline reached").to_error_info()
                )
            deadline = monotonic() + duration
            candidates = self.settings.candidates[: self.settings.max_requests // 2]
            facts: list[dict[str, JsonValue]] = []
            malformed = stdout_size = stderr_size = 0
            interval = max(
                2 / self.settings.request_rate,
                budgets.limits.capability_rate_window_seconds
                / budgets.limits.capability_rate_actions,
            )
            try:
                async with asyncio.timeout(duration):
                    with TemporaryDirectory(prefix="recon-ffuf-") as directory:
                        for index, candidate in enumerate(candidates):
                            if index:
                                # Upstream runTask retries once without waiting on rate ticker.
                                # Reserve two attempts and pace completed candidate groups.
                                await asyncio.sleep(interval)
                            for value in (root, address, self.settings.vhost_suffix):
                                checked = policy.scope_validator.validate_value(value)
                                if isinstance(checked, Failure):
                                    permit.release(ReservationOutcome.ABORTED)
                                    return checked
                            wordlist = Path(directory) / "approved-vhost.txt"
                            wordlist.write_text(candidate + "\n", encoding="ascii")
                            remaining = min(
                                deadline - monotonic(), budgets.state.remaining_seconds
                            )
                            if remaining <= 0:
                                raise TimeoutError
                            result = _checked_process(
                                await self.runner.run(
                                    _spec(
                                        self.executable,
                                        directory,
                                        (
                                            *_FLAGS,
                                            "-rate",
                                            str(self.settings.request_rate),
                                            "-w",
                                            str(wordlist) + ":FUZZ",
                                            "-H",
                                            "Host: FUZZ",
                                            "-u",
                                            root,
                                        ),
                                        remaining,
                                    )
                                ),
                                self.config.max_output_bytes,
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
                            if (
                                max(stdout_size, stderr_size)
                                > self.config.max_output_bytes
                            ):
                                raise ValueError("aggregate output bound")
                            fact, invalid = parse(result.value.stdout, root, candidate)
                            malformed += invalid
                            if fact is not None:
                                location = fact.get("location")
                                if location is not None:
                                    checked = policy.scope_validator.validate_value(
                                        urljoin(root, str(location))
                                    )
                                    fact["redirect_scope_status"] = (
                                        "rejected"
                                        if isinstance(checked, Failure)
                                        else "allowed"
                                    )
                                facts.append(fact)
                        if malformed and not facts:
                            raise ValueError("all output malformed")
                        output = normalize(
                            tuple(
                                sorted(facts, key=lambda f: str(f["candidate_value"]))
                            ),
                            malformed,
                            root,
                            candidates,
                            self.settings.candidates,
                            context,
                        )
                        if (
                            len(output.model_dump_json().encode())
                            > self.config.max_output_bytes
                        ):
                            raise ValueError("normalized output bound")
                        if (
                            monotonic() >= deadline
                            or budgets.state.remaining_seconds <= 0
                        ):
                            raise TimeoutError
                        permit.release(
                            ReservationOutcome.FAILED
                            if output.status == "partial"
                            else ReservationOutcome.COMPLETED
                        )
                        return Success[FuzzDiscoveryOutput](value=output)
            except TimeoutError:
                permit.release(ReservationOutcome.TIMEOUT)
                return Failure(
                    error=ToolTimeoutError(
                        "FFUF discovery deadline reached"
                    ).to_error_info()
                )
            except ParserError as exc:
                permit.release(ReservationOutcome.FAILED)
                return Failure(error=exc.to_error_info())
            except OSError:
                permit.release(ReservationOutcome.FAILED)
                return Failure(
                    error=ToolExecutionError("FFUF local setup failed").to_error_info()
                )
            except (ValueError, TypeError, AttributeError, RecursionError):
                permit.release(ReservationOutcome.FAILED)
                return Failure(
                    error=ParserError(
                        "Malformed or oversized FFUF output"
                    ).to_error_info()
                )

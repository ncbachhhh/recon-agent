"""Trusted one-page Katana extraction with adapter-owned bounded numeric crawl."""

import asyncio
import json
import os
import re
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory
from time import monotonic
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
from recon_agent.domain import ActionRequest
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
from recon_agent.tools.katana_models import (
    CrawlOutput,
    KatanaContext,
    KatanaInput,
    KatanaSettings,
)
from recon_agent.tools.katana_parser import followable, normalize, numeric_url, parse

# Depth-zero plus a positive crawl duration is deliberately accepted by reviewed
# Katana 1.8.0. Every child has depth one and is output BEFORE queue/scope handling;
# only the adapter-approved GET seed reaches makeRequest. No recursive tool traffic.
_FLAGS = (
    "-silent",
    "-nc",
    "-duc",
    "-j",
    "-or",
    "-ob",
    "-dr",
    "-d",
    "0",
    "-c",
    "1",
    "-p",
    "1",
    "-rl",
    "1",
    "-retry",
    "0",
    "-timeout",
    "10",
    "-mrs",
    "16384",
    "-mdp",
    "1",
    "-fs",
    "fqdn",
    "-jc",
    "-fx",
    "-do",
    "-ndef",
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
        args=("-config", os.devnull, *args),
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
                "Katana exited unsuccessfully",
                context=ErrorContext(tool="katana", exit_code=process.return_code),
            ).to_error_info()
        )
    if (
        process.stdout_truncated
        or process.stderr_truncated
        or len(process.stdout) > limit
        or len(process.stderr) > limit
    ):
        return Failure(
            error=ParserError("Katana output is truncated or oversized").to_error_info()
        )
    return Success[ProcessExecution](value=process)


@dataclass(frozen=True, slots=True)
class KatanaAdapter(ToolAdapter):
    executable: str
    config: ExecutionConfig
    settings: KatanaSettings = field(default_factory=KatanaSettings)
    runner: ProcessRunner | None = field(default=None, repr=False, compare=False)
    _verified: bool = field(default=False, init=False, repr=False)

    def __post_init__(self) -> None:
        try:
            config = ExecutionConfig.model_validate(self.config)
            settings = KatanaSettings.model_validate(self.settings)
            if not Path(self.executable).is_absolute() or "\x00" in self.executable:
                raise ValueError("absolute trusted executable required")
        except (ValueError, TypeError):
            raise ConfigurationError("Invalid trusted Katana composition") from None
        object.__setattr__(self, "config", config)
        object.__setattr__(self, "settings", settings)
        if self.runner is None:
            object.__setattr__(self, "runner", AsyncProcessRunner(config))

    @property
    def definition(self) -> AdapterDefinition:
        return AdapterDefinition(
            adapter_id="katana",
            descriptor=CapabilityDescriptor(
                capability=CapabilityId.CRAWL_WEB,
                description="Bounded read-only crawling of authorized numeric HTTP endpoints",
                risk_class=RiskClass.ACTIVE_SAFE,
            ),
            input_schema=KatanaInput,
            output_schema=CrawlOutput,
            parameter_target_fields=(),
        )

    @classmethod
    async def detect(
        cls,
        config: ExecutionConfig,
        *,
        settings: KatanaSettings | None = None,
        binary: str = "katana",
        runner: ProcessRunner | None = None,
    ) -> OperationResult[InstanceOf["KatanaAdapter"]]:
        if not isinstance(binary, str) or not binary.strip() or "\x00" in binary:
            raise ConfigurationError("Invalid trusted Katana binary setting")
        if sys.platform != "linux":
            return Failure(
                error=ToolUnavailableError(
                    "Katana profile requires Linux"
                ).to_error_info()
            )
        executable = shutil.which(binary)
        if executable is None:
            return Failure(
                error=ToolUnavailableError(
                    "Katana executable unavailable"
                ).to_error_info()
            )
        adapter = cls(
            str(Path(executable).absolute()),
            config,
            settings or KatanaSettings(),
            runner,
        )
        assert adapter.runner is not None
        try:
            with TemporaryDirectory(prefix="recon-katana-") as directory:
                result = _checked_process(
                    await adapter.runner.run(
                        _spec(
                            adapter.executable,
                            directory,
                            ("-version", "-nc", "-duc"),
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
                    r"Current version:[ \t]*v?([0-9]+\.[0-9]+\.[0-9]+)[ \t]*$",
                    text,
                    re.MULTILINE,
                ) != ["1.8.0"]:
                    return Failure(
                        error=ToolUnavailableError(
                            "Unsupported Katana version"
                        ).to_error_info()
                    )
        except (OSError, ValueError, TypeError, AttributeError):
            return Failure(
                error=ToolUnavailableError(
                    "Katana availability check failed"
                ).to_error_info()
            )
        object.__setattr__(adapter, "_verified", True)
        return Success[InstanceOf[KatanaAdapter]](value=adapter)

    async def execute(
        self,
        request: ActionRequest,
        *,
        policy: ActionPolicyValidator,
        budgets: BudgetController,
        context: KatanaContext,
        on_started: ExecutionStart | None = None,
    ) -> OperationResult[CrawlOutput]:
        try:
            request = ActionRequest.model_validate(request)
            context = KatanaContext.model_validate(context)
        except (ValueError, TypeError):
            return Failure(
                error=PlannerValidationError(
                    "Malformed crawl request/context"
                ).to_error_info()
            )
        if (
            request.capability != CapabilityId.CRAWL_WEB
            or policy.budget_eligibility is not budgets
            or request.asset_id not in (None, context.asset_id)
            or self.config.max_output_bytes > budgets.limits.max_output_bytes
        ):
            return Failure(
                error=PlannerValidationError(
                    "Crawl composition mismatch"
                ).to_error_info()
            )
        selected = policy.registry.resolve(request.capability)
        if isinstance(selected, Failure):
            return selected
        if selected.value is not self:
            return Failure(
                error=PlannerValidationError(
                    "Crawl registry binding mismatch"
                ).to_error_info()
            )
        if not self._verified:
            return Failure(
                error=ToolUnavailableError(
                    "Katana version has not been verified"
                ).to_error_info()
            )
        approved = policy.validate(request)
        if isinstance(approved, Failure):
            return approved
        try:
            root = numeric_url(approved.value.scope_match.canonical_target)
        except (ValueError, TypeError):
            return Failure(
                error=PlannerValidationError(
                    "Crawl containment requires numeric HTTP(S) URL"
                ).to_error_info()
            )
        address = urlsplit(root).hostname
        assert address is not None
        contact = policy.scope_validator.validate_value(address)
        if isinstance(contact, Failure):
            return contact
        reserved = budgets.reserve(
            approved.value.model_copy(
                update={"parameter_scope_matches": (contact.value,)}
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
            deadline = monotonic() + duration
            facts: dict[str, dict[str, JsonValue]] = {}
            malformed = stdout_size = stderr_size = 0
            contacted: list[str] = []
            seen = {root}
            queue = [(0, root)]
            limitations: set[str] = set()
            window = budgets.limits.capability_rate_window_seconds
            interval = max(1.0, window / budgets.limits.capability_rate_actions)
            try:
                async with asyncio.timeout(duration):
                    with TemporaryDirectory(prefix="recon-katana-") as directory:
                        while queue and len(contacted) < self.settings.max_pages:
                            depth, page = queue.pop(0)
                            if contacted:
                                await asyncio.sleep(interval)
                            # Fresh URL and concrete address checks AFTER pacing, before
                            # every process; approval/discovery is never a contact token.
                            for value in (page, address):
                                checked = policy.scope_validator.validate_value(value)
                                if isinstance(checked, Failure):
                                    permit.release(ReservationOutcome.ABORTED)
                                    return checked
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
                                            "-ct",
                                            f"{remaining:.6f}s",
                                            "-cs",
                                            f"^\\Q{page}\\E$",
                                            "-u",
                                            page,
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
                            contacted.append(page)
                            stdout_size += len(result.value.stdout)
                            stderr_size += len(result.value.stderr)
                            if (
                                max(stdout_size, stderr_size)
                                > self.config.max_output_bytes
                            ):
                                raise ValueError("aggregate output bound")
                            records, invalid = parse(result.value.stdout, page)
                            malformed += invalid
                            if not any(f["contacted"] for f in records):
                                limitations.add("unreported_page")
                            for fact in records:
                                # Stable JSON keys retain independent source-page lineage.
                                key = json.dumps(
                                    [
                                        fact["url"],
                                        fact["method"],
                                        fact["tag"],
                                        fact["attribute"],
                                        page,
                                    ],
                                    separators=(",", ":"),
                                )
                                if key in facts and facts[key] != fact:
                                    raise ValueError("conflicting crawl record")
                                facts[key] = fact
                                if len(facts) > self.settings.max_discoveries:
                                    raise ValueError("discovery bound")
                                if not followable(fact):
                                    continue
                                checked = policy.scope_validator.validate_value(
                                    str(fact["url"])
                                )
                                if isinstance(checked, Failure):
                                    continue
                                try:
                                    candidate = numeric_url(
                                        checked.value.canonical_target
                                    )
                                except ValueError:
                                    continue
                                if (
                                    urlsplit(candidate)[:2] != urlsplit(root)[:2]
                                    or candidate in seen
                                ):
                                    continue
                                seen.add(candidate)
                                if depth >= self.settings.max_depth:
                                    limitations.add("depth_limit")
                                    continue
                                queue.append((depth + 1, candidate))
                            queue.sort()
                        if queue:
                            limitations.add("page_limit")
                        if (
                            monotonic() >= deadline
                            or budgets.state.remaining_seconds <= 0
                        ):
                            raise TimeoutError
                        output = normalize(
                            tuple(facts[k] for k in sorted(facts)),
                            malformed,
                            tuple(contacted),
                            tuple(sorted(limitations)),
                            root,
                            context,
                        )
                        if (
                            len(output.model_dump_json().encode())
                            > self.config.max_output_bytes
                        ):
                            raise ValueError("normalized output bound")
                        permit.release(
                            ReservationOutcome.FAILED
                            if output.status == "partial"
                            else ReservationOutcome.COMPLETED
                        )
                        return Success[CrawlOutput](value=output)
            except TimeoutError:
                permit.release(ReservationOutcome.TIMEOUT)
                return Failure(
                    error=ToolTimeoutError(
                        "Katana crawl deadline reached"
                    ).to_error_info()
                )
            except OSError:
                permit.release(ReservationOutcome.FAILED)
                return Failure(
                    error=ToolExecutionError(
                        "Katana local setup failed"
                    ).to_error_info()
                )
            except (ValueError, TypeError, AttributeError, RecursionError):
                permit.release(ReservationOutcome.FAILED)
                return Failure(
                    error=ParserError(
                        "Malformed or oversized Katana output"
                    ).to_error_info()
                )

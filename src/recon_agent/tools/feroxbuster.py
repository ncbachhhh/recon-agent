"""Trusted Feroxbuster path discovery with adapter-owned finite directory recursion."""

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
from recon_agent.tools.feroxbuster_models import (
    WORDS,
    ContentDiscoveryOutput,
    FeroxbusterContext,
    FeroxbusterInput,
    FeroxbusterSettings,
)
from recon_agent.tools.feroxbuster_parser import directory_url, normalize, parse

# Tool recursion and ALL response-derived requests are disabled. Adapter owns
# finite same-origin directory traversal. Depth zero is NEVER passed to Ferox.
_FLAGS = (
    "--silent",
    "--json",
    "--no-state",
    "--no-recursion",
    "--dont-extract-links",
    "--dont-filter",
    "--scan-dir-listings",
    "--depth",
    "1",
    "--scan-limit",
    "1",
    "--timeout",
    "10",
    "--response-size-limit",
    "16384",
    "--methods",
    "GET",
    "--status-codes",
    *(str(s) for s in range(100, 600)),
)


def _ambient_config(executable: str) -> None:
    # Ferox has no config-disable flag; false defaults cannot undo ambient true.
    # HOME/XDG/cwd are private. Reject the two remaining search locations, including
    # dangling symlinks and unreadable paths. The operator owns trusted local files.
    for path in (
        Path("/etc/feroxbuster/ferox-config.toml"),
        Path(executable).resolve().parent / "ferox-config.toml",
    ):
        try:
            path.lstat()
        except FileNotFoundError:
            continue
        raise ToolUnavailableError("Ambient Feroxbuster configuration is unsupported")


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
                "Feroxbuster exited unsuccessfully",
                context=ErrorContext(tool="feroxbuster", exit_code=process.return_code),
            ).to_error_info()
        )
    if (
        process.stdout_truncated
        or process.stderr_truncated
        or len(process.stdout) > limit
        or len(process.stderr) > limit
    ):
        return Failure(
            error=ParserError(
                "Feroxbuster output is truncated or oversized"
            ).to_error_info()
        )
    return Success[ProcessExecution](value=process)


@dataclass(frozen=True, slots=True)
class FeroxbusterAdapter(ToolAdapter):
    executable: str
    config: ExecutionConfig
    settings: FeroxbusterSettings = field(default_factory=FeroxbusterSettings)
    runner: ProcessRunner | None = field(default=None, repr=False, compare=False)
    _verified: bool = field(default=False, init=False, repr=False)

    def __post_init__(self) -> None:
        try:
            config = ExecutionConfig.model_validate(self.config)
            settings = FeroxbusterSettings.model_validate(self.settings)
            if not Path(self.executable).is_absolute() or "\x00" in self.executable:
                raise ValueError("absolute trusted executable required")
        except (ValueError, TypeError):
            raise ConfigurationError(
                "Invalid trusted Feroxbuster composition"
            ) from None
        object.__setattr__(self, "config", config)
        object.__setattr__(self, "settings", settings)
        if self.runner is None:
            object.__setattr__(self, "runner", AsyncProcessRunner(config))

    @property
    def definition(self) -> AdapterDefinition:
        return AdapterDefinition(
            adapter_id="feroxbuster",
            descriptor=CapabilityDescriptor(
                capability=CapabilityId.DISCOVER_CONTENT,
                description="Bounded recursive path discovery of authorized numeric HTTP endpoints",
                risk_class=RiskClass.ACTIVE_SAFE,
            ),
            input_schema=FeroxbusterInput,
            output_schema=ContentDiscoveryOutput,
            parameter_target_fields=(),
        )

    @classmethod
    async def detect(
        cls,
        config: ExecutionConfig,
        *,
        settings: FeroxbusterSettings | None = None,
        binary: str = "feroxbuster",
        runner: ProcessRunner | None = None,
    ) -> OperationResult[InstanceOf["FeroxbusterAdapter"]]:
        if not isinstance(binary, str) or not binary.strip() or "\x00" in binary:
            raise ConfigurationError("Invalid trusted Feroxbuster binary setting")
        if sys.platform != "linux":
            return Failure(
                error=ToolUnavailableError(
                    "Feroxbuster profile requires Linux"
                ).to_error_info()
            )
        executable = shutil.which(binary)
        if executable is None:
            return Failure(
                error=ToolUnavailableError(
                    "Feroxbuster executable unavailable"
                ).to_error_info()
            )
        adapter = cls(
            str(Path(executable).absolute()),
            config,
            settings or FeroxbusterSettings(),
            runner,
        )
        assert adapter.runner is not None
        try:
            with TemporaryDirectory(prefix="recon-feroxbuster-") as directory:
                _ambient_config(adapter.executable)
                result = _checked_process(
                    await adapter.runner.run(
                        _spec(
                            adapter.executable,
                            directory,
                            ("--version",),
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
                    r"^feroxbuster ([0-9]+\.[0-9]+\.[0-9]+)[ \t]*$",
                    text,
                    re.MULTILINE,
                ) != ["2.13.1"]:
                    return Failure(
                        error=ToolUnavailableError(
                            "Unsupported Feroxbuster version"
                        ).to_error_info()
                    )
        except (OSError, ValueError, TypeError, AttributeError, ToolUnavailableError):
            return Failure(
                error=ToolUnavailableError(
                    "Feroxbuster availability check failed"
                ).to_error_info()
            )
        object.__setattr__(adapter, "_verified", True)
        return Success[InstanceOf[FeroxbusterAdapter]](value=adapter)

    async def execute(
        self,
        request: ActionRequest,
        *,
        policy: ActionPolicyValidator,
        budgets: BudgetController,
        context: FeroxbusterContext,
        on_started: ExecutionStart | None = None,
    ) -> OperationResult[ContentDiscoveryOutput]:
        try:
            request = ActionRequest.model_validate(request)
            context = FeroxbusterContext.model_validate(context)
        except (ValueError, TypeError):
            return Failure(
                error=PlannerValidationError(
                    "Malformed content discovery request/context"
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
                    "Content discovery composition mismatch"
                ).to_error_info()
            )
        selected = policy.registry.resolve(request.capability)
        if isinstance(selected, Failure):
            return selected
        if selected.value is not self:
            return Failure(
                error=PlannerValidationError(
                    "Content discovery registry binding mismatch"
                ).to_error_info()
            )
        if not self._verified:
            return Failure(
                error=ToolUnavailableError(
                    "Feroxbuster version has not been verified"
                ).to_error_info()
            )
        approved = policy.validate(request)
        if isinstance(approved, Failure):
            return approved
        try:
            directory_url(Target(id="ferox-input", kind="url", value=request.target))
            root = directory_url(approved.value.scope_match.canonical_target)
        except (ValueError, TypeError):
            return Failure(
                error=PlannerValidationError(
                    "Content discovery containment requires numeric HTTP(S) URL"
                ).to_error_info()
            )
        address = urlsplit(root).hostname
        assert address is not None
        contact = policy.scope_validator.validate_value(address)
        if isinstance(contact, Failure):
            return contact
        try:
            _ambient_config(self.executable)
        except (OSError, ValueError, ToolUnavailableError):
            return Failure(
                error=ToolUnavailableError(
                    "Feroxbuster configuration containment unavailable"
                ).to_error_info()
            )
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
            if duration <= 0:
                permit.release(ReservationOutcome.TIMEOUT)
                return Failure(
                    error=ToolTimeoutError(
                        "Feroxbuster deadline reached"
                    ).to_error_info()
                )
            deadline = monotonic() + duration
            facts: dict[str, dict[str, JsonValue]] = {}
            malformed = stdout_size = stderr_size = request_bound = 0
            unreported: set[str] = set()
            contacted: list[str] = []
            seen = {root}
            queue = [(0, root)]
            limitations: set[str] = set()
            window = budgets.limits.capability_rate_window_seconds
            interval = max(1.0, window / budgets.limits.capability_rate_actions)
            try:
                async with asyncio.timeout(duration):
                    with TemporaryDirectory(prefix="recon-feroxbuster-") as directory:
                        while queue and len(contacted) < self.settings.max_directories:
                            available = self.settings.max_requests - request_bound - 3
                            if available <= 0:
                                limitations.add("request_limit")
                                break
                            words = WORDS[:available]
                            if len(words) != len(WORDS):
                                limitations.add("request_limit")
                            depth, page = queue.pop(0)
                            if contacted:
                                # Include three unpaced startup/base GETs and fresh token
                                # burst in inter-process spacing; do not reset bursts freely.
                                await asyncio.sleep(
                                    max(interval, 7 / self.settings.request_rate)
                                )
                            candidates = (
                                page,
                                *(urljoin(page, word) for word in words),
                            )
                            for value in (*candidates, address):
                                checked = policy.scope_validator.validate_value(value)
                                if isinstance(checked, Failure):
                                    permit.release(ReservationOutcome.ABORTED)
                                    return checked
                            _ambient_config(self.executable)
                            wordlist = Path(directory) / "approved-words.txt"
                            wordlist.write_text(
                                "\n".join(words) + "\n", encoding="ascii"
                            )
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
                                            "--threads",
                                            str(self.settings.concurrency),
                                            "--rate-limit",
                                            str(self.settings.request_rate),
                                            "--wordlist",
                                            str(wordlist),
                                            "--url",
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
                            # Connectivity + directory heuristic + implicit empty word.
                            request_bound += 3 + len(words)
                            stdout_size += len(result.value.stdout)
                            stderr_size += len(result.value.stderr)
                            if (
                                max(stdout_size, stderr_size)
                                > self.config.max_output_bytes
                            ):
                                raise ValueError("aggregate output bound")
                            records, invalid = parse(
                                result.value.stdout, page, candidates
                            )
                            malformed += invalid
                            reported = {str(f["url"]) for f in records}
                            unreported.update(set(candidates) - reported)
                            if any(f["body_truncated"] for f in records):
                                limitations.add("response_body_limit")
                            for fact in records:
                                location = fact.get("location")
                                if location is not None:
                                    destination = urljoin(
                                        str(fact["url"]), str(location)
                                    )
                                    checked = policy.scope_validator.validate_value(
                                        destination
                                    )
                                    fact["redirect_scope_status"] = (
                                        "rejected"
                                        if isinstance(checked, Failure)
                                        else "allowed"
                                    )
                                key = json.dumps(
                                    [fact["url"], page], separators=(",", ":")
                                )
                                if key in facts and facts[key] != fact:
                                    raise ValueError("conflicting content record")
                                facts[key] = fact
                                candidate = str(fact["url"])
                                # Never follow redirects or infer directories from 403/names.
                                if not (
                                    200 <= int(str(fact["status_code"])) < 300
                                    and candidate.endswith("/")
                                    and candidate not in seen
                                ):
                                    continue
                                seen.add(candidate)
                                if depth >= self.settings.max_depth:
                                    limitations.add("depth_limit")
                                    continue
                                queue.append((depth + 1, candidate))
                            queue.sort()
                        if queue and len(contacted) >= self.settings.max_directories:
                            limitations.add("directory_limit")
                        if (
                            monotonic() >= deadline
                            or budgets.state.remaining_seconds <= 0
                        ):
                            raise TimeoutError
                        output = normalize(
                            tuple(facts[k] for k in sorted(facts)),
                            malformed,
                            tuple(contacted),
                            request_bound,
                            tuple(sorted(unreported)),
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
                        return Success[ContentDiscoveryOutput](value=output)
            except TimeoutError:
                permit.release(ReservationOutcome.TIMEOUT)
                return Failure(
                    error=ToolTimeoutError(
                        "Feroxbuster content discovery deadline reached"
                    ).to_error_info()
                )
            except (ToolUnavailableError, ParserError) as exc:
                permit.release(ReservationOutcome.FAILED)
                return Failure(error=exc.to_error_info())
            except OSError:
                permit.release(ReservationOutcome.FAILED)
                return Failure(
                    error=ToolExecutionError(
                        "Feroxbuster local setup failed"
                    ).to_error_info()
                )
            except (ValueError, TypeError, AttributeError, RecursionError):
                permit.release(ReservationOutcome.FAILED)
                return Failure(
                    error=ParserError(
                        "Malformed or oversized Feroxbuster output"
                    ).to_error_info()
                )

"""Shell-free asynchronous direct-child execution with bounded stream retention."""

import asyncio
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from time import monotonic
from typing import Protocol, TypedDict

from recon_agent.core.config.models import ExecutionConfig
from recon_agent.core.errors import (
    ErrorContext,
    ToolExecutionError,
    ToolTimeoutError,
    ToolUnavailableError,
)
from recon_agent.core.results import Failure, OperationResult, Success
from recon_agent.execution.models import ProcessExecution, ProcessSpec

_READ_BYTES = 16_384
_PIPE_BUFFER_BYTES = 65_536
_TERMINATE_GRACE_SECONDS = 0.5


class ProcessRunner(Protocol):
    """Execution-neutral injection boundary for future adapter fixture tests."""

    async def run(self, spec: ProcessSpec) -> OperationResult[ProcessExecution]: ...


class ProcessHandle(Protocol):
    """Internal spawn seam; fakes must implement direct-child lifecycle and pipes."""

    @property
    def stdout(self) -> asyncio.StreamReader | None: ...

    @property
    def stderr(self) -> asyncio.StreamReader | None: ...

    @property
    def returncode(self) -> int | None: ...

    async def wait(self) -> int: ...

    def terminate(self) -> None: ...

    def kill(self) -> None: ...


class _SpawnDirectory(TypedDict, total=False):
    cwd: str


async def _spawn(spec: ProcessSpec) -> ProcessHandle:
    directory: _SpawnDirectory = {}
    if spec.working_directory is not None:
        directory["cwd"] = spec.working_directory
    return await asyncio.create_subprocess_exec(
        spec.executable,
        *spec.args,
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        limit=_PIPE_BUFFER_BYTES,
        env=dict(spec.environment) if spec.environment is not None else None,
        **directory,
    )


async def _capture(
    stream: asyncio.StreamReader | None, limit: int
) -> tuple[bytes, bool]:
    if stream is None:
        raise OSError("capture pipe unavailable")
    retained = bytearray()
    truncated = False
    while chunk := await stream.read(_READ_BYTES):
        remaining = limit - len(retained)
        retained.extend(chunk[:remaining])
        truncated |= len(chunk) > remaining
    return bytes(retained), truncated


async def _terminate(process: ProcessHandle) -> None:
    if process.returncode is None:
        try:
            process.terminate()
        except ProcessLookupError:
            pass  # Child exited between the return-code check and signal.
        try:
            await asyncio.wait_for(process.wait(), _TERMINATE_GRACE_SECONDS)
        except TimeoutError:
            try:
                process.kill()
            except ProcessLookupError:
                pass
    await process.wait()


async def _settle[T](task: asyncio.Task[T]) -> T:
    """Finish owned cleanup even if the caller cancels again; then propagate it."""
    cancelled = False
    while not task.done():
        try:
            await asyncio.shield(task)
        except asyncio.CancelledError:
            cancelled = True
    value = task.result()
    if cancelled:
        raise asyncio.CancelledError
    return value


class AsyncProcessRunner:
    """Internal primitive, never an AI tool or public arbitrary-command endpoint.

    Config is validated/snapshotted explicitly; only invocation timeout and the
    per-stream retention limit are enforced here. Other budgets belong above it.
    The injected spawn seam is trusted test infrastructure, not configuration.
    """

    def __init__(
        self,
        config: ExecutionConfig,
        *,
        spawn: Callable[[ProcessSpec], Awaitable[ProcessHandle]] = _spawn,
    ) -> None:
        snapshot = ExecutionConfig.model_validate(config.model_dump())
        self._timeout = snapshot.default_timeout_seconds
        self._output_limit = snapshot.max_output_bytes
        self._spawn = spawn

    async def run(self, spec: ProcessSpec) -> OperationResult[ProcessExecution]:
        spec = ProcessSpec.model_validate(spec)
        timeout = spec.timeout_seconds or self._timeout
        stop = asyncio.Event()
        # The lifecycle owns spawn/cleanup. Shielding prevents cancellation from
        # losing a child handle while create_subprocess_exec is still completing.
        lifecycle = asyncio.create_task(self._execute(spec, stop))
        try:
            return await asyncio.wait_for(asyncio.shield(lifecycle), timeout)
        except TimeoutError:
            stop.set()
            await _settle(lifecycle)
            return Failure(
                error=ToolTimeoutError(
                    "Process execution deadline reached.",
                    context=ErrorContext(timeout_seconds=timeout),
                ).to_error_info()
            )
        except asyncio.CancelledError:
            stop.set()
            await _settle(lifecycle)
            raise

    async def _execute(
        self, spec: ProcessSpec, stop: asyncio.Event
    ) -> OperationResult[ProcessExecution]:
        started_at = datetime.now(UTC)
        started = monotonic()
        try:
            process = await self._spawn(spec)
        except (FileNotFoundError, PermissionError):
            return Failure(
                error=ToolUnavailableError(
                    "Process executable unavailable."
                ).to_error_info()
            )
        except (OSError, UnicodeError):
            return Failure(
                error=ToolExecutionError("Process could not start.").to_error_info()
            )

        stdout = asyncio.create_task(_capture(process.stdout, self._output_limit))
        stderr = asyncio.create_task(_capture(process.stderr, self._output_limit))
        exited = asyncio.create_task(process.wait())
        completion = asyncio.gather(exited, stdout, stderr)
        stopped = asyncio.create_task(stop.wait())
        try:
            await asyncio.wait(
                (completion, stopped), return_when=asyncio.FIRST_COMPLETED
            )
            if stop.is_set():
                await _terminate(process)
            await completion
            output, output_truncated = stdout.result()
            diagnostics, diagnostics_truncated = stderr.result()
            return Success[ProcessExecution](
                value=ProcessExecution(
                    argument_count=len(spec.args),
                    return_code=exited.result(),
                    stdout=output,
                    stderr=diagnostics,
                    stdout_truncated=output_truncated,
                    stderr_truncated=diagnostics_truncated,
                    started_at=started_at,
                    finished_at=datetime.now(UTC),
                    duration_seconds=monotonic() - started,
                )
            )
        except OSError:
            return Failure(
                error=ToolExecutionError("Process capture failed.").to_error_info()
            )
        finally:
            await _terminate(process)
            stopped.cancel()
            completion.cancel()
            for task in (exited, stdout, stderr):
                task.cancel()
            # Await every owned task/future; no detached drain/stop/wait work.
            await asyncio.gather(
                stopped, completion, exited, stdout, stderr, return_exceptions=True
            )

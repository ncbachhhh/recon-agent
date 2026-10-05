"""Deterministic fake-process tests for the internal execution boundary."""

import asyncio
from datetime import UTC
from unittest.mock import AsyncMock

import pytest
from pydantic import TypeAdapter, ValidationError

from recon_agent.core.config.models import ExecutionConfig
from recon_agent.core.errors import ErrorCode
from recon_agent.core.results import OperationResult
from recon_agent.execution import AsyncProcessRunner, ProcessExecution, ProcessSpec
from recon_agent.execution import runner as implementation


class FakeProcess:
    def __init__(
        self, stdout=b"", stderr=b"", code=0, *, running=False, ignore_terminate=False
    ):
        self.stdout = asyncio.StreamReader()
        self.stderr = asyncio.StreamReader()
        self.stdout.feed_data(stdout)
        self.stderr.feed_data(stderr)
        self.returncode = None
        self.exited = asyncio.Event()
        self.terminated = asyncio.Event()
        self.ignore_terminate = ignore_terminate
        self.killed = False
        self.waited = False
        if not running:
            self.finish(code)

    def finish(self, code):
        self.returncode = code
        for stream in (self.stdout, self.stderr):
            if stream is not None:
                stream.feed_eof()
        self.exited.set()

    async def wait(self):
        await self.exited.wait()
        self.waited = True
        return self.returncode

    def terminate(self):
        self.terminated.set()
        if not self.ignore_terminate:
            self.finish(-15)

    def kill(self):
        self.killed = True
        self.finish(-9)


def spec(**updates):
    return ProcessSpec.model_validate({"executable": "fixture-program", **updates})


def fake_runner(process, **config):
    spawn = AsyncMock(return_value=process)
    return AsyncProcessRunner(ExecutionConfig(**config), spawn=spawn), spawn


@pytest.mark.parametrize(
    "updates",
    [
        {"executable": ""},
        {"executable": " \t"},
        {"executable": "a\x00b"},
        {"executable": 3},
        {"args": "--flag value"},
        {"args": ["--flag"]},
        {"args": (1,)},
        {"args": (None,)},
        {"args": (b"value",)},
        {"args": ("a\x00b",)},
        {"timeout_seconds": 0},
        {"timeout_seconds": -1},
        {"timeout_seconds": float("inf")},
        {"timeout_seconds": float("nan")},
        {"timeout_seconds": True},
        {"timeout_seconds": "1"},
        {"shell_command": "arbitrary"},
        {"cwd": "somewhere"},
        {"env": {}},
        {"stdin": "input"},
    ],
)
def test_invalid_process_spec(updates):
    with pytest.raises(ValidationError):
        spec(**updates)


def test_spec_preserves_arguments_and_omits_sensitive_repr():
    value = spec(args=("", "a b", "secret-fixture-argument"))
    assert value.args == ("", "a b", "secret-fixture-argument")
    assert "secret-fixture-argument" not in repr(value)
    assert "fixture-program" not in repr(value)
    assert ProcessSpec.model_validate_json(value.model_dump_json()) == value
    with pytest.raises(ValidationError):
        value.executable = "other"


def test_runner_revalidates_spec_and_rejects_command_string():
    async def check():
        process = FakeProcess()
        runner, spawn = fake_runner(process)
        for value in ("program --flag", ProcessSpec.model_construct(executable="")):
            with pytest.raises(ValidationError):
                await runner.run(value)
        spawn.assert_not_called()

    asyncio.run(check())


@pytest.mark.parametrize("code", [0, 1, 17, -15])
def test_runner_exit_output_timing_and_roundtrip(code):
    async def check():
        process = FakeProcess(b"hello\nworld\n", b"diagnostic\nnext\n", code)
        runner, spawn = fake_runner(process)
        request = spec(args=("first", "second"))
        result = await runner.run(request)
        assert result.status == "success"
        execution = result.value
        assert execution.return_code == code
        assert execution.argument_count == 2
        assert execution.stdout == b"hello\nworld\n"
        assert execution.stderr == b"diagnostic\nnext\n"
        assert not execution.stdout_truncated and not execution.stderr_truncated
        assert execution.started_at.tzinfo == UTC
        assert execution.finished_at.tzinfo == UTC
        assert execution.duration_seconds >= 0
        assert "hello" not in repr(execution)
        assert process.waited and not process.terminated.is_set()
        spawn.assert_awaited_once_with(request)
        adapter = TypeAdapter(OperationResult[ProcessExecution])
        assert adapter.validate_json(adapter.dump_json(result)) == result

    asyncio.run(check())


@pytest.mark.parametrize("size", [0, 1, 32, 33, 200_000])
def test_runner_per_stream_bounded_capture(size):
    async def check():
        process = FakeProcess(b"x" * size, b"y" * size)
        runner, _ = fake_runner(process, max_output_bytes=32)
        result = await runner.run(spec())
        assert result.status == "success"
        assert result.value.stdout == b"x" * min(size, 32)
        assert result.value.stderr == b"y" * min(size, 32)
        assert result.value.stdout_truncated is (size > 32)
        assert result.value.stderr_truncated is (size > 32)

    asyncio.run(check())


@pytest.mark.parametrize(
    "error,code",
    [
        (FileNotFoundError("unsafe-path"), ErrorCode.TOOL_UNAVAILABLE),
        (PermissionError("unsafe-path"), ErrorCode.TOOL_UNAVAILABLE),
        (OSError("unsafe-environment"), ErrorCode.TOOL_EXECUTION_FAILED),
        (
            UnicodeEncodeError("utf-8", "unsafe-surrogate-\ud800", 0, 1, "invalid"),
            ErrorCode.TOOL_EXECUTION_FAILED,
        ),
    ],
)
def test_runner_spawn_failure_is_canonical_and_safe(error, code):
    async def check():
        spawn = AsyncMock(side_effect=error)
        runner = AsyncProcessRunner(ExecutionConfig(), spawn=spawn)
        result = await runner.run(spec(args=("sensitive-argument",)))
        assert result.status == "failure"
        assert result.error.code == code
        assert not result.error.retryable
        dump = result.model_dump_json()
        assert "unsafe" not in dump and "sensitive-argument" not in dump
        adapter = TypeAdapter(OperationResult[ProcessExecution])
        assert adapter.validate_json(adapter.dump_json(result)) == result

    asyncio.run(check())


@pytest.mark.parametrize("override", [None, 0.1])
def test_runner_timeout_terminates_and_reaps(override):
    async def check():
        process = FakeProcess(b"partial-output", running=True)
        runner, _ = fake_runner(process, default_timeout_seconds=0.2)
        result = await runner.run(spec(timeout_seconds=override))
        assert result.status == "failure"
        assert result.error.code == ErrorCode.TOOL_TIMEOUT
        assert result.error.context.timeout_seconds == (override or 0.2)
        assert "partial-output" not in result.model_dump_json()
        assert process.terminated.is_set() and process.waited
        assert process.returncode == -15

    asyncio.run(check())


def test_runner_timeout_escalates_to_kill():
    async def check():
        process = FakeProcess(running=True, ignore_terminate=True)
        runner, _ = fake_runner(process, default_timeout_seconds=0.1)
        result = await runner.run(spec())
        assert result.status == "failure"
        assert result.error.code == ErrorCode.TOOL_TIMEOUT
        assert process.killed and process.waited and process.returncode == -9

    asyncio.run(check())


def test_runner_override_and_configuration_snapshot():
    async def check():
        config = ExecutionConfig(default_timeout_seconds=0.01, max_output_bytes=3)
        process = FakeProcess(b"abcdef", running=True)
        runner = AsyncProcessRunner(config, spawn=AsyncMock(return_value=process))
        config.max_output_bytes = 100
        loop = asyncio.get_running_loop()
        loop.call_later(0.05, process.finish, 0)
        result = await runner.run(spec(timeout_seconds=1))
        assert result.status == "success"
        assert result.value.stdout == b"abc" and result.value.stdout_truncated

    asyncio.run(check())


def test_runner_revalidates_config():
    config = ExecutionConfig()
    config.__dict__["max_output_bytes"] = 0
    with pytest.raises(ValidationError):
        AsyncProcessRunner(config)


def test_runner_cancellation_during_spawn_waits_for_handle_cleanup():
    async def check():
        process = FakeProcess(running=True)
        spawning = asyncio.Event()
        release = asyncio.Event()

        async def spawn(request):
            spawning.set()
            await release.wait()
            return process

        runner = AsyncProcessRunner(ExecutionConfig(), spawn=spawn)
        task = asyncio.create_task(runner.run(spec()))
        await spawning.wait()
        task.cancel()
        await asyncio.sleep(0)
        assert not task.done()
        release.set()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert process.terminated.is_set() and process.waited

    asyncio.run(check())


def test_runner_repeated_cancellation_cannot_interrupt_cleanup():
    async def check():
        process = FakeProcess(running=True, ignore_terminate=True)
        runner, _ = fake_runner(process)
        task = asyncio.create_task(runner.run(spec()))
        # Wait for the lifecycle to acquire the handle and begin pipe reads.
        await asyncio.sleep(0)
        task.cancel()
        await process.terminated.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert process.killed and process.waited
        assert not [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]

    asyncio.run(check())


def test_runner_timeout_during_spawn_still_cleans_up():
    async def check():
        process = FakeProcess(running=True)

        async def spawn(request):
            await asyncio.sleep(0.1)
            return process

        runner = AsyncProcessRunner(
            ExecutionConfig(default_timeout_seconds=0.05), spawn=spawn
        )
        result = await runner.run(spec())
        assert (
            result.status == "failure" and result.error.code == ErrorCode.TOOL_TIMEOUT
        )
        assert process.terminated.is_set() and process.waited

    asyncio.run(check())


@pytest.mark.parametrize("missing_pipe", [False, True])
def test_runner_capture_failure_cleans_up(missing_pipe):
    async def check():
        process = FakeProcess(running=True)
        if missing_pipe:
            process.stdout = None
        else:
            process.stdout.set_exception(OSError("unsafe-output-error"))
        runner, _ = fake_runner(process)
        result = await runner.run(spec())
        assert result.status == "failure"
        assert result.error.code == ErrorCode.TOOL_EXECUTION_FAILED
        assert "unsafe-output-error" not in result.model_dump_json()
        assert process.terminated.is_set() and process.waited
        assert not [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]

    asyncio.run(check())


@pytest.mark.parametrize("ignore_terminate", [False, True])
def test_runner_signal_exit_race(ignore_terminate):
    async def check():
        process = FakeProcess(running=True, ignore_terminate=ignore_terminate)

        def already_exited():
            process.finish(0)
            raise ProcessLookupError

        if ignore_terminate:
            process.kill = already_exited
        else:
            process.terminate = already_exited
        runner, _ = fake_runner(process, default_timeout_seconds=0.05)
        result = await runner.run(spec())
        assert (
            result.status == "failure" and result.error.code == ErrorCode.TOOL_TIMEOUT
        )
        assert process.waited and process.returncode == 0

    asyncio.run(check())


def test_runner_duration_uses_monotonic_clock(monkeypatch):
    ticks = iter((100.0, 100.75))
    monkeypatch.setattr(implementation, "monotonic", lambda: next(ticks))

    async def check():
        runner, _ = fake_runner(FakeProcess())
        result = await runner.run(spec())
        assert result.status == "success"
        assert result.value.duration_seconds == 0.75

    asyncio.run(check())


def test_spawn_uses_literal_argv_devnull_and_bounded_pipes(monkeypatch):
    async def check():
        process = FakeProcess()
        spawn = AsyncMock(return_value=process)
        monkeypatch.setattr(asyncio, "create_subprocess_exec", spawn)
        request = spec(args=(";", "$HOME", "hello world"))
        result = await AsyncProcessRunner(ExecutionConfig()).run(request)
        assert result.status == "success"
        spawn.assert_awaited_once_with(
            request.executable,
            *request.args,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            limit=65_536,
        )

    asyncio.run(check())


def test_runner_cancellation_during_timeout_cleanup_propagates():
    async def check():
        process = FakeProcess(running=True, ignore_terminate=True)
        runner, _ = fake_runner(process, default_timeout_seconds=0.05)
        task = asyncio.create_task(runner.run(spec()))
        await process.terminated.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert process.killed and process.waited

    asyncio.run(check())


def test_runner_emits_no_logs_or_argv_metadata(caplog):
    async def check():
        runner, _ = fake_runner(FakeProcess(b"sensitive-output"))
        result = await runner.run(spec(args=("sensitive-argument",)))
        assert result.status == "success"
        assert not {"argv", "args", "executable", "environment"}.intersection(
            ProcessExecution.model_fields
        )

    asyncio.run(check())
    assert not [r for r in caplog.records if r.name.startswith("recon_agent")]


def test_runner_allows_independent_awaitable_invocations():
    async def check():
        first, second = FakeProcess(running=True), FakeProcess(running=True)
        acquired = asyncio.Event()
        calls = 0

        async def spawn(request):
            nonlocal calls
            calls += 1
            if calls == 2:
                acquired.set()
            return first if request.args == ("first",) else second

        runner = AsyncProcessRunner(ExecutionConfig(), spawn=spawn)
        tasks = [
            asyncio.create_task(runner.run(spec(args=(name,))))
            for name in ("first", "second")
        ]
        await asyncio.wait_for(acquired.wait(), 1)
        first.finish(1)
        second.finish(2)
        results = await asyncio.gather(*tasks)
        assert [r.value.return_code for r in results if r.status == "success"] == [1, 2]

    asyncio.run(check())

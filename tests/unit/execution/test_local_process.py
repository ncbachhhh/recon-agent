"""Explicitly marked harmless local sys.executable tests; no shell or network."""

import asyncio
import json
import sys

import pytest
from pydantic import TypeAdapter

from recon_agent.core.config.models import ExecutionConfig
from recon_agent.core.errors import ErrorCode
from recon_agent.core.results import OperationResult
from recon_agent.execution import AsyncProcessRunner, ProcessExecution, ProcessSpec
from recon_agent.execution.runner import _spawn

pytestmark = pytest.mark.local_process


def python_spec(script, *args, timeout=None):
    return ProcessSpec(
        executable=sys.executable,
        args=("-I", "-c", script, *args),
        timeout_seconds=timeout,
    )


@pytest.mark.parametrize("code", [0, 1, 23])
def test_local_process_return_codes(code):
    async def check():
        result = await AsyncProcessRunner(ExecutionConfig()).run(
            python_spec(f"import sys; sys.exit({code})")
        )
        assert result.status == "success" and result.value.return_code == code
        assert result.value.stdout == result.value.stderr == b""

    asyncio.run(check())


@pytest.mark.parametrize(
    "stdout,stderr",
    [
        (b"", b""),
        (b"normal", b""),
        (b"", b"diagnostic"),
        (b"one\ntwo\n", b"first\nsecond\n"),
        ("Xin chào ☃".encode(), "診断".encode()),
        (b"a\xff\xfe\x00", b"\x80invalid"),
    ],
)
def test_local_process_separate_raw_streams_and_json(stdout, stderr):
    async def check():
        script = f"import os; os.write(1, {stdout!r}); os.write(2, {stderr!r})"
        result = await AsyncProcessRunner(ExecutionConfig()).run(python_spec(script))
        assert result.status == "success"
        assert result.value.stdout == stdout and result.value.stderr == stderr
        adapter = TypeAdapter(OperationResult[ProcessExecution])
        assert adapter.validate_json(adapter.dump_json(result)) == result

    asyncio.run(check())


def test_local_process_shell_metacharacters_are_literal_and_no_side_effect(tmp_path):
    sentinel = tmp_path / "SHOULD_NOT_EXIST"
    arguments = (
        "hello world",
        "a;b",
        "a&&b",
        "a||b",
        "$(echo injected)",
        "$HOME",
        "$",
        "*.txt",
        "?",
        "~",
        "foo|bar",
        ">output",
        "<input",
        '"quoted"',
        "'single'",
        "`echo injected`",
        f"x; touch {sentinel}",
        f"$(touch {sentinel})",
        "",
        f"hello; {sys.executable} -c \"open({str(sentinel)!r}, 'w').close()\"",
    )

    async def check():
        result = await AsyncProcessRunner(ExecutionConfig()).run(
            python_spec("import json,sys; print(json.dumps(sys.argv[1:]))", *arguments)
        )
        assert result.status == "success"
        assert tuple(json.loads(result.value.stdout)) == arguments
        assert not sentinel.exists()

    asyncio.run(check())


@pytest.mark.parametrize("limit", [1, 1024, 16_384])
def test_local_process_large_simultaneous_streams_drain_without_deadlock(limit):
    async def check():
        # Alternation deadlocks a sequential full-stream reader once a pipe fills.
        script = (
            "import os\n"
            "for _ in range(32):\n"
            " os.write(1, b'x' * 8192)\n"
            " os.write(2, b'y' * 8192)\n"
        )
        result = await AsyncProcessRunner(
            ExecutionConfig(max_output_bytes=limit, default_timeout_seconds=5)
        ).run(python_spec(script))
        assert result.status == "success" and result.value.return_code == 0
        assert result.value.stdout == b"x" * limit
        assert result.value.stderr == b"y" * limit
        assert result.value.stdout_truncated and result.value.stderr_truncated

    asyncio.run(check())


def test_local_process_missing_executable_is_unavailable(tmp_path):
    async def check():
        result = await AsyncProcessRunner(ExecutionConfig()).run(
            ProcessSpec(executable=str(tmp_path / "nonexistent-recon-fixture-83b456"))
        )
        assert result.status == "failure"
        assert result.error.code == ErrorCode.TOOL_UNAVAILABLE
        assert str(tmp_path) not in result.model_dump_json()

    asyncio.run(check())


def test_local_process_stdin_is_noninteractive_eof():
    async def check():
        result = await AsyncProcessRunner(ExecutionConfig()).run(
            python_spec("import sys; print(repr(sys.stdin.buffer.read()))")
        )
        assert result.status == "success" and result.value.stdout == b"b''\n"

    asyncio.run(check())


@pytest.mark.parametrize("cancel", [False, True])
def test_local_process_timeout_or_cancel_reaps_direct_child(tmp_path, cancel):
    async def check():
        ready_path = tmp_path / "ready"
        handles = []
        spawned = asyncio.Event()

        async def spawn(request):
            handle = await _spawn(request)
            handles.append(handle)
            spawned.set()
            return handle

        runner = AsyncProcessRunner(ExecutionConfig(), spawn=spawn)
        task = asyncio.create_task(
            runner.run(
                python_spec(
                    "import sys,time; from pathlib import Path; "
                    "print('partial', flush=True); "
                    "Path(sys.argv[1]).write_text('ready'); time.sleep(60)",
                    str(ready_path),
                    timeout=1.0 if not cancel else 10,
                )
            )
        )
        try:
            await asyncio.wait_for(spawned.wait(), 5)
            if cancel:

                async def ready():
                    while not ready_path.exists():
                        await asyncio.sleep(0.01)

                await asyncio.wait_for(ready(), 5)
                task.cancel()
                with pytest.raises(asyncio.CancelledError):
                    await asyncio.wait_for(task, 5)
            else:
                result = await asyncio.wait_for(task, 5)
                assert result.status == "failure"
                assert result.error.code == ErrorCode.TOOL_TIMEOUT
                assert "partial" not in result.model_dump_json()
                assert ready_path.read_text() == "ready"
            process = handles[0]
            assert process.returncode is not None
            assert await asyncio.wait_for(process.wait(), 1) == process.returncode
            # On POSIX, waitpid distinguishes actual reaping from merely exiting.
            if sys.platform != "win32":
                import os

                with pytest.raises(ChildProcessError):
                    os.waitpid(process.pid, os.WNOHANG)
        finally:
            if not task.done():
                task.cancel()
            await asyncio.gather(task, return_exceptions=True)

    asyncio.run(check())

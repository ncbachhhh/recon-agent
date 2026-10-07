"""Trusted child cwd is literal and never changes the parent's directory."""

import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError

from recon_agent.core.config.models import ExecutionConfig
from recon_agent.core.results import Success
from recon_agent.execution import AsyncProcessRunner, ProcessSpec
from recon_agent.execution.runner import _spawn


@pytest.mark.parametrize(
    "value", ["", "relative", ".", "/bad\x00path", "/" + "x" * 8192, 12]
)
def test_invalid_working_directory(value):
    with pytest.raises(ValidationError):
        ProcessSpec(executable="trusted", working_directory=value)


def test_spawn_passes_literal_cwd(monkeypatch, tmp_path):
    spawn = AsyncMock()
    monkeypatch.setattr(asyncio, "create_subprocess_exec", spawn)
    directory = str(tmp_path / "literal ; $HOME")
    spec = ProcessSpec(
        executable="trusted", args=("literal",), working_directory=directory
    )
    asyncio.run(_spawn(spec))
    assert spawn.call_args.kwargs["cwd"] == directory
    assert spawn.call_args.args == ("trusted", "literal")
    assert "shell" not in spawn.call_args.kwargs


@pytest.mark.local_process
def test_actual_child_cwd_and_parent_isolation(tmp_path):
    prior = os.getcwd()
    directory = tmp_path / "isolated ; $HOME"
    directory.mkdir()
    spec = ProcessSpec(
        executable=sys.executable,
        working_directory=str(directory),
        args=(
            "-I",
            "-c",
            "import pathlib; print(pathlib.Path.cwd()); pathlib.Path('fixture.txt').write_text('fixture')",
        ),
    )
    result = asyncio.run(AsyncProcessRunner(ExecutionConfig()).run(spec))
    assert isinstance(result, Success)
    assert result.value.return_code == 0
    assert result.value.stdout.decode().strip() == str(directory)
    assert (directory / "fixture.txt").read_text() == "fixture"
    assert os.getcwd() == prior
    assert not (Path(prior) / "fixture.txt").exists()

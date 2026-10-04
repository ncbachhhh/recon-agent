"""Offline checks for the installed package's placeholder entry point."""

from pytest import CaptureFixture

from recon_agent.cli.main import main


def test_placeholder_succeeds_and_reports_status(capsys: CaptureFixture[str]) -> None:
    assert main() == 0
    captured = capsys.readouterr()
    assert captured.out == (
        "recon-agent is not yet implemented (development baseline only).\n"
    )
    assert captured.err == ""

"""Offline configuration contract checks, independent of machine environment."""

import importlib
import logging
from pathlib import Path
from unittest.mock import Mock

import pytest
from pydantic import SecretStr

from recon_agent.core.config import (
    AppConfig,
    ProviderSecrets,
    load_config,
    load_provider_secrets,
)
from recon_agent.core.errors import ConfigurationError


def test_config_defaults_are_restrictive_and_serializable() -> None:
    config = load_config(environ={})
    assert set(AppConfig.model_fields) == {
        "scope",
        "execution",
        "planner",
        "tools",
        "persistence",
        "logging",
        "reporting",
    }
    assert not config.scope.allow_subdomains
    assert not config.scope.allow_private_ips
    assert set(config.scope.model_dump()) == {"allow_subdomains", "allow_private_ips"}
    assert not config.planner.enabled
    assert not config.tools.enabled
    assert not config.persistence.enabled
    assert config.execution.max_concurrency == 1
    assert config.execution.default_timeout_seconds == 30.0
    assert config.execution.max_actions == 100
    assert config.execution.max_duration_seconds == 600.0
    assert config.execution.max_output_bytes == 1_048_576
    assert config.reporting.default_formats == ["json"]
    assert config.model_dump(mode="json")["persistence"]["database_path"] == (
        "recon-agent.sqlite3"
    )
    assert AppConfig.model_validate_json(config.model_dump_json()) == config


def test_config_file_applies_all_sections(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    path.write_text("""
[scope]
allow_private_ips = true
allow_subdomains = true
[execution]
default_timeout_seconds = 15
max_concurrency = 2
max_output_bytes = 512
max_actions = 20
max_duration_seconds = 60
[planner]
enabled = true
provider = "groq"
model = "operator-selected-model"
max_iterations = 3
[tools]
enabled = true
[persistence]
enabled = true
database_path = "state/session.sqlite3"
[logging]
level = "WARNING"
structured = false
[reporting]
output_directory = "output"
default_formats = ["json", "html"]
""")
    config = load_config(path, environ={})
    assert config.scope.allow_private_ips and config.scope.allow_subdomains
    assert config.execution.default_timeout_seconds == 15.0
    assert config.execution.max_concurrency == 2
    assert config.execution.max_output_bytes == 512
    assert config.execution.max_actions == 20
    assert config.execution.max_duration_seconds == 60.0
    assert config.planner.enabled and config.planner.max_iterations == 3
    assert config.planner.model == "operator-selected-model"
    assert config.tools.enabled and config.persistence.enabled
    assert config.persistence.database_path == Path("state/session.sqlite3")
    assert config.logging.level == "WARNING" and not config.logging.structured
    assert config.reporting.output_directory == Path("output")
    assert config.reporting.default_formats == ["json", "html"]
    assert sorted(p.name for p in tmp_path.iterdir()) == ["config.toml"]


def test_config_complete_precedence_and_partial_merge(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    path.write_text("[execution]\nmax_concurrency = 2\nmax_output_bytes = 512\n")
    environment = {"RECON_AGENT_EXECUTION__MAX_CONCURRENCY": "3"}
    overrides = {"execution": {"max_concurrency": 4}}
    assert load_config(environ={}).execution.max_concurrency == 1
    assert load_config(path, environ={}).execution.max_concurrency == 2
    assert load_config(path, environ=environment).execution.max_concurrency == 3
    config = load_config(path, environ=environment, overrides=overrides)
    assert config.execution.max_concurrency == 4
    assert config.execution.max_output_bytes == 512
    assert config.execution.default_timeout_seconds == 30.0
    assert environment == {"RECON_AGENT_EXECUTION__MAX_CONCURRENCY": "3"}
    assert overrides == {"execution": {"max_concurrency": 4}}
    assert load_config(path, environ=environment, overrides=overrides) == config


def test_config_reads_process_environment_only_when_requested(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Isolate every namespaced value, including any set by the developer.
    import os

    for key in list(os.environ):
        if key.startswith("RECON_AGENT_") or key == "GROQ_API_KEY":
            monkeypatch.delenv(key)
    monkeypatch.setenv("RECON_AGENT_EXECUTION__MAX_CONCURRENCY", "8")
    assert load_config().execution.max_concurrency == 8
    assert load_config(environ={}).execution.max_concurrency == 1
    monkeypatch.setenv("GROQ_API_KEY", "sensitive-test-value")
    assert load_provider_secrets().groq_api_key is not None
    assert load_provider_secrets(environ={}).groq_api_key is None


def test_config_environment_typed_values() -> None:
    config = load_config(
        environ={
            "RECON_AGENT_SCOPE__ALLOW_PRIVATE_IPS": "true",
            "RECON_AGENT_EXECUTION__DEFAULT_TIMEOUT_SECONDS": "2.5",
            "RECON_AGENT_PLANNER__ENABLED": "true",
            "RECON_AGENT_PLANNER__MODEL": "123",
            "RECON_AGENT_LOGGING__LEVEL": "DEBUG",
            "RECON_AGENT_PERSISTENCE__DATABASE_PATH": "local.sqlite3",
            "RECON_AGENT_REPORTING__DEFAULT_FORMATS": '["json", "terminal"]',
            "UNRELATED": "ignored",
        }
    )
    assert config.scope.allow_private_ips is True
    assert config.execution.default_timeout_seconds == 2.5
    assert config.planner.model == "123"
    assert config.logging.level == "DEBUG"
    assert config.persistence.database_path == Path("local.sqlite3")
    assert config.reporting.default_formats == ["json", "terminal"]


@pytest.mark.parametrize(
    ("section", "field", "value"),
    [
        ("execution", "default_timeout_seconds", 0),
        ("execution", "default_timeout_seconds", -1),
        ("execution", "default_timeout_seconds", float("inf")),
        ("execution", "default_timeout_seconds", float("nan")),
        ("execution", "default_timeout_seconds", True),
        ("execution", "default_timeout_seconds", "30"),
        ("execution", "max_concurrency", 0),
        ("execution", "max_concurrency", -1),
        ("execution", "max_concurrency", 1.5),
        ("execution", "max_concurrency", True),
        ("execution", "max_output_bytes", 0),
        ("execution", "max_actions", -1),
        ("execution", "max_duration_seconds", 0),
        ("execution", "max_duration_seconds", 10),
        ("scope", "allow_subdomains", "false"),
        ("scope", "allow_private_ips", 1),
        ("planner", "enabled", True),
        ("planner", "provider", "unsupported"),
        ("planner", "model", "   "),
        ("planner", "max_iterations", 0),
        ("logging", "level", "TRACE"),
        ("logging", "structured", "yes"),
        ("persistence", "database_path", ""),
        ("persistence", "database_path", "\x00"),
        ("persistence", "database_path", Path("\x00")),
        ("reporting", "default_formats", []),
        ("reporting", "default_formats", ["json", "json"]),
        ("reporting", "default_formats", ["xml"]),
        ("reporting", "output_directory", 42),
        ("tools", "enabled", "true"),
    ],
)
def test_config_invalid_effective_values(
    section: str,
    field: str,
    value: object,
) -> None:
    with pytest.raises(ConfigurationError):
        load_config(environ={}, overrides={section: {field: value}})


@pytest.mark.parametrize(
    "values",
    [
        {"unknown": {}},
        {"execution": {"max_concurency": 2}},
        {"scope": {"targets": ["example.test"]}},
        {"tools": {"command": "unrestricted"}},
        {"tools": {"extra_shell_args": []}},
        {"planner": {"groq_api_key": "sensitive-test-value"}},
        {"execution": []},
    ],
)
def test_config_unknown_keys_and_wrong_sections(values: dict[str, object]) -> None:
    with pytest.raises(ConfigurationError):
        load_config(environ={}, overrides=values)


@pytest.mark.parametrize(
    "raw",
    [
        "[execution]\nmax_concurency = 2\n",
        'execution = "incorrect structure"\n',
        '[execution]\nmax_concurrency = "2"\n',
        'groq_api_key = "sensitive-test-value"\n',
    ],
)
def test_config_invalid_file_data(tmp_path: Path, raw: str) -> None:
    path = tmp_path / "invalid.toml"
    path.write_text(raw)
    with pytest.raises(ConfigurationError) as error:
        load_config(path, environ={})
    assert "sensitive-test-value" not in str(error.value)


@pytest.mark.parametrize("raw", [b"[broken", b"sensitive-test-value", b"\xff"])
def test_config_malformed_file(tmp_path: Path, raw: bytes) -> None:
    path = tmp_path / "broken.toml"
    path.write_bytes(raw)
    with pytest.raises(ConfigurationError, match="invalid TOML") as error:
        load_config(path, environ={})
    assert "sensitive-test-value" not in str(error.value)
    assert error.value.__cause__ is not None


def test_config_missing_file_fails(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError) as error:
        load_config(tmp_path / "absent.toml", environ={})
    assert isinstance(error.value.__cause__, FileNotFoundError)


@pytest.mark.parametrize(
    "environment",
    [
        {"RECON_AGENT_EXECUTION__MAX_CONCURRENCY": "eight"},
        {"RECON_AGENT_EXECUTION__MAX_CONCURRENCY": '"8"'},
        {"RECON_AGENT_EXECUTION__MAX_CONCURRENCY": "0"},
        {"RECON_AGENT_SCOPE__ALLOW_SUBDOMAINS": "yes"},
        {"RECON_AGENT_SCOPE__ALLOW_SUBDOMAINS": "1"},
        {"RECON_AGENT_LOGGING__LEVEL": "TRACE"},
        {"RECON_AGENT_EXECUTION__MAX_CONCURENCY": "2"},
        {"RECON_AGENT_UNKNOWN__ENABLED": "true"},
        {"RECON_AGENT_EXECUTION": "{}"},
        {"RECON_AGENT_TOOLS__ENABLED__EXTRA": "true"},
        {"RECON_AGENT_PLANNER__GROQ_API_KEY": "sensitive-test-value"},
        {"RECON_AGENT_TOOLS__ENABLED": "false", "RECON_AGENT_tools__enabled": "true"},
    ],
)
def test_config_invalid_environment(environment: dict[str, str]) -> None:
    with pytest.raises(ConfigurationError) as error:
        load_config(environ=environment)
    assert "sensitive-test-value" not in str(error.value)


def test_config_secrets_are_separate_and_redacted() -> None:
    raw = "sensitive-test-value"
    config = load_config(environ={"GROQ_API_KEY": raw})
    secrets = load_provider_secrets(environ={"GROQ_API_KEY": raw})
    assert secrets.groq_api_key is not None
    assert secrets.groq_api_key.get_secret_value() == raw
    for text in (
        repr(config),
        config.model_dump_json(),
        repr(secrets),
        str(secrets.model_dump()),
        secrets.model_dump_json(),
        str(secrets.groq_api_key),
    ):
        assert raw not in text
    assert secrets.model_dump() == {}
    assert secrets.model_dump(include={"groq_api_key"}) == {}
    assert ProviderSecrets(groq_api_key=SecretStr(raw)).model_dump() == {}
    assert load_provider_secrets(environ={}).groq_api_key is None
    assert load_provider_secrets(environ={"GROQ_API_KEY": ""}).groq_api_key is None


def test_config_imports_and_loading_have_no_runtime_side_effects(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    forbidden = Mock(side_effect=AssertionError("runtime side effect"))
    monkeypatch.setattr(Path, "open", forbidden)
    monkeypatch.setattr(Path, "mkdir", forbidden)
    monkeypatch.setattr(logging, "basicConfig", forbidden)
    import recon_agent
    import recon_agent.core.config as config_module

    importlib.reload(recon_agent)
    importlib.reload(config_module)
    config = config_module.load_config(
        environ={},
        overrides={
            "tools": {"enabled": True},
            "planner": {"enabled": True, "model": "operator-selected-model"},
            "persistence": {"enabled": True, "database_path": "data/state.sqlite3"},
            "reporting": {"output_directory": "output"},
        },
    )
    assert config.persistence.enabled
    config_module.load_provider_secrets(environ={})
    forbidden.assert_not_called()
    assert list(tmp_path.iterdir()) == []


def test_config_example_matches_defaults() -> None:
    example = Path(__file__).parents[2] / "config.example.toml"
    assert load_config(example, environ={}) == load_config(environ={})

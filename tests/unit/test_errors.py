"""Stable operational failure contracts, isolated from future subsystem behavior."""

import importlib
import json
import logging
import tomllib
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from recon_agent.core import errors
from recon_agent.core.config import AppConfig, load_config, load_provider_secrets
from recon_agent.core.errors import (
    BudgetExhaustedError,
    CancelledError,
    ConfigurationError,
    ErrorCode,
    ErrorContext,
    ErrorInfo,
    ParserError,
    PlannerValidationError,
    PolicyError,
    ProviderError,
    ReconAgentError,
    ScopeRejectedError,
    StateTransitionError,
    ToolError,
    ToolExecutionError,
    ToolTimeoutError,
    ToolUnavailableError,
)
from recon_agent.domain import ActionResult, Service

CASES = [
    (StateTransitionError, ReconAgentError, "state_transition_invalid", "state"),
    (ConfigurationError, ReconAgentError, "configuration_invalid", "configuration"),
    (ScopeRejectedError, PolicyError, "scope_rejected", "policy"),
    (BudgetExhaustedError, PolicyError, "budget_exhausted", "policy"),
    (ToolUnavailableError, ToolError, "tool_unavailable", "tool"),
    (ToolTimeoutError, ToolError, "tool_timeout", "tool"),
    (ToolExecutionError, ToolError, "tool_execution_failed", "tool"),
    (ParserError, ToolError, "parse_failed", "tool"),
    (ProviderError, ReconAgentError, "provider_failed", "provider"),
    (PlannerValidationError, ReconAgentError, "planner_validation_failed", "planner"),
    (CancelledError, ReconAgentError, "cancelled", "cancellation"),
]


@pytest.mark.parametrize(("error_type", "parent", "code", "category"), CASES)
def test_error_categories_codes_messages_and_round_trip(
    error_type: type[ReconAgentError],
    parent: type[ReconAgentError],
    code: str,
    category: str,
) -> None:
    error = error_type("Concise diagnostic", context=ErrorContext(action_id="action-1"))
    assert isinstance(error, parent) and isinstance(error, ReconAgentError)
    assert str(error) == error.message == "Concise diagnostic"
    assert repr(error) == f"{error_type.__name__}('Concise diagnostic')"
    assert error.code.value == code and error.category.value == category
    assert not error.retryable
    assert error.context.action_id == "action-1"
    info = error.to_error_info()
    assert info.category == error.category
    assert info.model_dump(mode="json")["code"] == code
    assert set(info.model_dump()) == {"code", "message", "retryable", "context"}
    assert ErrorInfo.model_validate(info.model_dump()) == info
    assert ErrorInfo.model_validate_json(info.model_dump_json()) == info
    assert json.loads(info.model_dump_json()) == info.model_dump(mode="json")


@pytest.mark.parametrize("base", [ReconAgentError, PolicyError, ToolError])
def test_error_catch_boundaries_require_concrete_category(
    base: type[ReconAgentError],
) -> None:
    with pytest.raises(TypeError, match="concrete"):
        base("failure")


@pytest.mark.parametrize("error_type", [row[0] for row in CASES])
def test_error_retryability_is_explicit_and_not_authorization(
    error_type: type[ReconAgentError],
) -> None:
    if issubclass(error_type, ToolError) or error_type is ProviderError:
        error = error_type("Known transient failure", retryable=True)
        assert error.retryable and error.to_error_info().retryable
        assert not hasattr(error, "retry")
    else:
        with pytest.raises(ValidationError, match="not retryable"):
            error_type("Unapproved repeat", retryable=True)


def test_error_context_is_allowlisted_scalar_data() -> None:
    context = ErrorContext(
        action_id="a",
        target_id="t",
        capability="probe_http",
        tool="fixture",
        provider="fixture",
        timeout_seconds=30,
        exit_code=2,
        configuration_source="file",
    )
    assert ErrorContext.model_validate_json(context.model_dump_json()) == context
    assert context.model_dump(mode="json")["timeout_seconds"] == 30.0
    with pytest.raises(ValidationError, match="frozen"):
        context.action_id = "changed"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("action_id", ""),
        ("target_id", " "),
        ("tool", "x" * 257),
        ("provider", object()),
        ("capability", {"command": "data"}),
        ("timeout_seconds", -1),
        ("timeout_seconds", 0),
        ("timeout_seconds", float("inf")),
        ("timeout_seconds", float("nan")),
        ("timeout_seconds", True),
        ("timeout_seconds", "30"),
        ("exit_code", True),
        ("exit_code", 1.5),
        ("configuration_source", "unknown"),
    ],
)
def test_error_context_rejects_invalid_or_non_json_data(
    field: str, value: object
) -> None:
    with pytest.raises(ValidationError):
        ErrorContext.model_validate({field: value})


@pytest.mark.parametrize(
    "field",
    [
        "command",
        "shell_command",
        "script",
        "raw_environment",
        "environment",
        "api_key",
        "credentials",
        "traceback",
        "raw_exception",
        "stdout",
        "stderr",
    ],
)
@pytest.mark.parametrize("model", [ErrorInfo, ErrorContext])
def test_error_models_reject_secret_output_and_execution_dump_fields(
    field: str,
    model: type[ErrorInfo] | type[ErrorContext],
) -> None:
    values = (
        {"code": ErrorCode.TOOL_TIMEOUT, "message": "Deadline reached"}
        if model is ErrorInfo
        else {}
    )
    with pytest.raises(ValidationError) as error:
        model.model_validate({**values, field: "sensitive-test-value"})
    assert "sensitive-test-value" not in str(error.value)
    assert "sensitive-test-value" not in repr(error.value)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("code", "unknown"),
        ("message", ""),
        ("message", " "),
        ("message", "x" * 1025),
        ("retryable", 1),
        ("context", object()),
    ],
)
def test_error_info_validates_structure(field: str, value: object) -> None:
    values = {"code": ErrorCode.PARSE_FAILED, "message": "Invalid record", field: value}
    with pytest.raises(ValidationError):
        ErrorInfo.model_validate(values)


def test_error_info_revalidates_nested_context_and_is_frozen() -> None:
    with pytest.raises(ValidationError):
        ErrorInfo.model_validate(
            {
                "code": ErrorCode.TOOL_TIMEOUT,
                "message": "Deadline reached",
                "context": {"api_key": "sensitive-test-value"},
            }
        )
    info = ParserError("Invalid record").to_error_info()
    with pytest.raises(ValidationError, match="frozen"):
        info.message = "changed"


@pytest.mark.parametrize(
    ("file_data", "environment", "overrides", "cause_type", "source"),
    [
        (b"[broken sensitive-test-value", {}, {}, tomllib.TOMLDecodeError, "file"),
        (b"\xff", {}, {}, UnicodeDecodeError, "file"),
        (
            None,
            {"RECON_AGENT_EXECUTION__MAX_CONCURRENCY": "sensitive-test-value"},
            {},
            json.JSONDecodeError,
            "environment",
        ),
        (
            None,
            {},
            {"planner": {"groq_api_key": "sensitive-test-value"}},
            ValidationError,
            "validation",
        ),
    ],
)
def test_config_errors_chain_causes_without_copying_inputs_into_diagnostics(
    tmp_path: Path,
    file_data: bytes | None,
    environment: dict[str, str],
    overrides: dict[str, object],
    cause_type: type[Exception],
    source: str,
) -> None:
    path = None
    if file_data is not None:
        path = tmp_path / "config.toml"
        path.write_bytes(file_data)
    with pytest.raises(ConfigurationError) as caught:
        load_config(path, environ=environment, overrides=overrides)
    error = caught.value
    assert isinstance(error.__cause__, cause_type)
    assert error.context.configuration_source == source
    assert error.code is ErrorCode.CONFIGURATION_INVALID
    secrets = load_provider_secrets(environ={"GROQ_API_KEY": "sensitive-test-value"})
    for text in (
        str(error),
        repr(error),
        repr(error.to_error_info()),
        error.to_error_info().model_dump_json(),
        repr(secrets),
    ):
        assert "sensitive-test-value" not in text
    assert secrets.model_dump() == {}


@pytest.mark.parametrize("name", ["missing.toml", "directory", "\x00"])
def test_config_unreadable_path_is_project_error(tmp_path: Path, name: str) -> None:
    (tmp_path / "directory").mkdir()
    with pytest.raises(ConfigurationError) as error:
        load_config(tmp_path / name, environ={})
    assert isinstance(error.value.__cause__, (OSError, ValueError))
    assert error.value.context.configuration_source == "file"


def test_direct_model_validation_stays_pydantic() -> None:
    with pytest.raises(ValidationError):
        Service(id="s", asset_id="a", host_id="h", port=70000, transport="tcp")
    with pytest.raises(ValidationError):
        AppConfig.model_validate({"execution": {"max_concurrency": 0}})


@pytest.mark.parametrize(
    ("status", "error_type"),
    [
        ("partial", ParserError),
        ("failed", ToolExecutionError),
        ("rejected", ScopeRejectedError),
        ("rejected", PlannerValidationError),
        ("timeout", ToolTimeoutError),
        ("cancelled", CancelledError),
    ],
)
def test_action_result_shared_error_and_partial_evidence(
    status: str,
    error_type: type[ReconAgentError],
) -> None:
    result = ActionResult.model_validate(
        {
            "id": "r",
            "action_id": "a",
            "status": status,
            "recorded_at": datetime(2026, 10, 5, tzinfo=UTC),
            "error": error_type("Outcome limitation").to_error_info(),
            "execution_ids": ("execution-1",),
        }
    )
    assert result.error is not None
    assert result.error.code is error_type("Outcome limitation").code
    assert ActionResult.model_validate_json(result.model_dump_json()) == result


@pytest.mark.parametrize(
    ("status", "error_type"),
    [
        ("completed", ParserError),
        ("rejected", ParserError),
        ("timeout", ToolExecutionError),
        ("cancelled", ToolTimeoutError),
        ("failed", ScopeRejectedError),
        ("partial", CancelledError),
    ],
)
def test_action_result_cannot_relabel_failure_as_success_or_policy_outcome(
    status: str,
    error_type: type[ReconAgentError],
) -> None:
    with pytest.raises(ValidationError):
        ActionResult.model_validate(
            {
                "id": "r",
                "action_id": "a",
                "status": status,
                "recorded_at": datetime(2026, 10, 5, tzinfo=UTC),
                "error": error_type("Failure").to_error_info(),
            }
        )


def test_error_imports_conversion_and_serialization_have_no_runtime_side_effects(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    forbidden = Mock(side_effect=AssertionError("runtime side effect"))
    monkeypatch.setattr(Path, "open", forbidden)
    monkeypatch.setattr(Path, "mkdir", forbidden)
    monkeypatch.setattr(logging, "basicConfig", forbidden)
    # Reload only the export surface, preserving concrete class identities.
    import recon_agent.core

    importlib.reload(recon_agent.core)
    errors.ProviderError("Failure").to_error_info().model_dump_json()
    forbidden.assert_not_called()
    assert list(tmp_path.iterdir()) == []
    assert set(errors.__all__) == {
        "ErrorCode",
        "ErrorCategory",
        "ErrorContext",
        "ErrorInfo",
        "ReconAgentError",
        "ConfigurationError",
        "PolicyError",
        "ScopeRejectedError",
        "ScopeRejectionReason",
        "BudgetExhaustedError",
        "ToolError",
        "ToolUnavailableError",
        "ToolTimeoutError",
        "ToolExecutionError",
        "ParserError",
        "ProviderError",
        "PlannerValidationError",
        "CancelledError",
        "StateTransitionError",
    }

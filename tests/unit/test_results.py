"""Typed discriminated outcomes; also checked directly with strict Mypy."""

import json
from typing import assert_type

import pytest
from pydantic import TypeAdapter, ValidationError

from recon_agent.core.config import load_provider_secrets
from recon_agent.core.errors import ErrorInfo, ParserError, ProviderError
from recon_agent.core.results import Failure, OperationResult, Success
from recon_agent.domain import Service


def _port(result: OperationResult[Service]) -> int | None:
    if result.status == "success":
        assert_type(result.value, Service)
        return result.value.port
    assert_type(result.error, ErrorInfo)
    return None


def test_result_success_preserves_typed_value_and_json_round_trip() -> None:
    service = Service(id="s", asset_id="a", host_id="h", port=443, transport="tcp")
    result: OperationResult[Service] = Success[Service](value=service)
    assert _port(result) == 443
    adapter = TypeAdapter[OperationResult[Service]](OperationResult[Service])
    restored = adapter.validate_json(adapter.dump_json(result))
    assert restored == result
    assert isinstance(restored, Success)
    assert isinstance(restored.value, Service)
    assert restored.model_dump(mode="json")["value"]["port"] == 443
    assert Success[int](value=5).model_dump(mode="json") == {
        "status": "success",
        "value": 5,
    }


def test_result_failure_contains_serializable_error_without_value() -> None:
    failure = Failure(error=ParserError("Invalid record").to_error_info())
    result: OperationResult[Service] = failure
    assert _port(result) is None
    assert not hasattr(failure, "value")
    dumped = failure.model_dump(mode="json")
    assert dumped["status"] == "failure" and dumped["error"]["code"] == "parse_failed"
    assert json.loads(failure.model_dump_json()) == dumped
    adapter = TypeAdapter[OperationResult[Service]](OperationResult[Service])
    assert adapter.validate_json(failure.model_dump_json()) == failure
    assert Failure.model_validate(failure.model_dump()) == failure


@pytest.mark.parametrize(
    "data",
    [
        {"status": "success"},
        {"status": "failure"},
        {"status": "false", "value": 5},
        {"status": "success", "value": 5, "error": {}},
        {"status": "failure", "value": 5, "error": {}},
        {"status": "failure", "error": None},
        {"status": "unknown", "value": 5},
        {"status": 1, "value": 5},
        {"status": "success", "value": "5"},
    ],
)
def test_result_union_rejects_contradictory_missing_or_incorrect_data(
    data: dict[str, object],
) -> None:
    adapter = TypeAdapter[OperationResult[int]](OperationResult[int])
    with pytest.raises(ValidationError):
        adapter.validate_python(data)


@pytest.mark.parametrize("value", [1, 0, "true", False])
def test_success_discriminator_requires_success_tag(value: object) -> None:
    with pytest.raises(ValidationError):
        Success[int].model_validate({"status": value, "value": 5})


@pytest.mark.parametrize("value", [1, 0, "false", True])
def test_failure_discriminator_requires_failure_tag(value: object) -> None:
    with pytest.raises(ValidationError):
        Failure.model_validate(
            {"status": value, "error": ParserError("Failure").to_error_info()}
        )


@pytest.mark.parametrize(
    "field", ["command", "shell_command", "api_key", "raw_environment"]
)
def test_result_models_reject_extra_secret_and_command_fields(field: str) -> None:
    for model, data in (
        (Success[int], {"value": 5}),
        (Failure, {"error": ProviderError("Failure").to_error_info()}),
    ):
        with pytest.raises(ValidationError):
            model.model_validate({**data, field: "sensitive-test-value"})


def test_result_cannot_contain_exception_object_or_replace_failure_with_value() -> None:
    with pytest.raises(ValidationError):
        Failure.model_validate({"error": ParserError("Failure")})
    with pytest.raises(ValidationError, match="frozen"):
        Success[int](value=5).value = 6
    with pytest.raises(ValidationError):
        Success[int].model_validate({"status": "failure", "value": 5})


def test_result_keeps_modeled_credentials_redacted() -> None:
    secrets = load_provider_secrets(environ={"GROQ_API_KEY": "sensitive-test-value"})
    # Generic payloads retain their own safe serializer; no credential conversion.
    success = Success(value=secrets)
    assert success.model_dump(mode="json") == {"status": "success", "value": {}}
    assert "sensitive-test-value" not in repr(success)
    assert "sensitive-test-value" not in success.model_dump_json()

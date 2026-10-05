"""Offline registry facts and trust boundaries, with test-only adapter classes."""

import asyncio
import importlib
import json
import logging
import socket
import subprocess
from dataclasses import FrozenInstanceError
from itertools import permutations
from pathlib import Path
from unittest.mock import Mock

import pytest
from pydantic import BaseModel, ConfigDict, ValidationError

import recon_agent.tools as tools
from recon_agent.core.errors import ConfigurationError, ErrorCode, ErrorInfo
from recon_agent.core.results import Failure, Success
from recon_agent.domain import ActionRequest, PlannerDecision
from recon_agent.domain.capabilities import (
    CapabilityDescriptor,
    CapabilityId,
    RiskClass,
)
from recon_agent.execution import AsyncProcessRunner
from recon_agent.tools import (
    AdapterAvailability,
    AdapterDefinition,
    AdapterRegistration,
    CapabilityCatalogEntry,
    ToolAdapter,
    ToolRegistry,
)


class DnsInput(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    target: str


class DnsOutput(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    addresses: tuple[str, ...]


class FakeAdapter(ToolAdapter):
    """No execution methods; internal details deliberately unsuitable for planner."""

    def __init__(
        self,
        adapter_id: str = "fixture-dns",
        capability: CapabilityId = CapabilityId.RESOLVE_DNS,
    ) -> None:
        self._definition = AdapterDefinition(
            adapter_id=adapter_id,
            descriptor=CapabilityDescriptor(
                capability=capability,
                description="Collect metadata for an authorized target.",
                risk_class=RiskClass.ACTIVE_SAFE,
            ),
            input_schema=DnsInput,
            output_schema=DnsOutput,
        )
        self.executable = "/private/internal/fixture-binary"
        self.argv = ("--private-fixture-flag",)
        self.environment = {"PRIVATE_FIXTURE_VALUE": "internal-only"}
        self.runner = Mock(side_effect=AssertionError("must not execute"))

    @property
    def definition(self) -> AdapterDefinition:
        return self._definition


@pytest.fixture(autouse=True)
def no_runtime(monkeypatch: pytest.MonkeyPatch) -> Mock:
    blocked = Mock(side_effect=AssertionError("registry attempted runtime activity"))
    for name in (
        "socket",
        "getaddrinfo",
        "gethostbyname",
        "gethostbyname_ex",
        "gethostbyaddr",
        "create_connection",
    ):
        monkeypatch.setattr(socket, name, blocked)
    for name in ("Popen", "run", "call", "check_call", "check_output"):
        monkeypatch.setattr(subprocess, name, blocked)
    monkeypatch.setattr(asyncio, "create_subprocess_exec", blocked)
    monkeypatch.setattr(asyncio, "create_subprocess_shell", blocked)
    monkeypatch.setattr(AsyncProcessRunner, "run", blocked)
    yield blocked
    blocked.assert_not_called()


def registration(
    adapter: ToolAdapter,
    availability: AdapterAvailability = AdapterAvailability.AVAILABLE,
) -> AdapterRegistration:
    return AdapterRegistration(adapter, availability)


def test_explicit_composition_resolution_and_typed_contracts() -> None:
    adapter = FakeAdapter()
    registry = ToolRegistry((registration(adapter),))
    assert registry.is_known_capability(CapabilityId.RESOLVE_DNS)
    assert registry.has_capability("resolve_dns")
    assert registry.has_adapter("fixture-dns")
    outcome = registry.resolve(CapabilityId.RESOLVE_DNS)
    assert isinstance(outcome, Success)
    assert outcome.value is adapter
    definition = registry.definition("fixture-dns")
    assert isinstance(definition, Success)
    assert definition.value.adapter_id == "fixture-dns"
    assert definition.value.descriptor.capability is CapabilityId.RESOLVE_DNS
    assert definition.value.input_schema is DnsInput
    assert definition.value.output_schema is DnsOutput
    assert definition.value.input_schema.model_validate({"target": "example.test"})
    with pytest.raises(ValidationError):
        definition.value.input_schema.model_validate({"target": 123})
    adapter.runner.assert_not_called()


def test_empty_registry_does_not_claim_scanner_support() -> None:
    registry = ToolRegistry()
    assert (
        registry.list_capabilities()
        == registry.list_adapters()
        == registry.catalog()
        == ()
    )
    for capability in CapabilityId:
        assert registry.is_known_capability(capability)
        assert not registry.has_capability(capability)
        result = registry.resolve(capability)
        assert isinstance(result, Failure)
        assert result.error.code is ErrorCode.TOOL_UNAVAILABLE
    assert not registry.has_adapter("nmap")


@pytest.mark.parametrize(
    "capability",
    [
        "run_command",
        "execute_shell",
        "run_binary",
        "custom_command",
        "not_a_real_capability",
        "nmap",
        "resolve_dns --flag",
        "/bin/sh",
        "resolve_dns;command",
        "$(command)",
        "resolve_dns\n",
        " resolve_dns",
        "RESOLVE_DNS",
        "",
        "python.module",
        "x" * 2000,
    ],
)
def test_unknown_capability_fails_closed_without_execution(capability: str) -> None:
    adapter = FakeAdapter()
    registry = ToolRegistry((registration(adapter),))
    assert not registry.is_known_capability(capability)
    assert not registry.has_capability(capability)
    result = registry.resolve(capability)
    assert isinstance(result, Failure)
    assert result.error.code is ErrorCode.PLANNER_VALIDATION_FAILED
    assert not result.error.retryable
    assert result.error.context.capability is None  # Do not echo arbitrary input.
    assert ErrorInfo.model_validate_json(result.error.model_dump_json()) == result.error
    adapter.runner.assert_not_called()
    assert registry.list_adapters() == ("fixture-dns",)


@pytest.mark.parametrize("adapter_id", ["unknown", "/bin/sh", "nmap", "$(command)"])
def test_unknown_adapter_lookup_is_local_failure(adapter_id: str) -> None:
    registry = ToolRegistry()
    assert not registry.has_adapter(adapter_id)
    outcome = registry.definition(adapter_id)
    assert isinstance(outcome, Failure)
    assert outcome.error.code is ErrorCode.TOOL_UNAVAILABLE
    assert outcome.error.context.tool is None


@pytest.mark.parametrize("availability", list(AdapterAvailability))
def test_availability_is_declared_snapshot_not_registration_or_authority(
    availability: AdapterAvailability,
) -> None:
    adapter = FakeAdapter()
    registry = ToolRegistry((AdapterRegistration(adapter, availability),))
    assert registry.has_capability("resolve_dns")
    assert registry.catalog()[0].availability is availability
    result = registry.resolve("resolve_dns")
    if availability is AdapterAvailability.AVAILABLE:
        assert isinstance(result, Success) and result.value is adapter
    else:
        assert isinstance(result, Failure)
        assert result.error.code is ErrorCode.TOOL_UNAVAILABLE
        assert result.error.context.capability == "resolve_dns"
        assert result.error.context.tool == "fixture-dns"
    adapter.runner.assert_not_called()


def test_default_availability_is_not_checked_and_fails_closed() -> None:
    registry = ToolRegistry((AdapterRegistration(FakeAdapter()),))
    assert registry.catalog()[0].availability is AdapterAvailability.NOT_CHECKED
    assert isinstance(registry.resolve("resolve_dns"), Failure)


@pytest.mark.parametrize("same_instance", [True, False])
def test_duplicate_adapter_id_rejected(same_instance: bool) -> None:
    first = FakeAdapter()
    second = first if same_instance else FakeAdapter(capability=CapabilityId.PROBE_HTTP)
    with pytest.raises(ConfigurationError) as caught:
        ToolRegistry((registration(first), registration(second)))
    assert caught.value.code is ErrorCode.CONFIGURATION_INVALID
    assert caught.value.context.tool == "fixture-dns"


def test_conflicting_capability_rejected_without_fallback() -> None:
    entries = (registration(FakeAdapter("first")), registration(FakeAdapter("second")))
    for order in permutations(entries):
        with pytest.raises(ConfigurationError) as caught:
            ToolRegistry(order)
        assert caught.value.code is ErrorCode.CONFIGURATION_INVALID
        assert caught.value.context.capability == "resolve_dns"


@pytest.mark.parametrize(
    "adapter_id",
    [
        "",
        " ",
        " /bin/sh",
        "bad id",
        "bad;id",
        "bad/id",
        "bad.id",
        "bad\n",
        "A",
        "x" * 65,
    ],
)
def test_adapter_identity_rejects_ambiguous_or_executable_syntax(
    adapter_id: str,
) -> None:
    with pytest.raises(ValidationError):
        FakeAdapter(adapter_id)


@pytest.mark.parametrize("field", ["description", "capability", "risk_class"])
def test_descriptor_requires_complete_metadata(field: str) -> None:
    values = FakeAdapter().definition.descriptor.model_dump()
    del values[field]
    with pytest.raises(ValidationError):
        CapabilityDescriptor.model_validate(values)


@pytest.mark.parametrize("description", ["", " ", "x" * 1025, 123])
def test_description_is_bounded_strict_nonblank(description: object) -> None:
    values = FakeAdapter().definition.descriptor.model_dump()
    with pytest.raises(ValidationError):
        CapabilityDescriptor.model_validate({**values, "description": description})


FORBIDDEN = (
    "executable",
    "argv",
    "command",
    "shell_command",
    "script",
    "command_template",
    "import_path",
    "python_module",
    "adapter",
    "adapter_id",
    "environment",
    "runner",
)


@pytest.mark.parametrize("field", FORBIDDEN)
@pytest.mark.parametrize("model", [CapabilityDescriptor, CapabilityCatalogEntry])
def test_planner_descriptor_rejects_execution_and_implementation_fields(
    field: str,
    model: type[BaseModel],
) -> None:
    values = FakeAdapter().definition.descriptor.model_dump()
    if model is CapabilityCatalogEntry:
        values["availability"] = AdapterAvailability.AVAILABLE
    with pytest.raises(ValidationError):
        model.model_validate({**values, field: "private-fixture-value"})


def test_planner_catalog_explicit_projection_does_not_leak_internal_details() -> None:
    adapter = FakeAdapter()
    registry = ToolRegistry((registration(adapter),))
    entry = registry.catalog()[0]
    public = entry.model_dump(mode="json")
    assert set(public) == {"capability", "description", "risk_class", "availability"}
    assert public["capability"] == "resolve_dns"
    encoded = entry.model_dump_json()
    assert json.loads(encoded) == public
    assert CapabilityCatalogEntry.model_validate_json(encoded) == entry
    assert not any(key in public for key in FORBIDDEN)
    for secret in (
        adapter.executable,
        adapter.argv[0],
        "PRIVATE_FIXTURE_VALUE",
        "internal-only",
        "DnsInput",
        "DnsOutput",
        "fixture-dns",
        "FakeAdapter",
    ):
        assert secret not in encoded
    assert "input_schema" not in adapter.definition.model_dump()
    assert "output_schema" not in adapter.definition.model_dump()


def test_capability_and_risk_enum_wire_contracts_are_finite() -> None:
    assert len(CapabilityId) == 10
    assert set(RiskClass) == {RiskClass.PASSIVE, RiskClass.ACTIVE_SAFE}
    for capability in CapabilityId:
        descriptor = CapabilityDescriptor(
            capability=capability,
            description="Semantic operation",
            risk_class=RiskClass.PASSIVE,
        )
        assert descriptor.model_dump(mode="json")["capability"] == capability.value
        assert (
            CapabilityDescriptor.model_validate_json(descriptor.model_dump_json())
            == descriptor
        )
    with pytest.raises(ValidationError):
        CapabilityDescriptor.model_validate(
            {
                "capability": "run_command",
                "description": "Unknown",
                "risk_class": RiskClass.PASSIVE,
            }
        )


def test_listings_and_catalog_stable_across_composition_order() -> None:
    entries = (
        registration(FakeAdapter("z-dns")),
        registration(FakeAdapter("a-http", CapabilityId.PROBE_HTTP)),
        registration(FakeAdapter("m-tls", CapabilityId.INSPECT_TLS)),
    )
    expected = None
    for order in permutations(entries):
        registry = ToolRegistry(iter(order))
        actual = (
            registry.list_capabilities(),
            registry.list_adapters(),
            tuple(item.model_dump_json() for item in registry.catalog()),
        )
        assert registry.list_capabilities() == tuple(
            sorted(entry.adapter.definition.descriptor.capability for entry in entries)
        )
        assert registry.list_adapters() == ("a-http", "m-tls", "z-dns")
        if expected is None:
            expected = actual
        assert actual == expected


def test_composition_and_public_collections_are_immutable_snapshots() -> None:
    adapter = FakeAdapter()
    entries = [registration(adapter)]
    registry = ToolRegistry(entries)
    entries.clear()
    adapter._definition = FakeAdapter("changed", CapabilityId.PROBE_HTTP).definition
    assert registry.list_capabilities() == (CapabilityId.RESOLVE_DNS,)
    assert registry.list_adapters() == ("fixture-dns",)
    assert registry.catalog()[0].capability is CapabilityId.RESOLVE_DNS
    with pytest.raises(FrozenInstanceError):
        registry._capabilities = {}
    with pytest.raises(TypeError):
        registry._capabilities[CapabilityId.PROBE_HTTP] = object()
    with pytest.raises(TypeError):
        registry.list_capabilities()[0] = CapabilityId.PROBE_HTTP
    with pytest.raises(TypeError):
        registry.catalog()[0] = object()
    with pytest.raises(ValidationError):
        registry.catalog()[0].description = "changed"
    definition = registry.definition("fixture-dns")
    assert isinstance(definition, Success)
    with pytest.raises(ValidationError):
        definition.value.adapter_id = "changed"
    changed_dump = registry.catalog()[0].model_dump()
    changed_dump["description"] = "changed"
    assert registry.catalog()[0].description != "changed"
    assert isinstance(registry.resolve("resolve_dns"), Success)
    assert ToolRegistry().catalog() == ()


@pytest.mark.parametrize(
    "problem",
    ["schema", "identity", "capability", "availability", "adapter", "registration"],
)
def test_malformed_registration_is_canonical_configuration_error(problem: str) -> None:
    adapter = FakeAdapter()
    entry = registration(adapter)
    if problem == "schema":
        adapter._definition = adapter.definition.model_copy(
            update={"input_schema": str}
        )
    elif problem == "identity":
        adapter._definition = adapter.definition.model_copy(
            update={"adapter_id": "/bin/sh"}
        )
    elif problem == "capability":
        descriptor = adapter.definition.descriptor.model_copy(
            update={"capability": "run_command"}
        )
        adapter._definition = adapter.definition.model_copy(
            update={"descriptor": descriptor}
        )
    elif problem == "availability":
        entry = AdapterRegistration(adapter, "available")
    elif problem == "adapter":
        entry = AdapterRegistration(object())
    else:
        entry = object()
    with pytest.raises(ConfigurationError) as caught:
        ToolRegistry((entry,))
    assert caught.value.code is ErrorCode.CONFIGURATION_INVALID
    assert not caught.value.retryable
    assert "/bin/sh" not in caught.value.to_error_info().model_dump_json()


@pytest.mark.parametrize("config", [{}, {"strict": True}, {"extra": "forbid"}])
@pytest.mark.parametrize("field", ["input_schema", "output_schema"])
def test_adapter_contracts_require_strict_extra_forbid(
    config: dict, field: str
) -> None:
    class LooseSchema(BaseModel):
        model_config = ConfigDict(**config)

    values = {
        "adapter_id": "fixture-dns",
        "descriptor": FakeAdapter().definition.descriptor,
        "input_schema": DnsInput,
        "output_schema": DnsOutput,
    }
    values[field] = LooseSchema
    with pytest.raises(ValidationError):
        AdapterDefinition.model_validate(values)


@pytest.mark.parametrize("capability", ["resolve_dns", "probe_http", "run_command"])
def test_action_request_remains_capability_intent_with_boundary_lookup(
    capability: str,
) -> None:
    request = ActionRequest(
        id="action-1",
        capability=capability,
        target="example.test",
        reason="Add evidence",
    )
    registry = ToolRegistry((registration(FakeAdapter()),))
    outcome = registry.resolve(request.capability)
    if capability == "resolve_dns":
        assert isinstance(outcome, Success)
    else:
        assert isinstance(outcome, Failure)
        assert outcome.error.code is (
            ErrorCode.TOOL_UNAVAILABLE
            if capability == "probe_http"
            else ErrorCode.PLANNER_VALIDATION_FAILED
        )
    assert ActionRequest.model_validate_json(request.model_dump_json()) == request
    assert not any(key in ActionRequest.model_fields for key in FORBIDDEN)
    assert not any(key in PlannerDecision.model_fields for key in FORBIDDEN)


@pytest.mark.parametrize("field", FORBIDDEN[:8])
def test_action_request_rejects_executable_and_import_parameters(field: str) -> None:
    with pytest.raises(ValidationError):
        ActionRequest(
            id="action-1",
            capability="resolve_dns",
            target="example.test",
            reason="Add evidence",
            parameters={"options": [{field.upper(): "private-fixture-value"}]},
        )


def test_import_construction_and_lookup_no_startup_or_execution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    blocked = Mock(side_effect=AssertionError("unexpected startup"))
    adapter = FakeAdapter()
    before = dict(logging.Logger.manager.loggerDict)
    for method in (
        "iterdir",
        "glob",
        "rglob",
        "read_text",
        "read_bytes",
        "write_text",
        "mkdir",
    ):
        monkeypatch.setattr(Path, method, blocked)
    monkeypatch.setattr(logging, "basicConfig", blocked)
    monkeypatch.setattr(importlib, "import_module", blocked)
    importlib.reload(tools)
    registry = ToolRegistry((registration(adapter),))
    assert isinstance(registry.resolve("resolve_dns"), Success)
    assert isinstance(registry.resolve("run_command"), Failure)
    registry.catalog()
    registry.list_capabilities()
    registry.list_adapters()
    registry.definition("fixture-dns")
    blocked.assert_not_called()
    adapter.runner.assert_not_called()
    assert before == logging.Logger.manager.loggerDict
    assert not hasattr(tools, "REGISTRY")
    assert not hasattr(registry, "register")

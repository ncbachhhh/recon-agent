"""Offline SMB profile, current authorization, resources and generic provenance."""

import asyncio
import base64
import json
import socket
import subprocess
from dataclasses import replace
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from recon_agent.core.config.models import ExecutionConfig
from recon_agent.core.errors import ConfigurationError, ErrorCode, StateTransitionError
from recon_agent.core.results import Failure, Success
from recon_agent.domain import (
    ActionRequest,
    ActionResult,
    Asset,
    Host,
    ReconStateMachine,
    Scope,
    Service,
    Target,
)
from recon_agent.domain.capabilities import CapabilityId, RiskClass
from recon_agent.domain.protocols import ProtocolFamily, ProtocolMetadataOutput
from recon_agent.execution import AsyncProcessRunner
from recon_agent.policy import (
    ActionCanonicalizer,
    ActionDeduplicator,
    ActionPolicyConfig,
    ActionPolicyValidator,
    BudgetController,
    ExecutionBudget,
    ScopeValidator,
)
from recon_agent.tools import AdapterAvailability, AdapterRegistration, ToolRegistry
from recon_agent.tools.smb import SmbAdapter
from recon_agent.tools.smb_models import (
    SmbContext,
    SmbInput,
    SmbOutput,
    SmbServiceBinding,
)
from recon_agent.tools.smb_parser import MAX_RESPONSE_BYTES

WHEN = datetime(2026, 10, 8, tzinfo=UTC)
CONTEXT = SmbContext(execution_id="smb-execution", collected_at=WHEN)
FIXTURES = Path(__file__).parents[2] / "fixtures/smb"


def fixture_wire(name):
    return bytes.fromhex(json.loads((FIXTURES / "negotiation.json").read_text())[name])


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    blocked = Mock(
        side_effect=AssertionError("SMB tests attempted real contact/process")
    )
    for name in (
        "getaddrinfo",
        "gethostbyname",
        "gethostbyname_ex",
        "gethostbyaddr",
        "create_connection",
    ):
        monkeypatch.setattr(socket, name, blocked)
    for name in ("connect", "connect_ex", "sendto", "bind", "listen"):
        original = getattr(socket.socket, name)

        def guarded(self, *args, _original=original, **kwargs):
            if self.family != socket.AF_UNIX:
                return blocked()
            return _original(self, *args, **kwargs)

        monkeypatch.setattr(socket.socket, name, guarded)
    for name in ("Popen", "run", "call", "check_call", "check_output"):
        monkeypatch.setattr(subprocess, name, blocked)
    monkeypatch.setattr(asyncio, "open_connection", blocked)
    monkeypatch.setattr(asyncio, "create_subprocess_exec", blocked)
    monkeypatch.setattr(asyncio, "create_subprocess_shell", blocked)
    monkeypatch.setattr(AsyncProcessRunner, "run", blocked)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    yield blocked
    blocked.assert_not_called()


def binding(**changes):
    observed = Service(
        id="service",
        asset_id="asset",
        host_id="host",
        port=445,
        transport="tcp",
        protocol="smb",
        product="Samba",
    )
    values = dict(host="example.test", address="192.0.2.10", service=observed)
    values.update(changes)
    return SmbServiceBinding(**values)


class FakeTransport:
    def __init__(self, result=None, mutate=None):
        self.result = result if result is not None else fixture_wire("smb302")
        self.calls = []
        self.mutate = mutate
        # Regression sentinel: any client SMB message/authentication path fails.
        self.authenticate = Mock(side_effect=AssertionError("must never authenticate"))
        self.send = Mock(side_effect=AssertionError("must never send SMB messages"))

    async def negotiate(self, address, port, timeout_seconds, max_bytes):
        self.calls.append((address, port, timeout_seconds, max_bytes))
        if self.mutate:
            self.mutate()
        if isinstance(self.result, BaseException):
            raise self.result
        if callable(self.result):
            return await self.result()
        return self.result


def compose(
    fake=None,
    bindings=None,
    scope=None,
    config=None,
    limits=None,
    availability=AdapterAvailability.AVAILABLE,
    clock=None,
):
    fake = fake or FakeTransport()
    config = config or ExecutionConfig()
    adapter = SmbAdapter(bindings or (binding(),), config, fake)
    registry = ToolRegistry((AdapterRegistration(adapter, availability),))
    validator = ScopeValidator(
        scope
        or Scope(
            id="scope",
            roots=(
                Target(id="name", kind="hostname", value="example.test"),
                Target(id="address", kind="cidr", value="192.0.2.0/24"),
                Target(id="ipv6", kind="ip", value="2001:db8::10"),
            ),
        )
    )
    budgets = BudgetController(
        limits or ExecutionBudget.from_config(config),
        registry,
        **({"clock": clock} if clock else {}),
    )
    owner = ReconStateMachine()
    dedup = ActionDeduplicator(ActionCanonicalizer(registry, validator), owner)
    policy = ActionPolicyValidator(
        registry,
        validator,
        ActionPolicyConfig(
            allowed_capabilities=frozenset({CapabilityId.INSPECT_PROTOCOL}),
            allowed_risk_classes=frozenset({RiskClass.ACTIVE_SAFE}),
        ),
        budgets,
        dedup,
    )
    return adapter, fake, policy, budgets, owner


def request(**changes):
    values = dict(
        id="action",
        capability="inspect_protocol",
        target="EXAMPLE.TEST.",
        asset_id="asset",
        reason="Inspect SMB metadata only",
        parameters={"family": "smb", "port": 445, "transport": "tcp"},
    )
    values.update(changes)
    return ActionRequest(**values)


def execute(c, action=None, **kwargs):
    return asyncio.run(
        c[0].execute(
            action or request(), policy=c[2], budgets=c[3], context=CONTEXT, **kwargs
        )
    )


def test_valid_smb_metadata_provenance_framework_registry_and_zero_authentication():
    c = compose(clock=lambda: 0.0)
    result = execute(c)
    assert isinstance(result, Success)
    out = result.value
    assert isinstance(out, ProtocolMetadataOutput)
    assert out.family is ProtocolFamily.SMB
    assert out.service == binding().service
    assert out.status == "completed" and not out.errors
    assert c[1].calls == [("192.0.2.10", 445, 30.0, MAX_RESPONSE_BYTES)]
    data = out.observations[0].data
    assert data["dialect"] == "3.0.2"
    assert data["signing_enabled"] and data["signing_required"]
    assert data["server_guid"] == "11223344-5566-7788-99aa-bbccddeeff00"
    assert data["service_id"] == "service" and data["host_id"] == "host"
    assert data["query_target"] == "example.test"
    assert data["port"] == 445 and data["transport"] == "tcp"
    assert data["authentication_attempted"] is False
    assert data["shares_collected"] is False and data["domain_collected"] is False
    assert data["workgroup_collected"] is False
    assert data["smb1_support"] is None and data["smb311_support"] is None
    assert data["dialect_inventory_complete"] is False
    evidence, observation = out.evidence[0], out.observations[0]
    assert evidence.trust == "untrusted"
    assert evidence.source == observation.source == "native_smb"
    assert evidence.execution_id == observation.execution_id == CONTEXT.execution_id
    assert evidence.collected_at == observation.observed_at == WHEN
    assert evidence.capability == "inspect_protocol"
    assert observation.evidence_ids == (evidence.id,)
    assert (
        evidence.sha256
        == sha256(
            json.dumps(
                data, sort_keys=True, separators=(",", ":"), ensure_ascii=True
            ).encode()
        ).hexdigest()
    )
    assert base64.b64decode(data["raw_response_base64"]) == fixture_wire("smb302")
    assert SmbOutput.model_validate_json(out.model_dump_json()) == out
    assert (
        execute(compose(clock=lambda: 0.0)).value.model_dump_json()
        == out.model_dump_json()
    )
    assert dict(c[3].state.host_actions) == {"example.test": 1, "192.0.2.10": 1}
    assert c[3].state.permitted_actions == 1 and c[3].state.active_executions == 0
    assert not c[4].state.action_requests
    c[1].authenticate.assert_not_called()
    c[1].send.assert_not_called()
    definition = c[0].definition
    assert definition.adapter_id == "native_smb" and definition.input_schema is SmbInput
    assert c[2].registry.catalog()[0].capability is CapabilityId.INSPECT_PROTOCOL
    assert ToolRegistry().catalog() == ()


@pytest.mark.parametrize(
    ("filename", "dialect", "enabled", "required"),
    [
        ("smb202", "2.0.2", True, False),
        ("smb21", "2.1", False, False),
        ("smb30", "3.0", False, True),
        ("smb302", "3.0.2", True, True),
    ],
)
def test_dialect_and_signing_fixtures_report_only_selected_metadata(
    filename, dialect, enabled, required
):
    out = execute(compose(FakeTransport(fixture_wire(filename)))).value
    data = out.observations[0].data
    assert data["dialect"] == dialect
    assert data["signing_enabled"] is enabled and data["signing_required"] is required
    assert data["signing_verified"] is False
    assert data["smb2_support"] is (True if dialect.startswith("2.") else None)
    assert data["smb3_support"] is (True if dialect.startswith("3.") else None)
    assert "finding" not in out.model_dump_json()


def test_hostile_remote_strings_remain_opaque_untrusted_data_never_actions():
    raw = fixture_wire("hostile")
    c = compose(FakeTransport(raw))
    out = execute(c).value
    assert base64.b64decode(out.observations[0].data["raw_response_base64"]) == raw
    assert out.evidence[0].trust == "untrusted"
    assert "domain" not in out.observations[0].data
    assert len(c[1].calls) == 1 and not c[4].state.action_requests
    c[1].authenticate.assert_not_called()
    c[1].send.assert_not_called()


@pytest.mark.parametrize("name", ["denied", "auth_required", "unsupported"])
def test_auth_dependent_and_unsupported_metadata_yields_limitation_without_fallback(
    name,
):
    c = compose(FakeTransport(fixture_wire(name)))
    out = execute(c)
    assert (
        isinstance(out, Failure) and out.error.code is ErrorCode.TOOL_EXECUTION_FAILED
    )
    assert len(c[1].calls) == 1 and c[3].state.active_executions == 0
    c[1].authenticate.assert_not_called()
    c[1].send.assert_not_called()


@pytest.mark.parametrize(
    ("name", "address", "port"),
    [
        ("192.0.2.10", "192.0.2.10", 445),
        ("2001:db8::10", "2001:db8::10", 2222),
        ("example.test", "2001:db8::10", 61234),
    ],
)
def test_numeric_ipv6_and_nonstandard_observed_ports(name, address, port):
    observed = binding().service.model_copy(update={"port": port})
    c = compose(bindings=(binding(host=name, address=address, service=observed),))
    out = execute(
        c,
        request(
            target=name, parameters={"family": "smb", "port": port, "transport": "tcp"}
        ),
    )
    assert isinstance(out, Success)
    assert c[1].calls[0][:2] == (address, port)


@pytest.mark.parametrize("target", ["outside.test", "badexample.test", "192.0.3.10"])
def test_outside_targets_reject_before_contact_or_spending(target):
    c = compose(clock=lambda: 0.0)
    before = c[3].state
    outcome = execute(c, request(target=target))
    assert (
        isinstance(outcome, Failure) and outcome.error.code is ErrorCode.SCOPE_REJECTED
    )
    assert c[1].calls == [] and c[3].state == before


def test_authorized_name_does_not_authorize_contact_address():
    c = compose(bindings=(binding(address="203.0.113.10"),), clock=lambda: 0.0)
    before = c[3].state
    result = execute(c)
    assert isinstance(result, Failure) and result.error.code is ErrorCode.SCOPE_REJECTED
    assert c[1].calls == [] and c[3].state == before


@pytest.mark.parametrize(
    "parameters",
    [
        {"family": "ssh", "port": 445, "transport": "tcp"},
        {"family": "smb", "port": 0, "transport": "tcp"},
        {"family": "smb", "port": 65536, "transport": "tcp"},
        {"family": "smb", "port": True, "transport": "tcp"},
        {"family": "smb", "port": "22", "transport": "tcp"},
        {"family": "smb", "port": 445, "transport": "udp"},
        {"family": "smb", "port": 2445, "transport": "tcp"},
        {},
    ],
)
def test_invalid_family_transport_ports_or_missing_service_binding(parameters):
    c = compose(clock=lambda: 0.0)
    before = c[3].state
    result = execute(c, request(parameters=parameters))
    assert (
        isinstance(result, Failure)
        and result.error.code is ErrorCode.PLANNER_VALIDATION_FAILED
    )
    assert not c[1].calls and c[3].state == before


@pytest.mark.parametrize(
    "key",
    [
        "username",
        "password",
        "private_key",
        "key_file",
        "public_key",
        "authenticate",
        "auth_method",
        "command",
        "shell",
        "share",
        "path",
        "ntlm_hash",
        "domain",
        "relay",
        "dialects",
        "security_mode",
        "session_setup",
        "argv",
        "raw_options",
        "extra_args",
        "executable",
        "proxy",
        "known_hosts",
    ],
)
def test_no_credentials_commands_or_low_level_options_in_registered_schema(key):
    values = {"family": "smb", "port": 445, "transport": "tcp", key: "fixture"}
    with pytest.raises(ValidationError):
        SmbInput.model_validate(values)
    c = compose(clock=lambda: 0.0)
    # Some keys reject already in ActionRequest; construct to exercise execute's
    # complete revalidation too, without weakening that upstream contract.
    action = request().model_copy(update={"parameters": values})
    outcome = execute(c, action)
    assert isinstance(outcome, Failure)
    assert not c[1].calls and c[3].state.permitted_actions == 0
    c[1].authenticate.assert_not_called()
    c[1].send.assert_not_called()


@pytest.mark.parametrize(
    "changes",
    [
        {"protocol": "http"},
        {"protocol": None},
        {"protocol": "smb/ftp"},
        {"product": "vsftpd"},
        {"transport": "udp"},
        {"port": True},
        {"port": 139},
        {"protocol": "netbios-ssn"},
    ],
)
def test_non_smb_or_malformed_observed_service_cannot_construct_operational_binding(
    changes,
):
    observed = binding().service.model_copy(update=changes)
    with pytest.raises(ConfigurationError):
        SmbAdapter(
            (binding().model_copy(update={"service": observed}),), ExecutionConfig()
        )


@pytest.mark.parametrize(
    "bindings",
    [
        (),
        [],
        (binding(), binding()),
        (binding(address="example.test"),),
        (binding(address="fe80::1%eth0"),),
        (binding(address="::ffff:192.0.2.10"),),
        (binding(host="EXAMPLE.TEST"),),
    ],
)
def test_invalid_trusted_settings_fail_closed(bindings):
    with pytest.raises(ConfigurationError):
        SmbAdapter(bindings, ExecutionConfig())


@pytest.mark.parametrize(
    "raw",
    [
        b"",
        b"\xfeSMB",
        b"\xffSMB" + bytes(100),
        b"x" * 8193,
        "remote",
        b"\0\0\0\x80" + bytes(128),
    ],
)
def test_malformed_or_oversized_negotiation_use_canonical_failure_no_auth(raw):
    c = compose(FakeTransport(raw))
    result = execute(c)
    assert isinstance(result, Failure) and result.error.code is ErrorCode.PARSE_FAILED
    assert "SMB-" not in result.error.message
    assert c[3].state.permitted_actions == 1 and c[3].state.active_executions == 0
    c[1].authenticate.assert_not_called()
    c[1].send.assert_not_called()


@pytest.mark.parametrize(
    ("error", "code"),
    [
        (TimeoutError(), ErrorCode.TOOL_TIMEOUT),
        (
            ConnectionRefusedError("secret native diagnostic"),
            ErrorCode.TOOL_EXECUTION_FAILED,
        ),
        (ConnectionError(), ErrorCode.TOOL_EXECUTION_FAILED),
        (OSError("unreachable"), ErrorCode.TOOL_EXECUTION_FAILED),
    ],
)
def test_canonical_timeout_closed_or_unreachable_without_native_error_leakage(
    error, code
):
    c = compose(FakeTransport(error))
    outcome = execute(c)
    assert isinstance(outcome, Failure) and outcome.error.code is code
    assert "secret" not in outcome.model_dump_json()
    assert len(c[1].calls) == 1
    assert c[3].state.permitted_actions == 1 and c[3].state.active_executions == 0


@pytest.mark.parametrize(
    "availability", [AdapterAvailability.UNAVAILABLE, AdapterAvailability.NOT_CHECKED]
)
def test_unavailable_registry_does_not_contact(availability):
    c = compose(availability=availability)
    result = execute(c)
    assert (
        isinstance(result, Failure) and result.error.code is ErrorCode.TOOL_UNAVAILABLE
    )
    assert not c[1].calls and c[3].state.permitted_actions == 0


def test_wrong_binding_budget_owner_asset_and_unsupported_target_kinds():
    c = compose()
    other = compose()
    result = asyncio.run(
        other[0].execute(request(), policy=c[2], budgets=c[3], context=CONTEXT)
    )
    assert isinstance(result, Failure) and not other[1].calls
    result = asyncio.run(
        c[0].execute(request(), policy=c[2], budgets=other[3], context=CONTEXT)
    )
    assert isinstance(result, Failure) and not c[1].calls
    assert isinstance(execute(c, request(asset_id="other")), Failure)
    assert isinstance(execute(c, request(target="http://example.test/")), Failure)
    assert isinstance(execute(c, request(target="192.0.2.0/24")), Failure)
    assert not c[1].calls and c[3].state.permitted_actions == 0


def test_numeric_binding_cannot_substitute_another_authorized_address():
    c = compose(bindings=(binding(host="192.0.2.11", address="192.0.2.10"),))
    result = execute(c, request(target="192.0.2.11"))
    assert isinstance(result, Failure) and not c[1].calls


def test_policy_risk_and_allowlist_checks_precede_contact():
    c = compose()
    for config in [
        ActionPolicyConfig(),
        ActionPolicyConfig(
            allowed_capabilities=frozenset({CapabilityId.INSPECT_PROTOCOL}),
            allowed_risk_classes=frozenset({RiskClass.PASSIVE}),
        ),
    ]:
        policy = replace(c[2], config=config)
        result = asyncio.run(
            c[0].execute(request(), policy=policy, budgets=c[3], context=CONTEXT)
        )
        assert isinstance(result, Failure)
    assert not c[1].calls and c[3].state.permitted_actions == 0


def test_actual_adapter_timeout_bounds_injected_transport_and_cancellation_releases_permit():
    async def never():
        await asyncio.Event().wait()

    c = compose(
        FakeTransport(never), config=ExecutionConfig(default_timeout_seconds=0.01)
    )
    result = execute(c)
    assert isinstance(result, Failure) and result.error.code is ErrorCode.TOOL_TIMEOUT
    assert c[3].state.active_executions == 0

    async def cancel():
        c = compose(FakeTransport(never))
        task = asyncio.create_task(
            c[0].execute(request(), policy=c[2], budgets=c[3], context=CONTEXT)
        )
        await asyncio.sleep(0)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert c[3].state.permitted_actions == 1 and c[3].state.active_executions == 0

    asyncio.run(cancel())


@pytest.mark.parametrize("limit", [1, 128, 1024])
def test_capture_and_serialized_output_limits_fail_closed(limit):
    c = compose(config=ExecutionConfig(max_output_bytes=limit))
    result = execute(c)
    assert isinstance(result, Failure) and result.error.code is ErrorCode.PARSE_FAILED
    assert c[1].calls[0][3] <= limit
    assert c[3].state.active_executions == 0


def test_session_deadline_drops_metadata_and_initial_exhaustion_never_contacts():
    clock = [0.0]
    c = compose(
        FakeTransport(mutate=lambda: clock.__setitem__(0, 10.0)),
        limits=ExecutionBudget(max_duration_seconds=10.0),
        clock=lambda: clock[0],
    )
    result = execute(c)
    assert isinstance(result, Failure) and result.error.code is ErrorCode.TOOL_TIMEOUT
    assert c[3].state.permitted_actions == 1 and c[3].state.active_executions == 0
    result = execute(c, request(id="second"))
    assert (
        isinstance(result, Failure) and result.error.code is ErrorCode.BUDGET_EXHAUSTED
    )
    assert len(c[1].calls) == 1


def test_start_rejection_and_final_scope_recheck_never_contact():
    c = compose()
    result = execute(
        c,
        on_started=lambda: Failure(
            error=StateTransitionError("fixture").to_error_info()
        ),
    )
    assert isinstance(result, Failure) and not c[1].calls
    assert c[3].state.permitted_actions == 1 and c[3].state.active_executions == 0
    c = compose()

    def change_scope():
        object.__setattr__(c[2], "scope_validator", ScopeValidator(Scope(id="denied")))
        return Success[None](value=None)

    result = execute(c, on_started=change_scope)
    assert isinstance(result, Failure) and result.error.code is ErrorCode.SCOPE_REJECTED
    assert not c[1].calls and c[3].state.active_executions == 0


def test_generic_state_ingestion_and_completed_alias_dedup_prevent_second_contact():
    c = compose(limits=ExecutionBudget(capability_rate_actions=2), clock=lambda: 0.0)
    owner = c[4]
    assert isinstance(
        owner.record_facts(
            assets=(Asset(id="asset", kind="host", value="example.test"),),
            hosts=(Host(id="host", asset_id="asset", value="192.0.2.10"),),
            services=(binding().service,),
        ),
        Success,
    )
    action = request()
    dedup = c[2].completed_action_eligibility
    assert isinstance(dedup.record_request(action, recorded_at=WHEN), Success)
    assert isinstance(
        owner.mark_action_approved(
            action.id, policy_reference="policy", recorded_at=WHEN
        ),
        Success,
    )
    output = execute(
        c,
        action,
        on_started=lambda: (
            Success[None](value=None)
            if isinstance(
                owner.mark_action_started(
                    action.id, execution_id=CONTEXT.execution_id, recorded_at=WHEN
                ),
                Success,
            )
            else None
        ),
    ).value
    recorded = ActionResult(
        id="result",
        action_id=action.id,
        status=output.status,
        recorded_at=WHEN,
        execution_ids=(CONTEXT.execution_id,),
        observations=output.observations,
        evidence=output.evidence,
    )
    assert isinstance(owner.record_action_result(recorded), Success)
    before = c[3].state
    rejected = execute(c, request(id="second", target="example.test"))
    assert (
        isinstance(rejected, Failure)
        and rejected.error.code is ErrorCode.PLANNER_VALIDATION_FAILED
    )
    assert (
        rejected.error.message
        == "Equivalent action is not eligible for another attempt"
    )
    assert len(c[1].calls) == 1 and c[3].state == before
    assert owner.state.services[0] == binding().service
    out = owner.state.observations
    assert out
    assert out[0].source == "native_smb"


@pytest.mark.parametrize(
    "limits",
    [
        ExecutionBudget(max_actions=1, capability_rate_actions=2),
        ExecutionBudget(max_actions_per_host=1, capability_rate_actions=2),
        ExecutionBudget(),
        ExecutionBudget(
            max_session_output_bytes=2 * 1048576, capability_rate_actions=2
        ),
    ],
)
def test_repeated_direct_calls_obey_shared_action_host_rate_and_output_admission(
    limits,
):
    c = compose(limits=limits, clock=lambda: 0.0)
    assert isinstance(execute(c), Success)
    before = c[3].state
    outcome = execute(c, request(id="second"))
    assert (
        isinstance(outcome, Failure)
        and outcome.error.code is ErrorCode.BUDGET_EXHAUSTED
    )
    assert len(c[1].calls) == 1 and c[3].state == before


def test_start_callback_registry_change_and_deadline_abort_prevent_contact():
    c = compose()

    def change_registry():
        object.__setattr__(c[2], "registry", ToolRegistry())
        return Success[None](value=None)

    result = execute(c, on_started=change_registry)
    assert (
        isinstance(result, Failure) and result.error.code is ErrorCode.TOOL_UNAVAILABLE
    )
    assert not c[1].calls and c[3].state.active_executions == 0
    clock = [0.0]
    c = compose(
        clock=lambda: clock[0], limits=ExecutionBudget(max_duration_seconds=1.0)
    )

    def expire():
        clock[0] = 1.0
        return Success[None](value=None)

    result = execute(c, on_started=expire)
    assert isinstance(result, Failure) and result.error.code is ErrorCode.TOOL_TIMEOUT
    assert not c[1].calls and c[3].state.active_executions == 0


def test_smb_input_preserves_exact_framework_fields_only():
    assert set(SmbInput.model_fields) == {"family", "port", "transport"}
    data = {"family": "smb", "port": 445, "transport": "tcp"}
    assert (
        SmbInput.model_validate_json(json.dumps(data)).model_dump(mode="json") == data
    )
    for name in (
        "authenticate",
        "session_setup",
        "execute_command",
        "write_file",
        "read_file",
        "delete_file",
        "tree_connect",
        "relay",
        "load_hash",
    ):
        assert not hasattr(compose()[0], name)


def test_real_native_adapter_profile_uses_one_scoped_negotiation_only(monkeypatch):
    from recon_agent.tools.native_smb import NativeSmbTransport

    raw = fixture_wire("hostile")
    reader = Mock()
    from unittest.mock import AsyncMock

    reader.readexactly = AsyncMock(side_effect=[raw[:4], raw[4:]])
    writer = Mock()
    writer.drain = AsyncMock()
    connection = AsyncMock(return_value=(reader, writer))
    monkeypatch.setattr(asyncio, "open_connection", connection)
    c = compose(NativeSmbTransport())
    result = execute(c)
    assert isinstance(result, Success)
    connection.assert_awaited_once()
    assert connection.call_args.args == ("192.0.2.10", 445)
    writer.write.assert_called_once()
    sent = writer.write.call_args.args[0]
    assert len(sent) == 112 and sent[16:18] == b"\0\0"
    assert sent[20:68] == bytes(48)  # No session/tree/auth/compound/WRITE.
    writer.close.assert_called_once()
    writer.transport.abort.assert_called_once()
    writer.authenticate.assert_not_called()
    assert result.value.evidence[0].trust == "untrusted"
    assert c[3].state.permitted_actions == 1 and c[3].state.active_executions == 0

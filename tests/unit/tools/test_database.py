"""Offline database profile, current authorization, resources and generic provenance."""

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
from recon_agent.tools.database import DatabaseAdapter
from recon_agent.tools.database_models import (
    DatabaseContext,
    DatabaseInput,
    DatabaseOutput,
    DatabaseServiceBinding,
)
from recon_agent.tools.database_parser import MAX_RESPONSE_BYTES, parse_metadata

WHEN = datetime(2026, 10, 8, tzinfo=UTC)
CONTEXT = DatabaseContext(execution_id="database-execution", collected_at=WHEN)
FIXTURES = Path(__file__).parents[2] / "fixtures/database"


def fixture_wire(name):
    return bytes.fromhex(json.loads((FIXTURES / "handshakes.json").read_text())[name])


def mysql_frame(version=b"8.0.40", tail=None, protocol=10):
    # Independent fixture grammar, not the production parser or builder.
    tail = (
        tail
        if tail is not None
        else bytes.fromhex(
            "2a000000616263646566676800ffff210200ffff15000000000000000000006a6b6c6d6e6f707172737475006d7973716c5f6e61746976655f70617373776f726400"
        )
    )
    payload = bytes([protocol]) + version + b"\0" + tail
    return len(payload).to_bytes(3, "little") + b"\0" + payload


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    blocked = Mock(
        side_effect=AssertionError("database tests attempted real contact/process")
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
        port=3306,
        transport="tcp",
        protocol="mysql",
        product="MySQL",
    )
    values = dict(host="example.test", address="192.0.2.10", service=observed)
    values.update(changes)
    return DatabaseServiceBinding(**values)


class FakeTransport:
    def __init__(self, result=None, mutate=None):
        self.result = result if result is not None else fixture_wire("mysql")
        self.calls = []
        self.mutate = mutate
        # Regression sentinel: any arbitrary command/authentication path fails.
        self.authenticate = Mock(side_effect=AssertionError("must never authenticate"))
        self.send = Mock(
            side_effect=AssertionError("must never send arbitrary database messages")
        )

    async def inspect(self, address, port, database_type, timeout_seconds, max_bytes):
        self.calls.append((address, port, database_type, timeout_seconds, max_bytes))
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
    adapter = DatabaseAdapter(bindings or (binding(),), config, fake)
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
        reason="Inspect database metadata only",
        parameters={
            "family": "database",
            "database_type": "mysql",
            "port": 3306,
            "transport": "tcp",
        },
    )
    values.update(changes)
    return ActionRequest(**values)


def execute(c, action=None, **kwargs):
    return asyncio.run(
        c[0].execute(
            action or request(), policy=c[2], budgets=c[3], context=CONTEXT, **kwargs
        )
    )


@pytest.mark.parametrize(
    ("name", "address", "port"),
    [
        ("192.0.2.10", "192.0.2.10", 3306),
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
            target=name,
            parameters={
                "family": "database",
                "database_type": "mysql",
                "port": port,
                "transport": "tcp",
            },
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
        {"family": "smb", "port": 3306, "transport": "tcp"},
        {"family": "database", "database_type": "mysql", "port": 0, "transport": "tcp"},
        {
            "family": "database",
            "database_type": "mysql",
            "port": 65536,
            "transport": "tcp",
        },
        {
            "family": "database",
            "database_type": "mysql",
            "port": True,
            "transport": "tcp",
        },
        {
            "family": "database",
            "database_type": "mysql",
            "port": "3306",
            "transport": "tcp",
        },
        {
            "family": "database",
            "database_type": "mysql",
            "port": 3306,
            "transport": "udp",
        },
        {
            "family": "database",
            "database_type": "mysql",
            "port": 3333,
            "transport": "tcp",
        },
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
        "query",
        "database",
        "connection_string",
        "commands",
        "collection",
        "table",
        "schema",
        "uri",
        "options",
        "redis_command",
        "mongo_command",
        "argv",
        "raw_options",
        "extra_args",
        "executable",
        "proxy",
        "known_hosts",
    ],
)
def test_no_credentials_commands_or_low_level_options_in_registered_schema(key):
    values = {
        "family": "database",
        "database_type": "mysql",
        "port": 3306,
        "transport": "tcp",
        key: "fixture",
    }
    with pytest.raises(ValidationError):
        DatabaseInput.model_validate(values)
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
        {"protocol": "database/ftp"},
        {"product": "vsftpd"},
        {"transport": "udp"},
        {"port": True},
    ],
)
def test_non_database_or_malformed_observed_service_cannot_construct_operational_binding(
    changes,
):
    observed = binding().service.model_copy(update=changes)
    with pytest.raises(ConfigurationError):
        DatabaseAdapter(
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
        DatabaseAdapter(bindings, ExecutionConfig())


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
    assert c[1].calls[0][4] <= limit
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
    assert out[0].source == "native_database"


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


def test_mysql_provenance_framework_and_no_authenticated_operation():
    c = compose(clock=lambda: 0.0)
    result = execute(c)
    assert isinstance(result, Success)
    out = result.value
    assert isinstance(out, ProtocolMetadataOutput)
    assert out.family is ProtocolFamily.DATABASE
    assert out.service == binding().service
    assert out.status == "completed" and not out.errors
    assert c[1].calls == [("192.0.2.10", 3306, "mysql", 30.0, MAX_RESPONSE_BYTES)]
    data = out.observations[0].data
    assert data["server_version"] == "8.0.40"
    assert data["protocol_version"] == 10
    assert data["connection_id"] == 42
    assert data["capability_flags"] == 0xFFFFFFFF
    assert data["character_set"] == 33 and data["status_flags"] == 2
    assert data["ssl_supported"] is True
    assert data["application_bytes_sent"] == 0
    for name in (
        "authentication_attempted",
        "queries_sent",
        "data_accessed",
        "remote_mutation",
        "tls_negotiated",
    ):
        assert data[name] is False
    evidence, observation = out.evidence[0], out.observations[0]
    assert evidence.trust == "untrusted"
    assert evidence.source == observation.source == "native_database"
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
    assert base64.b64decode(data["raw_response_base64"]) == fixture_wire("mysql")
    assert DatabaseOutput.model_validate_json(out.model_dump_json()) == out
    assert execute(compose(clock=lambda: 0.0)).value == out
    assert dict(c[3].state.host_actions) == {"example.test": 1, "192.0.2.10": 1}
    assert c[3].state.active_executions == 0
    c[1].authenticate.assert_not_called()
    c[1].send.assert_not_called()
    assert c[0].definition.adapter_id == "native_database"
    assert c[0].definition.input_schema is DatabaseInput
    assert not ToolRegistry().catalog()


@pytest.mark.parametrize("protocol", ["mysql", "mariadb", "MYSQL", "MariaDB"])
def test_mysql_mariadb_service_aliases_and_reported_product(protocol):
    c = compose(
        FakeTransport(fixture_wire("mariadb")),
        bindings=(
            binding(
                service=binding().service.model_copy(update={"protocol": protocol})
            ),
        ),
    )
    out = execute(c).value
    assert out.observations[0].data["product_hint"] == "MariaDB"
    assert out.observations[0].data["server_version"] == "5.5.5-10.11.6-MariaDB"


def test_remote_version_instructions_remain_data_and_do_not_add_contacts():
    c = compose(FakeTransport(fixture_wire("hostile")))
    out = execute(c).value
    assert "DROP TABLE" in out.observations[0].data["server_version"]
    assert out.observations[0].data["product_hint"] is None
    assert len(c[1].calls) == 1
    c[1].authenticate.assert_not_called()
    c[1].send.assert_not_called()


@pytest.mark.parametrize("protocol", ["postgres", "postgresql", "PostgreSQL"])
@pytest.mark.parametrize("wire,ssl", [(b"S", True), (b"N", False)])
def test_postgresql_signal_is_partial_without_version_or_startup(protocol, wire, ssl):
    observed = binding().service.model_copy(
        update={"protocol": protocol, "product": "PostgreSQL", "port": 5432}
    )
    c = compose(FakeTransport(wire), bindings=(binding(service=observed),))
    out = execute(
        c,
        request(
            parameters={
                "family": "database",
                "database_type": "postgresql",
                "port": 5432,
                "transport": "tcp",
            }
        ),
    ).value
    assert out.status == "partial" and out.errors[0].code is ErrorCode.PARSE_FAILED
    data = out.observations[0].data
    assert data["ssl_supported"] is ssl
    assert data["server_version"] is None and data["protocol_version"] is None
    assert data["limitation"] == "version_unavailable"
    assert data["application_bytes_sent"] == 8
    assert data["authentication_attempted"] is False
    assert out.service == observed and len(c[1].calls) == 1


@pytest.mark.parametrize("protocol", ["redis", "mongodb", "ms-sql-s"])
def test_catalog_protocol_without_reviewed_profile_rejects_before_spending_or_contact(
    protocol,
):
    observed = binding().service.model_copy(
        update={"protocol": protocol, "product": None}
    )
    c = compose(bindings=(binding(service=observed),), clock=lambda: 0.0)
    before = c[3].state
    result = execute(
        c,
        request(
            parameters={
                "family": "database",
                "database_type": protocol,
                "port": 3306,
                "transport": "tcp",
            }
        ),
    )
    assert (
        isinstance(result, Failure) and result.error.code is ErrorCode.TOOL_UNAVAILABLE
    )
    assert c[3].state == before and not c[1].calls


@pytest.mark.parametrize(
    "kind",
    [
        "postgresql",
        "redis",
        "mongodb",
        "ms-sql-s",
        "mysql/postgresql",
        "MYSQL",
        "unknown",
        "database",
        "oracle",
    ],
)
def test_type_mismatch_unknown_ambiguous_or_uncanonical_fails_without_contact(kind):
    c = compose(clock=lambda: 0.0)
    result = execute(
        c,
        request(
            parameters={
                "family": "database",
                "database_type": kind,
                "port": 3306,
                "transport": "tcp",
            }
        ),
    )
    assert (
        isinstance(result, Failure)
        and result.error.code is ErrorCode.PLANNER_VALIDATION_FAILED
    )
    assert not c[1].calls and c[3].state.permitted_actions == 0


@pytest.mark.parametrize(
    "raw",
    [
        b"",
        b"abc",
        b"\x01\x00\x00\x01\x0a",
        b"\x01\x00\x00\x00\xff",
        b"\xff\xff\xff\x00\x0a",
        b"\x02\x00\x00\x00\x0a\x00",
        mysql_frame() + b"extra",
        mysql_frame(b"\xff"),
        mysql_frame(b"bad\x1bversion"),
        mysql_frame(b""),
        mysql_frame(b"x" * 256),
        mysql_frame(tail=b"\x00" * 14),
        mysql_frame(tail=b"\x00" * 16),
        mysql_frame(tail=b"\x00" * 12 + b"\x01" + b"\x00" * 18),
    ],
)
def test_malformed_mysql_fails_canonically_without_authentication(raw):
    c = compose(FakeTransport(raw))
    result = execute(c)
    assert isinstance(result, Failure) and result.error.code is ErrorCode.PARSE_FAILED
    assert c[3].state.active_executions == 0
    c[1].authenticate.assert_not_called()


@pytest.mark.parametrize("raw", [b"Sextra", b"R", b"E", b"", b"\x00", b"AUTH required"])
def test_postgresql_malformed_auth_or_error_signal_never_falls_back(raw):
    c = compose(
        FakeTransport(raw),
        bindings=(
            binding(
                service=binding().service.model_copy(
                    update={"protocol": "postgresql", "product": None}
                )
            ),
        ),
    )
    result = execute(
        c,
        request(
            parameters={
                "family": "database",
                "database_type": "postgresql",
                "port": 3306,
                "transport": "tcp",
            }
        ),
    )
    assert isinstance(result, Failure) and result.error.code is ErrorCode.PARSE_FAILED
    assert len(c[1].calls) == 1
    c[1].authenticate.assert_not_called()
    c[1].send.assert_not_called()


def test_old_or_incomplete_mysql_metadata_is_explicitly_partial():
    for raw, limitation in [
        (mysql_frame(tail=b"\x00" * 15), "incomplete_greeting"),
        (mysql_frame(protocol=9), "unsupported_handshake"),
    ]:
        out = execute(compose(FakeTransport(raw))).value
        assert out.status == "partial" and out.errors[0].code is ErrorCode.PARSE_FAILED
        assert out.observations[0].data["limitation"] == limitation


def test_database_schema_and_adapter_expose_no_driver_query_or_mutation_api():
    assert set(DatabaseInput.model_fields) == {
        "family",
        "database_type",
        "port",
        "transport",
    }
    for name in (
        "authenticate",
        "login",
        "query",
        "execute_command",
        "cursor",
        "select",
        "insert",
        "update",
        "delete",
        "get",
        "set",
        "find",
        "list_databases",
        "list_collections",
        "list_users",
        "read_file",
        "write_file",
    ):
        assert not hasattr(compose()[0], name)
    with pytest.raises(ValueError):
        parse_metadata(b"S", "redis")


@pytest.mark.parametrize("code", [1045, 1130, 1040])
def test_mysql_server_error_auth_required_boundary_has_no_login_retry_or_raw_error_leak(
    code,
):
    payload = (
        b"\xff" + code.to_bytes(2, "little") + b"#28000password required outside.test"
    )
    raw = len(payload).to_bytes(3, "little") + b"\0" + payload
    c = compose(FakeTransport(raw))
    result = execute(c)
    assert (
        isinstance(result, Failure)
        and result.error.code is ErrorCode.TOOL_EXECUTION_FAILED
    )
    assert "outside.test" not in result.model_dump_json()
    assert len(c[1].calls) == 1 and c[3].state.active_executions == 0
    c[1].authenticate.assert_not_called()
    c[1].send.assert_not_called()


@pytest.mark.parametrize("raw", [None, "wire", bytearray(b"wire"), b"x" * 4097])
def test_untrusted_transport_capture_must_be_bounded_bytes(raw):
    c = compose()
    c[1].result = raw
    result = execute(c)
    assert isinstance(result, Failure) and result.error.code is ErrorCode.PARSE_FAILED
    assert c[3].state.active_executions == 0


def test_one_database_adapter_handles_separate_observed_types_without_arbitrary_routing():
    observed = binding().service.model_copy(
        update={
            "id": "pg",
            "protocol": "postgresql",
            "product": "PostgreSQL",
            "port": 5432,
        }
    )
    c = compose(
        bindings=(binding(), binding(service=observed)),
        limits=ExecutionBudget(capability_rate_actions=2),
        clock=lambda: 0.0,
    )
    assert execute(c).value.database_type == "mysql"
    c[1].result = b"S"
    out = execute(
        c,
        request(
            id="pg",
            parameters={
                "family": "database",
                "database_type": "postgresql",
                "port": 5432,
                "transport": "tcp",
            },
        ),
    ).value
    assert out.database_type == "postgresql" and out.service.id == "pg"
    assert [call[2] for call in c[1].calls] == ["mysql", "postgresql"]


def test_partial_postgresql_generic_state_lineage_retains_unavailability():
    observed = binding().service.model_copy(
        update={"protocol": "postgresql", "product": None}
    )
    c = compose(FakeTransport(b"N"), bindings=(binding(service=observed),))
    owner = c[4]
    assert isinstance(
        owner.record_facts(
            assets=(Asset(id="asset", kind="host", value="example.test"),),
            hosts=(Host(id="host", asset_id="asset", value="example.test"),),
            services=(observed,),
        ),
        Success,
    )
    action = request(
        parameters={
            "family": "database",
            "database_type": "postgresql",
            "port": 3306,
            "transport": "tcp",
        }
    )
    assert isinstance(
        c[2].completed_action_eligibility.record_request(action, recorded_at=WHEN),
        Success,
    )
    assert isinstance(
        owner.mark_action_approved(
            action.id, policy_reference="policy", recorded_at=WHEN
        ),
        Success,
    )

    def start():
        assert isinstance(
            owner.mark_action_started(
                action.id, execution_id=CONTEXT.execution_id, recorded_at=WHEN
            ),
            Success,
        )
        return Success[None](value=None)

    out = execute(c, action, on_started=start).value
    assert isinstance(
        owner.record_action_result(
            ActionResult(
                id="result",
                action_id=action.id,
                status=out.status,
                recorded_at=WHEN,
                execution_ids=(CONTEXT.execution_id,),
                observations=out.observations,
                evidence=out.evidence,
                error=out.errors[0],
            )
        ),
        Success,
    )
    assert owner.state.observations[0].data["limitation"] == "version_unavailable"
    assert owner.state.services[0] == observed
    assert owner.state.evidence[0].trust == "untrusted"


@pytest.mark.parametrize("port", [3333, 3306])
def test_missing_database_type_never_uses_port_to_infer_protocol(port):
    c = compose()
    result = execute(
        c, request(parameters={"family": "database", "port": port, "transport": "tcp"})
    )
    assert isinstance(result, Failure) and not c[1].calls


@pytest.mark.parametrize(
    "changes",
    [
        {"protocol": "mysql", "product": "PostgreSQL"},
        {"protocol": "mysql", "product": "Redis"},
        {"protocol": "mysql/postgresql"},
        {"protocol": "oracle"},
    ],
)
def test_conflicting_or_unassigned_database_service_never_becomes_operational(changes):
    with pytest.raises(ConfigurationError):
        DatabaseAdapter(
            (binding(service=binding().service.model_copy(update=changes)),),
            ExecutionConfig(),
        )


def test_database_type_is_data_contract_not_arbitrary_driver_or_dispatch_name():
    from recon_agent.tools.database_models import database_type

    for protocol, expected in [
        (None, None),
        ("mysql", "mysql"),
        ("mariadb", "mysql"),
        ("postgres", "postgresql"),
        ("redis", "redis"),
        ("mongodb", "mongodb"),
        ("ms-sql-s", "ms-sql-s"),
        ("db", None),
        ("ｍysql", None),
    ]:
        assert (
            database_type(binding().service.model_copy(update={"protocol": protocol}))
            == expected
        )


@pytest.mark.parametrize(
    "kind,wire,port,status",
    [
        ("mysql", fixture_wire("mysql"), 3306, "completed"),
        ("postgresql", b"S", 5432, "partial"),
    ],
)
def test_native_adapter_end_to_end_uses_bound_service_fixed_wire_and_generic_output(
    monkeypatch, kind, wire, port, status
):
    from recon_agent.tools.native_database import NativeDatabaseTransport

    unread = b"AUTH; SELECT data; scan outside.test"
    remaining = [wire + unread]
    writes = []
    closed = []
    abort = Mock()

    class Reader:
        async def readexactly(self, size):
            value, remaining[0] = remaining[0][:size], remaining[0][size:]
            assert len(value) == size
            return value

    class Writer:
        transport = Mock(abort=abort)

        def write(self, value):
            assert kind == "postgresql" and value == bytes.fromhex("0000000804d2162f")
            writes.append(value)

        async def drain(self):
            pass

        def close(self):
            closed.append(True)

    async def connect(address, supplied_port, **kwargs):
        assert address == "192.0.2.10" and supplied_port == port
        return Reader(), Writer()

    monkeypatch.setattr(asyncio, "open_connection", connect)
    observed = binding().service.model_copy(
        update={"protocol": kind, "port": port, "product": None}
    )
    c = compose(NativeDatabaseTransport(), bindings=(binding(service=observed),))
    result = execute(
        c,
        request(
            parameters={
                "family": "database",
                "database_type": kind,
                "port": port,
                "transport": "tcp",
            }
        ),
    )
    assert isinstance(result, Success) and result.value.status == status
    assert result.value.service == observed
    assert remaining[0] == unread and closed == [True]
    assert len(writes) == (kind == "postgresql")
    abort.assert_called_once()
    assert c[3].state.active_executions == 0


def test_mysql_exact_version_and_frame_capture_boundaries_preserve_opaque_tail():
    raw = mysql_frame(b"x" * 255)
    assert parse_metadata(raw, "mysql").server_version == "x" * 255
    payload = raw[4:] + b"opaque" * ((4096 - len(raw)) // 6)
    payload += b"x" * (4092 - len(payload))
    framed = len(payload).to_bytes(3, "little") + b"\0" + payload
    assert len(framed) == 4096
    assert parse_metadata(framed, "mysql").server_version == "x" * 255

"""Offline SMTP profile, current authorization, resources and generic provenance."""

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
from recon_agent.tools.smtp import SmtpAdapter
from recon_agent.tools.smtp_models import (
    SmtpContext,
    SmtpInput,
    SmtpOutput,
    SmtpServiceBinding,
)
from recon_agent.tools.smtp_parser import MAX_CAPTURE_BYTES, parse_capture

WHEN = datetime(2026, 10, 8, tzinfo=UTC)
CONTEXT = SmtpContext(execution_id="smtp-execution", collected_at=WHEN)
FIXTURES = Path(__file__).parents[2] / "fixtures/smtp"


def fixture_wire(name):
    return json.loads((FIXTURES / "replies.json").read_text())[name].encode("utf-8")


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    blocked = Mock(
        side_effect=AssertionError("SMTP tests attempted real contact/process")
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
        port=25,
        transport="tcp",
        protocol="smtp",
        product="Postfix",
    )
    values = dict(host="example.test", address="192.0.2.10", service=observed)
    values.update(changes)
    return SmtpServiceBinding(**values)


class FakeTransport:
    def __init__(self, result=None, mutate=None):
        self.result = result if result is not None else fixture_wire("postfix")
        self.calls = []
        self.mutate = mutate
        # Regression sentinel: any authentication/arbitrary command path fails.
        self.authenticate = Mock(side_effect=AssertionError("must never authenticate"))
        self.send = Mock(
            side_effect=AssertionError("must never send arbitrary SMTP messages")
        )

    async def inspect(self, address, port, timeout_seconds, max_bytes):
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
    adapter = SmtpAdapter(bindings or (binding(),), config, fake)
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
        reason="Inspect SMTP metadata only",
        parameters={"family": "smtp", "port": 25, "transport": "tcp"},
    )
    values.update(changes)
    return ActionRequest(**values)


def execute(c, action=None, **kwargs):
    return asyncio.run(
        c[0].execute(
            action or request(), policy=c[2], budgets=c[3], context=CONTEXT, **kwargs
        )
    )


def test_valid_smtp_metadata_provenance_registry_and_no_auth_mail_enumeration():
    c = compose(clock=lambda: 0.0)
    result = execute(c)
    assert isinstance(result, Success)
    out = result.value
    assert isinstance(out, ProtocolMetadataOutput) and out.family is ProtocolFamily.SMTP
    assert out.service == binding().service
    assert out.status == "completed" and not out.errors
    assert c[1].calls == [("192.0.2.10", 25, 30.0, MAX_CAPTURE_BYTES)]
    data = out.observations[0].data
    assert data["banner"] == "220 mail.example.test ESMTP Postfix 3.9.1"
    assert data["product_hint"] == "Postfix" and data["version_hint"] == "3.9.1"
    assert data["extensions"] == [
        "STARTTLS",
        "AUTH LOGIN PLAIN",
        "SIZE 52428800",
        "8BITMIME",
    ]
    assert data["extensions_collected"] and data["starttls_advertised"] is True
    assert data["auth_mechanisms"] == ["LOGIN", "PLAIN"]
    assert data["size_advertised"] is True and data["size_limit"] == 52428800
    assert data["ehlo_server_text"] == "mail.example.test Hello"
    assert data["service_id"] == "service" and data["host_id"] == "host"
    assert data["query_target"] == "example.test" and data["port"] == 25
    for flag in (
        "authentication_attempted",
        "mail_sent",
        "enumeration_performed",
        "tls_negotiated",
    ):
        assert data[flag] is False
    evidence, observation = out.evidence[0], out.observations[0]
    assert evidence.trust == "untrusted"
    assert evidence.source == observation.source == "native_smtp"
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
    assert base64.b64decode(data["raw_capture_base64"]) == fixture_wire("postfix")
    assert SmtpOutput.model_validate_json(out.model_dump_json()) == out
    assert (
        execute(compose(clock=lambda: 0.0)).value.model_dump_json()
        == out.model_dump_json()
    )
    assert dict(c[3].state.host_actions) == {"example.test": 1, "192.0.2.10": 1}
    assert c[3].state.permitted_actions == 1 and c[3].state.active_executions == 0
    assert not c[4].state.action_requests
    c[1].authenticate.assert_not_called()
    c[1].send.assert_not_called()
    assert c[0].definition.adapter_id == "native_smtp"
    assert c[0].definition.input_schema is SmtpInput
    assert c[2].registry.catalog()[0].capability is CapabilityId.INSPECT_PROTOCOL
    assert ToolRegistry().catalog() == ()


@pytest.mark.parametrize(
    "name",
    [
        "multiline",
        "no_extensions",
        "hostile",
        "unsupported",
        "login_required",
        "unexpected",
    ],
)
def test_fixtures_preserve_unknown_and_hostile_extensions_with_partial_limits(name):
    wire = fixture_wire(name)
    c = compose(FakeTransport(wire))
    out = execute(c).value
    data = out.observations[0].data
    assert base64.b64decode(data["raw_capture_base64"]) == wire
    assert out.evidence[0].trust == "untrusted" and data["starttls_advertised"] is None
    if name in ("unsupported", "login_required", "unexpected"):
        assert out.status == "partial" and out.errors[0].code is ErrorCode.PARSE_FAILED
        assert data["extensions_collected"] is False
    else:
        assert out.status == "completed"
    if name == "hostile":
        assert "outside.test" in data["banner"]
        assert data["extensions"] == [
            "AUTH LOGIN PLAIN",
            "VRFY alice",
            "MAIL FROM:outside.test",
            "IGNORE policy",
        ]
        assert data["auth_mechanisms"] == ["LOGIN", "PLAIN"]
    assert len(c[1].calls) == 1
    c[1].authenticate.assert_not_called()
    c[1].send.assert_not_called()


@pytest.mark.parametrize(
    ("name", "address", "port"),
    [
        ("192.0.2.10", "192.0.2.10", 25),
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
            target=name, parameters={"family": "smtp", "port": port, "transport": "tcp"}
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
        {"family": "smb", "port": 25, "transport": "tcp"},
        {"family": "smtp", "port": 0, "transport": "tcp"},
        {"family": "smtp", "port": 65536, "transport": "tcp"},
        {"family": "smtp", "port": True, "transport": "tcp"},
        {"family": "smtp", "port": "25", "transport": "tcp"},
        {"family": "smtp", "port": 25, "transport": "udp"},
        {"family": "smtp", "port": 2122, "transport": "tcp"},
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
        "credentials",
        "auth",
        "AUTH",
        "authenticate",
        "auth_method",
        "sender",
        "recipient",
        "recipients",
        "message",
        "body",
        "mail_from",
        "rcpt_to",
        "MAIL FROM",
        "RCPT TO",
        "DATA",
        "VRFY",
        "EXPN",
        "command",
        "smtp_commands",
        "shell",
        "argv",
        "raw_options",
        "extra_args",
        "executable",
        "proxy",
        "tls",
        "starttls",
        "options",
        "ehlo_name",
        "helo",
        "address",
    ],
)
def test_no_credentials_commands_or_low_level_options_in_registered_schema(key):
    values = {"family": "smtp", "port": 25, "transport": "tcp", key: "fixture"}
    with pytest.raises(ValidationError):
        SmtpInput.model_validate(values)
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
        {"protocol": "smtp/smtp"},
        {"product": "OpenSSH"},
        {"transport": "udp"},
        {"port": True},
        {"port": 465},
        {"protocol": "smtps"},
    ],
)
def test_non_smtp_or_malformed_observed_service_cannot_construct_operational_binding(
    changes,
):
    observed = binding().service.model_copy(update=changes)
    with pytest.raises(ConfigurationError):
        SmtpAdapter(
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
        SmtpAdapter(bindings, ExecutionConfig())


@pytest.mark.parametrize(
    "raw",
    [
        b"",
        b"not smtp\r\n",
        b"220bad\r\n",
        b"220 bad\n",
        b"220 missing",
        b"220 bad\x00\r\n",
        b"220 bad\xff\r\n",
        b"220-unterminated\r\n",
        b"220-start\r\n221 end\r\n",
        b"220 " + b"x" * 510 + b"\r\n",
        b"220-start\r\n" + b"220-x\r\n" * 64 + b"220 end\r\n",
        b"x" * MAX_CAPTURE_BYTES,
        b"160 unsupported code\r\n",
        b"299 invalid second digit\r\n",
    ],
)
def test_malformed_or_oversized_greetings_use_canonical_failure_no_auth(raw):
    c = compose(FakeTransport(raw))
    result = execute(c)
    assert isinstance(result, Failure) and result.error.code is ErrorCode.PARSE_FAILED
    assert c[3].state.permitted_actions == 1 and c[3].state.active_executions == 0
    c[1].authenticate.assert_not_called()
    c[1].send.assert_not_called()


@pytest.mark.parametrize(
    "reply",
    [
        b"",
        b"250-bad\r\n",
        b"250-mail.example.test\r\nSTARTTLS\r\n250 SIZE\r\n",
        b"250-mail.example.test\r\n251 STARTTLS\r\n",
        b"250-mail.example.test\r\n250-STARTTLS\r\n550 end\r\n",
        b"250 good\r\n220 extra\r\n",
        b"250-mail.example.test\r\n250 \r\n",
        b"334 Password required\r\n",
        b"250-mail.example.test\r\n250-STARTTLS extra\r\n250 AUTH LOGIN\r\n",
        b"250-mail.example.test\r\n250 SIZE -1\r\n",
        b"250-mail.example.test\r\n250 AUTH=LOGIN PLAIN\r\n",
        b"250-mail.example.test\r\n250 AUTH bad!\r\n",
        b"250-mail.example.test\r\n250 AUTH\r\n",
        b"250-mail.example.test\r\n250 SIZE 1 2\r\n",
        b"250-mail.example.test\r\n250-UTF8\r\n250 \xff\r\n",
        b"250\r\n",
    ],
)
def test_malformed_or_unexpected_ehlo_preserves_banner_as_partial(reply):
    c = compose(FakeTransport(b"220 mail.example.test\r\n" + reply))
    out = execute(c).value
    assert out.status == "partial" and out.errors[0].code is ErrorCode.PARSE_FAILED
    assert out.observations[0].data["banner"] == "220 mail.example.test"
    assert out.observations[0].data["extensions_collected"] is False
    assert len(c[1].calls) == 1


@pytest.mark.parametrize("code", [421, 530, 500])
def test_greeting_denial_is_canonical_without_login_fallback(code):
    c = compose(FakeTransport(f"{code} denied\r\n".encode()))
    result = execute(c)
    assert (
        isinstance(result, Failure)
        and result.error.code is ErrorCode.TOOL_EXECUTION_FAILED
    )
    c[1].authenticate.assert_not_called()


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
    assert out[0].source == "native_smtp"


def test_exact_reply_length_utf8_code_only_and_conservative_product_hints():
    wire = b"220 " + b"x" * 506 + b"\r\n250 mail.example.test\r\n"
    assert parse_capture(wire).extensions_collected
    assert parse_capture(b"220\r\n250 mail.example.test\r\n").extensions_collected
    for banner, product in [
        ("220 mail.example.test ESMTP Exim 4.98.1", "Exim"),
        ("220 mail.example.test ESMTP Postfix", "Postfix"),
        ("220 custom server é", None),
    ]:
        metadata = parse_capture((banner + "\r\n250 mail.example.test\r\n").encode())
        assert metadata.product_hint == product and metadata.starttls_advertised is None


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


def test_smtp_input_preserves_exact_framework_fields_only():
    assert set(SmtpInput.model_fields) == {"family", "port", "transport"}
    data = {"family": "smtp", "port": 25, "transport": "tcp"}
    assert (
        SmtpInput.model_validate_json(json.dumps(data)).model_dump(mode="json") == data
    )
    for name in (
        "authenticate",
        "execute_command",
        "login",
        "sendmail",
        "send_message",
        "auth",
        "vrfy",
        "expn",
        "starttls",
        "send_command",
    ):
        assert not hasattr(compose()[0], name)


def test_partial_output_ingests_existing_generic_state_contract_with_canonical_error():
    c = compose(FakeTransport(fixture_wire("login_required")))
    owner = c[4]
    owner.record_facts(
        assets=(Asset(id="asset", kind="host", value="example.test"),),
        hosts=(Host(id="host", asset_id="asset", value="192.0.2.10"),),
        services=(binding().service,),
    )
    action = request()
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

    def started():
        outcome = owner.mark_action_started(
            action.id, execution_id=CONTEXT.execution_id, recorded_at=WHEN
        )
        assert isinstance(outcome, Success)
        return Success[None](value=None)

    out = execute(c, on_started=started).value
    result = ActionResult(
        id="partial",
        action_id=action.id,
        status="partial",
        recorded_at=WHEN,
        execution_ids=(CONTEXT.execution_id,),
        observations=out.observations,
        evidence=out.evidence,
        error=out.errors[0],
    )
    assert isinstance(owner.record_action_result(result), Success)
    assert owner.state.evidence[0].trust == "untrusted"
    assert owner.state.action_results[0].status == "partial"
    with pytest.raises(ValidationError):
        SmtpOutput.model_validate(out.model_copy(update={"errors": ()}))


@pytest.mark.parametrize("excluded", ["example.test", "192.0.2.10"])
def test_subject_and_numeric_contact_exclusions_prevent_spending(excluded):
    scope = Scope(
        id="scope",
        roots=(
            Target(id="name", kind="hostname", value="example.test"),
            Target(id="address", kind="cidr", value="192.0.2.0/24"),
        ),
        exclusions=(
            Target(
                id="excluded",
                kind="hostname" if excluded == "example.test" else "ip",
                value=excluded,
            ),
        ),
    )
    c = compose(scope=scope, clock=lambda: 0.0)
    before = c[3].state
    result = execute(c)
    assert isinstance(result, Failure) and result.error.code is ErrorCode.SCOPE_REJECTED
    assert c[1].calls == [] and c[3].state == before


@pytest.mark.parametrize(
    "raw", [None, "220 bad", bytearray(b"220 bad\r\n"), b"x" * (MAX_CAPTURE_BYTES + 1)]
)
def test_untrusted_transport_type_and_aggregate_bound_fail_closed(raw):
    fake = FakeTransport()
    fake.result = raw
    c = compose(fake)
    result = execute(c)
    assert isinstance(result, Failure) and result.error.code is ErrorCode.PARSE_FAILED
    assert c[3].state.active_executions == 0


@pytest.mark.parametrize(
    "extension,advertised",
    [
        ("STARTTLS", True),
        ("starttls", True),
        ("X-STARTTLS", None),
        ("AUTH STARTTLS", None),
    ],
)
def test_starttls_is_exact_extension_without_negotiation(extension, advertised):
    out = execute(
        compose(
            FakeTransport(
                f"220 mail.example.test\r\n250-mail.example.test\r\n250 {extension}\r\n".encode()
            )
        )
    ).value
    assert out.observations[0].data["starttls_advertised"] is advertised
    assert out.observations[0].data["tls_negotiated"] is False


@pytest.mark.parametrize(
    "extension,limit",
    [("SIZE", None), ("SIZE 0", 0), ("SIZE 12345", 12345), ("size 00010", 10)],
)
def test_size_claim_is_metadata_only(extension, limit):
    out = execute(
        compose(
            FakeTransport(
                f"220 mail.example.test\r\n250-mail.example.test\r\n250 {extension}\r\n".encode()
            )
        )
    ).value
    assert out.observations[0].data["size_advertised"] is True
    assert out.observations[0].data["size_limit"] == limit
    assert out.observations[0].data["mail_sent"] is False


def test_server_hello_is_never_an_extension_or_authority():
    out = execute(compose(FakeTransport(b"220 banner\r\n250 STARTTLS\r\n"))).value
    assert out.observations[0].data["extensions"] == []
    assert out.observations[0].data["starttls_advertised"] is None


@pytest.mark.parametrize(
    "name,port", [("smtp", 25), ("submission", 587), ("SMTP", 2525)]
)
def test_reviewed_smtp_and_submission_services_are_explicit_native_alternatives(
    name, port
):
    service = binding().service.model_copy(update={"protocol": name, "port": port})
    c = compose(bindings=(binding(service=service),))
    assert isinstance(
        execute(
            c, request(parameters={"family": "smtp", "port": port, "transport": "tcp"})
        ),
        Success,
    )
    assert c[1].calls[0][:2] == ("192.0.2.10", port)


@pytest.mark.parametrize(
    "extensions",
    [
        "250-SIZE 1\r\n250 SIZE 2\r\n",
        "250 SIZE " + "9" * 21 + "\r\n",
        "250 AUTH " + "A" * 21 + "\r\n",
        "250-STARTTLS\r\n250 bad!keyword\r\n",
        "250 AUTH PLAIN  LOGIN\r\n",
    ],
)
def test_malformed_or_conflicting_extension_details_are_partial_not_guessed(extensions):
    out = execute(
        compose(
            FakeTransport(
                (
                    "220 mail.example.test\r\n250-mail.example.test\r\n" + extensions
                ).encode()
            )
        )
    ).value
    assert out.status == "partial"
    assert out.observations[0].data["starttls_advertised"] is None
    assert not out.observations[0].data["auth_mechanisms"]


def test_unknown_duplicate_extensions_and_mechanisms_preserve_reported_order():
    wire = b"220 banner\r\n250-mail.example.test\r\n250-AUTH LOGIN PLAIN\r\n250-AUTH PLAIN LOGIN X-CUSTOM\r\n250-X-UNKNOWN opaque\r\n250 X-UNKNOWN opaque\r\n"
    out = execute(compose(FakeTransport(wire))).value
    data = out.observations[0].data
    assert data["auth_mechanisms"] == ["LOGIN", "PLAIN", "X-CUSTOM"]
    assert data["extensions"][-2:] == ["X-UNKNOWN opaque", "X-UNKNOWN opaque"]


def test_implicit_tls_request_rejects_before_contact_or_reservation():
    c = compose(clock=lambda: 0.0)
    before = c[3].state
    result = execute(
        c, request(parameters={"family": "smtp", "port": 465, "transport": "tcp"})
    )
    assert isinstance(result, Failure)
    assert c[1].calls == [] and c[3].state == before

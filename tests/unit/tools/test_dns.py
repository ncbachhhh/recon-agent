"""Operational DNS adapter exercised offline, including its native exchange seam."""

import asyncio
import json
import socket
import subprocess
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import dns.exception
import dns.flags
import dns.message
import dns.query
import dns.rcode
import dns.rdatatype
import dns.rrset
import pytest
from pydantic import ValidationError

from recon_agent.core.config.models import ExecutionConfig
from recon_agent.core.errors import ConfigurationError, ErrorCode
from recon_agent.core.results import Failure, Success
from recon_agent.domain import (
    ActionRequest,
    ActionResult,
    ReconStateMachine,
    Scope,
    Target,
)
from recon_agent.domain.budgets import ReservationOutcome
from recon_agent.domain.capabilities import CapabilityId, RiskClass
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
from recon_agent.tools.dns import DnsAdapter
from recon_agent.tools.dns_models import (
    RECORD_TYPES,
    DnsContext,
    DnsInput,
    DnsOutput,
    DnsQueryResult,
    DnsRecord,
)
from recon_agent.tools.native_dns import NativeDnsResolver

FIXTURE = json.loads(
    (Path(__file__).parents[2] / "fixtures/dns/answers.json").read_text()
)
WHEN = datetime(2026, 10, 6, tzinfo=UTC)
CONTEXT = DnsContext(asset_id="asset", execution_id="execution", collected_at=WHEN)


@pytest.fixture(autouse=True)
def no_contact_or_process(monkeypatch):
    blocked = Mock(side_effect=AssertionError("unexpected network/process contact"))
    for name in (
        "getaddrinfo",
        "gethostbyname",
        "gethostbyname_ex",
        "gethostbyaddr",
        "create_connection",
    ):
        monkeypatch.setattr(socket, name, blocked)
    # AF_UNIX event loop self-pipes are local machinery, not DNS/network contact.
    for name in ("connect", "connect_ex", "sendto", "bind", "listen"):
        original = getattr(socket.socket, name)

        def guarded(self, *args, _original=original, **kwargs):
            if self.family != socket.AF_UNIX:
                return blocked()
            return _original(self, *args, **kwargs)

        monkeypatch.setattr(socket.socket, name, guarded)
    for name in ("Popen", "run", "call", "check_call", "check_output"):
        monkeypatch.setattr(subprocess, name, blocked)
    monkeypatch.setattr(asyncio, "create_subprocess_exec", blocked)
    monkeypatch.setattr(asyncio, "create_subprocess_shell", blocked)
    yield
    blocked.assert_not_called()


class FakeResolver:
    def __init__(self, mutate=None, error=None):
        self.calls = []
        self.mutate = mutate
        self.error = error

    async def exchange(self, query, nameserver, timeout_seconds):
        self.calls.append(
            (query.question[0].name.to_text(), nameserver, timeout_seconds)
        )
        if self.error:
            raise self.error
        response = dns.message.make_response(query)
        record_type = dns.rdatatype.to_text(query.question[0].rdtype)
        response.answer.append(
            dns.rrset.from_text(
                FIXTURE["owner"],
                FIXTURE["ttl"],
                "IN",
                record_type,
                *FIXTURE["records"][record_type],
            )
        )
        if self.mutate:
            self.mutate(response)
        return response


def compose(
    resolver=None,
    *,
    config=None,
    nameserver="192.0.2.53",
    roots=None,
    availability=AdapterAvailability.AVAILABLE,
    limits=None,
    clock=None,
):
    config = config or ExecutionConfig()
    fake = resolver or FakeResolver()
    adapter = DnsAdapter(nameserver, config, fake)
    registry = ToolRegistry((AdapterRegistration(adapter, availability),))
    scope = ScopeValidator(
        Scope(
            id="scope",
            roots=roots
            if roots is not None
            else (
                Target(id="root", kind="domain", value="example.test"),
                Target(id="resolver", kind="ip", value="192.0.2.53"),
            ),
        )
    )
    budgets = BudgetController(
        limits or ExecutionBudget.from_config(config),
        registry,
        **({"clock": clock} if clock else {}),
    )
    state = ReconStateMachine()
    dedup = ActionDeduplicator(ActionCanonicalizer(registry, scope), state)
    policy = ActionPolicyValidator(
        registry,
        scope,
        ActionPolicyConfig(
            allowed_capabilities=frozenset({CapabilityId.RESOLVE_DNS}),
            allowed_risk_classes=frozenset({RiskClass.ACTIVE_SAFE}),
        ),
        budgets,
        dedup,
    )
    return adapter, fake, policy, budgets, state


def request(types=None, **changes):
    values = dict(
        id="action",
        capability="resolve_dns",
        target="EXAMPLE.test.",
        parameters={} if types is None else {"record_types": types},
        reason="Collect DNS evidence",
    )
    values.update(changes)
    return ActionRequest(**values)


def execute(composition, action=None, context=CONTEXT):
    adapter, _, policy, budgets, _ = composition
    selected = policy.registry.resolve("resolve_dns")
    assert isinstance(selected, Success) and selected.value is adapter
    return asyncio.run(
        adapter.execute(
            action or request(), policy=policy, budgets=budgets, context=context
        )
    )


@pytest.mark.parametrize("record_type", RECORD_TYPES)
def test_common_records_normalize_with_provenance(record_type):
    composition = compose()
    result = execute(composition, request([record_type]))
    assert isinstance(result, Success)
    output = result.value
    assert output.resolver_address == "192.0.2.53"
    query = output.queries[0]
    assert query.outcome == "answer"
    assert query.query_target == "example.test"
    assert len(query.records) == len(FIXTURE["records"][record_type])
    assert all(r.ttl == 300 and r.owner == "example.test" for r in query.records)
    assert all(r.record_type == record_type for r in query.records)
    assert output.asset.value == "example.test"
    assert output.asset.observation_ids == tuple(o.id for o in output.observations)
    for observation in output.observations:
        assert observation.kind == "dns" and observation.source == "native_dns"
        assert observation.asset_id == CONTEXT.asset_id
        assert observation.execution_id == CONTEXT.execution_id
        assert observation.observed_at == WHEN
        assert observation.data["query_target"] == "example.test"
        assert observation.evidence_ids == (output.evidence[0].id,)
    evidence = output.evidence[0]
    assert evidence.trust == "untrusted" and evidence.capability == "resolve_dns"
    assert evidence.origin == "example.test" and evidence.execution_id == "execution"
    assert evidence.collected_at == WHEN and evidence.locator == "queries/0"
    assert len(evidence.sha256) == 64
    assert composition[1].calls == [("example.test.", "192.0.2.53", 30.0)] or (
        composition[1].calls[0][2] <= 30.0
    )
    assert composition[3].state.active_executions == 0
    assert dict(composition[3].state.outcomes) == {ReservationOutcome.COMPLETED: 1}
    assert DnsOutput.model_validate_json(output.model_dump_json()) == output
    if record_type == "AAAA":
        assert {r.value for r in query.records} == {"2001:db8::1", "2001:db8::2"}
    if record_type in ("CNAME", "NS", "MX"):
        assert all(
            r.value.endswith("outside.test") and r.value.islower()
            for r in query.records
        )
    if record_type == "MX":
        assert {r.preference for r in query.records} == {10, 20}
    if record_type == "TXT":
        assert any(r.txt_chunks_hex == ("ff00",) for r in query.records)
        assert any("ignore policy" in r.value for r in query.records)
        assert any(len(r.txt_chunks_hex) == 2 for r in query.records)


def test_default_queries_are_fixed_sorted_and_never_follow_discoveries():
    c = compose()
    result = execute(c)
    assert isinstance(result, Success)
    assert [q.record_type for q in result.value.queries] == sorted(RECORD_TYPES)
    assert len(c[1].calls) == 6
    assert {call[0] for call in c[1].calls} == {"example.test."}
    for value in (
        "alias.outside.test",
        "ns1.outside.test",
        "mail.outside.test",
        "192.0.2.10",
        "2001:db8::1",
    ):
        assert isinstance(c[2].scope_validator.validate_value(value), Failure)
        denied = execute(compose(), request(["A"], target=value))
        assert (
            isinstance(denied, Failure)
            and denied.error.code == ErrorCode.SCOPE_REJECTED
        )
    assert len(c[2].scope_validator.scope.roots) == 2
    assert c[3].state.permitted_actions == 1
    assert c[3].state.host_actions == (("192.0.2.53", 1), ("example.test", 1))


def test_state_ingestion_keeps_lineage_and_dedup_remains_effective():
    c = compose()
    output = execute(c, request(["A"])).value
    owner = c[4]
    action = request(["A"])
    assert isinstance(
        owner.record_asset(output.asset.model_copy(update={"observation_ids": ()})),
        Success,
    )
    assert isinstance(owner.record_action_requested(action, recorded_at=WHEN), Success)
    assert isinstance(
        owner.mark_action_approved(
            action.id, policy_reference="policy", recorded_at=WHEN
        ),
        Success,
    )
    assert isinstance(
        owner.mark_action_started(
            action.id, execution_id="execution", recorded_at=WHEN
        ),
        Success,
    )
    result = ActionResult(
        id="result",
        action_id=action.id,
        status="completed",
        recorded_at=WHEN,
        observations=output.observations,
        evidence=output.evidence,
        execution_ids=("execution",),
    )
    assert isinstance(owner.record_action_result(result), Success)
    assert owner.state.observations == output.observations
    denied = execute(c, request(["A"]))
    assert isinstance(denied, Failure)
    assert len(c[1].calls) == 1


@pytest.mark.parametrize("outcome", ["no_answer", "nxdomain"])
def test_negative_answers_are_completed_structured_evidence(outcome):
    def mutate(response):
        response.answer.clear()
        if outcome == "nxdomain":
            response.set_rcode(dns.rcode.NXDOMAIN)

    c = compose(FakeResolver(mutate))
    result = execute(c, request(["A"]))
    assert isinstance(result, Success)
    assert result.value.queries[0].outcome == outcome
    assert result.value.queries[0].records == ()
    assert result.value.observations[0].data["outcome"] == outcome
    assert result.value.evidence[0].trust == "untrusted"


@pytest.mark.parametrize(
    "error,code",
    [
        (TimeoutError("secret"), ErrorCode.TOOL_TIMEOUT),
        (dns.exception.Timeout(), ErrorCode.TOOL_TIMEOUT),
        (OSError("secret"), ErrorCode.TOOL_EXECUTION_FAILED),
        (dns.query.UnexpectedSource("secret"), ErrorCode.TOOL_EXECUTION_FAILED),
        (dns.exception.FormError("secret"), ErrorCode.PARSE_FAILED),
        (dns.query.BadResponse("secret"), ErrorCode.PARSE_FAILED),
        (ValueError("secret"), ErrorCode.PARSE_FAILED),
    ],
)
def test_exchange_failures_are_canonical_bounded_and_charge_attempt(error, code):
    c = compose(FakeResolver(error=error))
    result = execute(c, request(["A", "AAAA"]))
    assert isinstance(result, Failure) and result.error.code == code
    assert "secret" not in result.model_dump_json()
    assert not result.error.retryable
    assert len(c[1].calls) == 1
    assert c[3].state.permitted_actions == 1 and c[3].state.active_executions == 0
    outcome = (
        ReservationOutcome.TIMEOUT
        if code == ErrorCode.TOOL_TIMEOUT
        else ReservationOutcome.FAILED
    )
    assert dict(c[3].state.outcomes) == {outcome: 1}


@pytest.mark.parametrize(
    "rcode", [dns.rcode.SERVFAIL, dns.rcode.REFUSED, dns.rcode.FORMERR]
)
def test_resolver_rcodes_are_infrastructure_failures(rcode):
    c = compose(FakeResolver(lambda response: response.set_rcode(rcode)))
    result = execute(c, request(["A"]))
    assert (
        isinstance(result, Failure)
        and result.error.code == ErrorCode.TOOL_EXECUTION_FAILED
    )


def change_id(response):
    response.id ^= 1


def wrong_question(response):
    response.question = dns.message.make_query("outside.test.", "A").question


def wrong_type(response):
    response.answer = [
        dns.rrset.from_text("example.test.", 10, "IN", "NS", "outside.test.")
    ]


def bad_ttl(response):
    response.answer[0].ttl = -1


@pytest.mark.parametrize(
    "mutate",
    [
        change_id,
        wrong_question,
        wrong_type,
        bad_ttl,
        lambda r: setattr(r, "flags", r.flags | dns.flags.TC),
        lambda r: setattr(r, "flags", r.flags & ~dns.flags.QR),
        lambda r: r.set_rcode(dns.rcode.NXDOMAIN),
        lambda r: setattr(r.answer[0], "rdclass", dns.rdataclass.CH),
    ],
)
def test_malformed_response_is_parse_failure(mutate):
    c = compose(FakeResolver(mutate))
    result = execute(c, request(["A"]))
    assert isinstance(result, Failure) and result.error.code == ErrorCode.PARSE_FAILED
    assert len(c[1].calls) == 1


@pytest.mark.parametrize(
    "target",
    [
        "outside.test",
        "sub.example.test",
        "example.test.evil",
        "example.test;id",
        "$(whoami)",
        "-example.test",
        "example..test",
        "éxample.test",
        "xn--example.test",
        "example.test..",
        "example.test\n",
        "*.example.test",
        "",
    ],
)
def test_bad_or_unauthorized_target_never_resolves(target):
    c = compose()
    action = request(["A"]).model_copy(update={"target": target})
    result = execute(c, action)
    assert isinstance(result, Failure)
    assert c[1].calls == [] and c[3].state.permitted_actions == 0


@pytest.mark.parametrize(
    "target,kind",
    [
        ("192.0.2.10", "ip"),
        ("2001:db8::1", "ip"),
        ("https://example.test/path", "url"),
        ("192.0.2.0/24", "cidr"),
    ],
)
def test_authorized_non_hostname_targets_reject_before_exchange(target, kind):
    c = compose(roots=(Target(id="root", kind=kind, value=target),))
    result = execute(c, request(["A"], target=target))
    assert isinstance(result, Failure)
    assert result.error.code == (
        ErrorCode.BUDGET_EXHAUSTED
        if kind == "cidr"
        else ErrorCode.PLANNER_VALIDATION_FAILED
    )
    assert c[1].calls == []


@pytest.mark.parametrize(
    "parameters",
    [
        {"record_types": []},
        {"record_types": ["ANY"]},
        {"record_types": ["AXFR"]},
        {"record_types": ["a"]},
        {"record_types": ["A", "A"]},
        {"record_types": "A"},
        {"record_types": [1]},
        {"record_types": [True]},
        {"server": "outside.test"},
        {"resolver": "192.0.2.53"},
        {"timeout": 0},
        {"packet": "raw"},
        {"flags": ["-x"]},
        {"executable": "dig"},
        {"command": "dig example.test"},
        {"target": "outside.test"},
    ],
)
def test_strict_parameters_never_dispatch(parameters):
    c = compose()
    result = execute(c, request(["A"]).model_copy(update={"parameters": parameters}))
    assert (
        isinstance(result, Failure)
        and result.error.code == ErrorCode.PLANNER_VALIDATION_FAILED
    )
    assert c[1].calls == [] and c[3].state.permitted_actions == 0


@pytest.mark.parametrize(
    "availability", [AdapterAvailability.NOT_CHECKED, AdapterAvailability.UNAVAILABLE]
)
def test_unavailable_binding_never_dispatches(availability):
    c = compose(availability=availability)
    result = asyncio.run(
        c[0].execute(request(), policy=c[2], budgets=c[3], context=CONTEXT)
    )
    assert (
        isinstance(result, Failure) and result.error.code == ErrorCode.TOOL_UNAVAILABLE
    )
    assert c[1].calls == []


def test_missing_resolver_authorization_and_exclusions_deny():
    c = compose(roots=(Target(id="root", kind="domain", value="example.test"),))
    result = execute(c)
    assert isinstance(result, Failure) and result.error.code == ErrorCode.SCOPE_REJECTED
    assert c[1].calls == [] and c[3].state.permitted_actions == 0
    original = compose()
    scope = ScopeValidator(
        Scope(
            id="scope",
            roots=original[2].scope_validator.scope.roots,
            exclusions=(Target(id="exclude", kind="hostname", value="example.test"),),
        )
    )
    policy = replace(original[2], scope_validator=scope)
    result = asyncio.run(
        original[0].execute(
            request(), policy=policy, budgets=original[3], context=CONTEXT
        )
    )
    assert isinstance(result, Failure) and original[1].calls == []


@pytest.mark.parametrize(
    "nameserver",
    ["resolver.test", "192.0.2.53;id", "::ffff:192.0.2.53", "fe80::1%eth0", ""],
)
def test_trusted_endpoint_must_be_unambiguous_numeric_address(nameserver):
    with pytest.raises(ConfigurationError):
        DnsAdapter(nameserver, ExecutionConfig())


@pytest.mark.parametrize(
    "change", ["binding", "budget", "policy", "capability", "context", "asset"]
)
def test_execution_revalidates_composition(change):
    c = compose()
    adapter, fake, policy, budgets, _ = c
    action, context = request(["A"]), CONTEXT
    if change == "binding":
        adapter = DnsAdapter("192.0.2.53", ExecutionConfig(), fake)
    elif change == "budget":
        budgets = compose()[3]
    elif change == "policy":
        policy = replace(policy, config=ActionPolicyConfig())
    elif change == "capability":
        action = action.model_copy(update={"capability": "enumerate_subdomains"})
    elif change == "context":
        context = CONTEXT.model_copy(update={"collected_at": datetime(2026, 1, 1)})
    elif change == "asset":
        action = action.model_copy(update={"asset_id": "another"})
    result = asyncio.run(
        adapter.execute(action, policy=policy, budgets=budgets, context=context)
    )
    assert (
        isinstance(result, Failure)
        and result.error.code == ErrorCode.PLANNER_VALIDATION_FAILED
    )
    assert fake.calls == []


def test_deterministic_order_duplicates_and_alias_records():
    def mutate(response):
        response.answer.reverse()
        for rrset in response.answer:
            items = list(rrset)
            rrset.clear()
            for item in reversed(items):
                rrset.add(item)

    first = execute(compose(), request(["AAAA", "A"]))
    second = execute(compose(FakeResolver(mutate)), request(["A", "AAAA"]))
    assert first == second

    def alias(response):
        response.answer.append(
            dns.rrset.from_text(
                "example.test.", 20, "IN", "CNAME", "alias.outside.test."
            )
        )
        response.answer.append(
            dns.rrset.from_text("alias.outside.test.", 30, "IN", "A", "203.0.113.7")
        )
        response.answer.append(response.answer[0])

    c = compose(FakeResolver(alias))
    result = execute(c, request(["A"]))
    assert isinstance(result, Success) and len(result.value.queries[0].records) == 4
    assert any(r.owner == "alias.outside.test" for r in result.value.queries[0].records)
    assert c[1].calls[0][0] == "example.test." and len(c[1].calls) == 1


def test_native_transport_uses_fixed_bounded_udp_and_no_fallback(monkeypatch):
    exchange = AsyncMock(
        side_effect=lambda query, *_args, **_kwargs: dns.message.make_response(query)
    )
    monkeypatch.setattr(dns.asyncquery, "udp", exchange)
    c = compose(NativeDnsResolver(), clock=lambda: 10.0)
    result = execute(c, request(["A"]))
    assert (
        isinstance(result, Success) and result.value.queries[0].outcome == "no_answer"
    )
    args, kwargs = exchange.call_args
    assert (
        args[1] == "192.0.2.53"
        and args[0].question[0].name.to_text() == "example.test."
    )
    assert args[0].payload == 1232 and args[0].edns == 0
    assert kwargs == dict(
        timeout=30.0,
        port=53,
        ignore_unexpected=False,
        ignore_errors=False,
        raise_on_truncation=True,
    )


def test_cancellation_and_outer_timeout_release_resources():
    class Hanging:
        async def exchange(self, *args):
            await asyncio.Event().wait()

    async def cancel():
        c = compose(Hanging())
        task = asyncio.create_task(
            c[0].execute(request(["A"]), policy=c[2], budgets=c[3], context=CONTEXT)
        )
        await asyncio.sleep(0)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert c[3].state.active_executions == 0
        assert dict(c[3].state.outcomes) == {ReservationOutcome.CANCELLED: 1}
        assert c[3].state.permitted_actions == 1

    asyncio.run(cancel())
    c = compose(Hanging(), config=ExecutionConfig(default_timeout_seconds=0.01))
    result = execute(c, request(["A"]))
    assert isinstance(result, Failure) and result.error.code == ErrorCode.TOOL_TIMEOUT
    assert c[3].state.active_executions == 0


def test_output_limit_and_record_bounds_fail_closed():
    c = compose(config=ExecutionConfig(max_output_bytes=100))
    result = execute(c, request(["A"]))
    assert isinstance(result, Failure) and result.error.code == ErrorCode.PARSE_FAILED
    assert dict(c[3].state.outcomes) == {ReservationOutcome.FAILED: 1}

    def too_many(response):
        response.answer = [
            dns.rrset.from_text(
                "example.test.",
                10,
                "IN",
                "A",
                *[f"192.0.{i // 256}.{i % 256}" for i in range(257)],
            )
        ]

    result = execute(compose(FakeResolver(too_many)), request(["A"]))
    assert isinstance(result, Failure) and result.error.code == ErrorCode.PARSE_FAILED


def test_budget_and_session_deadline_checks_before_resolution():
    c = compose(clock=lambda: 10.0, limits=ExecutionBudget(max_actions=1))
    assert isinstance(execute(c, request(["A"])), Success)
    assert execute(c, request(["AAAA"])).error.code == ErrorCode.BUDGET_EXHAUSTED
    assert len(c[1].calls) == 1
    clock = Mock(return_value=10.0)
    c = compose(clock=clock)
    clock.return_value = 610.0
    assert execute(c).error.code == ErrorCode.BUDGET_EXHAUSTED
    assert c[1].calls == []


@pytest.mark.parametrize(
    "model,fields",
    [
        (
            DnsQueryResult,
            dict(query_target="example.test", record_type="A", outcome="answer"),
        ),
        (
            DnsQueryResult,
            dict(
                query_target="example.test",
                record_type="A",
                outcome="no_answer",
                records=(
                    DnsRecord(
                        owner="example.test", record_type="A", value="192.0.2.1", ttl=0
                    ),
                ),
            ),
        ),
        (
            DnsRecord,
            dict(owner="example.test", record_type="MX", value="mail.test", ttl=1),
        ),
        (
            DnsRecord,
            dict(
                owner="example.test",
                record_type="A",
                value="192.0.2.1",
                ttl=1,
                preference=1,
            ),
        ),
        (
            DnsRecord,
            dict(
                owner="example.test",
                record_type="A",
                value="192.0.2.1",
                ttl=1,
                txt_chunks_hex=("ff",),
            ),
        ),
    ],
)
def test_internal_output_contract_consistency(model, fields):
    with pytest.raises(ValidationError):
        model(**fields)


def test_query_schema_canonical_defaults():
    assert DnsInput(record_types=["NS", "A"]).record_types == ["A", "NS"]
    assert DnsInput().record_types == sorted(RECORD_TYPES)


def test_nxdomain_alias_retains_cname_without_querying_destination():
    def mutate(response):
        response.answer = [
            dns.rrset.from_text(
                "example.test.", 20, "IN", "CNAME", "missing.outside.test."
            )
        ]
        response.set_rcode(dns.rcode.NXDOMAIN)

    c = compose(FakeResolver(mutate))
    result = execute(c, request(["A"]))
    assert isinstance(result, Success)
    assert result.value.queries[0].outcome == "nxdomain"
    assert result.value.queries[0].records[0].value == "missing.outside.test"
    assert len(c[1].calls) == 1
    assert isinstance(
        c[2].scope_validator.validate_value("missing.outside.test"), Failure
    )


def test_shared_resolver_host_budget_is_enforced_atomically():
    c = compose(
        clock=lambda: 10.0,
        limits=ExecutionBudget(max_actions_per_host=1, capability_rate_actions=10),
    )
    assert isinstance(execute(c, request(["A"])), Success)
    scope = ScopeValidator(
        Scope(
            id="scope",
            roots=(
                *c[2].scope_validator.scope.roots,
                Target(id="another", kind="hostname", value="another.test"),
            ),
        )
    )
    policy = replace(
        c[2],
        scope_validator=scope,
        completed_action_eligibility=ActionDeduplicator(
            ActionCanonicalizer(c[2].registry, scope), c[4]
        ),
    )
    result = asyncio.run(
        c[0].execute(
            request(["A"], target="another.test"),
            policy=policy,
            budgets=c[3],
            context=CONTEXT,
        )
    )
    assert (
        isinstance(result, Failure) and result.error.code == ErrorCode.BUDGET_EXHAUSTED
    )
    assert len(c[1].calls) == 1 and c[3].state.permitted_actions == 1


def test_session_expiry_during_exchange_discards_observations():
    clock = Mock(return_value=10.0)

    def expire(response):
        clock.return_value = 610.0

    c = compose(FakeResolver(expire), clock=clock)
    result = execute(c, request(["A", "AAAA"]))
    assert isinstance(result, Failure) and result.error.code == ErrorCode.TOOL_TIMEOUT
    assert len(c[1].calls) == 1
    assert dict(c[3].state.outcomes) == {ReservationOutcome.TIMEOUT: 1}


def test_aggregate_record_cap_is_not_reset_between_questions():
    def many(response):
        record_type = dns.rdatatype.to_text(response.question[0].rdtype)
        values = (
            [f"192.0.2.{i}" for i in range(150)]
            if record_type == "A"
            else [f"2001:db8::{i:x}" for i in range(150)]
        )
        response.answer = [
            dns.rrset.from_text("example.test.", 1, "IN", record_type, *values)
        ]

    c = compose(FakeResolver(many))
    result = execute(c, request(["A", "AAAA"]))
    assert isinstance(result, Failure) and result.error.code == ErrorCode.PARSE_FAILED
    assert len(c[1].calls) == 2


def test_oversized_txt_and_invalid_envelope_fail_without_partial_success():
    def large(response):
        response.answer = [
            dns.rrset.from_text(
                "example.test.", 1, "IN", "TXT", " ".join(['"' + "x" * 255 + '"'] * 40)
            )
        ]

    assert (
        execute(compose(FakeResolver(large)), request(["TXT"])).error.code
        == ErrorCode.PARSE_FAILED
    )

    class InvalidEnvelope:
        async def exchange(self, *args):
            return "run this command"

    assert (
        execute(compose(InvalidEnvelope()), request(["A"])).error.code
        == ErrorCode.PARSE_FAILED
    )


def test_nxdomain_output_rejects_non_alias_records():
    with pytest.raises(ValidationError):
        DnsQueryResult(
            query_target="example.test",
            record_type="A",
            outcome="nxdomain",
            records=(
                DnsRecord(
                    owner="example.test", record_type="A", value="192.0.2.1", ttl=1
                ),
            ),
        )

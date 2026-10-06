"""Actual M2 adapters, real policy/resources/state, and exclusively fake contacts."""

import asyncio
import builtins
import json
import socket
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import Mock

import dns.message
import dns.rrset
import pytest

from recon_agent.core.audit import AuditEventType
from recon_agent.core.config.models import ExecutionConfig
from recon_agent.core.errors import (
    ErrorCode,
    StateTransitionError,
    ToolTimeoutError,
    ToolUnavailableError,
)
from recon_agent.core.results import Failure, Success
from recon_agent.domain import (
    Asset,
    ReconState,
    ReconStateMachine,
    Scope,
    Target,
)
from recon_agent.domain.budgets import ReservationOutcome
from recon_agent.domain.capabilities import CapabilityId, RiskClass
from recon_agent.execution import ProcessExecution
from recon_agent.orchestration.discovery import DiscoveryRequest, DiscoveryWorkflow
from recon_agent.policy import (
    ActionPolicyConfig,
    BudgetController,
    ExecutionBudget,
    ScopeValidator,
)
from recon_agent.tools import AdapterAvailability, AdapterRegistration, ToolRegistry
from recon_agent.tools.dns import DnsAdapter
from recon_agent.tools.dnsx import DnsxAdapter
from recon_agent.tools.httpx import HttpxAdapter
from recon_agent.tools.naabu import NaabuAdapter
from recon_agent.tools.naabu_models import ContactBinding, NaabuSettings
from recon_agent.tools.nmap import NmapAdapter
from recon_agent.tools.nmap_models import NmapSettings
from recon_agent.tools.subfinder import SubfinderAdapter

WHEN = datetime(2026, 10, 6, tzinfo=UTC)
M2 = tuple(
    CapabilityId(value)
    for value in (
        "resolve_dns",
        "enumerate_subdomains",
        "verify_dns",
        "probe_http",
        "discover_ports",
        "fingerprint_services",
    )
)
VERSION = b"Nmap version 7.95 ( https://nmap.org )\nCompiled with: openssl\nCompiled without: liblua\n"


@pytest.fixture(autouse=True)
def no_contact(monkeypatch):
    blocked = Mock(side_effect=AssertionError("Unexpected contact/process/provider"))
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
    monkeypatch.setattr(asyncio, "create_subprocess_exec", blocked)
    monkeypatch.setattr(asyncio, "create_subprocess_shell", blocked)
    monkeypatch.setattr(
        "recon_agent.tools.nmap.shutil.which", lambda _: "/trusted/nmap"
    )
    original_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name == "groq" or name.startswith(
            ("recon_agent.providers", "recon_agent.planners")
        ):
            return blocked()
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    yield
    blocked.assert_not_called()


def process(raw):
    return Success(
        value=ProcessExecution(
            argument_count=1,
            return_code=0,
            stdout=raw,
            stderr=b"",
            stdout_truncated=False,
            stderr_truncated=False,
            started_at=WHEN,
            finished_at=WHEN,
            duration_seconds=0.0,
        )
    )


class Contacts:
    def __init__(self):
        self.state = None
        self.calls = []
        self.inputs = {}
        self.failures = {}
        self.subdomains = ("api.example.test", "excluded.example.test")
        self.addresses = ("192.0.2.10",)
        self.ports = (80, 443)
        self.before_contact = None
        self.wait = None

    def started(self, name):
        assert self.state.state.action_lifecycles[-1].phase.value == "started"
        self.calls.append(name)
        if self.before_contact:
            self.before_contact(name)

    async def exchange(self, query, address, timeout):
        if not self.calls or self.calls[-1] != "native_dns":
            self.started("native_dns")
        assert address == "192.0.2.53" and 0 < timeout <= 60
        response = dns.message.make_response(query)
        kind = dns.rdatatype.to_text(query.question[0].rdtype)
        records = {
            "A": "203.0.113.99",
            "CNAME": "outside.test.",
            "MX": "10 mail.outside.test.",
            "NS": "ns.outside.test.",
        }
        if kind in records:
            response.answer.append(
                dns.rrset.from_text("example.test.", 60, "IN", kind, records[kind])
            )
        return response

    async def run(self, spec):
        name = Path(spec.executable).name
        if spec.args == ("--version",):
            return process(VERSION)
        self.started(name)
        if self.wait and name == self.wait[0]:
            self.wait[1].set()
            await asyncio.Event().wait()
        if name in self.failures:
            return self.failures[name]
        if name == "subfinder":
            raw = b"\n".join(
                json.dumps(
                    dict(host=h, input="example.test", sources=["hackertarget"])
                ).encode()
                for h in self.subdomains
            )
        elif name in ("dnsx", "httpx", "naabu"):
            flag = "-l"
            values = Path(spec.args[spec.args.index(flag) + 1]).read_text().splitlines()
            self.inputs[name] = tuple(values)
            if name == "dnsx":
                raw = b"\n".join(
                    json.dumps(
                        dict(
                            host=h,
                            resolver=["192.0.2.53:53"],
                            status_code="NOERROR",
                            timestamp="2026-10-06T00:00:00Z",
                            all=[f"{h} 60 IN A 203.0.113.99"],
                        )
                    ).encode()
                    for h in values
                )
            elif name == "httpx":
                raw = b"\n".join(
                    json.dumps(
                        dict(
                            input=url,
                            url=url,
                            host_ip="192.0.2.10",
                            status_code=302,
                            failed=False,
                            location="https://outside.test/",
                            tech=["Example"],
                        )
                    ).encode()
                    for url in values
                )
            else:
                assert set(values) == set(self.addresses)
                raw = b"\n".join(
                    json.dumps(dict(ip=a, port=p, protocol="tcp", tls=False)).encode()
                    for a in values
                    for p in self.ports
                )
        else:
            assert name == "nmap"
            address = spec.args[-1]
            ports = [int(p) for p in spec.args[spec.args.index("-p") + 1].split(",")]
            self.inputs.setdefault(name, []).append((address, tuple(ports)))
            raw = (
                '<nmaprun scanner="nmap" version="7.95"><scaninfo type="connect" protocol="tcp"/>'
                f'<host><address addr="{address}" addrtype="ipv4"/><ports>'
                + "".join(
                    f'<port protocol="tcp" portid="{p}"><state state="open"/><service name="http" product="Example" version="1.2"/></port>'
                    for p in ports
                )
                + '</ports></host><runstats><finished exit="success"/></runstats></nmaprun>'
            ).encode()
        return process(raw)


def compose(*, missing=None, limits=None, scope=None, config=None, contacts=None):
    contacts = contacts or Contacts()
    config = config or ExecutionConfig()
    state = ReconStateMachine()
    contacts.state = state
    scope = scope or Scope(
        id="scope",
        allow_subdomains=True,
        roots=(
            Target(id="root", kind="domain", value="example.test"),
            Target(id="resolver", kind="ip", value="192.0.2.53"),
            Target(id="address", kind="ip", value="192.0.2.10"),
        ),
        exclusions=(
            Target(id="excluded", kind="hostname", value="excluded.example.test"),
        ),
    )
    nmap = asyncio.run(
        NmapAdapter.detect(
            config,
            settings=NmapSettings(data_directory="/trusted/data"),
            runner=contacts,
        )
    ).value
    adapters = (
        DnsAdapter("192.0.2.53", config, contacts),
        SubfinderAdapter("/trusted/subfinder", config, contacts),
        DnsxAdapter("/trusted/dnsx", "192.0.2.53", config, contacts),
        HttpxAdapter("/trusted/httpx", "192.0.2.53", ("192.0.2.10",), config, contacts),
        NaabuAdapter(
            "/trusted/naabu",
            config,
            NaabuSettings(
                bindings=(
                    ContactBinding(
                        hostname="example.test", addresses=contacts.addresses
                    ),
                    ContactBinding(
                        hostname="api.example.test", addresses=contacts.addresses
                    ),
                )
            ),
            contacts,
        ),
        nmap,
    )
    registry = ToolRegistry(
        tuple(
            AdapterRegistration(a, AdapterAvailability.AVAILABLE)
            for a in adapters
            if a.definition.descriptor.capability != missing
        )
    )
    budgets = BudgetController(
        limits or ExecutionBudget.from_config(config), registry, clock=lambda: 0.0
    )
    workflow = DiscoveryWorkflow(
        registry,
        ScopeValidator(scope),
        budgets,
        state,
        ActionPolicyConfig(
            allowed_capabilities=frozenset(M2),
            allowed_risk_classes=frozenset((RiskClass.PASSIVE, RiskClass.ACTIVE_SAFE)),
        ),
        now=lambda: WHEN,
    )
    return workflow, contacts


def run(workflow, run_id="run", target="example.test"):
    return asyncio.run(
        workflow.run(
            DiscoveryRequest(run_id=run_id, session_id="session", target=target)
        )
    )


def test_full_flow_state_lifecycle_scope_and_no_planner():
    workflow, contacts = compose()
    result = run(workflow)
    assert isinstance(result, Success)
    assert contacts.calls == [
        "native_dns",
        "subfinder",
        "dnsx",
        "httpx",
        "naabu",
        "nmap",
    ]
    state = result.value.state
    assert len(state.assets) == 6 and state.hosts and state.endpoints and state.services
    assert {o.source for o in state.observations} == {
        "native_dns",
        "subfinder",
        "dnsx",
        "httpx",
        "naabu",
        "nmap",
    }
    assert state.planner_decisions == ()
    assert all(
        e.trust == "untrusted" and e.sha256 and e.execution_id for e in state.evidence
    )
    assert {a.capability for a in state.action_requests} == {c.value for c in M2}
    assert all(
        [t.phase.value for t in a.transitions]
        == ["requested", "approved", "started", "completed"]
        for a in state.action_lifecycles
    )
    assert workflow.budgets.state.permitted_actions == 6
    assert workflow.budgets.state.active_executions == 0
    assert len(state.budget_snapshots) == 6
    assert ReconState.model_validate_json(state.model_dump_json()) == state
    assert contacts.inputs["dnsx"] == ("api.example.test.", "example.test.")
    assert all("excluded" not in h for h in contacts.inputs["httpx"])
    assert contacts.inputs["nmap"] == [("192.0.2.10", (80, 443))]
    assert any(o.data.get("value") == "203.0.113.99" for o in state.observations)
    assert any(
        o.data.get("hostname") == "excluded.example.test" for o in state.observations
    )
    fingerprints = [o for o in state.observations if o.source == "nmap"]
    assert all(o.data["discovery_evidence_ids"] for o in fingerprints)
    assert result.value.audit_events[-1].event_type is AuditEventType.SESSION_COMPLETED
    assert all(e.planner_decision_id is None for e in result.value.audit_events)


def test_repeated_workflow_is_deterministic_and_duplicates_skip():
    first, first_contacts = compose()
    second, second_contacts = compose()
    assert run(first) == run(second)
    old = first.state_machine.state
    repeated = run(first, "repeat")
    assert isinstance(repeated, Success)
    assert len(repeated.value.skipped_action_ids) == 6
    assert repeated.value.state == old
    assert first_contacts.calls == second_contacts.calls
    assert first.budgets.state.permitted_actions == 6
    assert repeated.value.outputs == ()
    assert run(first, "run").error.code is ErrorCode.STATE_TRANSITION_INVALID


@pytest.mark.parametrize(
    "dimension,value,expected_calls",
    [
        ("max_actions", 2, 2),
        ("max_actions_per_host", 2, 2),
        ("max_session_output_bytes", 4 * 1048576, 2),
    ],
)
def test_budget_stops_without_start_or_double_reservation(
    dimension, value, expected_calls
):
    workflow, contacts = compose(limits=ExecutionBudget(**{dimension: value}))
    result = run(workflow)
    assert result.error.code is ErrorCode.BUDGET_EXHAUSTED
    assert len(contacts.calls) == expected_calls
    state = workflow.state_machine.state
    assert state.action_results[-1].status == "rejected"
    assert state.action_results[-1].execution_ids == ()
    assert state.action_results[-1].error.code is ErrorCode.BUDGET_EXHAUSTED
    assert workflow.budgets.state.permitted_actions == expected_calls
    assert workflow.budgets.state.active_executions == 0


@pytest.mark.parametrize("missing", M2)
def test_missing_tool_rejected_without_fabricated_start_and_other_branches_continue(
    missing,
):
    workflow, contacts = compose(missing=missing)
    result = run(workflow)
    assert isinstance(result, Success)
    rejected = [r for r in result.value.state.action_results if r.status == "rejected"]
    assert len(rejected) == 1
    assert rejected[0].error.code is ErrorCode.TOOL_UNAVAILABLE
    assert rejected[0].execution_ids == ()
    assert all(
        a.transitions[-1].phase.value != "started"
        for a in result.value.state.action_lifecycles
    )
    if missing is CapabilityId.DISCOVER_PORTS:
        assert "nmap" not in contacts.calls


@pytest.mark.parametrize("name", ["subfinder", "dnsx", "httpx", "naabu", "nmap"])
@pytest.mark.parametrize(
    "failure",
    [
        Failure(error=ToolTimeoutError("Fake timeout").to_error_info()),
        Failure(error=ToolUnavailableError("Fake unavailable").to_error_info()),
        process(b"malformed"),
    ],
)
def test_tool_failures_preserve_prior_facts_and_continue(name, failure):
    workflow, contacts = compose()
    contacts.failures[name] = failure
    result = run(workflow)
    assert isinstance(result, Success)
    state = result.value.state
    failed = [r for r in state.action_results if r.status in ("failed", "timeout")]
    assert len(failed) == 1
    assert state.observations and state.observations[0].source == "native_dns"
    assert failed[0].observations == () and failed[0].execution_ids
    assert workflow.budgets.state.active_executions == 0
    if name != "naabu":
        assert "nmap" in contacts.calls


def test_zero_results_are_explicit_and_do_not_invent_services():
    workflow, contacts = compose()
    contacts.subdomains = ()
    contacts.ports = ()
    contacts.failures["dnsx"] = process(b"")
    contacts.failures["httpx"] = process(b"")
    result = run(workflow)
    assert isinstance(result, Success)
    assert len(result.value.state.action_results) == 5
    assert [r.status for r in result.value.state.action_results] == [
        "completed",
        "completed",
        "partial",
        "partial",
        "completed",
    ]
    assert not result.value.state.services and not result.value.state.endpoints
    assert "nmap" not in contacts.calls


@pytest.mark.parametrize("target", ["outside.test", "excluded.example.test"])
def test_seed_policy_denial_stops_all_contacts(target):
    workflow, contacts = compose()
    result = run(workflow, target=target)
    assert result.error.code is ErrorCode.SCOPE_REJECTED
    assert contacts.calls == []
    assert workflow.state_machine.state.action_results[0].status == "rejected"
    assert workflow.budgets.state.permitted_actions == 0


def test_resolver_and_bound_ip_require_independent_scope():
    scope = Scope(
        id="scope",
        allow_subdomains=True,
        roots=(Target(id="root", kind="domain", value="example.test"),),
    )
    workflow, contacts = compose(scope=scope)
    assert run(workflow).error.code is ErrorCode.SCOPE_REJECTED
    assert contacts.calls == []
    scope = Scope(
        id="scope",
        allow_subdomains=True,
        roots=(
            Target(id="root", kind="domain", value="example.test"),
            Target(id="resolver", kind="ip", value="192.0.2.53"),
        ),
    )
    workflow, contacts = compose(scope=scope)
    assert run(workflow).error.code is ErrorCode.SCOPE_REJECTED
    assert contacts.calls == ["native_dns", "subfinder", "dnsx"]
    assert workflow.budgets.state.permitted_actions == 3


def test_atomic_result_ingestion_failure_keeps_prior_state(monkeypatch):
    workflow, contacts = compose()
    original = ReconStateMachine.record_action_result
    before = []

    def reject(self, result, **facts):
        if (
            facts
            and facts["assets"][0].value == "example.test"
            and result.observations[0].source == "httpx"
        ):
            before.append(self.state)
            bad = Asset(
                id=facts["assets"][0].id,
                kind="host",
                value="example.test",
                observation_ids=("missing",),
            )
            return original(self, result, **{**facts, "assets": (bad,)})
        return original(self, result, **facts)

    monkeypatch.setattr(ReconStateMachine, "record_action_result", reject)
    result = run(workflow)
    assert result.error.code is ErrorCode.STATE_TRANSITION_INVALID
    assert workflow.state_machine.state == before[0]
    assert len(workflow.state_machine.state.action_results) == 3
    assert "naabu" not in contacts.calls
    assert workflow.budgets.state.active_executions == 0


def test_failed_start_callback_aborts_before_contact(monkeypatch):
    workflow, contacts = compose()
    monkeypatch.setattr(
        ReconStateMachine,
        "mark_action_started",
        lambda *a, **k: Failure(
            error=StateTransitionError("Fake invalid transition").to_error_info()
        ),
    )
    result = run(workflow)
    assert result.error.code is ErrorCode.STATE_TRANSITION_INVALID
    assert contacts.calls == []
    assert workflow.state_machine.state.action_lifecycles[0].phase.value == "approved"
    assert workflow.budgets.state.permitted_actions == 1
    assert dict(workflow.budgets.state.outcomes)[ReservationOutcome.ABORTED] == 1
    assert workflow.budgets.state.active_executions == 0


def test_cancellation_records_terminal_state_and_releases_resources():
    workflow, contacts = compose()

    async def scenario():
        entered = asyncio.Event()
        contacts.wait = ("httpx", entered)
        task = asyncio.create_task(
            workflow.run(
                DiscoveryRequest(
                    run_id="run", session_id="session", target="example.test"
                )
            )
        )
        await entered.wait()
        second = await workflow.run(
            DiscoveryRequest(
                run_id="other", session_id="session", target="example.test"
            )
        )
        assert second.error.code is ErrorCode.STATE_TRANSITION_INVALID
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(scenario())
    assert workflow.state_machine.state.action_results[-1].status == "cancelled"
    assert workflow.budgets.state.active_executions == 0
    assert (
        workflow.report.audit_events[-1].event_type is AuditEventType.SESSION_CANCELLED
    )


def test_candidate_bound_stops_before_verification():
    workflow, contacts = compose()
    contacts.subdomains = tuple(f"h{i}.example.test" for i in range(64))
    result = run(workflow)
    assert result.error.code is ErrorCode.PLANNER_VALIDATION_FAILED
    assert contacts.calls == ["native_dns", "subfinder"]
    assert len(workflow.state_machine.state.action_results) == 2


def test_rate_exhaustion_stops_second_fingerprint():
    contacts = Contacts()
    contacts.addresses = ("192.0.2.10", "192.0.2.11")
    scope = Scope(
        id="scope",
        allow_subdomains=True,
        roots=(
            Target(id="root", kind="domain", value="example.test"),
            Target(id="addresses", kind="cidr", value="192.0.2.0/24"),
        ),
        exclusions=(
            Target(id="excluded", kind="hostname", value="excluded.example.test"),
        ),
    )
    workflow, contacts = compose(scope=scope, contacts=contacts)
    result = run(workflow)
    assert result.error.code is ErrorCode.BUDGET_EXHAUSTED
    assert contacts.calls.count("nmap") == 1
    last = workflow.state_machine.state.action_results[-1]
    assert last.status == "rejected" and last.execution_ids == ()
    assert workflow.budgets.state.permitted_actions == 6
    assert workflow.budgets.state.active_executions == 0


@pytest.mark.parametrize("capability", M2)
def test_each_adapter_start_notification_failure_prevents_contact(
    capability, monkeypatch
):
    workflow, contacts = compose()
    original = ReconStateMachine.mark_action_started

    def mark(self, action_id, **kwargs):
        request = next(a for a in self.state.action_requests if a.id == action_id)
        if request.capability == capability.value:
            return Failure(
                error=StateTransitionError("Fake start failure").to_error_info()
            )
        return original(self, action_id, **kwargs)

    monkeypatch.setattr(ReconStateMachine, "mark_action_started", mark)
    result = run(workflow)
    assert result.error.code is ErrorCode.STATE_TRANSITION_INVALID
    assert workflow.state_machine.state.action_lifecycles[-1].phase.value == "approved"
    names = dict(
        zip(
            M2,
            ("native_dns", "subfinder", "dnsx", "httpx", "naabu", "nmap"),
            strict=True,
        )
    )
    assert names[capability] not in contacts.calls
    assert workflow.budgets.state.active_executions == 0
    assert dict(workflow.budgets.state.outcomes)[ReservationOutcome.ABORTED] == 1


def test_partial_valid_port_facts_continue_to_fingerprint():
    workflow, contacts = compose()
    contacts.failures["naabu"] = process(
        b'{"ip":"192.0.2.10","port":80,"protocol":"tcp","tls":false}\nmalformed'
    )
    result = run(workflow)
    assert isinstance(result, Success)
    assert result.value.state.action_results[-2].status == "partial"
    assert result.value.state.action_results[-2].error.code is ErrorCode.PARSE_FAILED
    assert contacts.inputs["nmap"] == [("192.0.2.10", (80,))]


def test_unavailable_registration_is_a_prestart_rejection():
    workflow, contacts = compose()
    adapters = []
    for entry in workflow.registry.catalog():
        adapter = workflow.registry.resolve(entry.capability).value
        availability = (
            AdapterAvailability.UNAVAILABLE
            if entry.capability is CapabilityId.PROBE_HTTP
            else AdapterAvailability.AVAILABLE
        )
        adapters.append(AdapterRegistration(adapter, availability))
    registry = ToolRegistry(adapters)
    workflow.registry = registry
    workflow.budgets = BudgetController(ExecutionBudget(), registry, clock=lambda: 0.0)
    result = run(workflow)
    assert isinstance(result, Success)
    rejected = next(
        r for r in result.value.state.action_results if r.status == "rejected"
    )
    assert (
        rejected.error.code is ErrorCode.TOOL_UNAVAILABLE
        and rejected.execution_ids == ()
    )
    assert "httpx" not in contacts.calls and "nmap" in contacts.calls


def test_undetected_nmap_snapshot_stays_unavailable():
    workflow, contacts = compose()
    original = workflow.registry.resolve(CapabilityId.FINGERPRINT_SERVICES).value
    undetected = NmapAdapter(
        original.executable, original.config, original.settings, contacts
    )
    clone = undetected.with_selections(())
    assert not clone._verified and not undetected._verified
    assert original._verified and original.settings.selections == ()


def test_invalid_start_notification_is_structured():
    from recon_agent.execution.lifecycle import notify_execution_start

    for callback in (lambda: None, lambda: {"status": "success", "value": 1}):
        result = notify_execution_start(callback)
        assert result.error.code is ErrorCode.STATE_TRANSITION_INVALID


def test_unsuccessful_terminal_subject_ingestion_is_atomic():
    workflow, contacts = compose()
    original = ReconStateMachine.record_action_result
    contacts.failures["httpx"] = process(b"malformed")
    before = []
    from unittest.mock import patch

    def wrong(self, result, **facts):
        if result.status == "failed":
            before.append(self.state)
            return original(
                self,
                result,
                assets=(Asset(id="forbidden", kind="host", value="example.test"),),
            )
        return original(self, result, **facts)

    with patch.object(ReconStateMachine, "record_action_result", wrong):
        result = run(workflow)
    assert result.error.code is ErrorCode.STATE_TRANSITION_INVALID
    assert workflow.state_machine.state == before[0]
    assert workflow.budgets.state.active_executions == 0


def test_final_scope_recheck_aborts_started_attempt_with_original_denial(monkeypatch):
    workflow, contacts = compose()
    original = ScopeValidator.validate_value
    mark = ReconStateMachine.mark_action_started
    active = [False]

    def started(self, action_id, **kwargs):
        changed = mark(self, action_id, **kwargs)
        if isinstance(changed, Success):
            active[0] = self.state.action_requests[-1].capability == "probe_http"
        return changed

    def current(self, value):
        # Scope/schema callbacks must not reenter the state owner during admission.
        return original(self, "outside.test" if active[0] else value)

    monkeypatch.setattr(ReconStateMachine, "mark_action_started", started)
    monkeypatch.setattr(ScopeValidator, "validate_value", current)
    result = run(workflow)
    assert result.error.code is ErrorCode.SCOPE_REJECTED
    terminal = workflow.state_machine.state.action_results[-1]
    assert terminal.status == "cancelled" and terminal.error.code is ErrorCode.CANCELLED
    assert terminal.execution_ids and not terminal.observations
    assert "httpx" not in contacts.calls and "naabu" not in contacts.calls
    assert any(
        e.error and e.error.code is ErrorCode.SCOPE_REJECTED
        for e in workflow.report.audit_events
    )
    assert workflow.budgets.state.active_executions == 0
    assert dict(workflow.budgets.state.outcomes)[ReservationOutcome.ABORTED] == 1


def test_disallowed_policy_is_terminal_without_contacts():
    workflow, contacts = compose()
    workflow.policy_config = ActionPolicyConfig()
    result = run(workflow)
    assert result.error.code is ErrorCode.PLANNER_VALIDATION_FAILED
    assert contacts.calls == []
    assert workflow.state_machine.state.action_results[0].status == "rejected"
    assert workflow.budgets.state.permitted_actions == 0

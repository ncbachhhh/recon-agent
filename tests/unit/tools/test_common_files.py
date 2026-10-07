"""Offline common-file execution, authorization, evidence and resource regressions."""

import asyncio
import base64
import socket
import subprocess
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from unittest.mock import Mock

import pytest

from recon_agent.core.config.models import ExecutionConfig
from recon_agent.core.errors import ConfigurationError, ErrorCode, StateTransitionError
from recon_agent.core.results import Failure, Success
from recon_agent.domain import (
    ActionRequest,
    ActionResult,
    ReconStateMachine,
    Scope,
    Target,
)
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
from recon_agent.tools import (
    AdapterAvailability,
    AdapterRegistration,
    ToolRegistry,
    common_files,
)
from recon_agent.tools.common_files import MAX_BODY_BYTES, CommonFilesAdapter
from recon_agent.tools.common_files_models import (
    COMMON_PATHS,
    CommonFilesContext,
    ContactBinding,
    HttpResponse,
)

WHEN = datetime(2026, 10, 7, tzinfo=UTC)
CONTEXT = CommonFilesContext(
    asset_id="asset", execution_id="execution", collected_at=WHEN
)
FIXTURES = Path(__file__).parents[2] / "fixtures/common_files"
BINDINGS = (
    ContactBinding(host="example.test", address="192.0.2.10"),
    ContactBinding(host="cdn.example.test", address="192.0.2.11"),
)


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    blocked = Mock(side_effect=AssertionError("unexpected network/process"))
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
    # Virtual pacing time; real asyncio timeout/cancellation still runs normally.
    clock = [100.0]
    sleeps = []
    original_sleep = asyncio.sleep

    async def sleep(seconds):
        sleeps.append(seconds)
        clock[0] += seconds
        await original_sleep(0)

    monkeypatch.setattr(common_files, "monotonic", lambda: clock[0])
    monkeypatch.setattr(common_files.asyncio, "sleep", sleep)
    yield sleeps
    blocked.assert_not_called()


def response(path="/robots.txt", **changes):
    values = dict(
        status_code=200,
        content_type="application/xml" if path == "/sitemap.xml" else "text/plain",
        body=(FIXTURES / path.rsplit("/", 1)[-1]).read_bytes(),
    )
    values.update(changes)
    return HttpResponse(**values)


class FakeTransport:
    def __init__(self, results=None, mutate=None):
        self.results = results or {}
        self.calls = []
        self.mutate = mutate

    async def get(self, url, address, timeout_seconds, max_body_bytes):
        self.calls.append((url, address, timeout_seconds, max_body_bytes))
        if self.mutate:
            self.mutate()
        path = "/" + url.split("/", 3)[-1]
        result = self.results.get(url, self.results.get(path))
        if isinstance(result, BaseException):
            raise result
        if callable(result):
            return await result()
        return result if result is not None else response(path)


def compose(
    fake=None,
    scope=None,
    config=None,
    limits=None,
    bindings=BINDINGS,
    availability=AdapterAvailability.AVAILABLE,
    clock=None,
):
    config = config or ExecutionConfig()
    fake = fake or FakeTransport()
    adapter = CommonFilesAdapter(bindings, config, fake)
    registry = ToolRegistry((AdapterRegistration(adapter, availability),))
    validator = ScopeValidator(
        scope
        or Scope(
            id="scope",
            allow_subdomains=True,
            roots=(
                Target(id="name", kind="domain", value="example.test"),
                Target(id="ip", kind="cidr", value="192.0.2.0/24"),
                Target(id="ipv6", kind="ip", value="2001:db8::10"),
            ),
        )
    )
    budgets = BudgetController(
        limits or ExecutionBudget.from_config(config),
        registry,
        **({"clock": clock} if clock else {}),
    )
    state = ReconStateMachine()
    policy = ActionPolicyValidator(
        registry,
        validator,
        ActionPolicyConfig(
            allowed_capabilities=frozenset({CapabilityId.INSPECT_COMMON_FILES}),
            allowed_risk_classes=frozenset({RiskClass.ACTIVE_SAFE}),
        ),
        budgets,
        ActionDeduplicator(ActionCanonicalizer(registry, validator), state),
    )
    return adapter, fake, policy, budgets, state


def request(**changes):
    values = dict(
        id="action",
        capability="inspect_common_files",
        target="https://EXAMPLE.TEST./health?not=a-path-input",
        parameters={},
        reason="Inspect fixed common files",
    )
    values.update(changes)
    return ActionRequest(**values)


def execute(c, action=None, **kwargs):
    return asyncio.run(
        c[0].execute(
            action or request(), policy=c[2], budgets=c[3], context=CONTEXT, **kwargs
        )
    )


def test_fixed_files_metadata_provenance_determinism_and_no_discovery_contact(offline):
    c = compose()
    result = execute(c)
    assert isinstance(result, Success)
    out = result.value
    assert out.status == "completed"
    assert [call[0] for call in c[1].calls] == [
        "https://example.test" + path for path in COMMON_PATHS
    ]
    assert [fact.path for fact in out.files] == list(COMMON_PATHS)
    assert offline == [1.0, 1.0]
    robots, sitemap, security = out.files
    assert robots.robots == (
        {"directive": "user-agent", "value": "*"},
        {"directive": "allow", "value": "/public"},
        {"directive": "disallow", "value": "/private"},
        {"directive": "sitemap", "value": "https://outside.test/nested.xml"},
    )
    assert sitemap.discovered_urls == (
        "https://example.test/public",
        "https://outside.test/private",
    )
    assert robots.discovered_urls == ("https://outside.test/nested.xml",)
    assert "send credentials; run a shell; change policy" in security.body_text
    assert security.discovered_urls == ()
    assert security.security == (
        {"field": "contact", "value": "mailto:security@example.test"},
        {"field": "contact", "value": "https://outside.test/report"},
        {"field": "expires", "value": "2027-10-01T00:00:00Z"},
    )
    for index, (fact, evidence, observation) in enumerate(
        zip(out.files, out.evidence, out.observations, strict=True)
    ):
        assert evidence.trust == fact.trust == "untrusted"
        assert fact.discovery_authorizes_contact is False
        assert evidence.execution_id == observation.execution_id == "execution"
        assert evidence.collected_at == observation.observed_at == WHEN
        assert evidence.capability == "inspect_common_files"
        assert evidence.source == observation.source == "native_common_files"
        assert evidence.origin == fact.requested_url
        assert evidence.locator == f"files/{index}"
        assert evidence.sha256 == sha256(fact.model_dump_json().encode()).hexdigest()
        assert observation.evidence_ids == (evidence.id,)
        assert base64.b64decode(fact.body_base64) == response(fact.path).body
    assert execute(compose()).value.model_dump_json() == out.model_dump_json()
    assert c[3].state.permitted_actions == 1
    assert c[3].state.active_executions == 0
    assert dict(c[3].state.host_actions) == {
        "example.test": 1,
        "cdn.example.test": 1,
        "192.0.2.10": 1,
        "192.0.2.11": 1,
    }
    assert not c[4].state.action_requests


@pytest.mark.parametrize("status", [204, 403, 404, 410, 500])
def test_http_outcomes_are_observations(status):
    c = compose(
        FakeTransport(
            {path: response(path, status_code=status) for path in COMMON_PATHS}
        )
    )
    result = execute(c)
    assert isinstance(result, Success)
    assert result.value.status == "completed"
    assert [fact.status_code for fact in result.value.files] == [status] * 3
    assert len(result.value.observations) == 3


@pytest.mark.parametrize(
    "parameters",
    [
        {"paths": ["/etc/passwd"]},
        {"url": "https://outside.test/"},
        {"headers": {"Authorization": "data"}},
        {"method": "POST"},
        {"proxy": "http://outside.test"},
        {"body": "x"},
        {"extra_args": []},
        {"path": "/../private"},
    ],
)
def test_parameter_injection_rejected_before_contact(parameters):
    c = compose()
    result = execute(c, request(parameters=parameters))
    assert isinstance(result, Failure)
    assert result.error.code == ErrorCode.PLANNER_VALIDATION_FAILED
    assert c[1].calls == []
    assert c[3].state.permitted_actions == 0


@pytest.mark.parametrize(
    "target",
    [
        "https://outside.test/",
        "example.test",
        "ftp://example.test/",
        "https://unbound.example.test/",
        "https://example.test/#fragment",
    ],
)
def test_invalid_initial_endpoint_never_contacts(target):
    c = compose()
    assert isinstance(execute(c, request(target=target)), Failure)
    assert c[1].calls == []
    assert c[3].state.permitted_actions == 0


def test_name_membership_does_not_authorize_contact_address():
    scope = Scope(
        id="scope", roots=(Target(id="root", kind="domain", value="example.test"),)
    )
    c = compose(scope=scope)
    result = execute(c)
    assert isinstance(result, Failure)
    assert result.error.code == ErrorCode.SCOPE_REJECTED
    assert not c[1].calls


@pytest.mark.parametrize(
    "target,bindings,address",
    [
        (
            "http://192.0.2.10:8080/",
            (ContactBinding(host="192.0.2.10", address="192.0.2.10"),),
            "192.0.2.10",
        ),
        (
            "https://[2001:db8::10]/",
            (ContactBinding(host="2001:db8::10", address="2001:db8::10"),),
            "2001:db8::10",
        ),
    ],
)
def test_numeric_http_contact(target, bindings, address):
    c = compose(bindings=bindings)
    result = execute(c, request(target=target))
    assert isinstance(result, Success)
    assert all(call[1] == address for call in c[1].calls)


def test_in_scope_bound_redirect_followed_after_independent_validation():
    c = compose(
        FakeTransport(
            {
                "https://example.test/robots.txt": response(
                    status_code=302, location="https://cdn.example.test/robots.txt"
                )
            }
        )
    )
    result = execute(c)
    assert isinstance(result, Success)
    fact = result.value.files[0]
    assert fact.final_url == "https://cdn.example.test/robots.txt"
    assert fact.contact_address == "192.0.2.11"
    assert fact.redirects[0].outcome == "followed"
    assert len(c[1].calls) == 4


@pytest.mark.parametrize(
    "location",
    [
        "https://outside.test/robots.txt",
        "https://unbound.example.test/robots.txt",
        "https://example.test/admin",
        "/../private",
        "/robots.txt?arbitrary=1",
        "file:///etc/passwd",
        "http://example.test/robots.txt",
        "https://192.0.2.99/robots.txt",
        "https://user:pass@example.test/robots.txt",
    ],
)
def test_redirect_rejection_never_contacts_destination(location):
    c = compose(
        FakeTransport({"/robots.txt": response(status_code=302, location=location)})
    )
    result = execute(c)
    assert isinstance(result, Success)
    fact = result.value.files[0]
    assert result.value.status == "partial"
    assert fact.status_code == 302
    assert fact.final_url == "https://example.test/robots.txt"
    assert fact.redirects[0].outcome == "rejected"
    assert len(c[1].calls) == 3


def test_redirect_loop_and_limit():
    c = compose(
        FakeTransport(
            {"/robots.txt": response(status_code=302, location="/robots.txt")}
        )
    )
    assert execute(c).value.files[0].redirects[0].outcome == "loop"
    bindings = BINDINGS + (
        ContactBinding(host="third.example.test", address="192.0.2.12"),
        ContactBinding(host="fourth.example.test", address="192.0.2.13"),
    )
    results = {
        f"https://{host}/robots.txt": response(
            status_code=302, location=f"https://{dest}/robots.txt"
        )
        for host, dest in zip(
            ["example.test", "cdn.example.test", "third.example.test"],
            ["cdn.example.test", "third.example.test", "fourth.example.test"],
            strict=True,
        )
    }
    c = compose(FakeTransport(results), bindings=bindings)
    fact = execute(c).value.files[0]
    assert fact.redirects[-1].outcome == "limit"
    assert len(c[1].calls) == 5
    assert all("fourth.example.test" not in call[0] for call in c[1].calls)


@pytest.mark.parametrize(
    "failure,code",
    [
        (TimeoutError(), ErrorCode.TOOL_TIMEOUT),
        (ConnectionError(), ErrorCode.TOOL_EXECUTION_FAILED),
        (ValueError(), ErrorCode.PARSE_FAILED),
    ],
)
def test_request_failure_is_partial_with_no_fabricated_status(failure, code):
    c = compose(FakeTransport({"/robots.txt": failure}))
    result = execute(c)
    assert isinstance(result, Success)
    assert result.value.status == "partial"
    assert result.value.files[0].status_code is None
    assert result.value.files[0].errors[0].code == code
    assert result.value.files[1].status_code == 200


def test_oversized_body_prefix_is_bounded_and_marked():
    c = compose(
        FakeTransport({"/robots.txt": response(body=b"x" * (MAX_BODY_BYTES + 1))})
    )
    fact = execute(c).value.files[0]
    assert fact.truncated
    assert fact.retained_bytes == MAX_BODY_BYTES
    assert len(base64.b64decode(fact.body_base64)) == MAX_BODY_BYTES
    assert fact.robots == ()
    assert fact.errors[0].code == ErrorCode.PARSE_FAILED


@pytest.mark.parametrize(
    "body",
    [
        b"not XML",
        b"<urlset>",
        b'<!DOCTYPE urlset SYSTEM "https://outside.test/dtd"><urlset/>',
        b'<!DOCTYPE urlset [<!ENTITY x SYSTEM "file:///etc/passwd">]><urlset><url><loc>&x;</loc></url></urlset>',
        b'<!DOCTYPE urlset [<!ENTITY x "a"><!ENTITY y "&x;&x;">]><urlset/>',
        "<urlset/>".encode("utf-16"),
        b'<?xml version="1.0" encoding="iso-8859-1"?><urlset/>',
        b"<urlset><url><loc><nested>https://outside.test</nested></loc></url></urlset>",
        b"<urlset><url><loc>file:///etc/passwd</loc></url></urlset>",
        b"<urlset><url/></urlset>",
        b"<unsupported/>",
    ],
)
def test_hostile_xml_cannot_contact_external_resources(body):
    c = compose(FakeTransport({"/sitemap.xml": response("/sitemap.xml", body=body)}))
    result = execute(c)
    assert isinstance(result, Success)
    fact = result.value.files[1]
    assert fact.errors[0].code == ErrorCode.PARSE_FAILED
    assert fact.discovered_urls == ()
    assert len(c[1].calls) == 3


def test_sitemap_index_is_observed_without_recursion():
    body = b"<sitemapindex><sitemap><loc>https://outside.test/nested.xml</loc></sitemap></sitemapindex>"
    c = compose(FakeTransport({"/sitemap.xml": response("/sitemap.xml", body=body)}))
    fact = execute(c).value.files[1]
    assert fact.discovered_urls == ("https://outside.test/nested.xml",)
    assert len(c[1].calls) == 3


@pytest.mark.parametrize(
    "changes",
    [{"content_type": "text/html"}, {"content_encoding": "gzip"}, {"body": b"\xff"}],
)
def test_unsupported_content_keeps_raw_evidence(changes):
    c = compose(FakeTransport({"/robots.txt": response(**changes)}))
    fact = execute(c).value.files[0]
    assert fact.errors
    assert fact.body_base64
    assert not fact.robots


def test_scope_rechecked_after_started_and_before_every_contact():
    c = compose()
    original = c[2].scope_validator.validate_value
    denied = [False]

    def validate(value):
        return original("https://outside.test/") if denied[0] else original(value)

    object.__setattr__(c[2].scope_validator, "validate_value", validate)

    def started():
        denied[0] = True
        return Success(value=None)

    result = execute(c, on_started=started)
    assert isinstance(result, Failure)
    assert result.error.code == ErrorCode.SCOPE_REJECTED
    assert not c[1].calls
    assert c[3].state.active_executions == 0


def test_start_failure_no_contact_preserves_charge():
    c = compose()
    result = execute(
        c,
        on_started=lambda: Failure(
            error=StateTransitionError("start rejected").to_error_info()
        ),
    )
    assert isinstance(result, Failure)
    assert not c[1].calls
    assert c[3].state.permitted_actions == 1
    assert c[3].state.active_executions == 0


def test_unavailable_and_wrong_registry_binding_no_contact():
    c = compose(availability=AdapterAvailability.NOT_CHECKED)
    assert execute(c).error.code == ErrorCode.TOOL_UNAVAILABLE
    assert not c[1].calls
    c = compose()
    other = CommonFilesAdapter(BINDINGS, ExecutionConfig(), FakeTransport())
    result = asyncio.run(
        other.execute(request(), policy=c[2], budgets=c[3], context=CONTEXT)
    )
    assert result.error.code == ErrorCode.PLANNER_VALIDATION_FAILED
    assert not other.transport.calls


def test_normalized_output_budget_failure():
    c = compose(config=ExecutionConfig(max_output_bytes=100))
    result = execute(c)
    assert isinstance(result, Failure)
    assert result.error.code == ErrorCode.PARSE_FAILED
    assert c[3].state.active_executions == 0


def test_host_and_action_budget_prevents_contact():
    c = compose(limits=ExecutionBudget(max_actions=1))
    assert isinstance(execute(c), Success)
    assert execute(c, request(id="second")).error.code == ErrorCode.BUDGET_EXHAUSTED
    assert len(c[1].calls) == 3


def test_cancellation_releases_concurrency_without_refund():
    async def scenario():
        entered = asyncio.Event()

        async def wait():
            entered.set()
            await asyncio.Event().wait()

        c = compose(FakeTransport({"/robots.txt": wait}))
        task = asyncio.create_task(
            c[0].execute(request(), policy=c[2], budgets=c[3], context=CONTEXT)
        )
        await entered.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert c[3].state.active_executions == 0
        assert c[3].state.permitted_actions == 1

    asyncio.run(scenario())


@pytest.mark.parametrize("partial", [False, True])
def test_real_state_ingestion_and_dedup(partial):
    c = (
        compose(
            FakeTransport(
                {
                    "/robots.txt": response(
                        status_code=302, location="https://outside.test/robots.txt"
                    )
                }
            )
        )
        if partial
        else compose()
    )
    action = request()
    state = c[4]
    assert isinstance(state.record_action_requested(action, recorded_at=WHEN), Success)
    assert isinstance(
        state.mark_action_approved(
            action.id, policy_reference="policy", recorded_at=WHEN
        ),
        Success,
    )

    def started():
        outcome = state.mark_action_started(
            action.id, execution_id="execution", recorded_at=WHEN
        )
        return outcome if isinstance(outcome, Failure) else Success(value=None)

    out = execute(c, action, on_started=started).value
    result = ActionResult(
        id="result",
        action_id=action.id,
        status=out.status,
        recorded_at=WHEN,
        execution_ids=("execution",),
        observations=out.observations,
        evidence=out.evidence,
        error=out.errors[0] if out.errors else None,
    )
    assert isinstance(state.record_action_result(result, assets=(out.asset,)), Success)
    assert isinstance(execute(c, request(id="replay")), Failure)
    assert len(c[1].calls) == 3


@pytest.mark.parametrize(
    "bindings",
    [
        (),
        BINDINGS + BINDINGS,
        (ContactBinding(host="example.test", address="not-ip"),),
        (ContactBinding(host="EXAMPLE.TEST", address="192.0.2.10"),),
        (ContactBinding(host="example.test", address="::ffff:192.0.2.10"),),
    ],
)
def test_invalid_trusted_configuration(bindings):
    with pytest.raises(ConfigurationError):
        CommonFilesAdapter(bindings, ExecutionConfig())


@pytest.mark.parametrize(
    "path,body",
    [
        ("/robots.txt", b"Allow: /x\n" * 257),
        ("/robots.txt", b"Disallow: /" + b"x" * 2048),
        ("/.well-known/security.txt", b"Contact: mailto:a@example.test\n" * 257),
        (
            "/sitemap.xml",
            b"<urlset>"
            + b"<url><loc>https://example.test/</loc></url>" * 257
            + b"</urlset>",
        ),
        (
            "/sitemap.xml",
            b"<urlset><url>"
            + b"<x>" * 17
            + b"</x>" * 17
            + b"<loc>https://example.test</loc></url></urlset>",
        ),
    ],
)
def test_metadata_bounds_are_atomic(path, body):
    c = compose(FakeTransport({path: response(path, body=body)}))
    fact = next(fact for fact in execute(c).value.files if fact.path == path)
    assert fact.errors
    assert fact.robots == fact.security == fact.discovered_urls == ()
    assert len(c[1].calls) == 3


def test_whole_action_deadline_stops_before_next_request():
    c = compose(config=ExecutionConfig(default_timeout_seconds=1.0))
    result = execute(c)
    assert isinstance(result, Failure)
    assert result.error.code == ErrorCode.TOOL_TIMEOUT
    assert len(c[1].calls) == 1
    assert c[3].state.active_executions == 0
    assert c[3].state.permitted_actions == 1


def test_expired_session_prevents_first_request():
    clock = [0.0]
    c = compose(
        clock=lambda: clock[0], limits=ExecutionBudget(max_duration_seconds=1.0)
    )
    clock[0] = 1.0
    assert execute(c).error.code == ErrorCode.BUDGET_EXHAUSTED
    assert c[1].calls == []


def test_session_expiry_during_http_releases_charge_and_stops():
    clock = [0.0]
    c = compose(
        FakeTransport(mutate=lambda: clock.__setitem__(0, 2.0)),
        clock=lambda: clock[0],
        limits=ExecutionBudget(max_duration_seconds=1.0),
    )
    result = execute(c)
    assert result.error.code == ErrorCode.TOOL_TIMEOUT
    assert len(c[1].calls) == 1
    assert c[3].state.active_executions == 0


def test_stricter_request_rate_is_obeyed(offline):
    c = compose(limits=ExecutionBudget(capability_rate_window_seconds=4.0))
    assert isinstance(execute(c), Success)
    assert offline == [4.0, 4.0]


def test_truncated_redirect_does_not_trigger_another_request():
    c = compose(
        FakeTransport(
            {
                "/robots.txt": response(
                    status_code=302,
                    truncated=True,
                    location="https://cdn.example.test/robots.txt",
                )
            }
        )
    )
    fact = execute(c).value.files[0]
    assert fact.truncated and fact.errors
    assert len(c[1].calls) == 3


def test_denied_changed_scope_after_first_contact_stops_next_contact():
    c = compose()
    original = c[2].scope_validator.validate_value
    denied = [False]

    def validate(value):
        return original("https://outside.test/") if denied[0] else original(value)

    object.__setattr__(c[2].scope_validator, "validate_value", validate)
    c[1].mutate = lambda: denied.__setitem__(0, True)
    result = execute(c)
    assert result.error.code == ErrorCode.SCOPE_REJECTED
    assert len(c[1].calls) == 1
    assert c[3].state.active_executions == 0


def test_native_transport_composes_with_real_adapter_and_fixed_requests(monkeypatch):
    from recon_agent.tools.native_http import NativeHttpTransport

    calls = []
    writers = []

    class Reader:
        def __init__(self, wire):
            self.wire = wire

        async def read(self, size):
            part, self.wire = self.wire[:size], self.wire[size:]
            return part

    class Writer:
        def __init__(self):
            self.data = b""
            self.transport = Mock()
            self.closed = False

        def write(self, value):
            self.data += value

        async def drain(self):
            pass

        def close(self):
            self.closed = True

    async def connect(address, port, **kwargs):
        path = COMMON_PATHS[len(calls)]
        reply = response(path)
        wire = (
            b"HTTP/1.1 200 OK\r\nContent-Type: "
            + reply.content_type.encode()
            + b"\r\nContent-Length: "
            + str(len(reply.body)).encode()
            + b"\r\n\r\n"
            + reply.body
        )
        writer = Writer()
        calls.append((address, port))
        writers.append(writer)
        return Reader(wire), writer

    monkeypatch.setattr(asyncio, "open_connection", connect)
    c = compose()
    adapter = CommonFilesAdapter(BINDINGS, ExecutionConfig(), NativeHttpTransport())
    # Recompose actual registry/policy/budgets; do not bypass adapter binding checks.
    registry = ToolRegistry(
        (AdapterRegistration(adapter, AdapterAvailability.AVAILABLE),)
    )
    budgets = BudgetController(ExecutionBudget(), registry)
    policy = ActionPolicyValidator(
        registry,
        c[2].scope_validator,
        c[2].config,
        budgets,
        ActionDeduplicator(ActionCanonicalizer(registry, c[2].scope_validator), c[4]),
    )
    result = asyncio.run(
        adapter.execute(request(), policy=policy, budgets=budgets, context=CONTEXT)
    )
    assert isinstance(result, Success)
    assert result.value.status == "completed"
    assert calls == [("192.0.2.10", 443)] * 3
    for path, writer in zip(COMMON_PATHS, writers, strict=True):
        assert writer.data.startswith(b"GET " + path.encode() + b" HTTP/1.1\r\n")
        assert writer.closed
        writer.transport.abort.assert_called_once()

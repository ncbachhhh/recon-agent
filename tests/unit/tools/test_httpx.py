"""HTTPX offline fixtures: every denied batch stays upstream of process contact."""

import asyncio
import json
import os
import socket
import subprocess
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from recon_agent.core.config.models import ExecutionConfig
from recon_agent.core.errors import (
    ConfigurationError,
    ErrorCode,
    ToolTimeoutError,
    ToolUnavailableError,
)
from recon_agent.core.results import Failure, Success
from recon_agent.domain import ActionRequest, ReconStateMachine, Scope, Target
from recon_agent.domain.capabilities import CapabilityId, RiskClass
from recon_agent.execution import ProcessExecution
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
from recon_agent.tools.httpx import HttpxAdapter
from recon_agent.tools.httpx_models import HttpProbeOutput, HttpxContext

WHEN = datetime(2026, 10, 6, tzinfo=UTC)
CONTEXT = HttpxContext(asset_id="asset", execution_id="execution", collected_at=WHEN)
FIXTURE = (Path(__file__).parents[2] / "fixtures/httpx/probing.jsonl").read_bytes()


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


def process(stdout=FIXTURE, **changes):
    values = dict(
        argument_count=19,
        return_code=0,
        stdout=stdout,
        stderr=b"",
        stdout_truncated=False,
        stderr_truncated=False,
        started_at=WHEN,
        finished_at=WHEN,
        duration_seconds=0.0,
    )
    values.update(changes)
    return Success(value=ProcessExecution(**values))


class FakeRunner:
    def __init__(self, result=None, mutate=None):
        self.result = result if result is not None else process()
        self.calls = []
        self.inputs = []
        self.mutate = mutate

    async def run(self, spec):
        self.calls.append(spec)
        env = dict(spec.environment)
        assert Path(env["HOME"]).is_dir()
        assert set(env) <= {
            "HOME",
            "USERPROFILE",
            "APPDATA",
            "LOCALAPPDATA",
            "XDG_CONFIG_HOME",
            "TMPDIR",
            "TMP",
            "TEMP",
            "SystemRoot",
        }
        if "-l" in spec.args:
            path = Path(spec.args[spec.args.index("-l") + 1])
            self.inputs.append(path.read_text())
            assert path.parent == Path(env["HOME"])
        if self.mutate:
            self.mutate()
        return self.result


def compose(
    fake=None,
    scope=None,
    config=None,
    limits=None,
    clock=None,
    availability=AdapterAvailability.AVAILABLE,
):
    config = config or ExecutionConfig()
    fake = fake or FakeRunner()
    adapter = HttpxAdapter(
        "/trusted/httpx", "192.0.2.53", ("192.0.2.10", "2001:db8::10"), config, fake
    )
    registry = ToolRegistry((AdapterRegistration(adapter, availability),))
    validator = ScopeValidator(
        scope
        or Scope(
            id="scope",
            allow_subdomains=True,
            roots=(
                Target(id="root", kind="domain", value="example.test"),
                Target(id="resolver", kind="ip", value="192.0.2.53"),
                Target(id="address", kind="ip", value="192.0.2.10"),
                Target(id="address6", kind="ip", value="2001:db8::10"),
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
            allowed_capabilities=frozenset({CapabilityId.PROBE_HTTP}),
            allowed_risk_classes=frozenset({RiskClass.ACTIVE_SAFE}),
        ),
        budgets,
        ActionDeduplicator(ActionCanonicalizer(registry, validator), state),
    )
    return adapter, fake, policy, budgets, state


def request(candidates=None, **changes):
    values = dict(
        id="action",
        capability="probe_http",
        target="EXAMPLE.TEST.",
        parameters={
            "candidates": candidates
            if candidates is not None
            else [
                "https://api.example.test/",
                "http://www.example.test:8080/health?x=1",
            ]
        },
        reason="Probe authorized HTTP candidates",
    )
    values.update(changes)
    return ActionRequest(**values)


def execute(c, action=None, context=CONTEXT):
    return asyncio.run(
        c[0].execute(action or request(), policy=c[2], budgets=c[3], context=context)
    )


def wire(url="https://api.example.test/", **changes):
    from urllib.parse import urlsplit

    parts = urlsplit(url)
    values = dict(
        input=url,
        url=url,
        status_code=200,
        host=parts.hostname,
        host_ip="192.0.2.10",
        scheme=parts.scheme,
        port=str(parts.port or (443 if parts.scheme == "https" else 80)),
        failed=False,
        method="GET",
    )
    values.update(changes)
    return json.dumps(values).encode() + b"\n"


def test_registry_argv_metadata_redirect_and_provenance():
    c = compose()
    result = execute(c)
    assert isinstance(result, Success)
    output = result.value
    assert output.status == "completed"
    assert len(output.observations) == len(output.endpoints) == 2
    assert output.candidates == tuple(sorted(request().parameters["candidates"]))
    spec = c[1].calls[0]
    args = spec.args
    assert spec.executable == "/trusted/httpx"
    assert args[:4] == ("-config", os.devnull, "-auth", "false")
    expected = (
        "-silent",
        "-nc",
        "-duc",
        "-json",
        "-stream",
        "-t",
        "1",
        "-rl",
        "1",
        "-retries",
        "0",
        "-timeout",
        "10",
        "-no-fallback-scheme",
        "-x",
        "GET",
        "-cdn",
        "false",
        "-random-agent=false",
        "-status-code",
        "-title",
        "-server",
        "-content-type",
        "-content-length",
        "-location",
        "-tech-detect",
        "-ip",
        "-response-size-to-read",
        "65536",
        "-response-size-to-save",
        "65536",
        "-allow",
        "192.0.2.10,2001:db8::10",
        "-r",
        "udp:192.0.2.53:53",
        "-l",
    )
    assert args[4:-1] == expected
    assert c[1].inputs == ["".join(url + "\n" for url in output.candidates)]
    assert not Path(args[-1]).exists()
    assert spec.timeout_seconds <= c[0].config.default_timeout_seconds
    assert "-fr" not in args and "-fhr" not in args and "-tls-probe" not in args
    assert "-csp-probe" not in args and "-favicon" not in args
    catalog = c[2].registry.catalog()
    assert catalog[0].capability == CapabilityId.PROBE_HTTP
    assert isinstance(c[2].registry.resolve("probe_http"), Success)
    assert ToolRegistry().list_adapters() == ()
    data = next(o.data for o in output.observations if o.data["status_code"] == 302)
    assert data["final_url"] == "https://api.example.test/"
    assert data["host"] == "api.example.test" and data["port"] == 443
    assert data["title"] == "Example API" and data["server"] == "nginx"
    assert data["content_type"] == "text/html" and data["content_length"] == 123
    assert data["technologies"] == ["Example", "nginx"]
    assert data["redirect_target"] == "https://external.test/login"
    assert data["redirect_scope_status"] == "rejected"
    assert data["redirect_authorized"] is False and data["redirect_followed"] is False
    assert isinstance(
        c[2].scope_validator.validate_value(data["redirect_target"]), Failure
    )
    assert len(c[1].calls) == 1
    for obs, endpoint in zip(output.observations, output.endpoints, strict=True):
        assert obs.source == "httpx" and obs.data["capability"] == "probe_http"
        assert obs.data["source_version"] == "1.9.0"
        assert obs.asset_id == endpoint.asset_id == CONTEXT.asset_id
        assert obs.execution_id == CONTEXT.execution_id and obs.observed_at == WHEN
        assert endpoint.url == obs.data["url"] and endpoint.method == "GET"
        assert endpoint.observation_ids == (obs.id,)
        assert obs.evidence_ids == (output.evidence[0].id,)
    evidence = output.evidence[0]
    assert evidence.source == "httpx" and evidence.capability == "probe_http"
    assert (
        evidence.trust == "untrusted" and evidence.execution_id == CONTEXT.execution_id
    )
    assert evidence.sha256 and len(evidence.sha256) == 64
    assert output == HttpProbeOutput.model_validate_json(output.model_dump_json())


@pytest.mark.parametrize(
    ("target", "url", "address"),
    [
        ("API.EXAMPLE.TEST.", "https://api.example.test/", "192.0.2.10"),
        ("192.0.2.10", "https://192.0.2.10/", "192.0.2.10"),
        ("2001:db8::10", "https://[2001:db8::10]/", "2001:db8::10"),
        ("https://api.example.test:443", "https://api.example.test/", "192.0.2.10"),
        (
            "http://api.example.test:80/health?a=b",
            "http://api.example.test/health?a=b",
            "192.0.2.10",
        ),
        (
            "https://api.example.test:8443/health",
            "https://api.example.test:8443/health",
            "192.0.2.10",
        ),
    ],
)
def test_primary_hostname_ip_url(target, url, address):
    c = compose(FakeRunner(process(wire(url, host_ip=address))))
    result = execute(c, request(candidates=[], target=target))
    assert isinstance(result, Success)
    assert result.value.status == "completed"
    assert result.value.endpoints[0].url == url
    assert c[1].inputs == [url + "\n"]


@pytest.mark.parametrize(
    "candidates",
    [
        ["external.test"],
        ["api.example.test", "external.test"],
        ["external.test", "api.example.test"],
        ["api.example.test", "192.0.2.11"],
        ["https://external.test/"],
        ["https://api.example.test/", "https://external.test/"],
    ],
)
def test_rejected_batch_never_reaches_input_or_runner(candidates, monkeypatch):
    create = Mock(side_effect=AssertionError("rejected input written"))
    monkeypatch.setattr("recon_agent.tools.httpx.TemporaryDirectory", create)
    c = compose()
    result = execute(c, request(candidates=candidates))
    assert isinstance(result, Failure) and result.error.code == ErrorCode.SCOPE_REJECTED
    assert c[1].calls == c[1].inputs == []
    create.assert_not_called()
    assert c[3].state.permitted_actions == 0


@pytest.mark.parametrize(
    "target",
    [
        "external.test",
        "https://user:pass@api.example.test/",
        "-fr",
        "api.example.test;id",
        "https://api.example.test\\evil/",
        "https://api.example.test/a,b",
        "https://api.example.test/#fragment",
        "192.0.2.0/24",
    ],
)
def test_bad_target_never_contacts(target):
    c = compose()
    result = execute(c, request(candidates=[], target=target))
    assert isinstance(result, Failure)
    assert c[1].calls == []


@pytest.mark.parametrize(
    "field",
    [
        "extra_args",
        "flags",
        "argv",
        "executable",
        "shell",
        "proxy",
        "headers",
        "follow_redirects",
        "follow_host_redirects",
        "method",
        "files",
        "ports",
        "resolver",
    ],
)
def test_planner_cannot_inject_execution_fields(field):
    c = compose()
    try:
        action = request(parameters={"candidates": ["api.example.test"], field: "-fr"})
    except ValidationError:
        return
    result = execute(c, action)
    assert (
        isinstance(result, Failure)
        and result.error.code == ErrorCode.PLANNER_VALIDATION_FAILED
    )
    assert c[1].calls == []


@pytest.mark.parametrize(
    "location,expected,status",
    [
        ("/login", "https://api.example.test/login", "allowed"),
        ("//external.test/login", "https://external.test/login", "rejected"),
        ("https://www.example.test/", "https://www.example.test/", "allowed"),
        ("javascript:alert(1)", "javascript:alert(1)", "rejected"),
    ],
)
def test_redirects_remain_evidence(location, expected, status):
    c = compose(FakeRunner(process(wire(location=location, status_code=302))))
    result = execute(c, request(candidates=["api.example.test"]))
    assert isinstance(result, Success)
    data = result.value.observations[0].data
    assert (
        data["redirect_target"] == expected and data["redirect_scope_status"] == status
    )
    assert data["redirect_authorized"] is False
    assert len(c[1].calls) == 1 and len(result.value.endpoints) == 1


def test_technology_is_untrusted_observation_only_and_absent_metadata_stays_absent():
    c = compose(FakeRunner(process(wire(tech=["WordPress", "WordPress", "PHP"]))))
    result = execute(c, request(candidates=["api.example.test"]))
    assert isinstance(result, Success)
    data = result.value.observations[0].data
    assert data["technologies"] == ["PHP", "WordPress"]
    assert (
        not {"title", "server", "content_type", "content_length", "redirect_target"}
        & data.keys()
    )
    assert len(c[1].calls) == 1


def test_duplicate_order_and_hash_are_deterministic():
    a = execute(compose(FakeRunner(process(FIXTURE))))
    b = execute(
        compose(
            FakeRunner(
                process(b"\n".join(reversed(FIXTURE.splitlines())) + b"\n" + FIXTURE)
            )
        )
    )
    assert isinstance(a, Success) and isinstance(b, Success)
    assert a.value == b.value


@pytest.mark.parametrize(
    "raw",
    [
        b"bad\n",
        b"[]\n",
        b"null\n",
        b"{}\n",
        b"\xff\n",
        b'{"url":"x","url":"y"}\n',
        wire(status_code=0),
        wire(status_code=True),
        wire(status_code="200"),
        wire(host_ip="192.0.2.11"),
        wire(host_ip="external.test"),
        wire(host="external.test"),
        wire(scheme="http"),
        wire(port="80"),
        wire(failed=True),
        wire(method="POST"),
        wire(url="https://external.test/"),
        wire(input="https://www.example.test/"),
        wire(final_url="https://external.test/"),
        wire(final_url="https://www.example.test/"),
        wire(chain_status_codes=[302, 200]),
        wire(chain=[{}]),
        wire(title="x" * 4097),
        wire(tech=["x"] * 65),
        wire(content_length=-1),
        wire(content_length=True),
        wire(location="x" * 2049),
    ],
)
def test_malformed_output_uses_parser_failure(raw):
    c = compose(FakeRunner(process(raw)))
    result = execute(c, request(candidates=["api.example.test"]))
    assert isinstance(result, Failure) and result.error.code == ErrorCode.PARSE_FAILED
    assert c[3].state.active_executions == 0


def test_partial_preserves_valid_records_and_empty_invents_no_live_endpoint():
    c = compose(FakeRunner(process(wire() + b"invalid\n")))
    result = execute(c)
    assert isinstance(result, Success)
    assert result.value.status == "partial" and result.value.malformed_lines == 1
    assert len(result.value.observations) == 1
    assert result.value.unreported_candidates == (
        "http://www.example.test:8080/health?x=1",
    )
    assert result.value.errors[0].code == ErrorCode.PARSE_FAILED
    empty = execute(compose(FakeRunner(process(b" \n\n"))))
    assert isinstance(empty, Success) and empty.value.status == "partial"
    assert empty.value.observations == empty.value.endpoints == ()
    assert (
        len(empty.value.evidence) == 1
        and empty.value.unreported_candidates == empty.value.candidates
    )


def test_conflicting_duplicates_discard_url_independent_of_order():
    from itertools import permutations

    raw = [
        wire(),
        wire(title="conflict"),
        wire(),
        wire("http://www.example.test:8080/health?x=1"),
    ]
    hashes = set()
    for perm in permutations(raw):
        result = execute(compose(FakeRunner(process(b"".join(perm)))))
        assert isinstance(result, Success) and result.value.status == "partial"
        assert result.value.malformed_lines == 3 and len(result.value.endpoints) == 1
        hashes.add(result.value.evidence[0].sha256)
    assert len(hashes) == 1


@pytest.mark.parametrize(
    "result,code",
    [
        (
            Failure(error=ToolUnavailableError("missing").to_error_info()),
            ErrorCode.TOOL_UNAVAILABLE,
        ),
        (
            Failure(error=ToolTimeoutError("timeout").to_error_info()),
            ErrorCode.TOOL_TIMEOUT,
        ),
        (process(return_code=7), ErrorCode.TOOL_EXECUTION_FAILED),
        (process(stdout_truncated=True), ErrorCode.PARSE_FAILED),
        (process(stderr_truncated=True), ErrorCode.PARSE_FAILED),
        (process(stderr=b"x" * 1048577), ErrorCode.PARSE_FAILED),
        (process(stdout=b"x" * 1048577), ErrorCode.PARSE_FAILED),
    ],
)
def test_canonical_runner_failures_and_bounds(result, code):
    c = compose(FakeRunner(result))
    out = execute(c)
    assert isinstance(out, Failure) and out.error.code == code
    if code == ErrorCode.TOOL_EXECUTION_FAILED:
        assert out.error.context.exit_code == 7
    assert c[3].state.active_executions == 0 and c[3].state.permitted_actions == 1


def test_cancellation_releases_budget_and_temp_input():
    class CancelRunner(FakeRunner):
        async def run(self, spec):
            await super().run(spec)
            raise asyncio.CancelledError

    c = compose(CancelRunner())
    with pytest.raises(asyncio.CancelledError):
        execute(c)
    assert c[3].state.active_executions == 0 and c[3].state.permitted_actions == 1
    assert not Path(c[1].calls[0].args[-1]).exists()


@pytest.mark.parametrize("omitted", ["resolver", "address", "address6"])
def test_infrastructure_and_every_allowed_address_need_independent_scope(omitted):
    scope = Scope(
        id="scope",
        allow_subdomains=True,
        roots=tuple(
            t for t in compose()[2].scope_validator.scope.roots if t.id != omitted
        ),
    )
    c = compose(scope=scope)
    result = execute(c)
    assert isinstance(result, Failure) and result.error.code == ErrorCode.SCOPE_REJECTED
    assert c[1].calls == []


@pytest.mark.parametrize(
    "version", ["1.9.0", "1.7.1", "1.9.1", "", "1.9.0\nCurrent Version: 1.9.0"]
)
def test_availability_reviewed_version_only(version, monkeypatch):
    monkeypatch.setattr(
        "recon_agent.tools.httpx.shutil.which", lambda _: "/trusted/httpx"
    )
    runner = FakeRunner(
        process(b"", stderr=f"[INF] Current Version: {version}\n".encode())
    )
    result = asyncio.run(
        HttpxAdapter.detect(
            ExecutionConfig(),
            nameserver="192.0.2.53",
            contact_addresses=("192.0.2.10",),
            runner=runner,
        )
    )
    assert isinstance(result, Success if version == "1.9.0" else Failure)
    assert runner.inputs == [] and "-version" in runner.calls[0].args
    assert not Path(dict(runner.calls[0].environment)["HOME"]).exists()


def test_missing_binary_no_install_or_process(monkeypatch):
    monkeypatch.setattr("recon_agent.tools.httpx.shutil.which", lambda _: None)
    fake = FakeRunner()
    result = asyncio.run(
        HttpxAdapter.detect(
            ExecutionConfig(),
            nameserver="192.0.2.53",
            contact_addresses=("192.0.2.10",),
            runner=fake,
        )
    )
    assert (
        isinstance(result, Failure) and result.error.code == ErrorCode.TOOL_UNAVAILABLE
    )
    assert fake.calls == []


@pytest.mark.parametrize(
    "changes",
    [
        {"executable": "httpx"},
        {"nameserver": "resolver.test"},
        {"nameserver": "2001:db8::53"},
        {"contact_addresses": ()},
        {"contact_addresses": ("external.test",)},
        {"contact_addresses": ("192.0.2.10",) * 65},
        {"contact_addresses": ["192.0.2.10"]},
    ],
)
def test_trusted_settings_are_validated(changes):
    values = dict(
        executable="/trusted/httpx",
        nameserver="192.0.2.53",
        contact_addresses=("192.0.2.10",),
        config=ExecutionConfig(),
        runner=FakeRunner(),
    )
    values.update(changes)
    with pytest.raises(ConfigurationError):
        HttpxAdapter(**values)


def test_unavailable_wrong_binding_and_bad_context_deny():
    from dataclasses import replace

    c = compose(availability=AdapterAvailability.UNAVAILABLE)
    assert execute(c).error.code == ErrorCode.TOOL_UNAVAILABLE and not c[1].calls
    c = compose()
    result = asyncio.run(
        replace(c[0]).execute(request(), policy=c[2], budgets=c[3], context=CONTEXT)
    )
    assert result.error.code == ErrorCode.PLANNER_VALIDATION_FAILED and not c[1].calls
    assert (
        execute(c, context=CONTEXT.model_copy(update={"asset_id": ""})).error.code
        == ErrorCode.PLANNER_VALIDATION_FAILED
    )
    assert (
        execute(c, request(asset_id="other")).error.code
        == ErrorCode.PLANNER_VALIDATION_FAILED
    )
    assert (
        execute(c, request(capability="discover_ports")).error.code
        == ErrorCode.PLANNER_VALIDATION_FAILED
    )
    assert not c[1].calls


def test_shared_host_rate_and_action_limits_precede_execution():
    for limits in (
        ExecutionBudget(max_actions_per_host=1),
        ExecutionBudget(capability_rate_actions=1),
        ExecutionBudget(max_actions=1),
    ):
        c = compose(limits=limits)
        assert isinstance(execute(c), Success)
        assert execute(c, request(id="second")).error.code == ErrorCode.BUDGET_EXHAUSTED
        assert len(c[1].calls) == 1
        assert {
            "example.test",
            "api.example.test",
            "www.example.test",
            "192.0.2.10",
            "2001:db8::10",
            "192.0.2.53",
        } == dict(c[3].state.host_actions).keys()


def test_session_expiry_during_runner_discards_facts():
    now = [0.0]
    c = compose(
        FakeRunner(mutate=lambda: now.__setitem__(0, 10000.0)), clock=lambda: now[0]
    )
    assert execute(c).error.code == ErrorCode.TOOL_TIMEOUT
    assert c[3].state.active_executions == 0


@pytest.mark.parametrize(
    "parameters",
    [
        {"candidates": ["api.example.test"] * 65},
        {"candidates": "api.example.test"},
        {"candidates": [1]},
        {"candidates": [""]},
        {"candidates": ["a" * 2049]},
    ],
)
def test_typed_input_bounds(parameters):
    c = compose()
    assert isinstance(execute(c, request(parameters=parameters)), Failure)
    assert c[1].calls == []


def test_canonical_duplicates_in_input_contact_once():
    c = compose(FakeRunner(process(wire())))
    output = execute(
        c,
        request(
            candidates=[
                "API.EXAMPLE.TEST.",
                "https://api.example.test:443",
                "api.example.test",
            ]
        ),
    )
    assert isinstance(output, Success) and output.value.status == "completed"
    assert c[1].inputs == ["https://api.example.test/\n"]


@pytest.mark.parametrize("raw", [wire() * 257, b" " * 65537 + b"{}\n"])
def test_parser_line_bounds(raw):
    c = compose(FakeRunner(process(raw)))
    assert execute(c).error.code == ErrorCode.PARSE_FAILED


def test_normalized_output_bound():
    raw = wire()
    # Captured bytes fit, but the provenance-rich envelope exceeds this allowance.
    c = compose(FakeRunner(process(raw)), config=ExecutionConfig(max_output_bytes=1024))
    assert len(raw) < 1024
    assert (
        execute(c, request(candidates=["api.example.test"])).error.code
        == ErrorCode.PARSE_FAILED
    )


def test_scoped_numeric_candidate_must_also_be_in_contact_set():
    original = compose()[2].scope_validator.scope
    scope = original.model_copy(
        update={
            "roots": (
                *original.roots,
                Target(id="extra", kind="ip", value="192.0.2.11"),
            )
        }
    )
    c = compose(scope=scope)
    result = execute(c, request(candidates=["192.0.2.11"]))
    assert result.error.code == ErrorCode.PLANNER_VALIDATION_FAILED and c[1].calls == []


def test_excluded_contact_address_is_rejected_even_with_allowed_name():
    original = compose()[2].scope_validator.scope
    scope = original.model_copy(
        update={"exclusions": (Target(id="exclude", kind="ip", value="192.0.2.10"),)}
    )
    c = compose(scope=scope)
    assert execute(c).error.code == ErrorCode.SCOPE_REJECTED and c[1].calls == []


def test_temp_setup_failure_is_canonical(monkeypatch):
    monkeypatch.setattr(
        "recon_agent.tools.httpx.TemporaryDirectory", Mock(side_effect=OSError("local"))
    )
    c = compose()
    assert execute(c).error.code == ErrorCode.TOOL_EXECUTION_FAILED
    assert c[1].calls == [] and c[3].state.active_executions == 0


@pytest.mark.parametrize(
    "result,code",
    [
        (process(b"\xff"), ErrorCode.TOOL_UNAVAILABLE),
        (
            Failure(error=ToolTimeoutError("timeout").to_error_info()),
            ErrorCode.TOOL_TIMEOUT,
        ),
        (process(return_code=7), ErrorCode.TOOL_EXECUTION_FAILED),
    ],
)
def test_availability_failure_contract(result, code, monkeypatch):
    monkeypatch.setattr(
        "recon_agent.tools.httpx.shutil.which", lambda _: "/trusted/httpx"
    )
    result = asyncio.run(
        HttpxAdapter.detect(
            ExecutionConfig(),
            nameserver="192.0.2.53",
            contact_addresses=("192.0.2.10",),
            runner=FakeRunner(result),
        )
    )
    assert isinstance(result, Failure) and result.error.code == code


@pytest.mark.parametrize(
    "target", ["https://API.EXAMPLE.test", "HTTPS://api.example.test:00443/"]
)
def test_shared_web_identity_denies_equivalent_primary_and_candidates(target):
    c = compose()
    first = request(
        target="https://api.example.test/", candidates=["https://api.example.test/"]
    )
    assert isinstance(c[4].record_action_requested(first, recorded_at=WHEN), Success)
    calls = len(c[1].calls)
    budget = c[3].state
    repeated = request(id="equivalent", target=target, candidates=[target])
    denied = c[2].validate(repeated)
    assert isinstance(denied, Failure)
    assert (
        denied.error.message == "Equivalent action is not eligible for another attempt"
    )
    outcome = execute(c, repeated)
    assert isinstance(outcome, Failure)
    assert outcome.error.code == ErrorCode.PLANNER_VALIDATION_FAILED
    assert len(c[1].calls) == calls
    assert replace(c[3].state, remaining_seconds=budget.remaining_seconds) == budget

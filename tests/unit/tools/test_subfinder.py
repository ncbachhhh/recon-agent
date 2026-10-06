"""Offline operational Subfinder tests. No real binary/provider contact."""

import asyncio
import json
import os
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
from recon_agent.core.errors import (
    ConfigurationError,
    ErrorCode,
    ToolExecutionError,
    ToolTimeoutError,
    ToolUnavailableError,
)
from recon_agent.core.results import Failure, Success
from recon_agent.domain import ActionRequest, ReconStateMachine, Scope, Target
from recon_agent.domain.budgets import ReservationOutcome
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
from recon_agent.tools.subfinder import SubfinderAdapter
from recon_agent.tools.subfinder_models import (
    SubdomainOutput,
    SubfinderContext,
    SubfinderInput,
)

WHEN = datetime(2026, 10, 6, tzinfo=UTC)
CONTEXT = SubfinderContext(
    asset_id="asset", execution_id="execution", collected_at=WHEN
)
FIXTURE = (
    Path(__file__).parents[2] / "fixtures/subfinder/discovery.jsonl"
).read_bytes()


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


def process(stdout=FIXTURE, stderr=b"", **changes):
    values = dict(
        argument_count=23,
        return_code=0,
        stdout=stdout,
        stderr=stderr,
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
        self.mutate = mutate
        self.directory = None

    async def run(self, spec):
        self.calls.append(spec)
        env = dict(spec.environment)
        self.directory = Path(env["HOME"])
        assert self.directory.is_dir()
        assert all(
            env[key] == str(self.directory)
            for key in (
                "HOME",
                "XDG_CONFIG_HOME",
                "APPDATA",
                "LOCALAPPDATA",
                "USERPROFILE",
            )
        )
        assert not any(
            key in env
            for key in (
                "GROQ_API_KEY",
                "HTTP_PROXY",
                "HTTPS_PROXY",
                "SUBFINDER_CONFIG",
                "SUBFINDER_PROVIDER_CONFIG",
            )
        )
        if self.mutate:
            self.mutate()
        return self.result


def compose(
    fake=None,
    config=None,
    scope=None,
    availability=AdapterAvailability.AVAILABLE,
    clock=None,
    limits=None,
):
    config = config or ExecutionConfig()
    fake = fake or FakeRunner()
    adapter = SubfinderAdapter("/trusted/subfinder", config, fake)
    registry = ToolRegistry((AdapterRegistration(adapter, availability),))
    validator = ScopeValidator(
        scope
        or Scope(
            id="scope", roots=(Target(id="root", kind="domain", value="example.test"),)
        )
    )
    budgets = BudgetController(
        limits or ExecutionBudget.from_config(config),
        registry,
        **({"clock": clock} if clock else {}),
    )
    state = ReconStateMachine()
    dedup = ActionDeduplicator(ActionCanonicalizer(registry, validator), state)
    policy = ActionPolicyValidator(
        registry,
        validator,
        ActionPolicyConfig(
            allowed_capabilities=frozenset({CapabilityId.ENUMERATE_SUBDOMAINS}),
            allowed_risk_classes=frozenset({RiskClass.PASSIVE}),
        ),
        budgets,
        dedup,
    )
    return adapter, fake, policy, budgets, state


def request(**changes):
    values = dict(
        id="action",
        capability="enumerate_subdomains",
        target="EXAMPLE.TEST.",
        parameters={},
        reason="Collect passive evidence",
    )
    values.update(changes)
    return ActionRequest(**values)


def execute(c, action=None, context=CONTEXT):
    return asyncio.run(
        c[0].execute(action or request(), policy=c[2], budgets=c[3], context=context)
    )


def wire(host="api.example.test", root="example.test", **changes):
    values = dict(host=host, input=root, sources=["hackertarget"])
    values.update(changes)
    return json.dumps(values).encode() + b"\n"


def test_fixture_normalization_provenance_and_no_followup_authority():
    scope = Scope(
        id="scope",
        roots=(Target(id="root", kind="domain", value="example.test"),),
        exclusions=(
            Target(id="excluded", kind="hostname", value="excluded.example.test"),
        ),
    )
    c = compose(scope=scope)
    result = execute(c)
    assert isinstance(result, Success)
    output = result.value
    assert output.hosts == (
        "api.example.test",
        "excluded.example.test",
        "www.example.test",
    )
    assert output.source_version == "2.9.0"
    assert (
        output.query_target == "example.test" and output.asset.value == "example.test"
    )
    assert len(output.observations) == 3
    for item in output.observations:
        assert item.kind == "metadata" and item.source == "subfinder"
        assert item.asset_id == "asset" and item.execution_id == "execution"
        assert item.observed_at == WHEN and item.evidence_ids == (
            output.evidence[0].id,
        )
        assert item.data["status"] == "discovered"
        assert item.data["capability"] == "enumerate_subdomains"
        assert item.data["provider_sources"] == ["hackertarget"]
        assert "authorized" not in item.data
        assert isinstance(
            c[2].scope_validator.validate_value(item.data["hostname"]), Failure
        )
    evidence = output.evidence[0]
    assert (
        evidence.source == "subfinder" and evidence.capability == "enumerate_subdomains"
    )
    assert evidence.trust == "untrusted" and evidence.origin == "example.test"
    assert evidence.collected_at == WHEN and evidence.execution_id == "execution"
    assert (
        evidence.artifact_reference == "memory:execution"
        and evidence.locator == "discovery"
    )
    snapshot = json.dumps(
        {
            "query_target": output.query_target,
            "source_version": output.source_version,
            "provider_sources": list(output.provider_sources),
            "hosts": list(output.hosts),
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    assert evidence.sha256 == sha256(snapshot.encode()).hexdigest()
    assert SubdomainOutput.model_validate_json(output.model_dump_json()) == output
    assert c[2].scope_validator.scope == scope
    assert len(c[1].calls) == 1
    c[1].calls.clear()
    denied = execute(c, request(target="api.example.test"))
    assert isinstance(denied, Failure) and denied.error.code == ErrorCode.SCOPE_REJECTED
    assert c[1].calls == []


def test_trusted_argv_is_fixed_and_environment_is_isolated(monkeypatch):
    for key in (
        "SUBFINDER_CONFIG",
        "SUBFINDER_PROVIDER_CONFIG",
        "HTTPS_PROXY",
        "GROQ_API_KEY",
    ):
        monkeypatch.setenv(key, "private-fixture-value")
    c = compose()
    assert isinstance(execute(c), Success)
    spec = c[1].calls[0]
    assert spec.executable == "/trusted/subfinder"
    assert spec.args == (
        "-config",
        os.devnull,
        "-pc",
        os.devnull,
        "-silent",
        "-nc",
        "-duc",
        "-json",
        "-cs",
        "-s",
        "hackertarget",
        "-rl",
        "1",
        "-rls",
        "hackertarget=1/s",
        "-t",
        "1",
        "-timeout",
        "10",
        "-max-time",
        "1",
        "-d",
        "example.test",
    )
    assert 0 < spec.timeout_seconds <= 30
    assert not c[1].directory.exists()
    assert "private-fixture-value" not in repr(spec)
    assert not {"environment", "executable", "args", "runner"}.intersection(
        c[2].registry.catalog()[0].model_dump()
    )
    assert c[3].state.permitted_actions == 1 and c[3].state.active_executions == 0
    assert dict(c[3].state.outcomes) == {ReservationOutcome.COMPLETED: 1}


@pytest.mark.parametrize(
    "raw, expected",
    [
        (b"", ()),
        (b"\n \t\n", ()),
        (wire(), ("api.example.test",)),
        (
            wire() + wire("WWW.EXAMPLE.TEST.") + wire(),
            ("api.example.test", "www.example.test"),
        ),
    ],
)
def test_single_multiple_duplicates_and_empty(raw, expected):
    c = compose(FakeRunner(process(stdout=raw)))
    output = execute(c).value
    assert output.hosts == expected
    assert len(output.observations) == len(expected)
    assert len(output.evidence) == 1


def test_output_order_is_deterministic():
    lines = FIXTURE.splitlines(keepends=True)
    assert (
        execute(compose()).value
        == execute(compose(FakeRunner(process(stdout=b"".join(reversed(lines)))))).value
    )


@pytest.mark.parametrize(
    "raw",
    [
        b"decorative banner",
        b"{",
        b"null",
        b"[]",
        b"\xff",
        b'{"host":"api.example.test","host":"www.example.test","input":"example.test","sources":["hackertarget"]}',
        wire("outside.test"),
        wire("badexample.test"),
        wire("example.test"),
        wire(root="outside.test"),
        wire(host="https://api.example.test"),
        wire(host="*.example.test"),
        wire(host="api..example.test"),
        wire(host="-bad.example.test"),
        wire(host="a_b.example.test"),
        wire(host="xn--foo.example.test"),
        wire(host="é.example.test"),
        wire(host="api.example.test.."),
        wire(host="api.example.test;touch sentinel"),
        wire(host="$(touch sentinel).example.test"),
        wire(host="api.example.test", sources=["crtsh"]),
        wire(sources=[]),
        wire(sources=["hackertarget", "hackertarget"]),
        wire(source="hackertarget"),
        wire(ip="192.0.2.1"),
        b'{"host":1,"input":"example.test","sources":["hackertarget"]}',
        wire() + b"malformed",
        b"\n" * 4097,
        b" " * 2049 + wire(),
    ],
)
def test_malformed_output_fails_closed_without_remote_diagnostics(raw):
    c = compose(FakeRunner(process(stdout=raw, stderr=b"private diagnostic")))
    outcome = execute(c)
    assert isinstance(outcome, Failure) and outcome.error.code == ErrorCode.PARSE_FAILED
    assert outcome.error.message == "Malformed or oversized Subfinder output"
    assert "private diagnostic" not in outcome.model_dump_json()
    assert not c[1].directory.exists() and c[3].state.active_executions == 0
    assert dict(c[3].state.outcomes) == {ReservationOutcome.FAILED: 1}


@pytest.mark.parametrize(
    "target",
    [
        "outside.test",
        "api.example.test",
        "example.test;touch sentinel",
        "$(touch sentinel)",
        "example.test -config private",
        "example.test|id",
        "example.test\n-d outside.test",
    ],
)
def test_rejected_root_never_runs(target):
    c = compose()
    result = execute(c, request(target=target))
    assert isinstance(result, Failure) and result.error.code == ErrorCode.SCOPE_REJECTED
    assert not c[1].calls and c[3].state.permitted_actions == 0


@pytest.mark.parametrize(
    "target, kind", [("192.0.2.1", "ip"), ("https://example.test/path", "url")]
)
def test_authorized_non_hostname_rejected(target, kind):
    c = compose(
        scope=Scope(id="scope", roots=(Target(id="root", kind=kind, value=target),))
    )
    assert (
        execute(c, request(target=target)).error.code
        == ErrorCode.PLANNER_VALIDATION_FAILED
    )
    assert not c[1].calls


@pytest.mark.parametrize(
    "name",
    [
        "flags",
        "extra_args",
        "config",
        "provider_config",
        "proxy",
        "resolvers",
        "shell",
        "command_string",
        "sources",
        "timeout_seconds",
        "root",
        "record_types",
    ],
)
def test_extra_planner_parameters_reject_before_dispatch(name):
    c = compose()
    result = execute(c, request(parameters={name: "-d outside.test;touch sentinel"}))
    assert result.error.code == ErrorCode.PLANNER_VALIDATION_FAILED
    assert not c[1].calls and c[3].state.permitted_actions == 0
    with pytest.raises(ValidationError):
        SubfinderInput.model_validate({name: "fixture"})


@pytest.mark.parametrize("key", ["executable", "argv", "command"])
def test_reserved_execution_parameters_fail_domain_boundary(key):
    with pytest.raises(ValidationError):
        request(parameters={key: "unsafe"})


@pytest.mark.parametrize(
    "error",
    [
        ToolTimeoutError("Fixed timeout"),
        ToolUnavailableError("Fixed missing"),
        ToolExecutionError("Fixed execution"),
    ],
)
def test_canonical_runner_failures_are_preserved(error):
    failure = Failure(error=error.to_error_info())
    c = compose(FakeRunner(failure))
    assert execute(c) == failure
    assert c[3].state.permitted_actions == 1 and c[3].state.active_executions == 0
    expected = (
        ReservationOutcome.TIMEOUT
        if isinstance(error, ToolTimeoutError)
        else ReservationOutcome.FAILED
    )
    assert dict(c[3].state.outcomes) == {expected: 1}


@pytest.mark.parametrize(
    "changes, code",
    [
        ({"return_code": 1}, ErrorCode.TOOL_EXECUTION_FAILED),
        ({"return_code": -9}, ErrorCode.TOOL_EXECUTION_FAILED),
        ({"stdout_truncated": True}, ErrorCode.PARSE_FAILED),
        ({"stderr_truncated": True}, ErrorCode.PARSE_FAILED),
        ({"stdout": b"a" * 1048577}, ErrorCode.PARSE_FAILED),
        ({"stderr": b"a" * 1048577}, ErrorCode.PARSE_FAILED),
    ],
)
def test_process_errors_truncation_and_bounds(changes, code):
    c = compose(FakeRunner(process(**changes)))
    result = execute(c)
    assert result.error.code == code
    if "return_code" in changes:
        assert result.error.context.exit_code == changes["return_code"]
    assert c[3].state.active_executions == 0


@pytest.mark.parametrize(
    "availability", [AdapterAvailability.UNAVAILABLE, AdapterAvailability.NOT_CHECKED]
)
def test_registry_unavailable_rejects(availability):
    c = compose(availability=availability)
    assert execute(c).error.code == ErrorCode.TOOL_UNAVAILABLE
    assert not c[1].calls


def test_stale_binding_and_context_and_budget_mismatch():
    c = compose()
    other = replace(c[0])
    assert (
        asyncio.run(
            other.execute(request(), policy=c[2], budgets=c[3], context=CONTEXT)
        ).error.code
        == ErrorCode.PLANNER_VALIDATION_FAILED
    )
    assert (
        execute(c, request(asset_id="another")).error.code
        == ErrorCode.PLANNER_VALIDATION_FAILED
    )
    assert (
        execute(
            c, context=CONTEXT.model_copy(update={"collected_at": "bad"})
        ).error.code
        == ErrorCode.PLANNER_VALIDATION_FAILED
    )
    different_budget = compose()[3]
    assert (
        asyncio.run(
            c[0].execute(
                request(), policy=c[2], budgets=different_budget, context=CONTEXT
            )
        ).error.code
        == ErrorCode.PLANNER_VALIDATION_FAILED
    )
    assert not c[1].calls


def test_config_snapshot_and_remaining_session_deadline():
    clock = [1.0]
    config = ExecutionConfig(default_timeout_seconds=20.0, max_duration_seconds=25.0)
    c = compose(config=config, clock=lambda: clock[0])
    config.default_timeout_seconds = 1.0
    clock[0] = 24.0
    assert isinstance(execute(c), Success)
    assert c[1].calls[0].timeout_seconds == 2.0


def test_session_expiry_after_runner():
    clock = [0.0]
    fake = FakeRunner(mutate=lambda: clock.__setitem__(0, 600.0))
    c = compose(fake, clock=lambda: clock[0])
    assert execute(c).error.code == ErrorCode.TOOL_TIMEOUT
    assert c[3].state.active_executions == 0


def test_output_and_host_count_bounds():
    c = compose(config=ExecutionConfig(max_output_bytes=100))
    assert execute(c).error.code == ErrorCode.PARSE_FAILED
    raw = b"".join(wire(f"h{i}.example.test") for i in range(1025))
    c = compose(FakeRunner(process(stdout=raw)))
    assert execute(c).error.code == ErrorCode.PARSE_FAILED


def test_normalized_output_bound():
    c = compose(
        FakeRunner(process(stdout=wire())), config=ExecutionConfig(max_output_bytes=200)
    )
    assert execute(c).error.code == ErrorCode.PARSE_FAILED


def test_cancelled_runner_cleans_temp_and_releases_permit():
    class Waiting(FakeRunner):
        async def run(self, spec):
            await super().run(spec)
            entered.set()
            await asyncio.Event().wait()

    async def check():
        nonlocal entered
        entered = asyncio.Event()
        c = compose(Waiting())
        task = asyncio.create_task(
            c[0].execute(request(), policy=c[2], budgets=c[3], context=CONTEXT)
        )
        await entered.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert c[3].state.active_executions == 0
        assert dict(c[3].state.outcomes) == {ReservationOutcome.CANCELLED: 1}
        assert not c[1].directory.exists()

    entered = None
    asyncio.run(check())


@pytest.mark.parametrize(
    "stdout, stderr",
    [
        (b"[INF] Current Version: v2.9.0\n", b""),
        (
            b"",
            b"[INF] Current Version: 2.9.0\n[INF] Subfinder Config Directory: /private/path",
        ),
    ],
)
def test_detect_binary_and_supported_version(monkeypatch, stdout, stderr):
    which = Mock(return_value="/trusted/subfinder")
    monkeypatch.setattr("recon_agent.tools.subfinder.shutil.which", which)
    fake = FakeRunner(process(stdout=stdout, stderr=stderr))
    result = asyncio.run(SubfinderAdapter.detect(ExecutionConfig(), runner=fake))
    assert isinstance(result, Success)
    which.assert_called_once_with("subfinder")
    spec = fake.calls[0]
    assert spec.args == (
        "-config",
        os.devnull,
        "-pc",
        os.devnull,
        "-version",
        "-nc",
        "-duc",
    )
    assert spec.timeout_seconds == 5.0
    assert "-d" not in spec.args and not fake.directory.exists()
    registry = ToolRegistry(
        (AdapterRegistration(result.value, AdapterAvailability.AVAILABLE),)
    )
    assert registry.resolve("enumerate_subdomains").value is result.value
    assert registry.catalog()[0].capability == CapabilityId.ENUMERATE_SUBDOMAINS


def test_missing_binary_never_probes(monkeypatch):
    monkeypatch.setattr("recon_agent.tools.subfinder.shutil.which", lambda binary: None)
    fake = FakeRunner()
    result = asyncio.run(
        SubfinderAdapter.detect(
            ExecutionConfig(), binary="/missing/subfinder", runner=fake
        )
    )
    assert result.error.code == ErrorCode.TOOL_UNAVAILABLE and not fake.calls


@pytest.mark.parametrize(
    "raw",
    [
        b"",
        b"2.9.0",
        b"Current Version: v2.8.0",
        b"Current Version: v2.10.0",
        b"Current Version: v2.9.0\nCurrent Version: v2.9.0",
        b"\xff",
    ],
)
def test_unknown_version_is_unavailable(monkeypatch, raw):
    monkeypatch.setattr(
        "recon_agent.tools.subfinder.shutil.which", lambda binary: "/trusted/subfinder"
    )
    fake = FakeRunner(process(stdout=raw))
    assert (
        asyncio.run(SubfinderAdapter.detect(ExecutionConfig(), runner=fake)).error.code
        == ErrorCode.TOOL_UNAVAILABLE
    )
    assert not fake.directory.exists()


@pytest.mark.parametrize(
    "error",
    [
        ToolUnavailableError("Fixed missing"),
        ToolTimeoutError("Fixed timeout"),
        ToolExecutionError("Fixed failure"),
    ],
)
def test_version_probe_failure_preserved(monkeypatch, error):
    monkeypatch.setattr(
        "recon_agent.tools.subfinder.shutil.which", lambda binary: "/trusted/subfinder"
    )
    failure = Failure(error=error.to_error_info())
    assert (
        asyncio.run(
            SubfinderAdapter.detect(ExecutionConfig(), runner=FakeRunner(failure))
        )
        == failure
    )


@pytest.mark.parametrize("binary", ["", " ", "bad\x00path", 2])
def test_invalid_operator_binary_setting(binary):
    with pytest.raises(ConfigurationError):
        asyncio.run(SubfinderAdapter.detect(ExecutionConfig(), binary=binary))


def test_invalid_settings_default_runner_and_inert_construction():
    with pytest.raises(ConfigurationError):
        SubfinderAdapter("relative-path", ExecutionConfig())
    with pytest.raises(ConfigurationError):
        SubfinderAdapter(
            "/trusted/subfinder",
            ExecutionConfig.model_construct(default_timeout_seconds=-1),
        )
    adapter = SubfinderAdapter("/trusted/subfinder", ExecutionConfig())
    assert adapter.runner is not None and ToolRegistry().catalog() == ()


def test_budget_stream_limit_mismatch_rejects_before_capture():
    c = compose(limits=ExecutionBudget(max_output_bytes=100))
    assert execute(c).error.code == ErrorCode.PLANNER_VALIDATION_FAILED
    assert not c[1].calls and c[3].state.permitted_actions == 0


def test_exhausted_budget_and_disabled_policy_do_not_dispatch():
    c = compose(config=ExecutionConfig(max_actions=1))
    assert isinstance(execute(c), Success)
    c[1].calls.clear()
    assert execute(c, request(id="next")).error.code == ErrorCode.BUDGET_EXHAUSTED
    assert not c[1].calls
    c = compose()
    policy = replace(c[2], config=ActionPolicyConfig())
    assert (
        asyncio.run(
            c[0].execute(request(), policy=policy, budgets=c[3], context=CONTEXT)
        ).error.code
        == ErrorCode.PLANNER_VALIDATION_FAILED
    )
    assert not c[1].calls


@pytest.mark.parametrize(
    "raw",
    [
        b"Current Version: v2.9.0-dev",
        b"Current Version: v2.9.0.1",
        b"Current Version: v2.9.0+modified",
    ],
)
def test_unreviewed_version_suffixes_reject(monkeypatch, raw):
    monkeypatch.setattr(
        "recon_agent.tools.subfinder.shutil.which", lambda binary: "/trusted/subfinder"
    )
    assert (
        asyncio.run(
            SubfinderAdapter.detect(
                ExecutionConfig(), runner=FakeRunner(process(stdout=raw))
            )
        ).error.code
        == ErrorCode.TOOL_UNAVAILABLE
    )

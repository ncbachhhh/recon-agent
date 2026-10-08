"""Offline Feroxbuster finite path discovery and contact regressions."""

import asyncio
import json
import socket
import subprocess
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import Mock
from urllib.parse import urlsplit

import pytest
from pydantic import ValidationError

from recon_agent.core.config.models import ExecutionConfig
from recon_agent.core.errors import ErrorCode, ToolTimeoutError, ToolUnavailableError
from recon_agent.core.results import Failure, Success
from recon_agent.domain import (
    ActionRequest,
    ActionResult,
    ReconStateMachine,
    Scope,
    Target,
)
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
from recon_agent.tools.feroxbuster import _FLAGS, FeroxbusterAdapter
from recon_agent.tools.feroxbuster_models import (
    WORDS,
    FeroxbusterContext,
    FeroxbusterInput,
    FeroxbusterSettings,
)
from recon_agent.tools.feroxbuster_parser import parse

WHEN = datetime(2026, 10, 7, tzinfo=UTC)
ROOT = "http://192.0.2.10/"
CONTEXT = FeroxbusterContext(
    asset_id="asset", execution_id="execution", collected_at=WHEN
)
FIXTURE = (
    Path(__file__).parents[2] / "fixtures/feroxbuster/discovery.jsonl"
).read_bytes()


@pytest.fixture(autouse=True)
def no_contact(monkeypatch):
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
    yield
    blocked.assert_not_called()


@pytest.fixture(autouse=True)
def isolated_operator_filesystem(monkeypatch):
    # Host scanner configuration is irrelevant to deterministic fake compatibility.
    original = Path.lstat

    def stat(path, *args, **kwargs):
        if str(path) == "/etc/feroxbuster/ferox-config.toml":
            raise FileNotFoundError
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "lstat", stat)


@pytest.fixture(autouse=True)
def fast_pacing(monkeypatch):
    async def sleep(_):
        pass

    monkeypatch.setattr("recon_agent.tools.feroxbuster.asyncio.sleep", sleep)


def process(raw=FIXTURE, **changes):
    values = dict(
        argument_count=30,
        return_code=0,
        stdout=raw,
        stderr=b"",
        stdout_truncated=False,
        stderr_truncated=False,
        started_at=WHEN,
        finished_at=WHEN,
        duration_seconds=0.0,
    )
    values.update(changes)
    return Success(value=ProcessExecution(**values))


def record(page, input_url, status=200, **changes):
    values = dict(
        type="response",
        url=input_url,
        original_url=page,
        path=urlsplit(input_url).path,
        wildcard=False,
        status=status,
        method="GET",
        content_length=123,
        line_count=1,
        word_count=2,
        headers={},
        extension="",
        truncated=False,
        timestamp=0,
    )
    values.update(changes)
    return json.dumps(values).encode() + b"\n"


def page_output(page, directory=False):
    return record(page, page) + b"".join(
        record(page, page + word, 200 if directory and word == "admin/" else 404)
        for word in WORDS
    )


class FakeRunner:
    def __init__(self, output=None):
        self.output = output
        self.calls = []
        self.version = b"feroxbuster 2.13.1\n"
        self.mutate = None

    async def run(self, spec):
        env = dict(spec.environment)
        assert Path(env["HOME"]).is_dir()
        assert spec.working_directory == env["HOME"]
        assert all(v == env["HOME"] for k, v in env.items() if k != "SystemRoot")
        if "--version" in spec.args:
            assert spec.args == ("--version",)
            return process(self.version)
        self.calls.append(spec)
        wordlist = Path(spec.args[spec.args.index("--wordlist") + 1])
        assert wordlist.parent == Path(env["HOME"])
        words = wordlist.read_text().splitlines()
        assert tuple(words) == WORDS[: len(words)]
        page = spec.args[-1]
        if self.mutate:
            self.mutate()
        if isinstance(self.output, dict):
            raw = self.output.get(page, page_output(page))
            return process(raw)
        if self.output is not None:
            return self.output
        return process(FIXTURE if page == ROOT else page_output(page))


def compose(fake=None, settings=None, scope=None, config=None, limits=None):
    fake = fake or FakeRunner()
    config = config or ExecutionConfig()
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(
            "recon_agent.tools.feroxbuster.shutil.which",
            lambda _: "/trusted/feroxbuster",
        )
        detected = asyncio.run(
            FeroxbusterAdapter.detect(config, settings=settings, runner=fake)
        )
    assert isinstance(detected, Success)
    adapter = detected.value
    registry = ToolRegistry(
        (AdapterRegistration(adapter, AdapterAvailability.AVAILABLE),)
    )
    validator = ScopeValidator(
        scope
        or Scope(
            id="scope",
            roots=(
                Target(id="ip", kind="ip", value="192.0.2.10"),
                Target(id="ip6", kind="ip", value="2001:db8::10"),
                Target(id="name", kind="domain", value="example.test"),
            ),
        )
    )
    budgets = BudgetController(limits or ExecutionBudget.from_config(config), registry)
    state = ReconStateMachine()
    policy = ActionPolicyValidator(
        registry,
        validator,
        ActionPolicyConfig(
            allowed_capabilities=frozenset({CapabilityId.DISCOVER_CONTENT}),
            allowed_risk_classes=frozenset({RiskClass.ACTIVE_SAFE}),
        ),
        budgets,
        ActionDeduplicator(ActionCanonicalizer(registry, validator), state),
    )
    return adapter, fake, policy, budgets, state


def request(**changes):
    values = dict(
        id="action",
        capability="discover_content",
        target=ROOT,
        parameters={},
        reason="authorized content discovery",
    )
    values.update(changes)
    return ActionRequest(**values)


def execute(c, action=None, **kwargs):
    adapter, _, policy, budgets, _ = c
    return asyncio.run(
        adapter.execute(
            action or request(),
            policy=policy,
            budgets=budgets,
            context=CONTEXT,
            **kwargs,
        )
    )


def test_registry_trusted_argv_and_normalization():
    c = compose()
    out = execute(c).value
    assert out.status == "completed"
    assert out.scanned_directories == (ROOT, ROOT + "admin/")
    assert out.request_upper_bound == 14
    assert len(out.endpoints) == 9
    assert {o.data["status_code"] for o in out.observations} == {
        200,
        204,
        301,
        403,
        404,
    }
    for spec in c[1].calls:
        assert spec.executable == "/trusted/feroxbuster"
        assert spec.args[: len(_FLAGS)] == _FLAGS
        assert spec.args[spec.args.index("--threads") + 1] == "1"
        assert spec.args[spec.args.index("--rate-limit") + 1] == "1"
        assert 0 < spec.timeout_seconds <= 30
        assert not set(
            (
                "--redirects",
                "--extract-links",
                "--force-recursion",
                "--proxy",
                "--collect-words",
                "--collect-backups",
                "--collect-extensions",
                "--headers",
                "--parallel",
                "--update",
                "--insecure",
            )
        ) & set(spec.args)
        assert spec.args[spec.args.index("--depth") + 1] == "1"
    assert c[2].registry.resolve("discover_content").value is c[0]
    assert (
        ToolRegistry().resolve("discover_content").error.code
        == ErrorCode.TOOL_UNAVAILABLE
    )
    catalog = c[2].registry.catalog()[0].model_dump_json()
    assert (
        "/trusted" not in catalog
        and "argv" not in catalog
        and "wordlist" not in catalog
    )
    redirect = next(o for o in out.observations if o.data["status_code"] == 301)
    assert redirect.data["redirect_scope_status"] == "rejected"
    assert redirect.data["redirect_authorized"] is False
    assert all(
        o.data["discovery_authorizes_contact"] is False for o in out.observations
    )
    assert all(
        o.data["content_length"] == 123
        and o.source == "feroxbuster"
        and o.execution_id == CONTEXT.execution_id
        and o.observed_at == WHEN
        and o.evidence_ids == (out.evidence[0].id,)
        for o in out.observations
    )
    assert out.evidence[0].origin == ROOT
    assert out.evidence[0].capability == "discover_content"
    assert out.evidence[0].execution_id == CONTEXT.execution_id
    assert out.evidence[0].sha256 and len(out.wordlist_sha256) == 64
    assert all(o.data["source_version"] == "2.13.1" for o in out.observations)


@pytest.mark.parametrize(
    "target",
    [
        "http://outside.test/",
        "http://192.0.2.11/",
        "https://example.test/",
        "example.test",
        "192.0.2.10",
        "http://192.0.2.10/#bad",
        "http://user@192.0.2.10/",
        "http://192.0.2.10/a,b/",
        "http://192.0.2.10/\\bad/",
        "--depth=99",
        "http://192.0.2.10/file",
        "http://192.0.2.10/?x=1",
        "http://192.0.2.10/%2e/",
        "http://192.0.2.10/../",
        "http://192.0.2.10//",
        "http://192.0.2.10/a?",
        "http://192.0.2.10/#",
    ],
)
def test_rejected_target_never_executes(target):
    c = compose()
    assert isinstance(execute(c, request(target=target)), Failure)
    assert c[1].calls == [] and c[3].state.permitted_actions == 0


@pytest.mark.parametrize(
    "parameters",
    [
        {"depth": 0},
        {"depth": 100},
        {"concurrency": 10},
        {"request_rate": 0},
        {"wordlist_path": "/etc/passwd"},
        {"wordlist_profile": "small-v1"},
        {"extra_args": ["--redirects"]},
        {"raw_flags": "--extract-links"},
        {"proxy": "http://outside.test/"},
        {"headers": {"Host": "outside.test"}},
        {"command": "sh"},
        {"argv": ["--depth", "0"]},
        {"binary": "sh"},
        {"wordlist": "https://outside.test/words"},
        {"profile": "huge"},
    ],
)
def test_planner_cannot_choose_flags_or_wordlists(parameters):
    c = compose()
    try:
        action = request(parameters=parameters)
    except ValidationError:
        assert not c[1].calls
        return
    assert isinstance(execute(c, action), Failure)
    assert not c[1].calls and c[3].state.permitted_actions == 0


@pytest.mark.parametrize(
    "changes",
    [
        {"max_depth": -1},
        {"max_depth": 4},
        {"max_depth": True},
        {"max_directories": 0},
        {"max_directories": 9},
        {"max_directories": "2"},
        {"max_requests": 3},
        {"max_requests": 57},
        {"request_rate": 0},
        {"request_rate": 5},
        {"request_rate": 1.0},
        {"concurrency": 0},
        {"concurrency": 3},
        {"concurrency": True},
        {"wordlist_profile": "huge"},
        {"wordlist_path": "/tmp/foo"},
        {"status_codes": [200]},
        {"extra_args": []},
    ],
)
def test_trusted_configuration_is_strict_and_bounded(changes):
    with pytest.raises(ValidationError):
        FeroxbusterSettings(**changes)


@pytest.mark.parametrize(
    "target",
    [
        "https://192.0.2.10/",
        "http://[2001:db8::10]/",
        "https://[2001:db8::10]:8443/path/",
        "http://192.0.2.10:8080/path/",
    ],
)
def test_numeric_http_endpoint_forms(target):
    c = compose(FakeRunner({target: page_output(target)}))
    assert execute(c, request(target=target)).value.scanned_directories == (target,)


@pytest.mark.parametrize(
    "depth,dirs,requests,expected,limitation",
    [
        (0, 8, 56, 1, "depth_limit"),
        (1, 1, 56, 1, "directory_limit"),
        (1, 8, 7, 1, "request_limit"),
        (1, 8, 10, 1, "request_limit"),
        (3, 8, 56, 2, None),
    ],
)
def test_finite_recursion_and_request_budget(
    depth, dirs, requests, expected, limitation
):
    # A final directory needs at least three overhead GETs plus one approved word.
    c = compose(
        settings=FeroxbusterSettings(
            max_depth=depth, max_directories=dirs, max_requests=requests
        )
    )
    # Partial budgets use a shorter approved prefix, so emit only admitted words.
    original = c[1].run

    async def bounded(spec):
        result = await original(spec)
        if "--version" in spec.args:
            return result
        words = (
            Path(spec.args[spec.args.index("--wordlist") + 1]).read_text().splitlines()
        )
        allowed = {spec.args[-1], *(spec.args[-1] + w for w in words)}
        return process(
            b"\n".join(
                line
                for line in result.value.stdout.splitlines()
                if json.loads(line)["url"] in allowed
            )
        )

    c[1].run = bounded
    out = execute(c).value
    assert len(c[1].calls) == expected
    assert out.request_upper_bound <= requests
    if limitation:
        assert limitation in out.limitations and out.status == "partial"
    assert c[3].state.active_executions == 0


def test_truncated_wordlist_reserves_startup_requests():
    c = compose(
        FakeRunner(process(record(ROOT, ROOT) + record(ROOT, ROOT + "admin/", 403))),
        settings=FeroxbusterSettings(max_requests=4),
    )
    out = execute(c).value
    assert out.request_upper_bound == 4 and out.limitations == ("request_limit",)
    assert len(c[1].calls) == 1


def test_depth_three_cannot_loop_or_expand_indefinitely():
    graph = {}
    page = ROOT
    for _ in range(4):
        graph[page] = page_output(page, directory=True)
        page += "admin/"
    c = compose(
        FakeRunner(graph),
        settings=FeroxbusterSettings(max_depth=3, max_directories=8, max_requests=56),
    )
    out = execute(c).value
    assert len(c[1].calls) == 4 and out.request_upper_bound == 28
    assert "depth_limit" in out.limitations


@pytest.mark.parametrize(
    "destination,scope_status",
    [(ROOT + "admin/", "allowed"), ("http://outside.test/", "rejected")],
)
def test_redirects_never_recurse(destination, scope_status):
    raw = page_output(ROOT).replace(b'"status": 404', b'"status": 301')
    rows = [json.loads(line) for line in raw.splitlines()]
    for row in rows:
        row["headers"] = {"location": destination}
    c = compose(
        FakeRunner(process(b"\n".join(json.dumps(row).encode() for row in rows)))
    )
    out = execute(c).value
    assert out.scanned_directories == (ROOT,)
    assert all(
        o.data["redirect_scope_status"] == scope_status for o in out.observations
    )
    assert all(not o.data["redirect_authorized"] for o in out.observations)
    assert (
        all(e.url != destination for e in out.endpoints)
        if "outside" in destination
        else True
    )
    assert len(c[1].calls) == 1


@pytest.mark.parametrize(
    "raw",
    [
        b"bad",
        b"{}",
        b"[]",
        b"null",
        b"\xff",
        b"{",
        b'{"type":"response","type":"response"}',
    ],
)
def test_all_malformed_output_fails(raw):
    c = compose(FakeRunner(process(raw)))
    assert execute(c).error.code == ErrorCode.PARSE_FAILED
    assert c[3].state.active_executions == 0


def test_partial_empty_and_missing_results():
    c = compose(FakeRunner(process(record(ROOT, ROOT) + b"bad\n")))
    out = execute(c).value
    assert out.status == "partial" and out.malformed_lines == 1
    assert len(out.unreported_urls) == 4 and len(out.endpoints) == 1
    c = compose(FakeRunner(process(b"")))
    out = execute(c).value
    assert out.status == "partial" and len(out.unreported_urls) == 5
    assert not out.observations and not out.endpoints and out.evidence


@pytest.mark.parametrize(
    "changes",
    [
        {"status": True},
        {"status": 600},
        {"content_length": -1},
        {"truncated": "false"},
        {"wildcard": True},
        {"path": "/other"},
        {"headers": {"location": "x" * 2049}},
        {"headers": {"location": "x\nflag"}},
        {"headers": []},
        {"method": "POST"},
        {"original_url": "http://outside.test/"},
        {"url": "http://outside.test/"},
    ],
)
def test_invalid_or_unexpected_machine_contacts(changes):
    c = compose(FakeRunner(process(record(ROOT, ROOT, **changes))))
    assert execute(c).error.code == ErrorCode.PARSE_FAILED
    assert len(c[1].calls) == 1


def test_deterministic_duplicates_and_conflicts():
    rows = FIXTURE.splitlines()
    settings = FeroxbusterSettings(max_depth=0)
    first = execute(
        compose(FakeRunner(process(b"\n".join(rows + rows))), settings=settings)
    ).value
    second = execute(
        compose(FakeRunner(process(b"\n".join(reversed(rows)))), settings=settings)
    ).value
    assert first == second
    c = compose(FakeRunner(process(record(ROOT, ROOT) + record(ROOT, ROOT, 403))))
    assert execute(c).error.code == ErrorCode.PARSE_FAILED


@pytest.mark.parametrize(
    "result,code",
    [
        (process(return_code=3), ErrorCode.TOOL_EXECUTION_FAILED),
        (process(stdout_truncated=True), ErrorCode.PARSE_FAILED),
        (process(stderr_truncated=True), ErrorCode.PARSE_FAILED),
        (
            Failure(error=ToolUnavailableError("missing").to_error_info()),
            ErrorCode.TOOL_UNAVAILABLE,
        ),
        (
            Failure(error=ToolTimeoutError("timeout").to_error_info()),
            ErrorCode.TOOL_TIMEOUT,
        ),
    ],
)
def test_canonical_runner_outcomes(result, code):
    c = compose(FakeRunner(result))
    assert execute(c).error.code == code
    assert c[3].state.active_executions == 0 and c[3].state.permitted_actions == 1


@pytest.mark.parametrize(
    "version",
    [
        b"2.13.1",
        b"feroxbuster 2.13.0\n",
        b"feroxbuster 2.13.1\nferoxbuster 2.13.1\n",
        b"\xff",
    ],
)
def test_unsupported_detection(version, monkeypatch):
    fake = FakeRunner()
    fake.version = version
    monkeypatch.setattr(
        "recon_agent.tools.feroxbuster.shutil.which", lambda _: "/trusted/feroxbuster"
    )
    out = asyncio.run(FeroxbusterAdapter.detect(ExecutionConfig(), runner=fake))
    assert out.error.code == ErrorCode.TOOL_UNAVAILABLE and not fake.calls


def test_missing_binary_and_unverified_adapter(monkeypatch):
    monkeypatch.setattr("recon_agent.tools.feroxbuster.shutil.which", lambda _: None)
    assert (
        asyncio.run(
            FeroxbusterAdapter.detect(ExecutionConfig(), runner=FakeRunner())
        ).error.code
        == ErrorCode.TOOL_UNAVAILABLE
    )
    c = compose()
    object.__setattr__(c[0], "_verified", False)
    assert execute(c).error.code == ErrorCode.TOOL_UNAVAILABLE and not c[1].calls


def test_ambient_configuration_rejects_before_probe_and_contact(monkeypatch, tmp_path):
    binary = tmp_path / "feroxbuster"
    binary.touch()
    (tmp_path / "ferox-config.toml").write_text("redirects = true\n")
    monkeypatch.setattr(
        "recon_agent.tools.feroxbuster.shutil.which", lambda _: str(binary)
    )
    fake = FakeRunner()
    assert (
        asyncio.run(
            FeroxbusterAdapter.detect(ExecutionConfig(), runner=fake)
        ).error.code
        == ErrorCode.TOOL_UNAVAILABLE
    )
    assert not fake.calls
    (tmp_path / "ferox-config.toml").unlink()
    c = compose()
    object.__setattr__(c[0], "executable", str(binary))
    (tmp_path / "ferox-config.toml").symlink_to(tmp_path / "missing")
    assert execute(c).error.code == ErrorCode.TOOL_UNAVAILABLE and not c[1].calls
    assert c[3].state.permitted_actions == 0


def test_scope_change_after_pacing_never_contacts(monkeypatch):
    c = compose()
    original = ScopeValidator.validate_value
    denied = False

    def checked(self, value):
        return (
            Failure(error=ToolUnavailableError("changed scope").to_error_info())
            if denied
            else original(self, value)
        )

    async def sleep(_):
        nonlocal denied
        denied = True

    monkeypatch.setattr(ScopeValidator, "validate_value", checked)
    monkeypatch.setattr("recon_agent.tools.feroxbuster.asyncio.sleep", sleep)
    assert isinstance(execute(c), Failure) and len(c[1].calls) == 1


def test_start_abort_and_final_scope_check(monkeypatch):
    c = compose()
    failure = Failure(error=ToolUnavailableError("abort").to_error_info())
    assert execute(c, on_started=lambda: failure) == failure and not c[1].calls
    c = compose()

    def started():
        monkeypatch.setattr(
            ScopeValidator, "validate_value", lambda self, value: failure
        )
        return Success(value=None)

    assert execute(c, on_started=started) == failure and not c[1].calls


def test_output_and_structural_bounds():
    for raw in (b"x" * 65537, b"\n" * 129):
        with pytest.raises(ValueError):
            parse(raw, ROOT, (ROOT,))
    c = compose(
        FakeRunner(process(b" " * 600)), config=ExecutionConfig(max_output_bytes=512)
    )
    assert execute(c).error.code == ErrorCode.PARSE_FAILED
    c = compose(
        FakeRunner(process(record(ROOT, ROOT))),
        config=ExecutionConfig(max_output_bytes=512),
    )
    assert execute(c).error.code == ErrorCode.PARSE_FAILED
    c = compose(
        FakeRunner(
            {
                ROOT: record(ROOT, ROOT) + record(ROOT, ROOT + "admin/"),
                ROOT + "admin/": page_output(ROOT + "admin/"),
            }
        ),
        config=ExecutionConfig(max_output_bytes=1000),
    )
    assert execute(c).error.code == ErrorCode.PARSE_FAILED


def test_body_prefix_is_explicit_partial():
    c = compose(FakeRunner(process(record(ROOT, ROOT, truncated=True))))
    assert "response_body_limit" in execute(c).value.limitations


def test_rate_threads_and_stricter_shared_pacing(monkeypatch):
    waits = []

    async def sleep(seconds):
        waits.append(seconds)

    monkeypatch.setattr("recon_agent.tools.feroxbuster.asyncio.sleep", sleep)
    c = compose(
        settings=FeroxbusterSettings(request_rate=4, concurrency=2),
        limits=ExecutionBudget(
            capability_rate_actions=1, capability_rate_window_seconds=8.0
        ),
    )
    assert isinstance(execute(c), Success) and waits == [8.0]
    assert c[1].calls[0].args[c[1].calls[0].args.index("--threads") + 1] == "2"
    assert c[1].calls[0].args[c[1].calls[0].args.index("--rate-limit") + 1] == "4"


def test_timeout_cancellation_and_temp_cleanup(monkeypatch):
    c = compose(config=ExecutionConfig(default_timeout_seconds=0.01))
    dirs = []

    async def waiting(spec):
        dirs.append(spec.working_directory)
        await asyncio.Future()

    c[1].run = waiting
    assert execute(c).error.code == ErrorCode.TOOL_TIMEOUT
    assert c[3].state.active_executions == 0 and all(not Path(p).exists() for p in dirs)
    c = compose()

    async def cancelled(spec):
        dirs.append(spec.working_directory)
        raise asyncio.CancelledError

    c[1].run = cancelled
    with pytest.raises(asyncio.CancelledError):
        execute(c)
    assert c[3].state.active_executions == 0 and c[3].state.permitted_actions == 1
    assert all(not Path(p).exists() for p in dirs)
    c = compose()
    now = [0.0]
    monkeypatch.setattr("recon_agent.tools.feroxbuster.monotonic", lambda: now[0])
    c[1].mutate = lambda: now.__setitem__(0, 60.0)
    assert execute(c).error.code == ErrorCode.TOOL_TIMEOUT


@pytest.mark.parametrize(
    "limits",
    [
        ExecutionBudget(max_actions=1),
        ExecutionBudget(max_actions_per_host=1),
        ExecutionBudget(max_concurrency=1),
        ExecutionBudget(max_session_output_bytes=2_097_152),
    ],
)
def test_shared_budget_reservation_denies_unfunded_execution(limits):
    c = compose(limits=limits)
    permit = c[3].reserve(c[2].validate(request()).value).value
    try:
        assert isinstance(execute(c), Failure) and not c[1].calls
    finally:
        permit.release()
    assert c[3].state.active_executions == 0


def test_state_ingestion_and_discovery_does_not_authorize():
    c = compose(settings=FeroxbusterSettings(max_depth=0))
    state = c[4]
    action = request()
    assert isinstance(state.record_action_requested(action, recorded_at=WHEN), Success)
    assert isinstance(
        state.mark_action_approved(
            action.id, policy_reference="policy", recorded_at=WHEN
        ),
        Success,
    )

    def started():
        out = state.mark_action_started(
            action.id, execution_id=CONTEXT.execution_id, recorded_at=WHEN
        )
        return out if isinstance(out, Failure) else Success(value=None)

    out = execute(c, on_started=started).value
    result = ActionResult(
        id="result",
        action_id=action.id,
        status=out.status,
        recorded_at=WHEN,
        execution_ids=(CONTEXT.execution_id,),
        observations=out.observations,
        evidence=out.evidence,
        error=out.errors[0],
    )
    assert isinstance(
        state.record_action_result(
            result, assets=(out.asset,), endpoints=out.endpoints
        ),
        Success,
    )
    assert len(state.state.endpoints) == 5
    assert isinstance(c[2].validate(request(id="repeat")), Failure)
    assert isinstance(
        c[2].validate(request(id="external", target="http://outside.test/")), Failure
    )
    assert len(c[1].calls) == 1


def test_inert_construction_and_input():
    assert FeroxbusterInput().model_dump() == {}
    adapter = FeroxbusterAdapter("/trusted/feroxbuster", ExecutionConfig())
    assert not adapter._verified and ToolRegistry().list_capabilities() == ()


def test_system_configuration_presence_rejects_before_detection(monkeypatch):
    original = Path.lstat

    def stat(path, *args, **kwargs):
        if str(path) == "/etc/feroxbuster/ferox-config.toml":
            return object()
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "lstat", stat)
    monkeypatch.setattr(
        "recon_agent.tools.feroxbuster.shutil.which", lambda _: "/trusted/feroxbuster"
    )
    fake = FakeRunner()
    assert (
        asyncio.run(
            FeroxbusterAdapter.detect(ExecutionConfig(), runner=fake)
        ).error.code
        == ErrorCode.TOOL_UNAVAILABLE
    )
    assert not fake.calls


def test_configuration_change_between_processes_rejects(monkeypatch):
    c = compose()
    calls = []

    def config(executable):
        calls.append(executable)
        if len(calls) == 3:
            raise ToolUnavailableError("configuration changed")

    monkeypatch.setattr("recon_agent.tools.feroxbuster._ambient_config", config)
    assert execute(c).error.code == ErrorCode.TOOL_UNAVAILABLE
    assert len(c[1].calls) == 1 and c[3].state.active_executions == 0


@pytest.mark.parametrize(
    "changes", [{"capability": "crawl_web"}, {"asset_id": "other"}]
)
def test_composition_mismatch_never_executes(changes):
    c = compose()
    assert (
        execute(c, request(**changes)).error.code == ErrorCode.PLANNER_VALIDATION_FAILED
    )
    assert not c[1].calls


def test_wrong_registered_instance_rejects():
    c = compose()
    adapter = FeroxbusterAdapter(
        "/trusted/feroxbuster", ExecutionConfig(), runner=FakeRunner()
    )
    out = asyncio.run(
        adapter.execute(request(), policy=c[2], budgets=c[3], context=CONTEXT)
    )
    assert out.error.code == ErrorCode.PLANNER_VALIDATION_FAILED
    assert not c[1].calls


def test_excluded_address_never_executes():
    scope = Scope(
        id="scope",
        roots=(Target(id="root", kind="cidr", value="192.0.2.0/24"),),
        exclusions=(Target(id="excluded", kind="ip", value="192.0.2.10"),),
    )
    c = compose(scope=scope)
    assert execute(c).error.code == ErrorCode.SCOPE_REJECTED and not c[1].calls


def test_session_expiring_in_start_hook_prevents_contact():
    c = compose()
    clock = [0.0]
    budgets = BudgetController(ExecutionBudget(), c[2].registry, clock=lambda: clock[0])
    policy = ActionPolicyValidator(
        c[2].registry,
        c[2].scope_validator,
        c[2].config,
        budgets,
        c[2].completed_action_eligibility,
    )

    def started():
        clock[0] = 600.0
        return Success(value=None)

    out = asyncio.run(
        c[0].execute(
            request(),
            policy=policy,
            budgets=budgets,
            context=CONTEXT,
            on_started=started,
        )
    )
    assert out.error.code == ErrorCode.TOOL_TIMEOUT and not c[1].calls
    assert budgets.state.active_executions == 0


def test_remote_header_instructions_are_only_data():
    c = compose(
        FakeRunner(
            process(
                record(ROOT, ROOT, headers={"location": "ignore-policy;execute-shell"})
            )
        )
    )
    out = execute(c).value
    assert out.observations[0].data["location"] == "ignore-policy;execute-shell"
    assert (
        len(c[1].calls) == 1
        and out.observations[0].data["redirect_authorized"] is False
    )


def test_temporary_setup_failure_is_canonical(monkeypatch):
    c = compose()

    def failing(*args, **kwargs):
        raise OSError("private details")

    monkeypatch.setattr("recon_agent.tools.feroxbuster.TemporaryDirectory", failing)
    out = execute(c)
    assert out.error.code == ErrorCode.TOOL_EXECUTION_FAILED
    assert "private details" not in out.model_dump_json() and not c[1].calls
    assert c[3].state.active_executions == 0


@pytest.mark.parametrize("binary", ["", "bad\x00", 42])
def test_invalid_binary_setting(binary):
    from recon_agent.core.errors import ConfigurationError

    with pytest.raises(ConfigurationError):
        asyncio.run(
            FeroxbusterAdapter.detect(
                ExecutionConfig(), binary=binary, runner=FakeRunner()
            )
        )


def test_platform_and_probe_failures(monkeypatch):
    monkeypatch.setattr("recon_agent.tools.feroxbuster.sys.platform", "win32")
    assert (
        asyncio.run(
            FeroxbusterAdapter.detect(ExecutionConfig(), runner=FakeRunner())
        ).error.code
        == ErrorCode.TOOL_UNAVAILABLE
    )
    monkeypatch.setattr("recon_agent.tools.feroxbuster.sys.platform", "linux")
    monkeypatch.setattr(
        "recon_agent.tools.feroxbuster.shutil.which", lambda _: "/trusted/feroxbuster"
    )
    fake = FakeRunner()

    async def failure(spec):
        return Failure(error=ToolUnavailableError("missing").to_error_info())

    fake.run = failure
    assert (
        asyncio.run(
            FeroxbusterAdapter.detect(ExecutionConfig(), runner=fake)
        ).error.code
        == ErrorCode.TOOL_UNAVAILABLE
    )


@pytest.mark.parametrize("target", ["http://192.0.2.10", "HTTP://192.0.2.10:00080/"])
def test_shared_web_identity_denies_equivalent_action_before_dispatch(target):
    c = compose()
    first = request()
    assert isinstance(c[4].record_action_requested(first, recorded_at=WHEN), Success)
    calls = len(c[1].calls)
    budget = c[3].state
    repeated = request(id="equivalent", target=target)
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

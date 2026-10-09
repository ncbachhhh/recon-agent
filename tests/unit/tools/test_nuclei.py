"""Offline foundation only: no scanner/template dispatch, even with valid policy."""

import asyncio
import base64
import json
import socket
import subprocess
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
from recon_agent.tools.nuclei import NucleiAdapter, NucleiProfilePolicy
from recon_agent.tools.nuclei_models import NucleiContext, NucleiInput, NucleiOutput
from recon_agent.tools.nuclei_parser import MAX_BYTES, MAX_LINE_BYTES, MAX_LINES

WHEN = datetime(2026, 10, 9, tzinfo=UTC)
CONTEXT = NucleiContext(
    asset_id="asset",
    execution_id="execution",
    collected_at=WHEN,
    query_target="https://example.test",
)
FIXTURE = (Path(__file__).parents[2] / "fixtures/nuclei/candidates.jsonl").read_bytes()
FIRST = json.loads(FIXTURE.splitlines()[0])


@pytest.fixture(autouse=True)
def no_contact_or_process(monkeypatch):
    blocked = Mock(side_effect=AssertionError("unexpected network/process contact"))
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    for name in (
        "getaddrinfo",
        "gethostbyname",
        "gethostbyname_ex",
        "gethostbyaddr",
        "create_connection",
    ):
        monkeypatch.setattr(socket, name, blocked)
    for name in (
        "connect",
        "connect_ex",
        "send",
        "sendall",
        "sendto",
        "bind",
        "listen",
    ):
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
        argument_count=0,
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


def wire(**changes):
    obj = dict(FIRST)
    obj.update(changes)
    return json.dumps(obj, separators=(",", ":")).encode() + b"\n"


class FakeRunner:
    def __init__(self, result=None):
        self.result = (
            result
            if result is not None
            else process(b"", stderr=b"[INF] Nuclei Engine Version: v3.4.10\n")
        )
        self.calls = []
        self.directories = []

    async def run(self, spec):
        self.calls.append(spec)
        directory = Path(spec.working_directory)
        assert directory.is_dir()
        self.directories.append(directory)
        assert dict(spec.environment) == {
            key: str(directory)
            for key in ("PATH", "HOME", "XDG_CONFIG_HOME", "XDG_CACHE_HOME", "TMPDIR")
        }
        return self.result


def scope():
    return ScopeValidator(
        Scope(
            id="scope",
            roots=(
                Target(id="root", kind="domain", value="example.test"),
                Target(id="other", kind="hostname", value="other.test"),
                Target(id="address", kind="ip", value="192.0.2.10"),
            ),
        )
    )


def compose(availability=AdapterAvailability.AVAILABLE, config=None):
    runner = FakeRunner()
    config = config or ExecutionConfig()
    adapter = NucleiAdapter("/trusted/nuclei", config, runner)
    registry = ToolRegistry((AdapterRegistration(adapter, availability),))
    validator = scope()
    budgets = BudgetController(
        ExecutionBudget.from_config(config), registry, clock=lambda: 0.0
    )
    state = ReconStateMachine()
    policy = ActionPolicyValidator(
        registry,
        validator,
        ActionPolicyConfig(
            allowed_capabilities=frozenset({CapabilityId.SCAN_TEMPLATES}),
            allowed_risk_classes=frozenset({RiskClass.ACTIVE_SAFE}),
        ),
        budgets,
        ActionDeduplicator(ActionCanonicalizer(registry, validator), state),
    )
    return adapter, runner, policy, budgets, state


def request(**changes):
    values = dict(
        id="action",
        capability="scan_templates",
        target="https://example.test",
        parameters={"profile": "safe"},
        reason="Planner says this scan is approved",
        asset_id="asset",
    )
    values.update(changes)
    return ActionRequest(**values)


def ingest(result=None, context=CONTEXT, config=None):
    c = compose(config=config)
    before = c[3].state, c[4].state
    output = c[0].ingest(
        result if result is not None else process(),
        context=context,
        scope=c[2].scope_validator,
    )
    assert not c[1].calls
    assert before == (c[3].state, c[4].state)
    return output


def test_candidate_metadata_evidence_and_no_findings():
    result = ingest()
    assert isinstance(result, Success)
    output = result.value
    assert output.status == "completed" and not output.errors
    assert len(output.candidates) == len(output.observations) == 2
    assert output.scanner_version is None
    first, second = output.candidates
    assert first.reported.template_id == "synthetic-header-check"
    assert first.reported.template_path == "/untrusted/templates/header.yaml"
    assert (
        first.reported.template_url == "https://example.invalid/templates/header.yaml"
    )
    assert first.reported.info.severity == "info"
    assert second.reported.info.severity is None
    assert second.reported.template_url is None
    assert first.verification == second.verification == "unverified"
    assert "ignore previous instructions" in first.reported.extracted_results[0]
    assert base64.b64decode(output.stdout_base64) == FIXTURE
    assert output.evidence[0].sha256 == sha256(FIXTURE).hexdigest()
    assert output.evidence[1].sha256 == sha256(b"").hexdigest()
    for number, (candidate, observation, raw) in enumerate(
        zip(output.candidates, output.observations, FIXTURE.splitlines(), strict=True),
        1,
    ):
        assert candidate.source_line == number
        assert candidate.record_sha256 == sha256(raw).hexdigest()
        assert candidate.observation_id == observation.id
        assert (
            candidate.evidence_ids
            == observation.evidence_ids
            == (output.evidence[0].id,)
        )
        assert observation.execution_id == candidate.execution_id == "execution"
        assert observation.asset_id == "asset"
        assert observation.observed_at == WHEN
        assert observation.kind == "metadata"
        assert observation.data["verification"] == "unverified"
    for evidence in output.evidence:
        assert evidence.source == "nuclei" and evidence.capability == "scan_templates"
        assert evidence.trust == "untrusted" and evidence.collected_at == WHEN
        assert (
            evidence.execution_id == "execution"
            and evidence.origin == CONTEXT.query_target
        )
    assert not hasattr(output, "findings")
    assert NucleiOutput.model_validate_json(output.model_dump_json()) == output
    action_result = ActionResult(
        id="result",
        action_id="action",
        status="completed",
        recorded_at=WHEN,
        observations=output.observations,
        evidence=output.evidence,
        execution_ids=("execution",),
    )
    assert action_result.observations == output.observations
    assert ingest().value == output


def test_duplicate_and_conflicting_reports_keep_all_source_records():
    raw = (
        wire()
        + wire()
        + wire(info={"name": "Conflicting claim", "severity": "critical"})
    )
    output = ingest(process(raw)).value
    assert output.status == "completed"
    assert [c.source_line for c in output.candidates] == [1, 2, 3]
    assert len({c.observation_id for c in output.candidates}) == 3
    assert output.candidates[0].record_sha256 == output.candidates[1].record_sha256
    assert output.candidates[2].reported.info.severity == "critical"
    assert base64.b64decode(output.stdout_base64) == raw


@pytest.mark.parametrize(
    "raw",
    [
        b"not-json\n",
        b"[]\n",
        b"null\n",
        b"1\n",
        b'"text"\n',
        b"{}\n",
        b"\xff\n",
        b'{"template-id":"x","template-id":"y"}\n',
        b'{"info":{"name":"x","name":"y"}}\n',
        b'{"unused":NaN}\n',
        b'{"unused":Infinity}\n',
        b"{" + b'"nested":[' * 1100 + b"0" + b"]}" * 1100 + b"\n",
        b"x" * (MAX_LINE_BYTES + 1) + b"\n",
    ],
)
def test_malformed_records_preserve_bytes_and_structured_failure(raw):
    output = ingest(process(raw, stderr=b"untrusted diagnostic\xff")).value
    assert (
        output.status == "failed" and not output.candidates and not output.observations
    )
    assert output.malformed_lines == 1
    assert output.errors[0].code is ErrorCode.PARSE_FAILED
    assert base64.b64decode(output.stdout_base64) == raw
    assert base64.b64decode(output.stderr_base64) == b"untrusted diagnostic\xff"
    assert "untrusted diagnostic" not in output.errors[0].model_dump_json()
    partial = ingest(process(wire() + raw)).value
    assert partial.status == "partial" and len(partial.candidates) == 1
    assert partial.malformed_lines == 1
    ActionResult(
        id="partial",
        action_id="action",
        status="partial",
        recorded_at=WHEN,
        observations=partial.observations,
        evidence=partial.evidence,
        error=partial.errors[0],
        execution_ids=("execution",),
    )


@pytest.mark.parametrize(
    "changes",
    [
        {"template-id": None},
        {"template-id": 1},
        {"template-id": ""},
        {"info": None},
        {"info": []},
        {"info": {"severity": "severe"}},
        {"info": {"severity": 3}},
        {"info": {"reference": "https://example.invalid"}},
        {"info": {"reference": ["x"] * 65}},
        {"info": {"name": "x" * 4097}},
        {"matcher-status": False},
        {"matcher-status": 1},
        {"matcher-status": "true"},
        {"matcher-status": None},
        {"error": "scanner failed"},
        {"error": None},
        {"type": ""},
        {"host": "https://outside.test"},
        {"matched-at": "https://outside.test"},
        {"url": "https://outside.test"},
        {"ip": "192.0.2.11"},
        {"ip": "https://example.test"},
        {"host": "https://other.test"},
        {"matched-at": "https://other.test"},
        {"url": "https://other.test"},
        {"host": "example.test:443"},
        {"host": "https://user@example.test"},
        {"matched-at": "file:///tmp/secret"},
        {"extracted-results": ["x"] * 65},
        {"extracted-results": [1]},
        {"timestamp": 1},
        {"ip": "192.0.2.10\x00"},
    ],
)
def test_invalid_or_unmatched_metadata_never_becomes_candidate(changes):
    output = ingest(process(wire(**changes))).value
    assert output.status == "failed" and not output.candidates
    assert output.errors[0].code is ErrorCode.PARSE_FAILED


@pytest.mark.parametrize(
    "field", ["template-id", "info", "type", "host", "matched-at", "matcher-status"]
)
def test_missing_required_fields(field):
    obj = dict(FIRST)
    del obj[field]
    output = ingest(process(json.dumps(obj).encode())).value
    assert output.status == "failed" and output.malformed_lines == 1


@pytest.mark.parametrize(
    "changes,expected",
    [
        ({"return_code": 2}, ErrorCode.TOOL_EXECUTION_FAILED),
        ({"stdout_truncated": True}, ErrorCode.PARSE_FAILED),
        ({"stderr_truncated": True}, ErrorCode.PARSE_FAILED),
        ({"stdout_truncated": True, "return_code": 2}, ErrorCode.TOOL_EXECUTION_FAILED),
    ],
)
def test_partial_process_results(changes, expected):
    output = ingest(process(**changes)).value
    assert output.status == "partial" and len(output.candidates) == 2
    assert output.errors[0].code is expected
    assert output.evidence[0].truncated == changes.get("stdout_truncated", False)
    assert output.evidence[1].truncated == changes.get("stderr_truncated", False)


def test_truncated_terminal_record_not_promoted():
    output = ingest(process(wire() + wire().rstrip(b"\n"), stdout_truncated=True)).value
    assert output.status == "partial" and len(output.candidates) == 1
    assert output.malformed_lines == 1


@pytest.mark.parametrize("raw", [b"", b"\n  \n"])
def test_empty_output_has_no_candidate_or_clean_target_claim(raw):
    output = ingest(process(raw)).value
    assert output.status == "completed" and not output.candidates
    assert not output.observations and len(output.evidence) == 2


@pytest.mark.parametrize(
    "changes",
    [
        {"stdout": b"x" * (MAX_BYTES + 1)},
        {"stderr": b"x" * (MAX_BYTES + 1)},
        {"stdout": b"\n" * (MAX_LINES + 1)},
    ],
)
def test_aggregate_bounds(changes):
    result = ingest(process(**changes))
    assert isinstance(result, Failure) and result.error.code is ErrorCode.PARSE_FAILED


def test_configured_capture_limit_and_constructed_context_revalidation():
    assert isinstance(ingest(config=ExecutionConfig(max_output_bytes=1)), Failure)
    assert isinstance(
        ingest(
            context=CONTEXT.model_copy(
                update={"collected_at": WHEN.replace(tzinfo=None)}
            )
        ),
        Failure,
    )
    outside = ingest(
        context=CONTEXT.model_copy(update={"query_target": "https://outside.test"})
    )
    assert outside.error.code is ErrorCode.SCOPE_REJECTED
    versioned = ingest(
        context=CONTEXT.model_copy(update={"scanner_version": "3.4.10"})
    ).value
    assert versioned.scanner_version == "3.4.10"


@pytest.mark.parametrize(
    "error",
    [
        ToolTimeoutError("deadline"),
        ToolUnavailableError("missing"),
        ToolExecutionError("launch failed"),
    ],
)
def test_canonical_runner_failures_are_preserved(error):
    failure = Failure(error=error.to_error_info())
    assert ingest(failure) == failure


@pytest.mark.parametrize(
    "profile",
    [
        "safe",
        "default",
        "passive",
        "approved",
        "non-destructive",
        "intrusive",
        "exploit",
        "oast",
    ],
)
def test_every_named_profile_denies_argv_and_dispatch_without_spending(profile):
    c = compose()
    action = request(parameters={"profile": profile})
    assert isinstance(c[2].validate(action), Success)  # Policy alone is insufficient.
    assert isinstance(c[0].scan_spec(NucleiInput(profile=profile)), Failure)
    before = c[3].state, c[4].state
    result = asyncio.run(
        c[0].execute(action, policy=c[2], budgets=c[3], context=CONTEXT)
    )
    assert result.error.code is ErrorCode.PLANNER_VALIDATION_FAILED
    assert "none exist" in result.error.message
    assert not c[1].calls
    assert before == (c[3].state, c[4].state)


@pytest.mark.parametrize(
    "profile",
    [
        "",
        "../safe",
        "/tmp/template.yaml",
        "-t",
        "safe --oast",
        "safe;id",
        "$(id)",
        "https://templates.test/a",
        "SAFE",
        "s" * 65,
        "safe\x00",
        1,
        None,
    ],
)
def test_raw_path_flag_and_malformed_profile_rejection(profile):
    with pytest.raises(ValidationError):
        NucleiInput.model_validate({"profile": profile})
    assert isinstance(
        NucleiProfilePolicy().resolve(NucleiInput.model_construct(profile=profile)),
        Failure,
    )
    c = compose()
    result = asyncio.run(
        c[0].execute(
            request(parameters={"profile": profile}),
            policy=c[2],
            budgets=c[3],
            context=CONTEXT,
        )
    )
    assert isinstance(result, Failure) and not c[1].calls


@pytest.mark.parametrize(
    "parameters",
    [
        {},
        {"profile": "safe", "templates": ["/tmp/a"]},
        {"profile": "safe", "flags": ["-t"]},
        {"profile": "safe", "approved": True},
        {"profile": "safe", "update": True},
        {"profile": "safe", "environment": {}},
        {"profile": "safe", "timeout": 0},
        {"profile": "safe", "target": "https://outside.test"},
    ],
)
def test_unexpected_planner_parameters_never_dispatch(parameters):
    c = compose()
    result = asyncio.run(
        c[0].execute(
            request(parameters=parameters), policy=c[2], budgets=c[3], context=CONTEXT
        )
    )
    assert result.error.code is ErrorCode.PLANNER_VALIDATION_FAILED
    assert not c[1].calls and c[3].state.permitted_actions == 0


@pytest.mark.parametrize(
    "target",
    [
        "https://outside.test",
        "https://example.test.evil.test",
        "https://user@example.test",
        "192.0.2.11",
    ],
)
def test_scope_rejection_precedes_profile_denial(target):
    c = compose()
    result = asyncio.run(
        c[0].execute(request(target=target), policy=c[2], budgets=c[3], context=CONTEXT)
    )
    assert result.error.code is ErrorCode.SCOPE_REJECTED
    assert not c[1].calls and c[3].state.permitted_actions == 0


@pytest.mark.parametrize(
    "availability", [AdapterAvailability.NOT_CHECKED, AdapterAvailability.UNAVAILABLE]
)
def test_unavailable_registration_never_dispatches(availability):
    c = compose(availability)
    result = asyncio.run(
        c[0].execute(request(), policy=c[2], budgets=c[3], context=CONTEXT)
    )
    assert result.error.code is ErrorCode.TOOL_UNAVAILABLE and not c[1].calls


def test_catalog_is_explicit_inert_and_hides_execution_fields():
    c = compose()
    assert not ToolRegistry().catalog()
    entry = c[2].registry.catalog()[0].model_dump(mode="json")
    assert set(entry) == {"capability", "description", "risk_class", "availability"}
    assert entry["capability"] == "scan_templates"
    assert "/trusted/nuclei" not in json.dumps(entry)
    assert c[0].definition.parameter_target_fields == ()
    assert not c[1].calls


def test_missing_binary_does_not_probe(monkeypatch):
    monkeypatch.setattr("recon_agent.tools.nuclei.shutil.which", lambda _: None)
    fake = FakeRunner()
    result = asyncio.run(NucleiAdapter.detect(ExecutionConfig(), runner=fake))
    assert result.error.code is ErrorCode.TOOL_UNAVAILABLE and not fake.calls


def detect(monkeypatch, fake):
    monkeypatch.setattr(
        "recon_agent.tools.nuclei.shutil.which", lambda _: "/trusted/nuclei"
    )
    return asyncio.run(NucleiAdapter.detect(ExecutionConfig(), runner=fake))


def test_fixed_isolated_version_argv_and_detection_does_not_enable_scans(monkeypatch):
    fake = FakeRunner()
    result = detect(monkeypatch, fake)
    assert isinstance(result, Success)
    spec = fake.calls[0]
    assert spec.executable == "/trusted/nuclei"
    assert spec.args == ("-duc", "-nc", "-config", "/dev/null", "-version")
    assert spec.timeout_seconds == 5.0
    assert all(not d.exists() for d in fake.directories)
    assert not ToolRegistry().catalog()
    assert isinstance(result.value.scan_spec(NucleiInput(profile="safe")), Failure)
    assert len(fake.calls) == 1


@pytest.mark.parametrize(
    "result,code",
    [
        (
            Failure(error=ToolTimeoutError("deadline").to_error_info()),
            ErrorCode.TOOL_TIMEOUT,
        ),
        (
            Failure(error=ToolUnavailableError("missing").to_error_info()),
            ErrorCode.TOOL_UNAVAILABLE,
        ),
        (process(b"", return_code=1), ErrorCode.TOOL_EXECUTION_FAILED),
        (process(b"", stdout_truncated=True), ErrorCode.PARSE_FAILED),
        (process(b"x" * (MAX_BYTES + 1)), ErrorCode.PARSE_FAILED),
        (process(b"\xff"), ErrorCode.TOOL_UNAVAILABLE),
        (
            process(b"[INF] Nuclei Engine Version: v3.4.11\n"),
            ErrorCode.TOOL_UNAVAILABLE,
        ),
        (
            process(b"[INF] Nuclei Engine Version: v3.4.10\n" * 2),
            ErrorCode.TOOL_UNAVAILABLE,
        ),
        (process(b"not a version"), ErrorCode.TOOL_UNAVAILABLE),
    ],
)
def test_probe_failures_are_structured_and_cleanup(monkeypatch, result, code):
    fake = FakeRunner(result)
    outcome = detect(monkeypatch, fake)
    assert isinstance(outcome, Failure) and outcome.error.code is code
    assert all(not d.exists() for d in fake.directories)


def test_cancellation_propagates_and_probe_directory_is_cleaned(monkeypatch):
    class CancelRunner(FakeRunner):
        async def run(self, spec):
            self.directories.append(Path(spec.working_directory))
            raise asyncio.CancelledError

    fake = CancelRunner()
    with pytest.raises(asyncio.CancelledError):
        detect(monkeypatch, fake)
    assert all(not d.exists() for d in fake.directories)


@pytest.mark.parametrize("binary", ["", " ", "bad\x00", None])
def test_invalid_trusted_binary_setting(binary):
    with pytest.raises(ConfigurationError):
        asyncio.run(NucleiAdapter.detect(ExecutionConfig(), binary=binary))


@pytest.mark.parametrize("executable", ["nuclei", "", "/bad\x00", None])
def test_invalid_trusted_adapter_executable(executable):
    with pytest.raises(ConfigurationError):
        NucleiAdapter(executable, ExecutionConfig())


@pytest.mark.parametrize(
    "changes",
    [
        {"capability": "probe_http"},
        {"asset_id": "other"},
        {"parameters": {"profile": " "}},
    ],
)
def test_request_composition_mismatch_stays_denied(changes):
    c = compose()
    result = asyncio.run(
        c[0].execute(request(**changes), policy=c[2], budgets=c[3], context=CONTEXT)
    )
    assert isinstance(result, Failure) and not c[1].calls


@pytest.mark.parametrize(
    "target,code",
    [
        ("https://outside.test", ErrorCode.SCOPE_REJECTED),
        ("https://other.test", ErrorCode.PLANNER_VALIDATION_FAILED),
    ],
)
def test_context_subject_cannot_change_request(target, code):
    c = compose()
    context = CONTEXT.model_copy(update={"query_target": target})
    result = asyncio.run(
        c[0].execute(request(), policy=c[2], budgets=c[3], context=context)
    )
    assert result.error.code is code and not c[1].calls


def test_other_registry_binding_and_budget_controller_are_denied():
    c = compose()
    other = compose()
    for policy, budgets in ((other[2], other[3]), (c[2], other[3])):
        result = asyncio.run(
            c[0].execute(request(), policy=policy, budgets=budgets, context=CONTEXT)
        )
        assert result.error.code is ErrorCode.PLANNER_VALIDATION_FAILED
        assert not c[1].calls and not other[1].calls


def test_existing_budget_dedup_and_default_policy_denials():
    c = compose()
    limits = ExecutionBudget(max_actions=1)
    budgets = BudgetController(limits, c[2].registry, clock=lambda: 0.0)
    policy = ActionPolicyValidator(
        c[2].registry,
        c[2].scope_validator,
        c[2].config,
        budgets,
        c[2].completed_action_eligibility,
    )
    approved = policy.validate(request()).value
    permit = budgets.reserve(approved).value
    permit.release()
    result = asyncio.run(
        c[0].execute(request(), policy=policy, budgets=budgets, context=CONTEXT)
    )
    assert result.error.code is ErrorCode.BUDGET_EXHAUSTED and not c[1].calls
    assert isinstance(
        c[4].record_action_requested(request(asset_id=None), recorded_at=WHEN), Success
    )
    duplicate = request(id="second")
    result = asyncio.run(
        c[0].execute(duplicate, policy=c[2], budgets=c[3], context=CONTEXT)
    )
    assert result.error.code is ErrorCode.PLANNER_VALIDATION_FAILED and not c[1].calls
    default = ActionPolicyValidator(c[2].registry, c[2].scope_validator)
    result = asyncio.run(
        c[0].execute(request(), policy=default, budgets=c[3], context=CONTEXT)
    )
    assert isinstance(result, Failure) and not c[1].calls


def test_unsupported_probe_platform_never_looks_up_binary(monkeypatch):
    monkeypatch.setattr("recon_agent.tools.nuclei.sys.platform", "unsupported")
    lookup = Mock(side_effect=AssertionError("must not probe"))
    monkeypatch.setattr("recon_agent.tools.nuclei.shutil.which", lookup)
    result = asyncio.run(NucleiAdapter.detect(ExecutionConfig()))
    assert result.error.code is ErrorCode.TOOL_UNAVAILABLE
    lookup.assert_not_called()


def test_bad_capture_instances_and_invalid_limits_fail_structurally():
    from recon_agent.tools.nuclei_parser import ingest as parse

    for limit in (0, -1, True, 1.0):
        result = parse(process(), context=CONTEXT, scope=scope(), output_limit=limit)
        assert result.error.code is ErrorCode.PARSE_FAILED
    bad = process().model_copy(update={"value": {"stdout": "not-a-process"}})
    assert (
        parse(bad, context=CONTEXT, scope=scope()).error.code is ErrorCode.PARSE_FAILED
    )


def test_parser_object_bounds():
    for raw in (
        wire(**{f"unused{i}": i for i in range(129)}),
        wire(info={f"unused{i}": i for i in range(65)}),
    ):
        output = ingest(process(raw)).value
        assert output.status == "failed" and output.malformed_lines == 1

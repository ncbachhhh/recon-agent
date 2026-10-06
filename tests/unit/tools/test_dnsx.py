"""DNSX offline fixtures: every denied batch stays upstream of process contact."""

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
from recon_agent.tools.dnsx import DnsxAdapter
from recon_agent.tools.dnsx_models import DnsxContext, DnsxOutput

WHEN = datetime(2026, 10, 6, tzinfo=UTC)
CONTEXT = DnsxContext(asset_id="asset", execution_id="execution", collected_at=WHEN)
FIXTURE = (Path(__file__).parents[2] / "fixtures/dnsx/verification.jsonl").read_bytes()


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
    adapter = DnsxAdapter("/trusted/dnsx", "192.0.2.53", config, fake)
    registry = ToolRegistry((AdapterRegistration(adapter, availability),))
    validator = ScopeValidator(
        scope
        or Scope(
            id="scope",
            allow_subdomains=True,
            roots=(
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
    policy = ActionPolicyValidator(
        registry,
        validator,
        ActionPolicyConfig(
            allowed_capabilities=frozenset({CapabilityId.VERIFY_DNS}),
            allowed_risk_classes=frozenset({RiskClass.ACTIVE_SAFE}),
        ),
        budgets,
        ActionDeduplicator(ActionCanonicalizer(registry, validator), state),
    )
    return adapter, fake, policy, budgets, state


def request(candidates=None, **changes):
    values = dict(
        id="action",
        capability="verify_dns",
        target="EXAMPLE.TEST.",
        parameters={
            "candidates": candidates
            if candidates is not None
            else ["www.example.test", "api.example.test"]
        },
        reason="Verify already discovered candidates",
    )
    values.update(changes)
    return ActionRequest(**values)


def execute(c, action=None, context=CONTEXT):
    return asyncio.run(
        c[0].execute(action or request(), policy=c[2], budgets=c[3], context=context)
    )


def wire(host="api.example.test.", records=None, **changes):
    values = dict(
        host=host,
        resolver=["192.0.2.53:53"],
        status_code="NOERROR",
        timestamp="2026-10-06T00:00:00Z",
        all=records
        if records is not None
        else ["api.example.test. 60 IN A 192.0.2.10"],
    )
    values.update(changes)
    return json.dumps(values).encode() + b"\n"


def test_trusted_argv_registry_scope_resources_and_provenance():
    c = compose()
    result = execute(c)
    assert isinstance(result, Success)
    output = result.value
    assert output.status == "completed" and output.candidates == (
        "api.example.test",
        "www.example.test",
    )
    spec = c[1].calls[0]
    assert spec.executable == "/trusted/dnsx"
    assert spec.args[:-1] == (
        "-auth",
        "false",
        "-silent",
        "-nc",
        "-duc",
        "-json",
        "-stream",
        "-t",
        "1",
        "-rl",
        "1",
        "-retry",
        "1",
        "-a",
        "-r",
        "udp:192.0.2.53:53",
        "-l",
    )
    assert c[1].inputs == ["api.example.test.\nwww.example.test.\n"]
    assert 0 < spec.timeout_seconds <= 30
    assert not Path(spec.args[-1]).exists()
    assert c[2].registry.resolve("verify_dns").value is c[0]
    assert c[2].registry.catalog()[0].risk_class is RiskClass.ACTIVE_SAFE
    assert set(c[2].registry.catalog()[0].model_dump()) == {
        "capability",
        "description",
        "risk_class",
        "availability",
    }
    assert c[0].definition.parameter_target_fields == ("candidates",)
    assert ToolRegistry().catalog() == ()
    assert all(
        query.wildcard_status == "suspected_shared_address" for query in output.queries
    )
    for item in output.observations:
        assert (
            item.kind == "dns"
            and item.source == "dnsx"
            and item.asset_id == CONTEXT.asset_id
        )
        assert item.execution_id == CONTEXT.execution_id and item.observed_at == WHEN
        assert item.evidence_ids == (output.evidence[0].id,)
        assert (
            item.data["capability"] == "verify_dns"
            and item.data["source_version"] == "1.2.2"
        )
        assert item.data["section"] == "unspecified"
    evidence = output.evidence[0]
    assert (
        evidence.capability == "verify_dns"
        and evidence.trust == "untrusted"
        and not evidence.truncated
    )
    assert (
        evidence.origin == "example.test"
        and evidence.execution_id == CONTEXT.execution_id
    )
    assert evidence.artifact_reference == "memory:execution"
    facts = output.model_dump(
        mode="json", exclude={"asset", "observations", "evidence", "errors"}
    )
    assert (
        evidence.sha256
        == sha256(
            json.dumps(facts, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
    )
    assert DnsxOutput.model_validate_json(output.model_dump_json()) == output
    assert c[3].state.permitted_actions == 1 and c[3].state.active_executions == 0
    assert dict(c[3].state.host_actions) == {
        "example.test": 1,
        "api.example.test": 1,
        "www.example.test": 1,
        "192.0.2.53": 1,
    }
    assert isinstance(c[2].scope_validator.validate_value("192.0.2.10"), Failure)


@pytest.mark.parametrize(
    "candidates",
    [
        ["api.example.test"],
        ["API.EXAMPLE.TEST.", "api.example.test", "api.example.test"],
    ],
)
def test_single_duplicate_canonical_candidates(candidates):
    c = compose(FakeRunner(process(wire())))
    result = execute(c, request(candidates))
    assert isinstance(result, Success) and result.value.status == "completed"
    assert c[1].inputs == ["api.example.test.\n"]
    assert result.value.queries[0].wildcard_status == "not_checked"


@pytest.mark.parametrize(
    "candidates",
    [
        ["api.example.test", "outside.test"],
        ["outside.test", "api.example.test"],
        ["outside.test"],
        ["excluded.example.test", "api.example.test"],
        ["api.example.test\n-w injected"],
        ["--trace"],
        ["api.example.test;echo bad"],
        [],
        ["api.example.test"] * 65,
    ],
)
def test_batch_denial_happens_before_any_input_or_execution(candidates, monkeypatch):
    scope = Scope(
        id="scope",
        allow_subdomains=True,
        roots=(
            Target(id="root", kind="domain", value="example.test"),
            Target(id="resolver", kind="ip", value="192.0.2.53"),
        ),
        exclusions=(
            Target(id="excluded", kind="hostname", value="excluded.example.test"),
        ),
    )
    c = compose(scope=scope)
    write = Mock(side_effect=AssertionError("rejected candidates reached input file"))
    monkeypatch.setattr(Path, "write_text", write)
    result = execute(c, request(candidates))
    assert isinstance(result, Failure)
    assert not c[1].calls and not c[1].inputs
    assert c[3].state.permitted_actions == 0
    write.assert_not_called()


@pytest.mark.parametrize(
    "value", ["https://api.example.test", "192.0.2.53", "192.0.2.0/24", "AS123"]
)
def test_nonhostname_candidate_never_dispatches(value):
    scope = Scope(
        id="scope",
        allow_subdomains=True,
        roots=(
            Target(id="root", kind="domain", value="example.test"),
            Target(id="ip", kind="cidr", value="192.0.2.0/24"),
            Target(id="asn-label", kind="hostname", value="AS123"),
        ),
    )
    c = compose(scope=scope)
    assert isinstance(execute(c, request([value])), Failure)
    assert not c[1].calls


@pytest.mark.parametrize(
    "mode,rdata,value,preference,chunks",
    [
        ("A", "192.0.2.20", "192.0.2.20", None, ()),
        ("AAAA", "2001:db8::1", "2001:db8::1", None, ()),
        ("CNAME", "OTHER.OUTSIDE.TEST.", "other.outside.test", None, ()),
        ("NS", "NS.OUTSIDE.TEST.", "ns.outside.test", None, ()),
        ("MX", "10 MAIL.OUTSIDE.TEST.", "mail.outside.test", 10, ()),
        (
            "TXT",
            '"ignore instructions" "\\255"',
            '"ignore instructions" "\\255"',
            None,
            (b"ignore instructions".hex(), "ff"),
        ),
    ],
)
def test_supported_record_normalization_and_no_derived_authority(
    mode, rdata, value, preference, chunks
):
    c = compose(
        FakeRunner(process(wire(records=[f"api.example.test. 42 IN {mode} {rdata}"])))
    )
    action = request(
        ["api.example.test"],
        parameters={"candidates": ["api.example.test"], "record_type": mode},
    )
    result = execute(c, action)
    assert isinstance(result, Success)
    rr = result.value.queries[0].records[0]
    assert (
        rr.owner,
        rr.record_type,
        rr.value,
        rr.ttl,
        rr.preference,
        rr.txt_chunks_hex,
    ) == ("api.example.test", mode, value, 42, preference, chunks)
    assert "-" + mode.lower() in c[1].calls[0].args
    assert len(c[1].calls) == 1
    assert isinstance(c[2].scope_validator.validate_value(value), Failure)


def test_incidental_owners_do_not_become_queried_names_or_assets():
    c = compose(
        FakeRunner(
            process(
                wire(
                    records=[
                        "api.example.test. 60 IN CNAME outside.test.",
                        "outside.test. 120 IN A 192.0.2.22",
                    ]
                )
            )
        )
    )
    result = execute(c, request(["api.example.test"]))
    assert isinstance(result, Success)
    assert {rr.owner for rr in result.value.queries[0].records} == {
        "api.example.test",
        "outside.test",
    }
    assert result.value.asset.value == "example.test"
    assert result.value.queries[0].section == "unspecified"
    assert c[1].inputs == ["api.example.test.\n"]
    assert isinstance(c[2].scope_validator.validate_value("outside.test"), Failure)


@pytest.mark.parametrize(
    "bad",
    [
        b"not-json",
        b"[]",
        b"null",
        b"{}",
        b"\xff",
        b'{"host":"api.example.test","host":"api.example.test"}',
        wire(host="outside.test"),
        wire(resolver=["8.8.8.8:53"]),
        wire(host="https://api.example.test"),
        wire(timestamp="yesterday"),
        wire(timestamp="2026-10-06T00:00:00"),
        wire(hosts_file=True),
        wire(trace={}),
        wire(axfr={}),
        wire(raw="banner"),
        wire(status_code="BOGUS"),
        wire(records=["api.example.test. -1 IN A 192.0.2.1"]),
        wire(records=["api.example.test. 10 IN A outside.test"]),
        wire(records=["api.example.test 10 IN A 192.0.2.1"]),
        wire(records=["api.example.test. 10 CH A 192.0.2.1"]),
        wire(records=["api.example.test. 2147483648 IN A 192.0.2.1"]),
    ],
)
def test_malformed_lines_preserve_valid_output_but_flag_partial(bad):
    c = compose(FakeRunner(process(bad + b"\n" + FIXTURE)))
    result = execute(c)
    assert isinstance(result, Success) and result.value.status == "partial"
    assert result.value.malformed_lines == 1 and len(result.value.queries) == 2
    assert result.value.errors[0].code == ErrorCode.PARSE_FAILED
    assert c[3].state.active_executions == 0
    only = compose(FakeRunner(process(bad)))
    assert execute(only).error.code == ErrorCode.PARSE_FAILED


@pytest.mark.parametrize("raw", [b"", b"\n \n"])
def test_empty_output_is_explicit_unreported_partial(raw):
    c = compose(FakeRunner(process(raw)))
    result = execute(c)
    assert isinstance(result, Success) and result.value.status == "partial"
    assert result.value.queries == () and result.value.observations == ()
    assert result.value.unreported_candidates == (
        "api.example.test",
        "www.example.test",
    )
    assert len(result.value.evidence) == 1 and result.value.errors


@pytest.mark.parametrize("status", ["NOERROR", "NXDOMAIN", "SERVFAIL", "REFUSED"])
def test_response_codes_and_missing_candidate_preserved(status):
    c = compose(FakeRunner(process(wire(records=[], status_code=status))))
    result = execute(c)
    assert isinstance(result, Success) and result.value.status == "partial"
    assert (
        result.value.queries[0].status_code == status
        and not result.value.queries[0].records
    )
    assert result.value.unreported_candidates == ("www.example.test",)


def test_order_duplicate_lines_and_snapshot_determinism():
    first = execute(compose()).value
    raw = b"\n".join(reversed(FIXTURE.splitlines())) + b"\n" + FIXTURE
    second = execute(
        compose(FakeRunner(process(raw))),
        request(["API.example.test.", "www.example.test", "api.example.test"]),
    ).value
    assert first == second


def test_conflicting_duplicate_is_not_selected_by_line_order():
    conflict = wire(records=["api.example.test. 60 IN A 192.0.2.99"])
    for raw in (FIXTURE + conflict, conflict + FIXTURE):
        result = execute(compose(FakeRunner(process(raw))))
        assert isinstance(result, Success) and result.value.status == "partial"
        assert tuple(q.query_target for q in result.value.queries) == (
            "www.example.test",
        )


@pytest.mark.parametrize(
    "result,code",
    [
        (process(return_code=7), ErrorCode.TOOL_EXECUTION_FAILED),
        (process(stdout_truncated=True), ErrorCode.PARSE_FAILED),
        (process(stderr_truncated=True), ErrorCode.PARSE_FAILED),
        (
            Failure(error=ToolTimeoutError("deadline").to_error_info()),
            ErrorCode.TOOL_TIMEOUT,
        ),
        (
            Failure(error=ToolUnavailableError("missing").to_error_info()),
            ErrorCode.TOOL_UNAVAILABLE,
        ),
    ],
)
def test_canonical_process_failures_and_cleanup(result, code):
    c = compose(FakeRunner(result))
    output = execute(c)
    assert isinstance(output, Failure) and output.error.code == code
    if code == ErrorCode.TOOL_EXECUTION_FAILED:
        assert output.error.context.exit_code == 7
    assert c[3].state.permitted_actions == 1 and c[3].state.active_executions == 0
    assert not Path(dict(c[1].calls[0].environment)["HOME"]).exists()


@pytest.mark.parametrize(
    "parameters",
    [
        {"candidates": ["api.example.test"], "record_type": "AXFR"},
        {"candidates": ["api.example.test"], "record_type": "-trace"},
        {"candidates": ["api.example.test"], "flags": ["-trace"]},
        {"candidates": ["api.example.test"], "resolver": "8.8.8.8"},
        {"candidates": ["api.example.test"], "shell": True},
        {"candidates": "api.example.test"},
        {},
    ],
)
def test_planner_input_cannot_supply_execution_options(parameters):
    c = compose()
    result = execute(c, request(parameters=parameters))
    assert isinstance(result, Failure) and not c[1].calls
    assert c[3].state.permitted_actions == 0


@pytest.mark.parametrize("reserved", ["argv", "executable", "command", "import_path"])
def test_reserved_domain_fields_reject_flags(reserved):
    with pytest.raises(ValidationError):
        request(parameters={"candidates": ["api.example.test"], reserved: "-trace"})


def test_discovery_does_not_authorize_verification():
    from recon_agent.tools.subfinder import _hosts

    assert _hosts(
        b'{"host":"excluded.example.test","input":"example.test","sources":["hackertarget"]}',
        "example.test",
    ) == ("excluded.example.test",)
    scope = Scope(
        id="scope",
        allow_subdomains=False,
        roots=(
            Target(id="root", kind="domain", value="example.test"),
            Target(id="resolver", kind="ip", value="192.0.2.53"),
        ),
    )
    c = compose(scope=scope)
    result = execute(c, request(["excluded.example.test"]))
    assert result.error.code == ErrorCode.SCOPE_REJECTED and not c[1].calls
    assert c[2].scope_validator.scope == scope


@pytest.mark.parametrize(
    "version", [b"Current Version: 1.2.2", b"Current Version: v1.2.2\n"]
)
def test_explicit_detection_supported_probe(version, monkeypatch):
    monkeypatch.setattr(
        "recon_agent.tools.dnsx.shutil.which", lambda binary: "/trusted/dnsx"
    )
    fake = FakeRunner(process(version))
    result = asyncio.run(
        DnsxAdapter.detect(ExecutionConfig(), nameserver="192.0.2.53", runner=fake)
    )
    assert isinstance(result, Success)
    assert fake.calls[0].args == ("-auth", "false", "-version", "-nc", "-duc")
    assert fake.calls[0].timeout_seconds == 5.0 and not fake.inputs
    assert not Path(dict(fake.calls[0].environment)["HOME"]).exists()


@pytest.mark.parametrize(
    "version",
    [
        b"1.2.2",
        b"Current Version: 1.2.1",
        b"Current Version: 1.3.0",
        b"Current Version: 1.2.2-dev",
        b"Current Version: 1.2.2\nCurrent Version: 1.2.2",
        b"\xff",
    ],
)
def test_detection_rejects_unknown_versions(version, monkeypatch):
    monkeypatch.setattr(
        "recon_agent.tools.dnsx.shutil.which", lambda binary: "/trusted/dnsx"
    )
    fake = FakeRunner(process(version))
    result = asyncio.run(
        DnsxAdapter.detect(ExecutionConfig(), nameserver="192.0.2.53", runner=fake)
    )
    assert result.error.code == ErrorCode.TOOL_UNAVAILABLE


def test_missing_binary_never_probes_or_installs(monkeypatch):
    monkeypatch.setattr("recon_agent.tools.dnsx.shutil.which", lambda binary: None)
    fake = FakeRunner()
    result = asyncio.run(
        DnsxAdapter.detect(ExecutionConfig(), nameserver="192.0.2.53", runner=fake)
    )
    assert result.error.code == ErrorCode.TOOL_UNAVAILABLE and not fake.calls


@pytest.mark.parametrize(
    "nameserver", ["resolver.test", "8.8.8.8:53", "2001:db8::53", "udp:192.0.2.53:53"]
)
def test_trusted_resolver_settings_are_numeric_ipv4_only(nameserver):
    with pytest.raises(ConfigurationError):
        DnsxAdapter("/trusted/dnsx", nameserver, ExecutionConfig(), FakeRunner())


def test_missing_resolver_authorization_denies_dispatch():
    c = compose(
        scope=Scope(
            id="scope",
            allow_subdomains=True,
            roots=(Target(id="root", kind="domain", value="example.test"),),
        )
    )
    assert execute(c).error.code == ErrorCode.SCOPE_REJECTED and not c[1].calls


def test_unavailable_registry_and_wrong_binding_deny():
    c = compose(availability=AdapterAvailability.UNAVAILABLE)
    assert execute(c).error.code == ErrorCode.TOOL_UNAVAILABLE and not c[1].calls
    c = compose()
    adapter = replace(c[0])
    result = asyncio.run(
        adapter.execute(request(), policy=c[2], budgets=c[3], context=CONTEXT)
    )
    assert result.error.code == ErrorCode.PLANNER_VALIDATION_FAILED and not c[1].calls


def test_action_rate_and_host_limits_are_shared_and_not_refunded():
    c = compose(limits=ExecutionBudget(max_actions_per_host=1))
    assert isinstance(execute(c), Success)
    assert execute(c, request(id="second")).error.code == ErrorCode.BUDGET_EXHAUSTED
    assert len(c[1].calls) == 1
    c = compose(limits=ExecutionBudget(capability_rate_actions=1))
    assert isinstance(execute(c), Success)
    assert execute(c, request(id="second")).error.code == ErrorCode.BUDGET_EXHAUSTED
    assert len(c[1].calls) == 1


def test_session_expiry_discards_process_facts():
    now = [0.0]
    c = compose(
        FakeRunner(mutate=lambda: now.__setitem__(0, 10000.0)), clock=lambda: now[0]
    )
    assert execute(c).error.code == ErrorCode.TOOL_TIMEOUT
    assert c[3].state.active_executions == 0


def test_cancellation_propagates_and_releases_temp_and_permit():
    class CancelRunner(FakeRunner):
        async def run(self, spec):
            await super().run(spec)
            raise asyncio.CancelledError

    c = compose(CancelRunner())
    with pytest.raises(asyncio.CancelledError):
        execute(c)
    assert c[3].state.active_executions == 0 and c[3].state.permitted_actions == 1
    assert not Path(dict(c[1].calls[0].environment)["HOME"]).exists()


def test_parser_and_normalized_output_bounds():
    for raw in (
        FIXTURE + b"\n" * 257,
        wire(records=["api.example.test. 60 IN A 192.0.2.1"] * 257),
        b"x" * 65537,
    ):
        c = compose(FakeRunner(process(raw)))
        assert execute(c).error.code == ErrorCode.PARSE_FAILED
    c = compose(
        FakeRunner(process(wire())), config=ExecutionConfig(max_output_bytes=512)
    )
    assert (
        execute(c, request(["api.example.test"])).error.code == ErrorCode.PARSE_FAILED
    )


def test_config_environment_isolation_and_inert_default_runner(monkeypatch):
    for key in (
        "DNSX_CONFIG",
        "GROQ_API_KEY",
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "PDCP_API_KEY",
    ):
        monkeypatch.setenv(key, "untrusted")
    c = compose()
    assert isinstance(execute(c), Success)
    assert all(
        os.environ.get(key) == "untrusted"
        for key in (
            "DNSX_CONFIG",
            "GROQ_API_KEY",
            "HTTP_PROXY",
            "HTTPS_PROXY",
            "PDCP_API_KEY",
        )
    )
    adapter = DnsxAdapter("/trusted/dnsx", "192.0.2.53", ExecutionConfig())
    assert adapter.runner is not None
    assert "trusted" not in repr(adapter) and "192.0.2.53" not in repr(adapter)


def test_conflicting_duplicate_counts_are_order_independent():
    from itertools import permutations

    records = (wire(), wire(), wire(records=["api.example.test. 60 IN A 192.0.2.99"]))
    outputs = [
        execute(
            compose(
                FakeRunner(process(b"".join(order) + FIXTURE.splitlines()[0] + b"\n"))
            )
        ).value
        for order in permutations(records)
    ]
    assert all(output == outputs[0] for output in outputs)
    assert outputs[0].malformed_lines == 3

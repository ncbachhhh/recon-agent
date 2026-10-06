"""Naabu offline fixtures: every denied batch stays upstream of process contact."""

import asyncio
import json
import os
import socket
import subprocess
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
from recon_agent.tools.naabu import NaabuAdapter
from recon_agent.tools.naabu_models import (
    ContactBinding,
    NaabuContext,
    NaabuSettings,
    PortDiscoveryOutput,
)

WHEN = datetime(2026, 10, 6, tzinfo=UTC)
CONTEXT = NaabuContext(asset_id="asset", execution_id="execution", collected_at=WHEN)
FIXTURE = (Path(__file__).parents[2] / "fixtures/naabu/ports.jsonl").read_bytes()


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
    settings=None,
):
    config = config or ExecutionConfig()
    fake = fake or FakeRunner()
    adapter = NaabuAdapter(
        "/trusted/naabu",
        config,
        settings
        if settings is not None
        else NaabuSettings(
            bindings=(
                ContactBinding(hostname="example.test", addresses=("192.0.2.10",)),
                ContactBinding(hostname="api.example.test", addresses=("192.0.2.10",)),
                ContactBinding(
                    hostname="www.example.test", addresses=("2001:db8::10",)
                ),
            )
        ),
        fake,
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
            allowed_capabilities=frozenset({CapabilityId.DISCOVER_PORTS}),
            allowed_risk_classes=frozenset({RiskClass.ACTIVE_SAFE}),
        ),
        budgets,
        ActionDeduplicator(ActionCanonicalizer(registry, validator), state),
    )
    return adapter, fake, policy, budgets, state


def request(candidates=None, **changes):
    values = dict(
        id="action",
        capability="discover_ports",
        target="EXAMPLE.TEST.",
        parameters={
            "candidates": candidates
            if candidates is not None
            else [
                "api.example.test",
                "www.example.test",
            ]
        },
        reason="Discover authorized TCP ports",
    )
    values.update(changes)
    return ActionRequest(**values)


def execute(c, action=None, context=CONTEXT):
    return asyncio.run(
        c[0].execute(action or request(), policy=c[2], budgets=c[3], context=context)
    )


def wire(ip="192.0.2.10", port=80, **changes):
    values = dict(ip=ip, port=port, protocol="tcp", tls=False)
    values.update(changes)
    return json.dumps(values).encode() + b"\n"


def test_registry_trusted_argv_and_generic_provenance():
    c = compose()
    result = execute(c)
    assert isinstance(result, Success)
    output = result.value
    assert output.status == "completed" and len(output.services) == 3
    assert len(output.hosts) == 2 and len(output.observations) == 3
    assert output.ports == (80, 443)
    assert c[2].registry.resolve("discover_ports").value is c[0]
    assert c[0].definition.parameter_target_fields == ("candidates",)
    spec = c[1].calls[0]
    assert spec.executable == "/trusted/naabu"
    assert spec.args[:-1] == (
        "-config",
        os.devnull,
        "-auth",
        "false",
        "-silent",
        "-nc",
        "-duc",
        "-json",
        "-stream",
        "-no-stdin",
        "-s",
        "c",
        "-Pn",
        "-iv",
        "4,6",
        "-c",
        "1",
        "-rate",
        "1",
        "-retries",
        "1",
        "-timeout",
        "1s",
        "-warm-up-time",
        "0",
        "-p",
        "80,443",
        "-l",
    )
    assert c[1].inputs == ["192.0.2.10\n2001:db8::10\n"]
    assert spec.timeout_seconds <= c[0].config.default_timeout_seconds
    assert not Path(spec.args[-1]).exists()
    evidence = output.evidence[0]
    assert evidence.source == "naabu" and evidence.capability == "discover_ports"
    assert evidence.execution_id == CONTEXT.execution_id
    assert evidence.trust == "untrusted" and evidence.origin == "example.test"
    assert evidence.collected_at == WHEN and len(evidence.sha256) == 64
    for i, service in enumerate(output.services):
        assert service.transport == "tcp" and service.protocol is None
        assert service.product is None and service.version is None
        assert service.asset_id == CONTEXT.asset_id
        assert service.host_id in {h.id for h in output.hosts}
        observation = output.observations[i]
        assert service.observation_ids == (observation.id,)
        assert observation.source == "naabu" and observation.kind == "service"
        assert observation.data["port"] == service.port
        assert observation.data["source_version"] == "2.3.5"
        assert observation.evidence_ids == (evidence.id,)
        assert observation.observed_at == WHEN
    assert PortDiscoveryOutput.model_validate_json(output.model_dump_json()) == output
    assert c[3].state.active_executions == 0 and c[3].state.permitted_actions == 1


@pytest.mark.parametrize(
    "target,ip",
    [
        ("EXAMPLE.TEST.", "192.0.2.10"),
        ("192.0.2.10", "192.0.2.10"),
        ("2001:DB8::10", "2001:db8::10"),
    ],
)
def test_authorized_hostname_and_ip(target, ip):
    c = compose(FakeRunner(process(wire(ip))))
    result = execute(c, request(target=target, parameters={}))
    assert isinstance(result, Success) and result.value.status == "completed"
    assert c[1].inputs == [ip + "\n"]
    assert result.value.services[0].port == 80


@pytest.mark.parametrize(
    "candidates",
    [
        ["api.example.test", "outside.test"],
        ["outside.test", "api.example.test"],
        ["outside.test"],
        ["192.0.2.10", "192.0.2.11"],
        ["api.example.test", "api.example.test\n-rate 999"],
    ],
)
def test_mixed_batch_never_creates_input_or_executes(candidates, monkeypatch):
    create = Mock(side_effect=AssertionError("denied batch reached temp creation"))
    monkeypatch.setattr("recon_agent.tools.naabu.TemporaryDirectory", create)
    c = compose()
    result = execute(c, request(candidates=candidates))
    assert isinstance(result, Failure)
    assert c[1].calls == c[1].inputs == [] and c[3].state.permitted_actions == 0
    create.assert_not_called()


@pytest.mark.parametrize(
    "target",
    [
        "outside.test",
        "192.0.2.11",
        "-host example.test",
        "example.test; id",
        "https://example.test/",
        "192.0.2.0/24",
    ],
)
def test_unsupported_and_outside_primary_denies(target):
    c = compose()
    assert isinstance(execute(c, request(target=target)), Failure)
    assert not c[1].calls


@pytest.mark.parametrize(
    "field",
    [
        "extra_args",
        "raw_ports",
        "command",
        "rate_override",
        "interface",
        "source_ip",
        "proxy",
        "ports",
        "port_ranges",
        "port_profile",
        "executable",
        "scan_type",
        "nmap",
        "service_version",
        "rate",
        "bindings",
    ],
)
def test_planner_cannot_inject_flags_or_limits(field):
    c = compose()
    result = execute(
        c,
        request(reason="override policy", priority=100).model_copy(
            update={"parameters": {field: "-p 1-65535", "candidates": []}}
        ),
    )
    assert result.error.code == ErrorCode.PLANNER_VALIDATION_FAILED
    assert not c[1].calls and c[3].state.permitted_actions == 0


@pytest.mark.parametrize(
    "parameters",
    [
        {"candidates": ["api.example.test"] * 65},
        {"candidates": "api.example.test"},
        {"candidates": [1]},
        {"candidates": [""]},
        {"candidates": ["a" * 255]},
    ],
)
def test_typed_batch_bounds(parameters):
    c = compose()
    assert isinstance(execute(c, request(parameters=parameters)), Failure)
    assert not c[1].calls


@pytest.mark.parametrize(
    "ranges",
    [
        (),
        ((0, 80),),
        ((80, 65536),),
        ((443, 80),),
        ((1, 65535),),
        ((1, 129),),
        ((1, 128), (200, 200)),
        ((True, 80),),
        (("80", 80),),
        ((80.0, 80),),
        ((80, 80),) * 17,
        [(80, 80)],
    ],
)
def test_operator_port_ranges_reject_invalid_excessive(ranges):
    with pytest.raises(ValidationError):
        NaabuSettings(port_ranges=ranges)


@pytest.mark.parametrize(
    "ranges,expected",
    [
        (((1, 1), (65535, 65535)), (1, 65535)),
        (((80, 82), (81, 83)), (80, 81, 82, 83)),
        (((1, 128),), tuple(range(1, 129))),
    ],
)
def test_operator_ranges_canonicalize_and_bound_argv(ranges, expected):
    settings = NaabuSettings(port_ranges=ranges)
    c = compose(FakeRunner(process(wire(port=expected[0]))), settings=settings)
    out = execute(c, request(target="192.0.2.10", parameters={}))
    assert isinstance(out, Success) and out.value.ports == expected
    args = c[1].calls[0].args
    assert args[args.index("-p") + 1] == ",".join(str(p) for p in expected)


@pytest.mark.parametrize(
    "raw",
    [
        b"invalid\n",
        b"\xff",
        b"[]\n",
        b"null\n",
        b"{}\n",
        wire(port=0),
        wire(port=-1),
        wire(port=65536),
        wire(port=True),
        wire(port="80"),
        wire(port=80.0),
        wire(port=22),
        wire(protocol="udp"),
        wire(tls=True),
        wire(ip="outside.test"),
        wire(ip="192.0.2.11"),
        wire(host="outside.test"),
        wire(ip="2001:DB8::10"),
        b'{"ip":"192.0.2.10","port":80,"port":443,"protocol":"tcp"}\n',
        b'{"ip":"192.0.2.10","port":',
        b"[" * 2000,
    ],
)
def test_malformed_unrequested_records_fail(raw):
    c = compose(FakeRunner(process(raw)))
    out = execute(c)
    assert out.error.code == ErrorCode.PARSE_FAILED
    assert c[3].state.active_executions == 0


def test_partial_preserves_valid_and_empty_invents_no_closed_ports():
    c = compose(FakeRunner(process(wire() + b'{"ip":')))
    output = execute(c).value
    assert output.status == "partial" and output.malformed_lines == 1
    assert len(output.services) == 1 and output.errors[0].code == ErrorCode.PARSE_FAILED
    empty = execute(compose(FakeRunner(process(b"\n \n")))).value
    assert empty.status == "completed" and empty.malformed_lines == 0
    assert empty.hosts == empty.services == empty.observations == ()
    assert len(empty.evidence) == 1


def test_deduplication_order_hash_and_inputs_are_deterministic():
    raws = [wire() + wire(port=443) + wire(), wire(port=443) + wire()]
    outputs = [
        execute(
            compose(FakeRunner(process(raw))),
            request(candidates=["API.EXAMPLE.TEST.", "api.example.test", "192.0.2.10"]),
        )
        for raw in raws
    ]
    assert outputs[0].value == outputs[1].value
    assert len(outputs[0].value.services) == 2


def test_no_implicit_address_authorization_and_missing_binding():
    name_only = Scope(
        id="s",
        allow_subdomains=True,
        roots=(Target(id="root", kind="domain", value="example.test"),),
    )
    c = compose(scope=name_only)
    assert execute(c).error.code == ErrorCode.SCOPE_REJECTED
    assert not c[1].calls and c[3].state.permitted_actions == 0
    c = compose(settings=NaabuSettings())
    assert execute(c).error.code == ErrorCode.PLANNER_VALIDATION_FAILED
    assert not c[1].calls


def test_exclusion_wins_for_bound_address():
    scope = compose()[2].scope_validator.scope.model_copy(
        update={"exclusions": (Target(id="exclude", kind="ip", value="192.0.2.10"),)}
    )
    c = compose(scope=scope)
    assert execute(c).error.code == ErrorCode.SCOPE_REJECTED and not c[1].calls


def test_aggregate_probe_and_contact_limits_deny():
    addresses = tuple(f"192.0.2.{i}" for i in range(1, 34))
    scope = Scope(
        id="s",
        roots=(
            Target(id="name", kind="hostname", value="example.test"),
            Target(id="range", kind="cidr", value="192.0.2.0/24"),
        ),
    )
    settings = NaabuSettings(
        port_ranges=((1, 128),),
        bindings=(ContactBinding(hostname="example.test", addresses=addresses),),
    )
    c = compose(settings=settings, scope=scope)
    assert (
        execute(c, request(parameters={})).error.code
        == ErrorCode.PLANNER_VALIDATION_FAILED
    )
    assert not c[1].calls and c[3].state.permitted_actions == 0
    settings = NaabuSettings(
        bindings=(
            ContactBinding(hostname="example.test", addresses=addresses),
            ContactBinding(
                hostname="api.example.test",
                addresses=tuple(f"192.0.2.{i}" for i in range(34, 67)),
            ),
        )
    )
    scope = scope.model_copy(
        update={
            "roots": (
                *scope.roots,
                Target(id="api", kind="hostname", value="api.example.test"),
            )
        }
    )
    c = compose(settings=settings, scope=scope)
    assert (
        execute(c, request(candidates=["example.test", "api.example.test"])).error.code
        == ErrorCode.PLANNER_VALIDATION_FAILED
    )
    assert not c[1].calls


@pytest.mark.parametrize(
    "binding",
    [
        ContactBinding(hostname="EXAMPLE.TEST", addresses=("192.0.2.10",)),
        ContactBinding(hostname="example.test.", addresses=("192.0.2.10",)),
        ContactBinding(hostname="example.test", addresses=("outside.test",)),
        ContactBinding(hostname="example.test", addresses=("2001:DB8::10",)),
        ContactBinding(hostname="example.test", addresses=("fe80::1%eth0",)),
    ],
)
def test_invalid_trusted_bindings(binding):
    with pytest.raises(ConfigurationError):
        compose(settings=NaabuSettings(bindings=(binding,)))


def test_absolute_executable_and_duplicate_bindings_required():
    with pytest.raises(ConfigurationError):
        NaabuAdapter("naabu", ExecutionConfig())
    with pytest.raises(ValidationError):
        NaabuSettings(
            bindings=(
                ContactBinding(hostname="example.test", addresses=("192.0.2.10",)),
            )
            * 2
        )


@pytest.mark.parametrize("raw", [wire() * 8193, b" " * 4097 + b"{}\n"])
def test_parser_line_limits(raw):
    assert (
        execute(compose(FakeRunner(process(raw)))).error.code == ErrorCode.PARSE_FAILED
    )


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


@pytest.mark.parametrize(
    "version", ["2.3.5", "1.7.1", "2.3.6", "", "2.3.5\nCurrent Version: 2.3.5"]
)
def test_availability_reviewed_version_only(version, monkeypatch):
    monkeypatch.setattr(
        "recon_agent.tools.naabu.shutil.which", lambda _: "/trusted/naabu"
    )
    runner = FakeRunner(
        process(b"", stderr=f"[INF] Current Version: {version}\n".encode())
    )
    result = asyncio.run(
        NaabuAdapter.detect(
            ExecutionConfig(),
            runner=runner,
        )
    )
    assert isinstance(result, Success if version == "2.3.5" else Failure)
    assert runner.inputs == [] and "-version" in runner.calls[0].args
    assert not Path(dict(runner.calls[0].environment)["HOME"]).exists()


def test_missing_binary_no_install_or_process(monkeypatch):
    monkeypatch.setattr("recon_agent.tools.naabu.shutil.which", lambda _: None)
    fake = FakeRunner()
    result = asyncio.run(
        NaabuAdapter.detect(
            ExecutionConfig(),
            runner=fake,
        )
    )
    assert (
        isinstance(result, Failure) and result.error.code == ErrorCode.TOOL_UNAVAILABLE
    )
    assert fake.calls == []


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
        execute(c, request(capability="probe_http")).error.code
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
        } == dict(c[3].state.host_actions).keys()


def test_session_expiry_during_runner_discards_facts():
    now = [0.0]
    c = compose(
        FakeRunner(mutate=lambda: now.__setitem__(0, 10000.0)), clock=lambda: now[0]
    )
    assert execute(c).error.code == ErrorCode.TOOL_TIMEOUT
    assert c[3].state.active_executions == 0


def test_normalized_output_bound():
    raw = wire()
    # Captured bytes fit, but the provenance-rich envelope exceeds this allowance.
    c = compose(FakeRunner(process(raw)), config=ExecutionConfig(max_output_bytes=1024))
    assert len(raw) < 1024
    assert (
        execute(c, request(candidates=["api.example.test"])).error.code
        == ErrorCode.PARSE_FAILED
    )


def test_temp_setup_failure_is_canonical(monkeypatch):
    monkeypatch.setattr(
        "recon_agent.tools.naabu.TemporaryDirectory", Mock(side_effect=OSError("local"))
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
        "recon_agent.tools.naabu.shutil.which", lambda _: "/trusted/naabu"
    )
    result = asyncio.run(
        NaabuAdapter.detect(
            ExecutionConfig(),
            runner=FakeRunner(result),
        )
    )
    assert isinstance(result, Failure) and result.error.code == code


def test_concurrent_attempt_rejects_before_second_dispatch():
    c = compose()
    approval = c[2].validate(request())
    held = c[3].reserve(approval.value).value
    with held:
        assert execute(c, request(id="second")).error.code == ErrorCode.BUDGET_EXHAUSTED
        assert not c[1].calls
    assert c[3].state.active_executions == 0


def test_smaller_budget_capture_and_different_controller_reject_composition():
    from dataclasses import replace

    c = compose(limits=ExecutionBudget(max_output_bytes=1024))
    assert execute(c).error.code == ErrorCode.PLANNER_VALIDATION_FAILED
    assert not c[1].calls
    c = compose()
    policy = replace(
        c[2], budget_eligibility=BudgetController(ExecutionBudget(), c[2].registry)
    )
    out = asyncio.run(
        c[0].execute(request(), policy=policy, budgets=c[3], context=CONTEXT)
    )
    assert out.error.code == ErrorCode.PLANNER_VALIDATION_FAILED and not c[1].calls


def test_generic_facts_ingest_with_host_service_lineage():
    c = compose()
    output = execute(c).value
    recorded = c[4].record_facts(
        assets=(output.asset,),
        hosts=output.hosts,
        services=output.services,
        observations=output.observations,
        evidence=output.evidence,
    )
    assert isinstance(recorded, Success)
    assert c[4].state.services == output.services


def test_final_scope_recheck_rejects_before_input_write(monkeypatch):
    from recon_agent.core.errors import ScopeRejectedError

    c = compose()
    original = ScopeValidator.validate_value
    calls = [0]

    def changed(self, value):
        calls[0] += 1
        if calls[0] == 4:  # primary + two members checked by policy
            return Failure(error=ScopeRejectedError("scope changed").to_error_info())
        return original(self, value)

    monkeypatch.setattr(ScopeValidator, "validate_value", changed)
    write = Mock(side_effect=AssertionError("scope rejection reached input write"))
    monkeypatch.setattr(Path, "write_text", write)
    assert execute(c).error.code == ErrorCode.SCOPE_REJECTED
    assert not c[1].calls and c[3].state.active_executions == 0
    write.assert_not_called()


def test_timeout_clamps_to_remaining_session_and_ambient_env_excluded(monkeypatch):
    monkeypatch.setenv("NAABU_CONFIG", "untrusted.yaml")
    monkeypatch.setenv("HTTPS_PROXY", "http://outside.test")
    monkeypatch.setenv("GROQ_API_KEY", "test-only-secret")
    now = [0.0]
    c = compose(limits=ExecutionBudget(max_duration_seconds=5.0), clock=lambda: now[0])
    now[0] = 4.0
    assert isinstance(execute(c), Success)
    assert c[1].calls[0].timeout_seconds == 1.0
    assert (
        not {"NAABU_CONFIG", "HTTPS_PROXY", "GROQ_API_KEY"}
        & dict(c[1].calls[0].environment).keys()
    )


@pytest.mark.parametrize("binary", ["", " ", "naabu\x00x", 1])
def test_invalid_detection_binary_setting(binary):
    with pytest.raises(ConfigurationError):
        asyncio.run(
            NaabuAdapter.detect(ExecutionConfig(), binary=binary, runner=FakeRunner())
        )


def test_operator_settings_detach_nested_constructed_models():
    binding = ContactBinding(hostname="example.test", addresses=("192.0.2.10",))
    settings = NaabuSettings(bindings=(binding,))
    c = compose(FakeRunner(process(wire())), settings=settings)
    object.__setattr__(binding, "addresses", ("192.0.2.11",))
    assert c[0].settings.bindings[0].addresses == ("192.0.2.10",)
    assert isinstance(execute(c, request(parameters={})), Success)

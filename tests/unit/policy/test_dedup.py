"""Offline semantic identity, lifecycle/retry eligibility and atomic admission."""

import asyncio
import importlib
import logging
import socket
import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from threading import Barrier
from unittest.mock import Mock

import pytest
from pydantic import BaseModel, ConfigDict, Field, JsonValue, ValidationError

from recon_agent.core.errors import (
    CancelledError,
    ErrorCode,
    PlannerValidationError,
    ToolExecutionError,
    ToolTimeoutError,
)
from recon_agent.core.results import Failure, Success
from recon_agent.domain import (
    ActionDedupDecision,
    ActionIdentity,
    ActionPhase,
    ActionRequest,
    ActionResult,
    DedupReason,
    PlannerDecision,
    ReconState,
    ReconStateMachine,
    Scope,
    Target,
)
from recon_agent.domain.capabilities import (
    CapabilityDescriptor,
    CapabilityId,
    RiskClass,
)
from recon_agent.execution import AsyncProcessRunner
from recon_agent.policy import (
    ActionCanonicalizer,
    ActionDedupConfig,
    ActionDeduplicator,
    ActionPolicyConfig,
    ActionPolicyValidator,
    BudgetController,
    ExecutionBudget,
    ScopeValidator,
)
from recon_agent.tools import (
    AdapterAvailability,
    AdapterDefinition,
    AdapterRegistration,
    ToolAdapter,
    ToolRegistry,
)

WHEN = datetime(2026, 10, 5, tzinfo=UTC)


class Parameters(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", validate_default=True)
    count: int = 1
    options: dict[str, JsonValue] = Field(default_factory=dict)
    peer: str = "example.test"
    peers: list[str] = Field(default_factory=list)


class FixtureAdapter(ToolAdapter):
    def __init__(self, capability, schema=Parameters, fields=("peer", "peers")):
        self._definition = AdapterDefinition(
            adapter_id=f"fixture-{capability}",
            descriptor=CapabilityDescriptor(
                capability=capability,
                description="Offline fixture",
                risk_class=RiskClass.PASSIVE,
            ),
            input_schema=schema,
            output_schema=Parameters,
            parameter_target_fields=fields,
        )

    @property
    def definition(self):
        return self._definition


@pytest.fixture(autouse=True)
def inert(monkeypatch):
    forbidden = Mock(side_effect=AssertionError("dedup must remain inert"))
    for name in (
        "socket",
        "getaddrinfo",
        "gethostbyname",
        "gethostbyname_ex",
        "gethostbyaddr",
        "getnameinfo",
        "create_connection",
    ):
        monkeypatch.setattr(socket, name, forbidden)
    for name in ("run", "Popen", "call", "check_call", "check_output"):
        monkeypatch.setattr(subprocess, name, forbidden)
    for name in ("create_subprocess_exec", "create_subprocess_shell"):
        monkeypatch.setattr(asyncio, name, forbidden)
    monkeypatch.setattr(AsyncProcessRunner, "run", forbidden)
    monkeypatch.setattr(ToolRegistry, "resolve", forbidden)
    monkeypatch.setattr(importlib, "import_module", forbidden)
    monkeypatch.setattr(logging, "basicConfig", forbidden)
    yield forbidden
    forbidden.assert_not_called()


def action(**changes):
    return ActionRequest(
        **{
            "id": "action",
            "capability": "probe_http",
            "target": "example.test",
            "parameters": {},
            "reason": "Inspect web",
            **changes,
        }
    )


def canonicalizer(
    schema=Parameters,
    fields=("peer", "peers"),
    availability=AdapterAvailability.AVAILABLE,
):
    registry = ToolRegistry(
        tuple(
            AdapterRegistration(FixtureAdapter(cap, schema, fields), availability)
            for cap in (CapabilityId.PROBE_HTTP, CapabilityId.RESOLVE_DNS)
        )
    )
    scope = ScopeValidator(
        Scope(
            id="scope",
            roots=(
                Target(id="root", kind="domain", value="example.test"),
                Target(id="other", kind="domain", value="other.test"),
                Target(id="v4", kind="cidr", value="192.0.2.0/24"),
                Target(id="v6", kind="cidr", value="2001:db8::/32"),
            ),
            allow_subdomains=True,
        )
    )
    return ActionCanonicalizer(registry, scope)


def dedup(retries=0, owner=None, **changes):
    return ActionDeduplicator(
        canonicalizer(**changes),
        owner or ReconStateMachine(),
        ActionDedupConfig(max_failed_retries=retries),
    )


def value(result):
    assert isinstance(result, Success), result
    return result.value


def deny(result, code=ErrorCode.PLANNER_VALIDATION_FAILED):
    assert isinstance(result, Failure), result
    assert result.error.code is code
    assert not result.error.retryable
    assert "secret-fixture" not in result.model_dump_json()
    return result


def record_phase(service, phase, *, request=None, retryable=False):
    request = request or action()
    owner = service.state_machine
    value(service.record_request(request, recorded_at=WHEN))
    if phase is ActionPhase.REQUESTED:
        return
    if phase in (ActionPhase.REJECTED, ActionPhase.CANCELLED):
        error = (
            PlannerValidationError("Denied")
            if phase is ActionPhase.REJECTED
            else CancelledError("Cancelled")
        )
        execution_ids = ()
    else:
        value(
            owner.mark_action_approved(
                request.id, policy_reference="local-policy", recorded_at=WHEN
            )
        )
        if phase is ActionPhase.APPROVED:
            return
        execution_id = f"execution-{request.id}"
        value(
            owner.mark_action_started(
                request.id, execution_id=execution_id, recorded_at=WHEN
            )
        )
        if phase is ActionPhase.STARTED:
            return
        execution_ids = (execution_id,)
        error = (
            ToolTimeoutError("Timed out", retryable=retryable)
            if phase is ActionPhase.TIMEOUT
            else ToolExecutionError("Failed", retryable=retryable)
        )
    value(
        owner.record_action_result(
            ActionResult(
                id=f"result-{request.id}",
                action_id=request.id,
                status=phase.value,
                recorded_at=WHEN,
                execution_ids=execution_ids,
                error=None if phase is ActionPhase.COMPLETED else error.to_error_info(),
            )
        )
    )


@pytest.mark.parametrize(
    "changes",
    [
        {},
        {"id": "new"},
        {"reason": "Check HTTP"},
        {"priority": 999},
        {"target": "EXAMPLE.TEST."},
        {
            "parameters": {
                "count": 1,
                "peer": "EXAMPLE.test.",
                "peers": [],
                "options": {},
            }
        },
    ],
)
def test_equivalent_planner_requests(changes):
    service = dedup()
    value(service.record_request(action(), recorded_at=WHEN))
    before = service.state_machine.state.model_dump_json()
    candidate = action(**changes)
    original = candidate.model_dump_json()
    decision = value(service.inspect(candidate))
    assert decision.duplicate and not decision.eligible
    assert decision.reason is DedupReason.IN_FLIGHT
    assert decision.matching_action_ids == ("action",)
    deny(service.record_request(candidate, recorded_at=WHEN))
    assert service.state_machine.state.model_dump_json() == before
    assert candidate.model_dump_json() == original


def test_regression_repeated_planner_cosmetics_do_not_enqueue_or_authorize():
    service = dedup()
    value(service.record_request(action(), recorded_at=WHEN))
    for number in range(12):
        recommendation = action(
            id=f"repeat-{number}",
            priority=number,
            reason=f"New reason {number}",
            decision_id=f"decision-{number}",
        )
        decision = PlannerDecision(
            id=f"decision-{number}",
            analysis_summary=f"New analysis {number}",
            created_at=WHEN,
            actions=(recommendation,),
        )
        value(service.state_machine.record_planner_decision(decision))
        deny(service.record_request(recommendation, recorded_at=WHEN))
        deny(service.check(recommendation))
    assert len(service.state_machine.state.action_requests) == 1
    assert service.state_machine.state.action_results == ()


@pytest.mark.parametrize(
    "left,right",
    [
        (
            {"b": [None, True, 1, 1.5], "a": {"z": "x", "c": ["y"]}},
            {"a": {"c": ["y"], "z": "x"}, "b": [None, True, 1, 1.5]},
        ),
        (
            {"a:b": "c", "d": {"x": [1, {"z": 0, "a": "雪"}]}},
            {"d": {"x": [1, {"a": "雪", "z": 0}]}, "a:b": "c"},
        ),
    ],
)
def test_nested_parameter_order_and_serialization(left, right):
    service = dedup()
    first = action(parameters={"options": left})
    second = action(id="other", reason="Other prose", parameters={"options": right})
    identity = value(service.canonicalizer.identify(first))
    assert value(service.canonicalizer.identify(second)) == identity
    assert ActionIdentity.model_validate(identity.model_dump()) == identity
    assert (
        ActionIdentity.model_validate_json(identity.model_dump_json()).key
        == identity.key
    )
    value(service.record_request(first, recorded_at=WHEN))
    decision = value(service.inspect(second))
    assert decision.duplicate
    assert (
        ActionDedupDecision.model_validate_json(decision.model_dump_json()) == decision
    )
    restored = ReconStateMachine(
        ReconState.model_validate_json(service.state_machine.state.model_dump_json())
    )
    assert value(dedup(owner=restored).inspect(second)) == decision


@pytest.mark.parametrize(
    "left,right",
    [
        (True, 1),
        (1, 1.0),
        (1, "1"),
        (None, "null"),
        ({"x": 1}, [["x", 1]]),
        ([1, 2], [2, 1]),
        ({"a": "b:c"}, {"a:b": "c"}),
        ("é", "e\u0301"),
    ],
)
def test_meaningful_json_types_order_and_text_remain_distinct(left, right):
    service = dedup()
    first = action(parameters={"options": {"x": left}})
    second = action(id="new", parameters={"options": {"x": right}})
    assert (
        value(service.canonicalizer.identify(first)).key
        != value(service.canonicalizer.identify(second)).key
    )
    value(service.record_request(first, recorded_at=WHEN))
    decision = value(service.inspect(second))
    assert not decision.duplicate and decision.eligible


@pytest.mark.parametrize(
    "changes",
    [
        {"capability": "resolve_dns"},
        {"target": "other.test"},
        {"parameters": {"count": 2}},
        {"parameters": {"peer": "other.test"}},
        {"parameters": {"peers": ["example.test"]}},
        {"parameters": {"options": {"reason": "Execution-relevant named field"}}},
    ],
)
def test_meaningful_action_changes_remain_new(changes):
    service = dedup()
    value(service.record_request(action(), recorded_at=WHEN))
    assert value(service.inspect(action(id="new", **changes))).reason is DedupReason.NEW


@pytest.mark.parametrize(
    "left,right",
    [
        ("EXAMPLE.TEST.", "example.test"),
        ("HTTPS://EXAMPLE.test.:00443/a?q=X#f", "https://example.test:443/a?q=X#f"),
        ("2001:0DB8:0:0:0:0:0:1", "2001:db8::1"),
        ("2001:0db8:0:0::/032", "2001:db8::/32"),
        ("https://[2001:0DB8::1]:00443/a", "https://[2001:db8::1]:443/a"),
        ("https://example.test", "https://EXAMPLE.test:443/"),
        ("https://example.test/#a", "https://example.test/#b"),
    ],
)
def test_established_primary_and_secondary_target_equivalents(left, right):
    service = dedup()
    first = action(target=left, parameters={"peer": left, "peers": [left]})
    second = action(
        id="other", target=right, parameters={"peer": right, "peers": [right]}
    )
    value(service.record_request(first, recorded_at=WHEN))
    assert value(service.inspect(second)).duplicate


@pytest.mark.parametrize(
    "left,right",
    [
        ("example.test", "https://example.test"),
        ("https://example.test/A", "https://example.test/a"),
        ("https://example.test/?a=1&b=2", "https://example.test/?b=2&a=1"),
        ("https://example.test/", "https://example.test/?"),
    ],
)
def test_no_extra_url_or_host_semantic_merging(left, right):
    service = dedup()
    value(service.record_request(action(target=left), recorded_at=WHEN))
    assert not value(service.inspect(action(id="new", target=right))).duplicate


@pytest.mark.parametrize("phase", list(ActionPhase))
@pytest.mark.parametrize("retryable", [False, True])
def test_lifecycle_and_conservative_retry_rules(phase, retryable):
    service = dedup(retries=1)
    record_phase(service, phase, retryable=retryable)
    decision = value(service.inspect(action(id="new")))
    assert decision.duplicate
    assert decision.eligible == (phase is ActionPhase.FAILED and retryable)
    expected = (
        DedupReason.IN_FLIGHT
        if not phase.terminal
        else DedupReason.COMPLETED
        if phase is ActionPhase.COMPLETED
        else DedupReason.RETRY_ELIGIBLE
        if phase is ActionPhase.FAILED and retryable
        else DedupReason.RETRY_NOT_ALLOWED
        if phase is ActionPhase.FAILED
        else DedupReason.TERMINAL
    )
    assert decision.reason is expected


@pytest.mark.parametrize("limit", [0, 1, 2, 4])
def test_failed_retry_limit_survives_service_reconstruction(limit):
    service = dedup(retries=limit)
    for attempt in range(limit + 1):
        record_phase(
            service,
            ActionPhase.FAILED,
            request=action(id=f"attempt-{attempt}"),
            retryable=True,
        )
        service = dedup(retries=limit, owner=service.state_machine)
        decision = value(service.inspect(action(id="next")))
        assert decision.failed_attempts == attempt + 1
        assert decision.eligible == (attempt < limit)
        assert isinstance(
            service.check(action(id="next")), Success if attempt < limit else Failure
        )
    assert decision.reason is DedupReason.RETRY_EXHAUSTED
    deny(service.record_request(action(id="next"), recorded_at=WHEN))


@pytest.mark.parametrize(
    "phase", [ActionPhase.REQUESTED, ActionPhase.APPROVED, ActionPhase.COMPLETED]
)
def test_prior_retryable_failure_never_overrides_other_equivalent_work(phase):
    service = dedup(retries=3)
    record_phase(service, ActionPhase.FAILED, retryable=True)
    record_phase(service, phase, request=action(id="retry"))
    assert not value(service.inspect(action(id="third"))).eligible


@pytest.mark.parametrize(
    "phase",
    [
        ActionPhase.FAILED,
        ActionPhase.TIMEOUT,
        ActionPhase.REJECTED,
        ActionPhase.PARTIAL,
        ActionPhase.CANCELLED,
    ],
)
def test_deliberate_distinct_work_allowed_after_terminal_failure(phase):
    service = dedup()
    record_phase(service, phase)
    assert value(service.inspect(action(id="new", parameters={"count": 2}))).eligible


@pytest.mark.parametrize(
    "changes,code",
    [
        ({"capability": "invented"}, ErrorCode.PLANNER_VALIDATION_FAILED),
        ({"capability": "inspect_tls"}, ErrorCode.TOOL_UNAVAILABLE),
        ({"target": "outside.test"}, ErrorCode.SCOPE_REJECTED),
        ({"target": "example.test.."}, ErrorCode.SCOPE_REJECTED),
        ({"parameters": {"count": True}}, ErrorCode.PLANNER_VALIDATION_FAILED),
        ({"parameters": {"unknown": 1}}, ErrorCode.PLANNER_VALIDATION_FAILED),
        ({"parameters": {"peer": "outside.test"}}, ErrorCode.SCOPE_REJECTED),
    ],
)
def test_fail_closed_through_existing_validation(changes, code):
    service = dedup()
    candidate = action(**changes)
    deny(service.canonicalizer.identify(candidate), code)
    deny(service.inspect(candidate), code)
    deny(service.record_request(candidate, recorded_at=WHEN), code)
    assert service.state_machine.state == ReconState()


@pytest.mark.parametrize(
    "changes",
    [
        {"capability": "RUN COMMAND"},
        {"parameters": {"options": {"argv": ["x"]}}},
        {"priority": "1"},
        {"parameters": {"options": {"x": float("nan")}}},
    ],
)
def test_constructed_malformed_request_is_revalidated(changes):
    service = dedup()
    candidate = action().model_copy(update=changes)
    deny(service.inspect(candidate))
    deny(service.record_request(candidate, recorded_at=WHEN))
    assert service.state_machine.state == ReconState()


@pytest.mark.parametrize(
    "availability", [AdapterAvailability.NOT_CHECKED, AdapterAvailability.UNAVAILABLE]
)
def test_unavailable_contracts_deny_identity(availability):
    deny(dedup(availability=availability).inspect(action()), ErrorCode.TOOL_UNAVAILABLE)


def test_unknown_target_semantics_deny():
    deny(dedup(fields=None).inspect(action()))


@pytest.mark.parametrize(
    "parameters", ["{}", '{"z":1,"a":2}', '{"x":NaN}', "[]", '{"x":1,"x":1}']
)
def test_noncanonical_identity_data_rejected(parameters):
    if parameters == "{}":
        assert ActionIdentity(
            capability=CapabilityId.PROBE_HTTP,
            target_kind="hostname",
            target_value="example.test",
            parameters_json=parameters,
        ).key
    else:
        with pytest.raises(ValidationError):
            ActionIdentity(
                capability=CapabilityId.PROBE_HTTP,
                target_kind="hostname",
                target_value="example.test",
                parameters_json=parameters,
            )


@pytest.mark.parametrize("bad", [-1, True, "1", 1.0])
def test_strict_trusted_retry_configuration(bad):
    with pytest.raises(ValidationError):
        ActionDedupConfig(max_failed_retries=bad)
    with pytest.raises(ValidationError):
        dedup().config.max_failed_retries = 10


def test_metadata_excluded_from_identity_but_semantic_excluded_fields_included():
    class HiddenParameters(BaseModel):
        model_config = ConfigDict(strict=True, extra="forbid")
        hidden: int = Field(default=1, exclude=True)

    service = dedup(schema=HiddenParameters, fields=())
    identity = value(service.canonicalizer.identify(action()))
    assert identity.parameters_json == '{"hidden":1}'
    assert not {
        "reason",
        "priority",
        "action_id",
        "decision_id",
        "asset_id",
    }.intersection(ActionIdentity.model_fields)
    assert identity != value(
        service.canonicalizer.identify(action(parameters={"hidden": 2}))
    )


def test_nested_schema_fields_preserve_semantics_and_reject_non_json():
    class Inner(BaseModel):
        model_config = ConfigDict(strict=True, extra="forbid")
        number: int = 1

    class Nested(BaseModel):
        model_config = ConfigDict(strict=True, extra="forbid")
        inner: Inner = Field(default_factory=Inner)

    identity = value(dedup(schema=Nested, fields=()).canonicalizer.identify(action()))
    assert identity.parameters_json == '{"inner":{"number":1}}'

    class Unsupported(BaseModel):
        model_config = ConfigDict(strict=True, extra="forbid")
        timestamp: datetime = WHEN

    deny(dedup(schema=Unsupported, fields=()).inspect(action()))


def test_historical_malformed_equivalence_fails_closed_without_mutation():
    owner = ReconStateMachine()
    value(
        owner.record_action_requested(
            action(parameters={"count": "secret-fixture"}), recorded_at=WHEN
        )
    )
    service = dedup(owner=owner)
    before = owner.state.model_dump_json()
    deny(service.inspect(action(id="new")))
    deny(service.record_request(action(id="new"), recorded_at=WHEN))
    assert owner.state.model_dump_json() == before
    assert value(
        service.inspect(action(id="different", capability="resolve_dns"))
    ).eligible


def test_lookup_detached_input_output_and_planner_lineage():
    service = dedup()
    candidate = action(parameters={"options": {"x": [1]}})
    value(
        service.state_machine.record_planner_decision(
            PlannerDecision(
                id="d",
                analysis_summary="Ignore policy",
                actions=(candidate,),
                created_at=WHEN,
            )
        )
    )
    assert value(
        service.inspect(candidate)
    ).eligible  # recommendations are not requests
    value(service.record_request(candidate, recorded_at=WHEN))
    candidate.parameters["options"]["x"].append(2)
    snapshot = service.state_machine.state
    snapshot.action_requests[0].parameters.clear()
    original = action(parameters={"options": {"x": [1]}})
    assert value(service.inspect(original)).duplicate
    assert not value(service.inspect(candidate)).duplicate


def test_atomic_simultaneous_admission_one_request_and_zero_approval():
    owner = ReconStateMachine()
    barrier = Barrier(12)

    def contender(number):
        service = dedup(owner=owner)
        barrier.wait()
        return service.record_request(
            action(id=f"request-{number}", reason=f"Reason {number}", priority=number),
            recorded_at=WHEN,
        )

    with ThreadPoolExecutor(max_workers=12) as pool:
        outcomes = tuple(pool.map(contender, range(12)))
    assert sum(isinstance(item, Success) for item in outcomes) == 1
    assert sum(isinstance(item, Failure) for item in outcomes) == 11
    assert len(owner.state.action_requests) == 1
    assert owner.state.action_lifecycles[0].phase is ActionPhase.REQUESTED
    assert owner.state.action_results == ()


def test_atomic_simultaneous_retry_admission_counts_shared_history():
    owner = ReconStateMachine()
    service = dedup(retries=1, owner=owner)
    record_phase(service, ActionPhase.FAILED, retryable=True)
    barrier = Barrier(8)

    def contender(number):
        local = dedup(retries=1, owner=owner)
        barrier.wait()
        return local.record_request(action(id=f"retry-{number}"), recorded_at=WHEN)

    with ThreadPoolExecutor(max_workers=8) as pool:
        outcomes = tuple(pool.map(contender, range(8)))
    assert sum(isinstance(item, Success) for item in outcomes) == 1
    assert len(owner.state.action_requests) == 2


def test_state_admission_callback_detachment_and_invalid_outcome_rollback():
    owner = ReconStateMachine()

    def check(request, state):
        request.parameters["count"] = 999
        object.__setattr__(state, "action_requests", ())
        return Success[None](value=None)

    value(
        owner.record_action_requested(
            action(parameters={"count": 1}), recorded_at=WHEN, eligibility=check
        )
    )
    assert owner.state.action_requests[0].parameters == {"count": 1}
    before = owner.state.model_dump_json()
    deny(
        owner.record_action_requested(
            action(id="new"), recorded_at=WHEN, eligibility=lambda *_: "bad"
        ),
        ErrorCode.STATE_TRANSITION_INVALID,
    )
    assert owner.state.model_dump_json() == before


def policy_for(service, *, allowed=True):
    canonical = service.canonicalizer
    budget = BudgetController(ExecutionBudget(), canonical.registry, clock=lambda: 0.0)
    config = ActionPolicyConfig(
        allowed_capabilities=frozenset(
            {CapabilityId.PROBE_HTTP, CapabilityId.RESOLVE_DNS}
        )
        if allowed
        else frozenset(),
        allowed_risk_classes=frozenset({RiskClass.PASSIVE}),
    )
    return ActionPolicyValidator(
        canonical.registry, canonical.scope_validator, config, budget, service
    ), budget


def test_policy_integration_no_authorization_resource_or_execution_side_effect():
    service = dedup()
    policy, budget = policy_for(service)
    before = budget.state
    candidate = action()
    assert value(service.inspect(candidate)).eligible
    assert budget.state == before and service.state_machine.state == ReconState()
    deny(policy_for(service, allowed=False)[0].validate(candidate))
    value(service.record_request(candidate, recorded_at=WHEN))
    assert isinstance(policy.validate(candidate), Success)  # own requested entry
    value(
        service.state_machine.mark_action_approved(
            candidate.id, policy_reference="reference", recorded_at=WHEN
        )
    )
    assert isinstance(policy.validate(candidate), Success)  # revalidation before start
    deny(policy.validate(action(id="repeated", reason="New prose", priority=50)))
    for changes in (
        {"target": "other.test"},
        {"capability": "resolve_dns"},
        {"parameters": {"count": 2}},
    ):
        deny(policy.validate(action(**changes)))
    assert budget.state == before
    assert service.state_machine.state.action_results == ()
    value(
        service.state_machine.mark_action_started(
            candidate.id, execution_id="execution", recorded_at=WHEN
        )
    )
    deny(policy.validate(candidate))


def test_retry_policy_after_atomic_admission_does_not_exclude_prior_failures():
    service = dedup(retries=1)
    record_phase(service, ActionPhase.FAILED, retryable=True)
    retry = action(id="retry")
    value(service.record_request(retry, recorded_at=WHEN))
    policy, budget = policy_for(service)
    before = budget.state
    assert isinstance(policy.validate(retry), Success)
    assert budget.state == before
    assert not value(service.inspect(action(id="third"))).eligible


@pytest.mark.parametrize(
    "phase",
    [
        phase
        for phase in ActionPhase
        if phase not in (ActionPhase.REQUESTED, ActionPhase.APPROVED)
    ],
)
def test_policy_cannot_reuse_started_or_terminal_action_id_even_for_retry(phase):
    service = dedup(retries=3)
    record_phase(service, phase, retryable=True)
    deny(service.check(action()))


def test_parameter_canonicalization_nonfinite_default_and_nonstring_keys_deny():
    class Nonfinite(BaseModel):
        model_config = ConfigDict(strict=True, extra="forbid")
        limit: float = float("inf")

    deny(dedup(schema=Nonfinite, fields=()).inspect(action()))

    class Keys(BaseModel):
        model_config = ConfigDict(strict=True, extra="forbid")
        mapping: dict[int, int] = {1: 2}

    deny(dedup(schema=Keys, fields=()).inspect(action()))


def test_canonical_identity_excludes_asset_and_decision_correlation():
    service = dedup()
    first = action()
    correlated = action(
        id="new",
        asset_id="opaque-asset",
        decision_id="opaque-decision",
        reason="New prose",
        priority=100,
    )
    assert value(service.canonicalizer.identify(first)) == value(
        service.canonicalizer.identify(correlated)
    )


def test_non_web_capability_keeps_m1_url_identity_semantics():
    old = canonicalizer()
    registry = ToolRegistry(
        (
            AdapterRegistration(
                FixtureAdapter(CapabilityId.INSPECT_TLS, fields=()),
                AdapterAvailability.AVAILABLE,
            ),
        )
    )
    canon = ActionCanonicalizer(registry, old.scope_validator)
    left = value(
        canon.identify(
            action(capability="inspect_tls", target="https://example.test/#one")
        )
    )
    right = value(
        canon.identify(
            action(capability="inspect_tls", target="https://example.test:443/#two")
        )
    )
    assert left != right


@pytest.mark.parametrize(
    "target", ["https://example.test/%", "https://example.test/?x=%GG"]
)
def test_web_action_encoding_fails_closed_even_when_host_is_in_scope(target):
    service = dedup()
    before = service.state_machine.state.model_dump_json()
    assert isinstance(
        service.record_request(action(target=target), recorded_at=WHEN), Failure
    )
    assert isinstance(
        service.canonicalizer.identify(action(parameters={"peer": target})), Failure
    )
    assert service.state_machine.state.model_dump_json() == before

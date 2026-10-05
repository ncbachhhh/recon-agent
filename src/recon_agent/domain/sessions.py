"""Validated in-memory snapshots and structural session composition."""

from collections.abc import Mapping
from typing import Literal, Protocol, Self

from pydantic import Field, model_validator

from recon_agent.domain._base import DomainModel, NonEmptyText, Record, Timestamp
from recon_agent.domain.actions import ActionRequest, ActionResult, PlannerDecision
from recon_agent.domain.assets import Asset, Endpoint, Host, Service
from recon_agent.domain.budgets import BudgetSnapshot
from recon_agent.domain.lifecycle import ActionLifecycle, ActionPhase
from recon_agent.domain.observations import Evidence, Observation
from recon_agent.domain.targets import Scope, Target


class _Identified(Protocol):
    @property
    def id(self) -> str: ...


def _index[T: _Identified](records: tuple[T, ...]) -> dict[str, T]:
    indexed = {record.id: record for record in records}
    if len(indexed) != len(records):
        raise ValueError("duplicate record identity")
    return indexed


def _references(ids: tuple[str, ...], records: Mapping[str, object]) -> None:
    if len(set(ids)) != len(ids) or any(
        identifier not in records for identifier in ids
    ):
        raise ValueError("unresolved or repeated lineage reference")


class ReconState(Record):
    """Authoritative snapshot owned by ReconStateMachine; no executable authority.

    Tuple collections are immutable; nested JSON in detached snapshots is data.
    The state owner defensively copies inputs and every exposed snapshot.
    """

    assets: tuple[Asset, ...] = ()
    hosts: tuple[Host, ...] = ()
    services: tuple[Service, ...] = ()
    endpoints: tuple[Endpoint, ...] = ()
    observations: tuple[Observation, ...] = ()
    evidence: tuple[Evidence, ...] = ()
    action_requests: tuple[ActionRequest, ...] = ()
    action_results: tuple[ActionResult, ...] = ()
    planner_decisions: tuple[PlannerDecision, ...] = ()
    action_lifecycles: tuple[ActionLifecycle, ...] = ()
    budget_snapshots: tuple[BudgetSnapshot, ...] = ()

    @model_validator(mode="after")
    def relationships_are_consistent(self) -> Self:
        assets, hosts = _index(self.assets), _index(self.hosts)
        services, endpoints = _index(self.services), _index(self.endpoints)
        observations, evidence = _index(self.observations), _index(self.evidence)
        requests, results = _index(self.action_requests), _index(self.action_results)
        decisions = _index(self.planner_decisions)
        _index(self.budget_snapshots)
        for snapshot in self.budget_snapshots:
            for buckets in (
                snapshot.state.host_actions,
                snapshot.state.capability_window_actions,
                snapshot.state.outcomes,
            ):
                if len({key for key, _ in buckets}) != len(buckets):
                    raise ValueError("duplicate budget snapshot bucket")
        for previous, current in zip(
            self.budget_snapshots, self.budget_snapshots[1:], strict=False
        ):
            if current.recorded_at < previous.recorded_at:
                raise ValueError("budget snapshot time cannot regress")

        subjects: tuple[Asset | Host | Service | Endpoint, ...] = (
            *self.assets,
            *self.hosts,
            *self.services,
            *self.endpoints,
        )
        for subject in subjects:
            asset_id = subject.id if isinstance(subject, Asset) else subject.asset_id
            if asset_id not in assets:
                raise ValueError("subject references unknown asset")
            _references(subject.observation_ids, observations)
            if any(
                observations[ref].asset_id != asset_id
                for ref in subject.observation_ids
            ):
                raise ValueError("subject observation belongs to another asset")
        for service in services.values():
            if (
                service.host_id not in hosts
                or hosts[service.host_id].asset_id != service.asset_id
            ):
                raise ValueError("service host ownership mismatch")
        for endpoint in endpoints.values():
            if endpoint.service_id is not None and (
                endpoint.service_id not in services
                or services[endpoint.service_id].asset_id != endpoint.asset_id
            ):
                raise ValueError("endpoint service ownership mismatch")
        for observation in observations.values():
            if observation.asset_id not in assets:
                raise ValueError("observation references unknown asset")
            _references(observation.evidence_ids, evidence)
            if observation.execution_id is not None and any(
                evidence[ref].execution_id not in (None, observation.execution_id)
                for ref in observation.evidence_ids
            ):
                raise ValueError("observation evidence execution mismatch")

        for decision in decisions.values():
            _references(decision.input_observation_ids, observations)
            _references(decision.input_evidence_ids, evidence)
            _index(decision.actions)
            for recommendation in decision.actions:
                if recommendation.decision_id not in (None, decision.id):
                    raise ValueError("recommendation decision reference mismatch")
        for request in requests.values():
            if request.asset_id is not None and request.asset_id not in assets:
                raise ValueError("action references unknown asset")
            if request.decision_id is not None:
                if request.decision_id not in decisions:
                    raise ValueError("action references unknown decision")
                recommendations = _index(decisions[request.decision_id].actions)
                if recommendations.get(request.id) != request:
                    raise ValueError("action differs from referenced recommendation")

        lifecycles = {record.action_id: record for record in self.action_lifecycles}
        if (
            len(lifecycles) != len(self.action_lifecycles)
            or lifecycles.keys() != requests.keys()
        ):
            raise ValueError("each action requires exactly one lifecycle")
        terminal_ids = set()
        execution_ids = set()
        execution_phases: dict[str, ActionPhase] = {}
        for action_id, lifecycle in lifecycles.items():
            request = requests[action_id]
            if request.decision_id is not None and (
                lifecycle.transitions[0].recorded_at
                < decisions[request.decision_id].created_at
            ):
                raise ValueError("action precedes its planner decision")
            started = next(
                (
                    event.execution_id
                    for event in lifecycle.transitions
                    if event.phase is ActionPhase.STARTED
                ),
                None,
            )
            if started is not None:
                if started in execution_ids:
                    raise ValueError("execution identity belongs to another action")
                execution_ids.add(started)
                execution_phases[started] = lifecycle.phase
            if not lifecycle.phase.terminal:
                continue
            last = lifecycle.transitions[-1]
            result = results.get(last.result_id) if last.result_id is not None else None
            if (
                result is None
                or result.action_id != action_id
                or result.status != lifecycle.phase
            ):
                raise ValueError("terminal lifecycle result mismatch")
            if result.recorded_at != last.recorded_at:
                raise ValueError("terminal result time mismatch")
            if started is None:
                if result.execution_ids:
                    raise ValueError("unstarted action cannot have executions")
            elif result.execution_ids != (started,):
                raise ValueError("result must reference the recorded execution")
            terminal_ids.add(result.id)
        if terminal_ids != results.keys():
            raise ValueError("result has no terminal lifecycle")
        for observation in observations.values():
            origins = (
                observation.execution_id,
                *(evidence[ref].execution_id for ref in observation.evidence_ids),
            )
            if any(
                origin in execution_phases
                and execution_phases[origin]
                not in (
                    ActionPhase.COMPLETED,
                    ActionPhase.PARTIAL,
                )
                for origin in origins
                if origin is not None
            ):
                raise ValueError(
                    "unfinished or unsuccessful action cannot support observations"
                )
        for result in results.values():
            _index(result.observations)
            _index(result.evidence)
            for observation in result.observations:
                if observations.get(observation.id) != observation:
                    raise ValueError("result observation conflicts with state")
            for item in result.evidence:
                if evidence.get(item.id) != item:
                    raise ValueError("result evidence conflicts with state")
            facts: tuple[Observation | Evidence, ...] = (
                *result.observations,
                *result.evidence,
            )
            for fact in facts:
                if (
                    fact.execution_id is not None
                    and fact.execution_id not in result.execution_ids
                ):
                    raise ValueError("result fact execution mismatch")
        return self


class ReconSession(DomainModel):
    """Session composition only; session orchestration/stop/resume remain future."""

    id: NonEmptyText
    targets: tuple[Target, ...] = Field(min_length=1)
    scope: Scope
    state: ReconState = Field(default_factory=ReconState)
    status: Literal["created", "running", "completed", "failed", "cancelled"] = (
        "created"
    )
    created_at: Timestamp
    stop_reason: NonEmptyText | None = None

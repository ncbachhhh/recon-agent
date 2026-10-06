"""Local state ownership and atomic validated transitions; no operational calls."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from threading import Lock

from pydantic import TypeAdapter, ValidationError

from recon_agent.core.errors import StateTransitionError
from recon_agent.core.results import Failure, OperationResult, Success
from recon_agent.domain.actions import ActionRequest, ActionResult, PlannerDecision
from recon_agent.domain.assets import Asset, Endpoint, Host, Service
from recon_agent.domain.budgets import BudgetSnapshot
from recon_agent.domain.lifecycle import ActionLifecycle, ActionPhase, ActionTransition
from recon_agent.domain.observations import Evidence, Observation
from recon_agent.domain.sessions import ReconState


@dataclass(slots=True)
class _OwnedState:
    value: ReconState


@dataclass(frozen=True, slots=True, init=False)
class ReconStateMachine:
    """One explicitly owned in-memory state; never authorization or execution.

    Inputs and returned snapshots are detached. Transitions validate the whole
    candidate before swapping owned state under a local lock. No counters, scope,
    adapters, policy tokens, clocks, dedup identities or runtime startup are owned.
    """

    _owned: _OwnedState
    _lock: Lock

    def __init__(self, initial: ReconState | None = None) -> None:
        try:
            validated = ReconState.model_validate(
                initial if initial is not None else ReconState()
            )
        except (ValidationError, TypeError, ValueError) as cause:
            raise StateTransitionError("Invalid initial recon state") from cause
        object.__setattr__(self, "_owned", _OwnedState(validated.model_copy(deep=True)))
        object.__setattr__(self, "_lock", Lock())

    @property
    def state(self) -> ReconState:
        with self._lock:
            return self._owned.value.model_copy(deep=True)

    def _commit(
        self,
        update: Callable[[ReconState], dict[str, object] | Failure],
    ) -> OperationResult[ReconState]:
        with self._lock:
            try:
                current = self._owned.value
                changes = update(current)
                if isinstance(changes, Failure):
                    return changes
                candidate = ReconState.model_validate(
                    {**current.model_dump(), **changes}
                )
                owned = candidate.model_copy(deep=True)
                result = Success[ReconState](value=candidate.model_copy(deep=True))
            except (ValidationError, TypeError, ValueError, AttributeError):
                return Failure(
                    error=StateTransitionError(
                        "State transition violates the state contract"
                    ).to_error_info()
                )
            self._owned.value = owned
            return result

    def record_facts(
        self,
        *,
        assets: tuple[Asset, ...] = (),
        hosts: tuple[Host, ...] = (),
        services: tuple[Service, ...] = (),
        endpoints: tuple[Endpoint, ...] = (),
        observations: tuple[Observation, ...] = (),
        evidence: tuple[Evidence, ...] = (),
    ) -> OperationResult[ReconState]:
        """Atomic related facts, including cyclic asset/observation references.

        IDs identify lineage, not semantic equivalence. Duplicate IDs reject;
        distinct IDs may contain identical content. No finding/scope inference.
        """
        return self._commit(
            lambda current: {
                "assets": (*current.assets, *assets),
                "hosts": (*current.hosts, *hosts),
                "services": (*current.services, *services),
                "endpoints": (*current.endpoints, *endpoints),
                "observations": (*current.observations, *observations),
                "evidence": (*current.evidence, *evidence),
            }
        )

    def record_asset(self, asset: Asset) -> OperationResult[ReconState]:
        return self.record_facts(assets=(asset,))

    def record_host(self, host: Host) -> OperationResult[ReconState]:
        return self.record_facts(hosts=(host,))

    def record_service(self, service: Service) -> OperationResult[ReconState]:
        return self.record_facts(services=(service,))

    def record_endpoint(self, endpoint: Endpoint) -> OperationResult[ReconState]:
        return self.record_facts(endpoints=(endpoint,))

    def record_observation(
        self, observation: Observation
    ) -> OperationResult[ReconState]:
        return self.record_facts(observations=(observation,))

    def record_evidence(self, evidence: Evidence) -> OperationResult[ReconState]:
        return self.record_facts(evidence=(evidence,))

    def record_planner_decision(
        self, decision: PlannerDecision
    ) -> OperationResult[ReconState]:
        """Record a recommendation only; do not enqueue or approve its actions."""
        return self._commit(
            lambda current: {
                "planner_decisions": (*current.planner_decisions, decision),
            }
        )

    def record_budget_snapshot(
        self, snapshot: BudgetSnapshot
    ) -> OperationResult[ReconState]:
        """Record caller-sampled facts; no budget arithmetic or controller access."""
        return self._commit(
            lambda current: {
                "budget_snapshots": (*current.budget_snapshots, snapshot),
            }
        )

    def record_action_requested(
        self,
        request: ActionRequest,
        *,
        recorded_at: datetime,
        eligibility: Callable[[ActionRequest, ReconState], OperationResult[None]]
        | None = None,
    ) -> OperationResult[ReconState]:
        """Record intent; optional trusted pure admission check runs under the lock.

        The check receives detached data and must not reenter this owner. This
        seam performs no authorization, resource reservation or execution.
        """

        def update(current: ReconState) -> dict[str, object] | Failure:
            validated = ActionRequest.model_validate(request)
            if eligibility is not None:
                outcome: OperationResult[None] = TypeAdapter(
                    OperationResult[None]
                ).validate_python(
                    eligibility(
                        validated.model_copy(deep=True), current.model_copy(deep=True)
                    )
                )
                if isinstance(outcome, Failure):
                    return outcome
            lifecycle = ActionLifecycle(
                action_id=validated.id,
                transitions=(
                    ActionTransition(
                        phase=ActionPhase.REQUESTED, recorded_at=recorded_at
                    ),
                ),
            )
            return {
                "action_requests": (*current.action_requests, validated),
                "action_lifecycles": (*current.action_lifecycles, lifecycle),
            }

        return self._commit(update)

    @staticmethod
    def _advance(
        current: ReconState,
        action_id: str,
        event: ActionTransition,
    ) -> tuple[ActionLifecycle, ...]:
        if not any(
            record.action_id == action_id for record in current.action_lifecycles
        ):
            raise ValueError("unknown action identity")
        return tuple(
            ActionLifecycle(
                action_id=record.action_id, transitions=(*record.transitions, event)
            )
            if record.action_id == action_id
            else record
            for record in current.action_lifecycles
        )

    def mark_action_approved(
        self,
        action_id: str,
        *,
        policy_reference: str,
        recorded_at: datetime,
    ) -> OperationResult[ReconState]:
        """Record a trusted caller's policy decision reference, never authorize.

        Future dispatch must revalidate ActionRequest through ActionPolicyValidator;
        this record/reference cannot be used as an executable/replay permission.
        """
        return self._commit(
            lambda current: {
                "action_lifecycles": self._advance(
                    current,
                    action_id,
                    ActionTransition(
                        phase=ActionPhase.APPROVED,
                        recorded_at=recorded_at,
                        policy_reference=policy_reference,
                    ),
                ),
            }
        )

    def mark_action_started(
        self,
        action_id: str,
        *,
        execution_id: str,
        recorded_at: datetime,
    ) -> OperationResult[ReconState]:
        """Record caller-owned execution identity; do not acquire resources or run."""
        return self._commit(
            lambda current: {
                "action_lifecycles": self._advance(
                    current,
                    action_id,
                    ActionTransition(
                        phase=ActionPhase.STARTED,
                        recorded_at=recorded_at,
                        execution_id=execution_id,
                    ),
                ),
            }
        )

    def record_action_result(
        self,
        result: ActionResult,
        *,
        assets: tuple[Asset, ...] = (),
        hosts: tuple[Host, ...] = (),
        services: tuple[Service, ...] = (),
        endpoints: tuple[Endpoint, ...] = (),
    ) -> OperationResult[ReconState]:
        """Atomically preserve terminal history and supplied facts, never infer them.

        Existing fact IDs can be referenced only with identical payloads; new IDs
        append. This is referential integrity, not content/action deduplication.
        """

        def update(current: ReconState) -> dict[str, object]:
            validated = ActionResult.model_validate(result)
            if validated.status not in ("completed", "partial") and (
                assets or hosts or services or endpoints
            ):
                raise ValueError("unsuccessful results cannot ingest subjects")
            known_observations = {item.id for item in current.observations}
            known_evidence = {item.id for item in current.evidence}
            return {
                "action_lifecycles": self._advance(
                    current,
                    validated.action_id,
                    ActionTransition(
                        phase=ActionPhase(validated.status),
                        recorded_at=validated.recorded_at,
                        result_id=validated.id,
                    ),
                ),
                "action_results": (*current.action_results, validated),
                "assets": (*current.assets, *assets),
                "hosts": (*current.hosts, *hosts),
                "services": (*current.services, *services),
                "endpoints": (*current.endpoints, *endpoints),
                "observations": (
                    *current.observations,
                    *(
                        item
                        for item in validated.observations
                        if item.id not in known_observations
                    ),
                ),
                "evidence": (
                    *current.evidence,
                    *(
                        item
                        for item in validated.evidence
                        if item.id not in known_evidence
                    ),
                ),
            }

        return self._commit(update)


__all__ = ["ReconStateMachine"]

"""Deterministic semantic equivalence over the existing authoritative state."""

from dataclasses import dataclass, field
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, JsonValue, ValidationError

from recon_agent.core.results import Failure, OperationResult, Success
from recon_agent.domain.actions import ActionRequest
from recon_agent.domain.identity import (
    ActionDedupDecision,
    ActionIdentity,
    DedupReason,
    canonical_json,
)
from recon_agent.domain.lifecycle import ActionPhase
from recon_agent.domain.sessions import ReconState
from recon_agent.domain.state import ReconStateMachine
from recon_agent.policy.actions import _invalid, _validate_action_inputs
from recon_agent.policy.scope import ScopeValidator
from recon_agent.tools import ToolRegistry


def _json_data(value: object) -> JsonValue:
    """Read actual validated fields; serializers/exclusions cannot hide semantics."""
    if isinstance(value, BaseModel):
        return {
            name: _json_data(getattr(value, name)) for name in type(value).model_fields
        }
    if isinstance(value, dict):
        if any(type(key) is not str for key in value):
            raise ValueError("parameter object keys must be strings")
        return {key: _json_data(nested) for key, nested in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_data(nested) for nested in value]
    if value is None:
        return None
    if isinstance(value, (str, bool, int, float)) and type(value) in (
        str,
        bool,
        int,
        float,
    ):
        return value
    raise ValueError("parameters must have JSON-compatible semantics")


class ActionDedupConfig(BaseModel):
    """Trusted local configuration; zero failed retries by default."""

    model_config = ConfigDict(
        extra="forbid", strict=True, frozen=True, revalidate_instances="always"
    )
    max_failed_retries: int = Field(default=0, ge=0)


@dataclass(frozen=True, slots=True)
class ActionCanonicalizer:
    """Scope/schema normalization alone grants no complete policy authorization."""

    registry: ToolRegistry
    scope_validator: ScopeValidator

    def identify(self, action: ActionRequest) -> OperationResult[ActionIdentity]:
        try:
            request = ActionRequest.model_validate(action)
        except (ValidationError, TypeError, ValueError):
            return _invalid("Malformed action request")
        facts = self.registry.capability_definition(request.capability)
        if isinstance(facts, Failure):
            return facts
        inputs = _validate_action_inputs(request, facts.value, self.scope_validator)
        if isinstance(inputs, Failure):
            return inputs
        normalized = inputs.value
        try:
            data = _json_data(normalized.parameters)
            # Field names come from the trusted registered schema. Reuse the
            # already validated matches in declared sequence, including defaults.
            assert isinstance(data, dict)
            matches = iter(normalized.parameter_scope_matches)
            for name in facts.value.parameter_target_fields or ():
                value = getattr(normalized.parameters, name)
                if isinstance(value, str):
                    data[name] = next(matches).canonical_target.value
                else:
                    data[name] = [next(matches).canonical_target.value for _ in value]
            target = normalized.scope_match.canonical_target
            if target.kind == "domain":
                raise ValueError("action target classification must be concrete")
            return Success[ActionIdentity](
                value=ActionIdentity(
                    capability=normalized.capability,
                    target_kind=target.kind,
                    target_value=target.value,
                    parameters_json=canonical_json(data),
                )
            )
        except (ValidationError, TypeError, ValueError, RecursionError):
            return _invalid("Parameters do not have canonical JSON semantics")


@dataclass(frozen=True, slots=True)
class ActionDeduplicator:
    """Read-only history eligibility plus atomic request admission, never dispatch.

    No ledger/cache: state remains owned solely by ReconStateMachine. Canonical
    identities are derived from its detached history using fixed trusted contracts.
    """

    canonicalizer: ActionCanonicalizer
    state_machine: ReconStateMachine
    config: ActionDedupConfig = field(default_factory=ActionDedupConfig)

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "config", ActionDedupConfig.model_validate(self.config)
        )

    def inspect(self, action: ActionRequest) -> OperationResult[ActionDedupDecision]:
        """Lookup includes all requests, even the supplied opaque action ID."""
        return self._inspect(action, self.state_machine.state)

    def _inspect(
        self,
        action: ActionRequest,
        state: ReconState,
        *,
        for_policy: bool = False,
    ) -> OperationResult[ActionDedupDecision]:
        identity = self.canonicalizer.identify(action)
        if isinstance(identity, Failure):
            return identity
        lifecycles = {item.action_id: item for item in state.action_lifecycles}
        results = {item.action_id: item for item in state.action_results}
        matching: list[str] = []
        for previous in state.action_requests:
            if (
                for_policy
                and previous.id == action.id
                and previous.capability != identity.value.capability
            ):
                return _invalid("Recorded action semantics changed")
            if previous.capability != identity.value.capability:
                continue
            prior_identity = self.canonicalizer.identify(previous)
            if isinstance(prior_identity, Failure):
                return _invalid("Historical action identity cannot be established")
            if for_policy and previous.id == action.id:
                if prior_identity.value != identity.value:
                    return _invalid("Recorded action semantics changed")
                # Revalidation of the admitted request must not reject itself.
                # Started/terminal records cannot be reused as dispatch tokens.
                if lifecycles[previous.id].phase in (
                    ActionPhase.REQUESTED,
                    ActionPhase.APPROVED,
                ):
                    continue
                return _invalid("Recorded action is no longer pending")
            if prior_identity.value == identity.value:
                matching.append(previous.id)
        matching.sort()
        phases = tuple(lifecycles[action_id].phase for action_id in matching)
        failures = phases.count(ActionPhase.FAILED)
        if not matching:
            reason = DedupReason.NEW
        elif any(not phase.terminal for phase in phases):
            reason = DedupReason.IN_FLIGHT
        elif ActionPhase.COMPLETED in phases:
            reason = DedupReason.COMPLETED
        elif any(phase is not ActionPhase.FAILED for phase in phases):
            reason = DedupReason.TERMINAL
        elif any(
            error is None or not error.retryable
            for action_id in matching
            for error in (results[action_id].error,)
        ):
            reason = DedupReason.RETRY_NOT_ALLOWED
        elif failures > self.config.max_failed_retries:
            reason = DedupReason.RETRY_EXHAUSTED
        else:
            reason = DedupReason.RETRY_ELIGIBLE
        return Success[ActionDedupDecision](
            value=ActionDedupDecision(
                identity=identity.value,
                matching_action_ids=tuple(matching),
                reason=reason,
                failed_attempts=failures,
            )
        )

    @staticmethod
    def _eligibility(
        outcome: OperationResult[ActionDedupDecision],
    ) -> OperationResult[None]:
        if isinstance(outcome, Failure):
            return outcome
        if not outcome.value.eligible:
            return _invalid("Equivalent action is not eligible for another attempt")
        return Success[None](value=None)

    def check(self, action: ActionRequest) -> OperationResult[None]:
        """ActionPolicyValidator seam; excludes only its own admitted pending entry."""
        return self._eligibility(
            self._inspect(action, self.state_machine.state, for_policy=True)
        )

    def record_request(
        self, action: ActionRequest, *, recorded_at: datetime
    ) -> OperationResult[ReconState]:
        """Atomically check equivalence and record REQUESTED, without approval."""
        try:
            request = ActionRequest.model_validate(action)
        except (ValidationError, TypeError, ValueError):
            return _invalid("Malformed action request")
        return self.state_machine.record_action_requested(
            request,
            recorded_at=recorded_at,
            eligibility=lambda request, state: self._eligibility(
                self._inspect(request, state)
            ),
        )


__all__ = ["ActionCanonicalizer", "ActionDedupConfig", "ActionDeduplicator"]

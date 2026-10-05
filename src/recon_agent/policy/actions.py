"""Pure local eligibility; structured decisions never dispatch or authorize replay."""

from dataclasses import dataclass, field
from typing import Protocol

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    InstanceOf,
    TypeAdapter,
    ValidationError,
)

from recon_agent.core.errors import BudgetExhaustedError, PlannerValidationError
from recon_agent.core.results import Failure, OperationResult, Success
from recon_agent.domain import ActionRequest
from recon_agent.domain._base import NonEmptyText
from recon_agent.domain.capabilities import CapabilityId, RiskClass
from recon_agent.policy.scope import ScopeMatch, ScopeValidator
from recon_agent.tools import ToolRegistry


class ActionPolicyConfig(BaseModel):
    """Explicit trusted allowlists. Empty defaults grant no capability or risk."""

    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        frozen=True,
        validate_default=True,
        revalidate_instances="always",
        hide_input_in_errors=True,
    )
    allowed_capabilities: frozenset[CapabilityId] = frozenset()
    allowed_risk_classes: frozenset[RiskClass] = frozenset()


class ActionEligibility(Protocol):
    """Trusted local check only; Success[None] means eligible, never reserved.

    M1-T06 supplies budget semantics; M1-T08 supplies completed/in-flight identity.
    Implementations must be deterministic and side-effect free, with no mutation
    of the supplied request. Dispatch will require atomic reservations separately.
    """

    def check(self, action: ActionRequest) -> OperationResult[None]: ...


@dataclass(frozen=True, slots=True)
class _MissingBudget:
    def check(self, action: ActionRequest) -> OperationResult[None]:
        return Failure(
            error=BudgetExhaustedError(
                "Budget eligibility is not established"
            ).to_error_info()
        )


@dataclass(frozen=True, slots=True)
class _MissingCompletedActions:
    def check(self, action: ActionRequest) -> OperationResult[None]:
        return _invalid("Completed-action eligibility is not established")


class ApprovedAction(BaseModel):
    """Internal validated data, not a serializable dispatch permission token.

    Typed parameters are deliberately omitted from dumps; neither this record nor
    its scope matches can be replayed to skip revalidation of the original request.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    action_id: NonEmptyText
    capability: CapabilityId
    scope_match: ScopeMatch
    parameter_scope_matches: tuple[ScopeMatch, ...] = ()
    parameters: InstanceOf[BaseModel] = Field(exclude=True, repr=False)


def _invalid(message: str) -> Failure:
    return Failure(error=PlannerValidationError(message).to_error_info())


@dataclass(frozen=True, slots=True)
class ActionPolicyValidator:
    """Compose snapshotted facts and explicit local policy; no execution methods.

    Defaults deny missing allowlists and eligibility services. Future composition
    must supply real eligibility services; only offline tests use permitting fakes.
    """

    registry: ToolRegistry
    scope_validator: ScopeValidator
    config: ActionPolicyConfig = field(default_factory=ActionPolicyConfig)
    budget_eligibility: ActionEligibility = field(default_factory=_MissingBudget)
    completed_action_eligibility: ActionEligibility = field(
        default_factory=_MissingCompletedActions
    )

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "config", ActionPolicyConfig.model_validate(self.config)
        )

    def validate(self, action: ActionRequest) -> OperationResult[ApprovedAction]:
        """Success is current eligibility; Failure uses canonical error codes.

        Revalidate even constructed/copied/mutated domain records, omit raw inputs
        from errors, and never consult reason/priority/planner analysis for policy.
        """
        try:
            request = ActionRequest.model_validate(action)
        except (ValidationError, TypeError, ValueError):
            return _invalid("Malformed action request")

        facts = self.registry.capability_definition(request.capability)
        if isinstance(facts, Failure):
            return facts
        definition = facts.value
        descriptor = definition.descriptor
        if descriptor.capability not in self.config.allowed_capabilities:
            return _invalid("Capability is not permitted by action policy")
        if descriptor.risk_class not in self.config.allowed_risk_classes:
            return _invalid("Risk class is not permitted by action policy")

        target = self.scope_validator.validate_value(request.target)
        if isinstance(target, Failure):
            return target
        try:
            parameters = definition.input_schema.model_validate(
                request.parameters, strict=True
            )
        except (ValidationError, TypeError, ValueError):
            return _invalid("Parameters do not satisfy the registered input schema")

        if definition.parameter_target_fields is None:
            return _invalid("Parameter target semantics are not established")
        matches: list[ScopeMatch] = []
        for name in definition.parameter_target_fields:
            value = getattr(parameters, name)
            values = (value,) if isinstance(value, str) else value
            if not isinstance(values, (tuple, list)) or any(
                not isinstance(candidate, str) for candidate in values
            ):
                return _invalid("Unsupported parameter target representation")
            for candidate in values:
                match = self.scope_validator.validate_value(candidate)
                if isinstance(match, Failure):
                    return match
                matches.append(match.value)

        for eligibility in (self.budget_eligibility, self.completed_action_eligibility):
            try:
                outcome: OperationResult[None] = TypeAdapter(
                    OperationResult[None]
                ).validate_python(eligibility.check(request))
            except (ValidationError, TypeError, ValueError):
                return _invalid("Action eligibility result is unsupported")
            if isinstance(outcome, Failure):
                return outcome

        return Success[ApprovedAction](
            value=ApprovedAction(
                action_id=request.id,
                capability=descriptor.capability,
                scope_match=target.value,
                parameter_scope_matches=tuple(matches),
                parameters=parameters,
            )
        )


__all__ = [
    "ActionEligibility",
    "ActionPolicyConfig",
    "ActionPolicyValidator",
    "ApprovedAction",
]

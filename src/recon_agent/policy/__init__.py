"""Deterministic target authorization, separate from domain declaration data."""

from recon_agent.core.errors import ScopeRejectionReason
from recon_agent.policy.actions import (
    ActionEligibility,
    ActionPolicyConfig,
    ActionPolicyValidator,
    ApprovedAction,
    BudgetEligibility,
)
from recon_agent.policy.budgets import (
    BudgetController,
    BudgetPermit,
    BudgetState,
    ExecutionBudget,
    ReservationOutcome,
)
from recon_agent.policy.dedup import (
    ActionCanonicalizer,
    ActionDedupConfig,
    ActionDeduplicator,
)
from recon_agent.policy.scope import ScopeMatch, ScopeValidator

__all__ = [
    "ActionCanonicalizer",
    "ActionDedupConfig",
    "ActionDeduplicator",
    "ActionEligibility",
    "ActionPolicyConfig",
    "ActionPolicyValidator",
    "ApprovedAction",
    "BudgetController",
    "BudgetEligibility",
    "BudgetPermit",
    "BudgetState",
    "ExecutionBudget",
    "ReservationOutcome",
    "ScopeMatch",
    "ScopeRejectionReason",
    "ScopeValidator",
]

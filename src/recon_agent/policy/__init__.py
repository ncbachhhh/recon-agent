"""Deterministic target authorization, separate from domain declaration data."""

from recon_agent.core.errors import ScopeRejectionReason
from recon_agent.policy.actions import (
    ActionEligibility,
    ActionPolicyConfig,
    ActionPolicyValidator,
    ApprovedAction,
)
from recon_agent.policy.scope import ScopeMatch, ScopeValidator

__all__ = [
    "ActionEligibility",
    "ActionPolicyConfig",
    "ActionPolicyValidator",
    "ApprovedAction",
    "ScopeMatch",
    "ScopeRejectionReason",
    "ScopeValidator",
]

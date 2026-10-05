"""Deterministic target authorization, separate from domain declaration data."""

from recon_agent.core.errors import ScopeRejectionReason
from recon_agent.policy.scope import ScopeMatch, ScopeValidator

__all__ = ["ScopeMatch", "ScopeRejectionReason", "ScopeValidator"]

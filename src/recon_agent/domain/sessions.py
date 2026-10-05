"""Aggregate containers only; no state transitions, budgets, resume or storage."""

from typing import Literal

from pydantic import Field

from recon_agent.domain._base import DomainModel, NonEmptyText, Timestamp
from recon_agent.domain.actions import ActionRequest, ActionResult, PlannerDecision
from recon_agent.domain.assets import Asset, Endpoint, Host, Service
from recon_agent.domain.observations import Evidence, Observation
from recon_agent.domain.targets import Scope, Target


class ReconState(DomainModel):
    """Typed snapshot containers. M1-T07 owns controlled mutation semantics."""

    assets: list[Asset] = Field(default_factory=list)
    hosts: list[Host] = Field(default_factory=list)
    services: list[Service] = Field(default_factory=list)
    endpoints: list[Endpoint] = Field(default_factory=list)
    observations: list[Observation] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    action_requests: list[ActionRequest] = Field(default_factory=list)
    action_results: list[ActionResult] = Field(default_factory=list)
    planner_decisions: list[PlannerDecision] = Field(default_factory=list)


class ReconSession(DomainModel):
    """Session composition, not proof of authorization or a runnable session."""

    id: NonEmptyText
    targets: tuple[Target, ...] = Field(min_length=1)
    scope: Scope
    state: ReconState = Field(default_factory=ReconState)
    status: Literal["created", "running", "completed", "failed", "cancelled"] = (
        "created"
    )
    created_at: Timestamp
    stop_reason: NonEmptyText | None = None

"""Action history records, never authorization, dispatch or retry eligibility."""

from enum import StrEnum
from typing import Self

from pydantic import Field, model_validator

from recon_agent.domain._base import NonEmptyText, Record, Timestamp


class ActionPhase(StrEnum):
    REQUESTED = "requested"
    APPROVED = "approved"
    STARTED = "started"
    COMPLETED = "completed"
    PARTIAL = "partial"
    REJECTED = "rejected"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

    @property
    def terminal(self) -> bool:
        return self not in (self.REQUESTED, self.APPROVED, self.STARTED)


def _follows(previous: ActionPhase, current: ActionPhase) -> bool:
    if previous is ActionPhase.REQUESTED:
        return current in (
            ActionPhase.APPROVED,
            ActionPhase.REJECTED,
            ActionPhase.CANCELLED,
        )
    if previous is ActionPhase.APPROVED:
        return current in (
            ActionPhase.STARTED,
            ActionPhase.REJECTED,
            ActionPhase.CANCELLED,
        )
    if previous is ActionPhase.STARTED:
        return current in (
            ActionPhase.COMPLETED,
            ActionPhase.PARTIAL,
            ActionPhase.FAILED,
            ActionPhase.CANCELLED,
            ActionPhase.TIMEOUT,
        )
    return False


class ActionTransition(Record):
    phase: ActionPhase
    recorded_at: Timestamp
    policy_reference: NonEmptyText | None = None
    execution_id: NonEmptyText | None = None
    result_id: NonEmptyText | None = None

    @model_validator(mode="after")
    def metadata_matches_phase(self) -> Self:
        if (self.policy_reference is not None) != (self.phase is ActionPhase.APPROVED):
            raise ValueError("approval requires only its policy reference")
        if (self.execution_id is not None) != (self.phase is ActionPhase.STARTED):
            raise ValueError("start requires only its execution reference")
        if (self.result_id is not None) != self.phase.terminal:
            raise ValueError("terminal phase requires its result reference")
        return self


class ActionLifecycle(Record):
    action_id: NonEmptyText
    transitions: tuple[ActionTransition, ...] = Field(min_length=1)

    @property
    def phase(self) -> ActionPhase:
        return self.transitions[-1].phase

    @model_validator(mode="after")
    def history_is_valid(self) -> Self:
        if self.transitions[0].phase is not ActionPhase.REQUESTED:
            raise ValueError("action history must begin with requested")
        for previous, current in zip(
            self.transitions, self.transitions[1:], strict=False
        ):
            if not _follows(previous.phase, current.phase):
                raise ValueError("invalid action lifecycle transition")
            if current.recorded_at < previous.recorded_at:
                raise ValueError("action transition time cannot regress")
        return self


__all__ = ["ActionLifecycle", "ActionPhase", "ActionTransition"]

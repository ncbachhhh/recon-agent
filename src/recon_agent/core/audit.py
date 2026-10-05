"""Non-authoritative autonomous reconnaissance event data, with no emission/I/O."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    JsonValue,
    StringConstraints,
    field_serializer,
    field_validator,
)

from recon_agent.core.errors import ErrorInfo
from recon_agent.core.redaction import redact_context


class AuditEventType(StrEnum):
    SESSION_STARTED = "session.started"
    SESSION_STOPPED = "session.stopped"
    SESSION_COMPLETED = "session.completed"
    SESSION_FAILED = "session.failed"
    SESSION_CANCELLED = "session.cancelled"
    ASSET_DISCOVERED = "asset.discovered"
    PLANNER_DECISION = "planner.decision"
    PLANNER_ACTION_REQUESTED = "planner.action_requested"
    POLICY_ACTION_APPROVED = "policy.action_approved"
    POLICY_ACTION_REJECTED = "policy.action_rejected"
    TOOL_EXECUTION_STARTED = "tool.execution_started"
    TOOL_EXECUTION_COMPLETED = "tool.execution_completed"
    TOOL_EXECUTION_FAILED = "tool.execution_failed"
    OBSERVATION_RECORDED = "observation.recorded"
    FINDING_RECORDED = "finding.recorded"
    BUDGET_EXHAUSTED = "budget.exhausted"


_Reference = Annotated[
    str, StringConstraints(min_length=1, max_length=256, pattern=r"\S")
]
_Summary = Annotated[
    str, StringConstraints(min_length=1, max_length=1024, pattern=r"\S")
]


class AuditEvent(BaseModel):
    """A supplied record of an operation/decision; never authority or replay logic.

    IDs/time are explicit. Context holds small summaries/references, not artifacts,
    transcripts or private reasoning. Its redaction does not change source evidence.
    """

    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        frozen=True,
        validate_default=True,
        revalidate_instances="always",
        hide_input_in_errors=True,
        allow_inf_nan=False,
    )

    event_id: _Reference
    event_type: AuditEventType
    timestamp: AwareDatetime
    session_id: _Reference
    severity: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    message: _Summary
    action_id: _Reference | None = None
    execution_id: _Reference | None = None
    planner_decision_id: _Reference | None = None
    asset_id: _Reference | None = None
    context: dict[str, JsonValue] = Field(default_factory=dict, repr=False)
    error: ErrorInfo | None = None

    @field_validator("timestamp")
    @classmethod
    def utc_timestamp(cls, value: datetime) -> datetime:
        return value.astimezone(UTC)

    @field_validator("context", mode="before")
    @classmethod
    def safe_context(cls, value: object) -> dict[str, JsonValue]:
        if not isinstance(value, dict):
            raise ValueError("audit context must be an object")
        return redact_context(value)

    @field_serializer("context")
    def serialized_context(self, value: dict[str, JsonValue]) -> dict[str, JsonValue]:
        return redact_context(value)


__all__ = ["AuditEvent", "AuditEventType"]

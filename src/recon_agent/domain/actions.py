"""Intent, outcomes and recommendations; nothing here authorizes or executes."""

from typing import Literal, Self

from pydantic import Field, JsonValue, field_validator, model_validator

from recon_agent.core.errors import ErrorCategory, ErrorCode, ErrorInfo
from recon_agent.domain._base import CapabilityName, NonEmptyText, Record, Timestamp
from recon_agent.domain.observations import Evidence, Observation

_EXECUTABLE_KEYS = frozenset(
    {
        "command",
        "shell_command",
        "raw_command",
        "command_template",
        "script",
        "bash",
        "raw_args",
        "argv",
        "extra_shell_args",
        "executable",
        "executable_path",
    }
)


def _data_only_parameters(value: JsonValue) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if key.casefold() in _EXECUTABLE_KEYS:
                raise ValueError("executable syntax keys are not capability parameters")
            _data_only_parameters(nested)
    elif isinstance(value, list):
        for nested in value:
            _data_only_parameters(nested)


class ActionRequest(Record):
    """Unapproved capability intent; later registry/policy validation is mandatory.

    Parameters are JSON data, never argv or executable syntax. Capability-name
    shape alone does not prove registration, safety, scope or permission.
    """

    id: NonEmptyText
    capability: CapabilityName
    target: NonEmptyText
    parameters: dict[NonEmptyText, JsonValue] = Field(default_factory=dict)
    reason: NonEmptyText
    priority: int = 0
    asset_id: NonEmptyText | None = None
    decision_id: NonEmptyText | None = None

    @field_validator("parameters")
    @classmethod
    def parameters_are_data(cls, value: dict[str, JsonValue]) -> dict[str, JsonValue]:
        _data_only_parameters(value)
        return value


class ActionResult(Record):
    """Action-specific outcome and evidence lineage, separate from generic outcomes."""

    id: NonEmptyText
    action_id: NonEmptyText
    status: Literal[
        "completed", "partial", "rejected", "failed", "cancelled", "timeout"
    ]
    recorded_at: Timestamp
    observations: tuple[Observation, ...] = ()
    evidence: tuple[Evidence, ...] = ()
    execution_ids: tuple[NonEmptyText, ...] = ()
    error: ErrorInfo | None = None

    @model_validator(mode="after")
    def outcome_is_consistent(self) -> Self:
        if self.status == "completed":
            if self.error is not None:
                raise ValueError("completed result cannot carry a failure")
        elif self.error is None:
            raise ValueError(
                "non-completed result requires structured error information"
            )
        if self.error is not None:
            if self.status == "rejected" and self.error.category not in (
                ErrorCategory.POLICY,
                ErrorCategory.PLANNER,
            ):
                raise ValueError("rejected result requires a policy/planner rejection")
            if (
                self.status == "timeout"
                and self.error.code is not ErrorCode.TOOL_TIMEOUT
            ):
                raise ValueError("timeout result requires tool_timeout")
            if (
                self.status == "cancelled"
                and self.error.code is not ErrorCode.CANCELLED
            ):
                raise ValueError("cancelled result requires cancelled")
            if self.status in ("failed", "partial") and self.error.category in (
                ErrorCategory.POLICY,
                ErrorCategory.PLANNER,
                ErrorCategory.CANCELLATION,
            ):
                raise ValueError("rejection/cancellation must use its terminal status")
        if self.status not in ("completed", "partial") and self.observations:
            raise ValueError("unsuccessful result cannot carry successful observations")
        return self


class PlannerDecision(Record):
    """Untrusted recommendation, never authorization or a collected fact."""

    id: NonEmptyText
    analysis_summary: NonEmptyText
    actions: tuple[ActionRequest, ...] = ()
    finished: bool = False
    created_at: Timestamp
    provider: NonEmptyText | None = None
    model: NonEmptyText | None = None
    input_observation_ids: tuple[NonEmptyText, ...] = ()
    input_evidence_ids: tuple[NonEmptyText, ...] = ()

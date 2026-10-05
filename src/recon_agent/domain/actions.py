"""Intent, outcomes and recommendations; nothing here authorizes or executes."""

from typing import Literal, Self

from pydantic import Field, JsonValue, field_validator, model_validator

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
    """Terminal outcome data; M0-T05 will supply structured error categories."""

    id: NonEmptyText
    action_id: NonEmptyText
    status: Literal[
        "completed", "partial", "rejected", "failed", "cancelled", "timeout"
    ]
    recorded_at: Timestamp
    observations: tuple[Observation, ...] = ()
    evidence: tuple[Evidence, ...] = ()
    execution_ids: tuple[NonEmptyText, ...] = ()
    failure_reason: NonEmptyText | None = None

    @model_validator(mode="after")
    def outcome_is_consistent(self) -> Self:
        if self.status == "completed":
            if self.failure_reason is not None:
                raise ValueError("completed result cannot carry a failure reason")
        elif self.failure_reason is None:
            raise ValueError(
                "non-completed result requires a failure/limitation reason"
            )
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

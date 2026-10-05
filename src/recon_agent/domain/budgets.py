"""Pure read-only budget facts; enforcement remains in policy/budgets.py."""

from enum import StrEnum
from json import dumps
from typing import Annotated

from pydantic import ConfigDict, Field, TypeAdapter, ValidationInfo, field_validator
from pydantic.dataclasses import dataclass

from recon_agent.domain._base import NonEmptyText, Record, Timestamp
from recon_agent.domain.capabilities import CapabilityId

Count = Annotated[int, Field(ge=0)]


class ReservationOutcome(StrEnum):
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    ABORTED = "aborted"


@dataclass(
    frozen=True,
    slots=True,
    config=ConfigDict(
        strict=True,
        extra="forbid",
        revalidate_instances="always",
        allow_inf_nan=False,
    ),
)
class BudgetState:
    """Detached structural snapshot; never an input to the budget controller."""

    permitted_actions: Count
    remaining_actions: Count
    active_executions: Count
    reserved_output_bytes: Count
    remaining_output_bytes: Count
    remaining_seconds: Annotated[float, Field(ge=0)]
    host_actions: tuple[tuple[NonEmptyText, Count], ...]
    capability_window_actions: tuple[tuple[CapabilityId, Count], ...]
    outcomes: tuple[tuple[ReservationOutcome, Count], ...]

    @property
    def expired(self) -> bool:
        return self.remaining_seconds == 0.0


class BudgetSnapshot(Record):
    """Caller-timestamped ledger facts; recording never consumes or resets work."""

    id: NonEmptyText
    recorded_at: Timestamp
    state: BudgetState

    @field_validator("state", mode="before")
    @classmethod
    def python_snapshot_dict(cls, value: object, info: ValidationInfo) -> object:
        # Python dumps need the strict constructor. JSON revalidation uses the
        # dataclass JSON schema to preserve its tuple/enum encodings.
        if isinstance(value, dict):
            if info.mode == "json":
                return TypeAdapter(BudgetState).validate_json(dumps(value))
            return BudgetState(**value)
        return value


__all__ = ["BudgetSnapshot", "BudgetState", "ReservationOutcome"]

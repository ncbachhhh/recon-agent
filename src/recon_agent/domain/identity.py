"""Portable semantic identity and dedup decisions; never executable authority."""

import json
from enum import StrEnum
from typing import Literal, Self

from pydantic import Field, model_validator

from recon_agent.domain._base import NonEmptyText, Record
from recon_agent.domain.capabilities import CapabilityId


def canonical_json(value: object) -> str:
    """Unambiguous JSON encoding, with sorted keys and finite numbers only."""
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    )


class ActionIdentity(Record):
    """Execution semantics only; opaque request/planner IDs are excluded."""

    version: Literal["action-v1"] = "action-v1"
    capability: CapabilityId
    target_kind: Literal["hostname", "ip", "cidr", "url"]
    target_value: NonEmptyText
    parameters_json: NonEmptyText

    @model_validator(mode="after")
    def parameters_are_canonical(self) -> Self:
        value = json.loads(self.parameters_json)
        if not isinstance(value, dict) or canonical_json(value) != self.parameters_json:
            raise ValueError("parameters must be a canonical JSON object")
        return self

    @property
    def key(self) -> str:
        """Full versioned identity, without hash collision or delimiter ambiguity."""
        return canonical_json(
            {
                "version": self.version,
                "capability": self.capability,
                "target": {"kind": self.target_kind, "value": self.target_value},
                "parameters": json.loads(self.parameters_json),
            }
        )


class DedupReason(StrEnum):
    NEW = "new"
    RETRY_ELIGIBLE = "retry_eligible"
    IN_FLIGHT = "in_flight"
    COMPLETED = "completed"
    TERMINAL = "terminal"
    RETRY_NOT_ALLOWED = "retry_not_allowed"
    RETRY_EXHAUSTED = "retry_exhausted"


class ActionDedupDecision(Record):
    """Normal typed policy outcome inside the existing OperationResult contract."""

    identity: ActionIdentity
    matching_action_ids: tuple[NonEmptyText, ...] = ()
    reason: DedupReason
    failed_attempts: int = Field(default=0, ge=0)

    @property
    def duplicate(self) -> bool:
        return bool(self.matching_action_ids)

    @property
    def eligible(self) -> bool:
        return self.reason in (DedupReason.NEW, DedupReason.RETRY_ELIGIBLE)


__all__ = ["ActionDedupDecision", "ActionIdentity", "DedupReason"]

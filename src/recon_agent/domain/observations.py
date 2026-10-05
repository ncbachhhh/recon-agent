"""Traceable facts and untrusted evidence references, independent of adapters."""

from typing import Annotated, Literal

from pydantic import Field, JsonValue, StringConstraints

from recon_agent.domain._base import CapabilityName, NonEmptyText, Record, Timestamp


class Evidence(Record):
    """Reference to source material. Never reads artifacts or trusts remote text."""

    id: NonEmptyText
    source: NonEmptyText
    origin: NonEmptyText
    artifact_reference: NonEmptyText
    collected_at: Timestamp
    execution_id: NonEmptyText | None = None
    capability: CapabilityName | None = None
    locator: NonEmptyText | None = None
    sha256: Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")] | None = None
    trust: Literal["untrusted"] = "untrusted"
    truncated: bool = False
    redacted: bool = False


class Observation(Record):
    """Collected/tool-reported fact, distinct from any interpreted Finding."""

    id: NonEmptyText
    kind: Literal["dns", "service", "http", "tls", "endpoint", "metadata"]
    asset_id: NonEmptyText
    source: NonEmptyText
    data: dict[NonEmptyText, JsonValue]
    observed_at: Timestamp
    evidence_ids: tuple[NonEmptyText, ...] = Field(min_length=1)
    execution_id: NonEmptyText | None = None

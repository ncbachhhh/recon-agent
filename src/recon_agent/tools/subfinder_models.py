"""Internal strict Subfinder schemas, projecting into generic domain evidence."""

from typing import Literal

from pydantic import Field

from recon_agent.domain import Asset, Evidence, Observation
from recon_agent.domain._base import NonEmptyText, Record, Timestamp


class SubfinderInput(Record):
    """No planner options; the only root is ActionRequest.target."""


class SubfinderContext(Record):
    asset_id: NonEmptyText
    execution_id: NonEmptyText
    collected_at: Timestamp


class SubfinderLine(Record):
    """Reviewed -json -cs wire format; no extra/provider-controlled fields."""

    host: str = Field(min_length=1, max_length=254)
    input: str = Field(min_length=1, max_length=254)
    sources: list[Literal["hackertarget"]] = Field(min_length=1, max_length=1)


class SubdomainOutput(Record):
    """Capability-local envelope, not a new top-level domain result entity."""

    query_target: NonEmptyText
    source_version: Literal["2.9.0"] = "2.9.0"
    provider_sources: tuple[Literal["hackertarget"], ...] = ("hackertarget",)
    hosts: tuple[str, ...] = ()
    asset: Asset
    observations: tuple[Observation, ...]
    evidence: tuple[Evidence, ...]

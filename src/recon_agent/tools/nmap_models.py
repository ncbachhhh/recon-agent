"""Finite service fingerprinting input and trusted prior-discovery selections."""

from typing import Annotated, Literal, Self

from pydantic import Field, field_validator, model_validator

from recon_agent.core.errors import ErrorInfo
from recon_agent.domain import Asset, Evidence, Host, Observation, Service
from recon_agent.domain._base import NonEmptyText, Port, Record
from recon_agent.tools.dns_models import DnsContext

Text = Annotated[str, Field(min_length=1, max_length=254)]


class NmapInput(Record):
    """Required integer TCP ports; no implicit defaults or flag grammar."""

    ports: list[Port] = Field(min_length=1, max_length=128)

    @field_validator("ports")
    @classmethod
    def canonical_port_set(cls, value: list[int]) -> list[int]:
        # Policy and semantic dedup consume this same canonical schema output.
        return sorted(set(value))


class DiscoveredPortSelection(Record):
    """Operator-approved prior facts, separate from planner input and scope."""

    address: Text
    hostname: Text | None = None
    ports: tuple[Port, ...] = Field(min_length=1, max_length=128)
    evidence_ids: tuple[NonEmptyText, ...] = Field(min_length=1, max_length=128)


class NmapSettings(Record):
    """Trusted installation data path and finite approved discovery snapshots."""

    data_directory: Annotated[str, Field(min_length=1, max_length=4096)]
    selections: tuple[DiscoveredPortSelection, ...] = Field(default=(), max_length=64)

    @model_validator(mode="after")
    def unique_subjects(self) -> Self:
        subjects = [
            s.hostname if s.hostname is not None else s.address for s in self.selections
        ]
        if len(subjects) != len(set(subjects)) or "\x00" in self.data_directory:
            raise ValueError("ambiguous selections or data directory")
        return self


class NmapContext(DnsContext):
    """Caller owns explicit IDs/time, lifecycle and evidence retention."""


class ServiceFingerprintOutput(Record):
    query_target: Text
    contact_address: Text
    ports: tuple[int, ...]
    discovery_evidence_ids: tuple[str, ...]
    source_version: Literal["7.95"] = "7.95"
    status: Literal["completed", "partial"]
    unreported_ports: tuple[int, ...]
    errors: tuple[ErrorInfo, ...] = ()
    asset: Asset
    hosts: tuple[Host, ...]
    services: tuple[Service, ...]
    observations: tuple[Observation, ...]
    evidence: tuple[Evidence, ...]


class NmapPort(Record):
    port: Port
    state: Literal[
        "open", "closed", "filtered", "unfiltered", "open|filtered", "closed|filtered"
    ]
    name: NonEmptyText | None = None
    product: NonEmptyText | None = None
    version: NonEmptyText | None = None
    extra_info: NonEmptyText | None = None
    service_fingerprint: NonEmptyText | None = None
    tunnel: NonEmptyText | None = None
    method: Literal["table", "probed"] | None = None
    confidence: Annotated[int, Field(ge=0, le=10)] | None = None
    cpes: tuple[NonEmptyText, ...] = Field(default=(), max_length=16)

"""Typed port discovery contracts; only trusted composition selects scan limits."""

from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from recon_agent.core.errors import ErrorInfo
from recon_agent.domain import Asset, Evidence, Host, Observation, Service
from recon_agent.domain._base import Port, Record
from recon_agent.tools.dns_models import DnsContext

Candidate = Annotated[str, Field(min_length=1, max_length=254)]


class NaabuInput(Record):
    """Empty candidates selects the primary host; otherwise an atomic batch."""

    candidates: list[Candidate] = Field(default_factory=list, max_length=64)


class ContactBinding(Record):
    """Operator assertion of intended numeric contacts, never inferred DNS data."""

    hostname: Candidate
    addresses: tuple[Candidate, ...] = Field(min_length=1, max_length=64)


class NaabuSettings(Record):
    """Operator-only inclusive TCP ranges; no textual port/flag grammar."""

    port_ranges: tuple[tuple[Port, Port], ...] = Field(
        default=((80, 80), (443, 443)), min_length=1, max_length=16
    )
    bindings: tuple[ContactBinding, ...] = Field(default=(), max_length=64)

    @model_validator(mode="after")
    def bounded_ranges(self) -> Self:
        if any(start > end or end - start >= 128 for start, end in self.port_ranges):
            raise ValueError("reversed port range")
        if (
            len({p for start, end in self.port_ranges for p in range(start, end + 1)})
            > 128
        ):
            raise ValueError("approved port set exceeds 128")
        if len({binding.hostname for binding in self.bindings}) != len(self.bindings):
            raise ValueError("duplicate hostname binding")
        return self

    @property
    def ports(self) -> tuple[int, ...]:
        return tuple(sorted({p for a, b in self.port_ranges for p in range(a, b + 1)}))


class NaabuContext(DnsContext):
    """Explicit subject/execution/time; caller owns lifecycle and ingestion."""


class PortDiscoveryOutput(Record):
    query_target: Candidate
    candidates: tuple[str, ...]
    bindings: tuple[ContactBinding, ...]
    contact_addresses: tuple[str, ...]
    ports: tuple[int, ...]
    source_version: Literal["2.3.5"] = "2.3.5"
    status: Literal["completed", "partial"]
    malformed_lines: int = Field(ge=0)
    errors: tuple[ErrorInfo, ...] = ()
    asset: Asset
    hosts: tuple[Host, ...]
    services: tuple[Service, ...]
    observations: tuple[Observation, ...]
    evidence: tuple[Evidence, ...]


class NaabuLine(Record):
    ip: Candidate
    host: Candidate | None = None
    port: Port
    protocol: Literal["tcp"]
    tls: Literal[False] = False

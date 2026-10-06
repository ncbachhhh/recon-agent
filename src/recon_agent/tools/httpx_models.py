"""Internal HTTP probing schemas; domain facts use generic endpoints/evidence."""

from typing import Annotated, Literal

from pydantic import Field

from recon_agent.core.errors import ErrorInfo
from recon_agent.domain import Asset, Endpoint, Evidence, Observation
from recon_agent.domain._base import Record
from recon_agent.tools.dns_models import DnsContext

Candidate = Annotated[str, Field(min_length=1, max_length=2048)]
Hint = Annotated[str, Field(max_length=4096)]


class HttpxInput(Record):
    """Empty candidates probes the primary target; otherwise an atomic batch."""

    candidates: list[Candidate] = Field(default_factory=list, max_length=64)


class HttpxContext(DnsContext):
    """Caller owns subject, lifecycle and explicit execution/time identity."""


class HttpProbeOutput(Record):
    """Adapter envelope, not a new scanner-specific domain result entity."""

    query_target: Candidate
    candidates: tuple[str, ...]
    contact_addresses: tuple[str, ...]
    resolver_address: str
    source_version: Literal["1.9.0"] = "1.9.0"
    status: Literal["completed", "partial"]
    malformed_lines: int = Field(ge=0)
    unreported_candidates: tuple[str, ...]
    errors: tuple[ErrorInfo, ...] = ()
    asset: Asset
    endpoints: tuple[Endpoint, ...]
    observations: tuple[Observation, ...]
    evidence: tuple[Evidence, ...]


class HttpxLine(Record):
    """Selected fields from reviewed JSONL; optional facts remain absent."""

    input: Candidate
    url: Candidate
    host_ip: Annotated[str, Field(min_length=1, max_length=45)]
    status_code: int = Field(ge=100, le=599)
    failed: Literal[False]
    final_url: Candidate | None = None
    scheme: Literal["http", "https"] | None = None
    host: Annotated[str, Field(max_length=254)] | None = None
    port: Annotated[str, Field(pattern=r"^[0-9]{1,5}$")] | None = None
    method: Literal["GET"] | None = None
    title: Hint | None = None
    webserver: Hint | None = None
    content_type: Hint | None = None
    content_length: int | None = Field(default=None, ge=0, le=9223372036854775807)
    location: Candidate | None = None
    tech: list[Annotated[str, Field(min_length=1, max_length=256)]] | None = Field(
        default=None, max_length=64
    )

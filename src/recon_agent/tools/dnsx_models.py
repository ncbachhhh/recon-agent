"""Strict bulk verification contracts; scanner evidence never grants authority."""

from typing import Annotated, Literal

from pydantic import Field, JsonValue

from recon_agent.core.errors import ErrorInfo
from recon_agent.domain import Asset, Evidence, Observation
from recon_agent.domain._base import NonEmptyText, Record
from recon_agent.tools.dns_models import DnsContext, DnsRecord, DnsRecordType

Candidate = Annotated[str, Field(min_length=1, max_length=254)]


class DnsxInput(Record):
    """All batch entries are secondary policy targets, including duplicates."""

    candidates: list[Candidate] = Field(min_length=1, max_length=64)
    record_type: DnsRecordType = "A"


class DnsxContext(DnsContext):
    """Caller supplies the authorized primary subject; batch facts retain names."""


class DnsxQuery(Record):
    query_target: NonEmptyText
    status_code: Literal[
        "NOERROR", "NXDOMAIN", "SERVFAIL", "REFUSED", "FORMERR", "NOTIMP"
    ]
    records: tuple[DnsRecord, ...]
    wildcard_status: Literal["not_checked", "suspected_shared_address"] = "not_checked"
    # DNSX merges Answer, Ns and Extra; section/answer attribution is unavailable.
    section: Literal["unspecified"] = "unspecified"


class DnsxOutput(Record):
    query_target: NonEmptyText
    candidates: tuple[str, ...]
    record_type: DnsRecordType
    resolver_address: NonEmptyText
    source_version: Literal["1.2.2"] = "1.2.2"
    status: Literal["completed", "partial"]
    malformed_lines: int = Field(ge=0)
    unreported_candidates: tuple[str, ...]
    queries: tuple[DnsxQuery, ...]
    errors: tuple[ErrorInfo, ...] = ()
    asset: Asset
    observations: tuple[Observation, ...]
    evidence: tuple[Evidence, ...]


class DnsxLine(Record):
    """Reviewed JSONL metadata. Aggregated arrays/raw_resp are never trusted facts."""

    host: Candidate
    resolver: list[str] = Field(min_length=1, max_length=1)
    status_code: Literal[
        "NOERROR", "NXDOMAIN", "SERVFAIL", "REFUSED", "FORMERR", "NOTIMP"
    ]
    timestamp: str = Field(min_length=1, max_length=64)
    all: list[Annotated[str, Field(max_length=8192)]] = Field(
        default_factory=list, max_length=256
    )
    ttl: int = Field(default=0, ge=0, le=4294967295)
    a: list[Candidate] = Field(default_factory=list, max_length=256)
    aaaa: list[Candidate] = Field(default_factory=list, max_length=256)
    cname: list[Candidate] = Field(default_factory=list, max_length=256)
    mx: list[Candidate] = Field(default_factory=list, max_length=256)
    ns: list[Candidate] = Field(default_factory=list, max_length=256)
    txt: list[Annotated[str, Field(max_length=8192)]] = Field(
        default_factory=list, max_length=256
    )
    ptr: list[Candidate] = Field(default_factory=list, max_length=256)
    srv: list[Candidate] = Field(default_factory=list, max_length=256)
    caa: list[Annotated[str, Field(max_length=8192)]] = Field(
        default_factory=list, max_length=256
    )
    soa: list[dict[str, JsonValue]] = Field(default_factory=list, max_length=256)
    raw_resp: dict[str, JsonValue] | None = None
    has_internal_ips: bool = False
    internal_ips: list[Candidate] = Field(default_factory=list, max_length=256)
    status_code_raw: int = Field(default=0, ge=0, le=65535)
    hosts_file: Literal[False] = False

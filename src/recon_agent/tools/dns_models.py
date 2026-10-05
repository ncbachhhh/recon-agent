"""Strict capability contracts and internal normalized DNS facts, never authority."""

from typing import Annotated, Literal, Self

from pydantic import Field, field_validator, model_validator

from recon_agent.domain import Asset, Evidence, Observation
from recon_agent.domain._base import NonEmptyText, Record, Timestamp

DnsRecordType = Literal["A", "AAAA", "CNAME", "MX", "NS", "TXT"]
RECORD_TYPES: tuple[DnsRecordType, ...] = ("A", "AAAA", "CNAME", "MX", "NS", "TXT")


class DnsInput(Record):
    """Primary hostname comes from ActionRequest.target, not a second parameter."""

    record_types: list[DnsRecordType] = Field(
        default_factory=lambda: list(RECORD_TYPES), min_length=1, max_length=6
    )

    @field_validator("record_types")
    @classmethod
    def canonical_types(cls, value: list[DnsRecordType]) -> list[DnsRecordType]:
        if len(set(value)) != len(value):
            raise ValueError("duplicate DNS record types")
        return sorted(value)


class DnsContext(Record):
    """Trusted caller supplies subject/execution identity and explicit UTC time."""

    asset_id: NonEmptyText
    execution_id: NonEmptyText
    collected_at: Timestamp


class DnsRecord(Record):
    """Internal DNS fact projected into existing Observation.data."""

    owner: NonEmptyText
    record_type: DnsRecordType
    value: str = Field(max_length=8192)
    ttl: Annotated[int, Field(ge=0, le=2147483647)]
    preference: Annotated[int, Field(ge=0, le=65535)] | None = None
    # TXT is arbitrary octets. Hex retains each character-string losslessly.
    txt_chunks_hex: tuple[str, ...] = ()

    @model_validator(mode="after")
    def type_fields(self) -> Self:
        if (self.record_type == "MX") != (self.preference is not None):
            raise ValueError("only MX requires preference")
        if self.record_type != "TXT" and self.txt_chunks_hex:
            raise ValueError("only TXT has chunks")
        return self


class DnsQueryResult(Record):
    query_target: NonEmptyText
    record_type: DnsRecordType
    outcome: Literal["answer", "no_answer", "nxdomain"]
    records: tuple[DnsRecord, ...] = ()

    @model_validator(mode="after")
    def outcome_records(self) -> Self:
        if self.outcome == "answer" and not self.records:
            raise ValueError("answer outcome requires records")
        if self.outcome == "no_answer" and self.records:
            raise ValueError("no-answer outcome forbids records")
        if self.outcome == "nxdomain" and any(
            record.record_type != "CNAME" for record in self.records
        ):
            raise ValueError("NXDOMAIN may retain only alias records")
        return self


class DnsOutput(Record):
    resolver_address: NonEmptyText
    transport: Literal["udp"] = "udp"
    queries: tuple[DnsQueryResult, ...]
    asset: Asset
    observations: tuple[Observation, ...]
    evidence: tuple[Evidence, ...]

"""Strict TLS inspection envelopes; certificate data never grants authority."""

from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from recon_agent.core.errors import ErrorInfo
from recon_agent.domain import Asset, Evidence, Observation
from recon_agent.domain._base import Port, Record
from recon_agent.tools.dns_models import DnsContext

Candidate = Annotated[str, Field(min_length=1, max_length=2048)]
Text = Annotated[str, Field(max_length=4096)]


class TlsxInput(Record):
    """One port per candidate; empty candidates selects the primary target."""

    candidates: list[Candidate] = Field(default_factory=list, max_length=64)
    port: Port | None = None


class TlsxBinding(Record):
    hostname: Annotated[str, Field(min_length=1, max_length=254)]
    addresses: tuple[Annotated[str, Field(min_length=1, max_length=45)], ...] = Field(
        min_length=1, max_length=64
    )


class TlsxSettings(Record):
    """Operator-selected numeric contacts and a finite allowed port set."""

    bindings: tuple[TlsxBinding, ...] = Field(default=(), max_length=64)
    ports: tuple[Port, ...] = Field(default=(443,), min_length=1, max_length=64)

    @model_validator(mode="after")
    def unique_settings(self) -> Self:
        if len({b.hostname for b in self.bindings}) != len(self.bindings):
            raise ValueError("duplicate hostname binding")
        if len(set(self.ports)) != len(self.ports):
            raise ValueError("duplicate allowed port")
        return self


class TlsxContact(Record):
    host: Candidate
    address: Annotated[str, Field(min_length=1, max_length=45)]
    port: Port


class TlsxContext(DnsContext):
    """Caller supplies subject, execution identity and aware UTC collection time."""


class TlsInspectionOutput(Record):
    query_target: Candidate
    candidates: tuple[str, ...]
    contacts: tuple[TlsxContact, ...]
    source_version: Literal["1.4.0"] = "1.4.0"
    status: Literal["completed", "partial"]
    malformed_lines: int = Field(ge=0)
    unreported_contacts: tuple[TlsxContact, ...]
    errors: tuple[ErrorInfo, ...] = ()
    asset: Asset
    observations: tuple[Observation, ...]
    evidence: tuple[Evidence, ...]


class TlsxLine(Record):
    """Selected bounded source-reviewed JSON fields, not a domain entity."""

    host: Candidate
    ip: Annotated[str, Field(min_length=1, max_length=45)] | None = None
    port: Annotated[str, Field(pattern=r"^[0-9]{1,5}$")]
    probe_status: bool
    error: Text | None = None
    sni: Annotated[str, Field(max_length=254)] | None = None
    tls_connection: Literal["ctls"] | None = None
    tls_version: Literal["tls10", "tls11", "tls12", "tls13"] | None = None
    cipher: Text | None = None
    key_exchange: Text | None = None
    subject_dn: Text | None = None
    subject_cn: Text | None = None
    subject_org: list[Text] | None = Field(default=None, max_length=64)
    subject_an: list[Text] | None = Field(default=None, max_length=128)
    issuer_dn: Text | None = None
    issuer_cn: Text | None = None
    issuer_org: list[Text] | None = Field(default=None, max_length=64)
    serial: Text | None = None
    fingerprint_hash: dict[str, Annotated[str, Field(max_length=256)]] | None = Field(
        default=None, max_length=3
    )
    not_before: Text | None = None
    not_after: Text | None = None
    expired: bool | None = None
    client_cert_required: bool | None = None

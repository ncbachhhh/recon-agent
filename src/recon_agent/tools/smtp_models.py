"""Unauthenticated SMTP profile and trusted observed-service/contact snapshots."""

from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from recon_agent.core.errors import ErrorInfo
from recon_agent.domain import Service
from recon_agent.domain._base import NonEmptyText, Record, Timestamp
from recon_agent.domain.protocols import (
    ProtocolFamily,
    ProtocolMetadataInput,
    ProtocolMetadataOutput,
)


class SmtpInput(ProtocolMetadataInput):
    """Specialize the framework contract; no login, commands or wire options."""

    family: Literal["smtp"]


class SmtpServiceBinding(Record):
    """Trusted caller-selected prior Service, scoped host and numeric contact.

    Discovery/provenance alone grants no permission. The adapter rechecks all
    relevance and current scope immediately before its single contact.
    """

    host: Annotated[str, Field(min_length=1, max_length=253)]
    address: Annotated[str, Field(min_length=1, max_length=45)]
    service: Service


class SmtpContext(Record):
    execution_id: NonEmptyText
    collected_at: Timestamp


class SmtpReply(Record):
    code: int
    lines: tuple[str, ...]
    multiline: bool


class SmtpMetadata(Record):
    """Reported ESMTP advertisements, never verified identity or functionality."""

    banner: str
    greeting_code: int
    product_hint: str | None = None
    version_hint: str | None = None
    ehlo_server_text: str | None = None
    extensions: tuple[str, ...] = ()
    extensions_collected: bool = False
    starttls_advertised: bool | None = None
    auth_mechanisms: tuple[str, ...] = ()
    size_advertised: bool | None = None
    size_limit: int | None = None
    ehlo_reply_code: int | None = None
    limitation: str | None = None


class SmtpOutput(ProtocolMetadataOutput):
    """Generic framework output plus explicit profile and partial limitations."""

    family: Literal[ProtocolFamily.SMTP] = ProtocolFamily.SMTP
    query_target: NonEmptyText
    contact_address: NonEmptyText
    profile: Literal["greeting_ehlo_v1"] = "greeting_ehlo_v1"
    status: Literal["completed", "partial"]
    errors: tuple[ErrorInfo, ...] = Field(default=(), max_length=1)

    @model_validator(mode="after")
    def profile_outcome(self) -> Self:
        if (self.status == "partial") != bool(self.errors):
            raise ValueError("partial SMTP metadata requires a limitation")
        return self

"""Unauthenticated FTP profile and trusted observed-service/contact snapshots."""

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


class FtpInput(ProtocolMetadataInput):
    """Specialize the framework contract; no login, commands or wire options."""

    family: Literal["ftp"]


class FtpServiceBinding(Record):
    """Trusted caller-selected prior Service, scoped host and numeric contact.

    Discovery/provenance alone grants no permission. The adapter rechecks all
    relevance and current scope immediately before its single contact.
    """

    host: Annotated[str, Field(min_length=1, max_length=253)]
    address: Annotated[str, Field(min_length=1, max_length=45)]
    service: Service


class FtpContext(Record):
    execution_id: NonEmptyText
    collected_at: Timestamp


class FtpReply(Record):
    code: int
    lines: tuple[str, ...]
    multiline: bool


class FtpMetadata(Record):
    """Reported pre-authentication metadata, never server identity verification."""

    banner: str
    greeting_code: int
    product_hint: str | None = None
    version_hint: str | None = None
    features: tuple[str, ...] = ()
    features_collected: bool = False
    tls_advertised: bool | None = None
    feat_reply_code: int | None = None
    limitation: str | None = None


class FtpOutput(ProtocolMetadataOutput):
    """Generic framework output plus explicit profile and partial limitations."""

    family: Literal[ProtocolFamily.FTP] = ProtocolFamily.FTP
    query_target: NonEmptyText
    contact_address: NonEmptyText
    profile: Literal["greeting_feat_v1"] = "greeting_feat_v1"
    status: Literal["completed", "partial"]
    errors: tuple[ErrorInfo, ...] = Field(default=(), max_length=1)

    @model_validator(mode="after")
    def profile_outcome(self) -> Self:
        if (self.status == "partial") != bool(self.errors):
            raise ValueError("partial FTP metadata requires a limitation")
        return self

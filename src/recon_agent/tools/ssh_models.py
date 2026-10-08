"""Receive-only SSH profile and trusted observed-service/contact snapshots."""

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


class SshInput(ProtocolMetadataInput):
    """Specialize the framework contract; no login, commands or wire options."""

    family: Literal["ssh"]


class SshServiceBinding(Record):
    """Trusted caller-selected prior Service, scoped host and numeric contact.

    Discovery/provenance alone grants no permission. The adapter rechecks all
    relevance and current scope immediately before its single contact.
    """

    host: Annotated[str, Field(min_length=1, max_length=253)]
    address: Annotated[str, Field(min_length=1, max_length=45)]
    service: Service


class SshContext(Record):
    execution_id: NonEmptyText
    collected_at: Timestamp


class SshGreeting(Record):
    """Parsed reported identification; software claims are never verified facts."""

    banner: str
    protocol_version: str
    software_version: str
    comments: str | None = None
    preamble: tuple[str, ...] = ()
    product_hint: str | None = None
    version_hint: str | None = None
    supported_protocol: bool


class SshOutput(ProtocolMetadataOutput):
    """Generic framework output plus explicit profile and partial limitations."""

    family: Literal[ProtocolFamily.SSH] = ProtocolFamily.SSH
    query_target: NonEmptyText
    contact_address: NonEmptyText
    profile: Literal["server_identification_v1"] = "server_identification_v1"
    status: Literal["completed", "partial"]
    errors: tuple[ErrorInfo, ...] = Field(default=(), max_length=1)

    @model_validator(mode="after")
    def profile_outcome(self) -> Self:
        if (self.status == "partial") != bool(self.errors):
            raise ValueError("partial SSH metadata requires a limitation")
        return self

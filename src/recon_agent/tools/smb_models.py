"""Negotiate-only SMB profile and trusted observed-service/contact snapshots."""

from typing import Annotated, Literal

from pydantic import Field

from recon_agent.core.errors import ErrorInfo
from recon_agent.domain import Service
from recon_agent.domain._base import NonEmptyText, Record, Timestamp
from recon_agent.domain.protocols import (
    ProtocolFamily,
    ProtocolMetadataInput,
    ProtocolMetadataOutput,
)


class SmbInput(ProtocolMetadataInput):
    """Specialize the framework contract; no login, commands or wire options."""

    family: Literal["smb"]


class SmbServiceBinding(Record):
    """Trusted caller-selected prior Service, scoped host and numeric contact.

    Discovery/provenance alone grants no permission. The adapter rechecks all
    relevance and current scope immediately before its single contact.
    """

    host: Annotated[str, Field(min_length=1, max_length=253)]
    address: Annotated[str, Field(min_length=1, max_length=45)]
    service: Service


class SmbContext(Record):
    execution_id: NonEmptyText
    collected_at: Timestamp


SmbDialect = Literal["2.0.2", "2.1", "3.0", "3.0.2"]


class SmbMetadata(Record):
    """Reported negotiation facts, never verified configuration or identity."""

    dialect: SmbDialect
    signing_enabled: bool
    signing_required: bool
    server_guid: str
    capabilities: int
    max_transaction_size: int
    max_read_size: int
    max_write_size: int
    system_time_filetime: int
    server_start_time_filetime: int
    security_buffer_length: int


class SmbOutput(ProtocolMetadataOutput):
    """Success completes negotiation only; inaccessible data is never fabricated."""

    family: Literal[ProtocolFamily.SMB] = ProtocolFamily.SMB
    query_target: NonEmptyText
    contact_address: NonEmptyText
    profile: Literal["smb2_negotiate_v1"] = "smb2_negotiate_v1"
    status: Literal["completed"]
    errors: tuple[ErrorInfo, ...] = Field(default=(), max_length=0)

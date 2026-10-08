"""Finite database semantic inputs and trusted prior Service snapshots."""

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

DatabaseType = Literal["mysql", "postgresql", "redis", "mongodb", "ms-sql-s"]


def database_type(service: Service) -> DatabaseType | None:
    """Exact canonical identities from the existing reviewed relevance catalog."""
    name = service.protocol
    if name is None or not name.isascii():
        return None
    match name.lower():
        case "mysql" | "mariadb":
            return "mysql"
        case "postgresql" | "postgres":
            return "postgresql"
        case "redis":
            return "redis"
        case "mongodb":
            return "mongodb"
        case "ms-sql-s":
            return "ms-sql-s"
    return None


class DatabaseInput(ProtocolMetadataInput):
    """No credentials, connection strings, query, command or low-level options."""

    family: Literal["database"]
    database_type: DatabaseType


class DatabaseServiceBinding(Record):
    host: Annotated[str, Field(min_length=1, max_length=253)]
    address: Annotated[str, Field(min_length=1, max_length=45)]
    service: Service


class DatabaseContext(Record):
    execution_id: NonEmptyText
    collected_at: Timestamp


class DatabaseMetadata(Record):
    database_type: Literal["mysql", "postgresql"]
    profile: Literal["mysql_greeting_v1", "postgresql_ssl_support_v1"]
    protocol_version: int | None = None
    server_version: str | None = None
    product_hint: str | None = None
    connection_id: int | None = None
    capability_flags: int | None = None
    character_set: int | None = None
    status_flags: int | None = None
    ssl_supported: bool | None = None
    limitation: (
        Literal["incomplete_greeting", "unsupported_handshake", "version_unavailable"]
        | None
    ) = None


class DatabaseOutput(ProtocolMetadataOutput):
    family: Literal[ProtocolFamily.DATABASE] = ProtocolFamily.DATABASE
    query_target: NonEmptyText
    contact_address: NonEmptyText
    database_type: Literal["mysql", "postgresql"]
    profile: Literal["mysql_greeting_v1", "postgresql_ssl_support_v1"]
    status: Literal["completed", "partial"]
    errors: tuple[ErrorInfo, ...] = Field(default=(), max_length=1)

    @model_validator(mode="after")
    def profile_outcome(self) -> Self:
        if (self.status == "partial") != bool(self.errors):
            raise ValueError("partial database metadata requires a limitation")
        if (self.database_type == "mysql") != (self.profile == "mysql_greeting_v1"):
            raise ValueError("database profile must match type")
        return self

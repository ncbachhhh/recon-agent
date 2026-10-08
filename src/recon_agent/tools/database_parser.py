"""Bounded pre-authentication metadata; opaque remote tails remain evidence only."""

import base64
import json
import re
from hashlib import sha256

from recon_agent.core.errors import ParserError, ToolExecutionError
from recon_agent.domain import Evidence, Observation
from recon_agent.tools.database_models import (
    DatabaseContext,
    DatabaseMetadata,
    DatabaseOutput,
    DatabaseServiceBinding,
)

MAX_RESPONSE_BYTES = 4096
MAX_VERSION_BYTES = 255


def mysql_payload_size(header: bytes, max_bytes: int) -> int:
    if len(header) != 4 or header[3] != 0:
        raise ValueError("invalid initial MySQL packet header")
    size = int.from_bytes(header[:3], "little")
    if not 1 <= size <= max_bytes - 4:
        raise ValueError("MySQL packet bound")
    return size


def parse_mysql(raw: bytes) -> DatabaseMetadata:
    size = mysql_payload_size(raw[:4], MAX_RESPONSE_BYTES)
    if len(raw) != size + 4:
        raise ValueError("incomplete or extra MySQL frame")
    payload = raw[4:]
    protocol = payload[0]
    if protocol == 0xFF and len(payload) >= 3:
        # Server ERR is a denial, never an invitation to provide credentials.
        raise ToolExecutionError("Database metadata unavailable or access required")
    # Auth packets and unknown handshake grammars cannot yield a version.
    if protocol != 10:
        if protocol != 9:
            raise ValueError("unsupported MySQL initial packet")
        return DatabaseMetadata(
            database_type="mysql",
            profile="mysql_greeting_v1",
            protocol_version=9,
            limitation="unsupported_handshake",
        )
    end = payload.find(b"\0", 1, MAX_VERSION_BYTES + 2)
    if end < 2:
        raise ValueError("invalid MySQL server version")
    version = payload[1:end].decode("utf-8")
    if any(ord(char) < 32 or ord(char) == 127 for char in version):
        raise ValueError("MySQL version contains control characters")
    tail = payload[end + 1 :]
    if len(tail) < 15 or tail[12] != 0:
        raise ValueError("incomplete MySQL fixed greeting fields")
    lower = int.from_bytes(tail[13:15], "little")
    # Older V10 greetings may stop after the low capability word.
    extended = len(tail) >= 31
    if len(tail) != 15 and not extended:
        raise ValueError("truncated MySQL extended greeting")
    flags = lower | (int.from_bytes(tail[18:20], "little") << 16 if extended else 0)
    # Product hints require the entire version grammar; no instruction substrings.
    hint = None
    if re.fullmatch(
        r"[0-9]+(?:\.[0-9]+){2}(?:-[0-9]+(?:\.[0-9]+){2})?-MariaDB(?:-[A-Za-z0-9.+~_-]+)?",
        version,
        re.ASCII,
    ):
        hint = "MariaDB"
    elif re.fullmatch(
        r"[0-9]+(?:\.[0-9]+){2}(?:-[A-Za-z0-9.+~_-]+)?", version, re.ASCII
    ):
        hint = "MySQL-compatible"
    return DatabaseMetadata(
        database_type="mysql",
        profile="mysql_greeting_v1",
        protocol_version=10,
        server_version=version,
        product_hint=hint,
        connection_id=int.from_bytes(tail[:4], "little"),
        capability_flags=flags,
        character_set=tail[15] if extended else None,
        status_flags=int.from_bytes(tail[16:18], "little") if extended else None,
        ssl_supported=bool(flags & 0x800),
        limitation=None if extended else "incomplete_greeting",
    )


def parse_postgresql(raw: bytes) -> DatabaseMetadata:
    if raw not in (b"S", b"N"):
        raise ValueError("invalid PostgreSQL SSL support signal")
    # SSLRequest has no StartupMessage/user/database and reveals no server version.
    return DatabaseMetadata(
        database_type="postgresql",
        profile="postgresql_ssl_support_v1",
        ssl_supported=raw == b"S",
        limitation="version_unavailable",
    )


def parse_metadata(raw: bytes, database_type: str) -> DatabaseMetadata:
    if type(raw) is not bytes or not 1 <= len(raw) <= MAX_RESPONSE_BYTES:
        raise ValueError("database metadata byte bound")
    if database_type == "mysql":
        return parse_mysql(raw)
    if database_type == "postgresql":
        return parse_postgresql(raw)
    raise ValueError("unsupported database profile")


def normalize(
    raw: bytes,
    metadata: DatabaseMetadata,
    target: str,
    binding: DatabaseServiceBinding,
    context: DatabaseContext,
) -> DatabaseOutput:
    snapshot = json.dumps(
        dict(
            query_target=target,
            contact_address=binding.address,
            service_id=binding.service.id,
            host_id=binding.service.host_id,
            port=binding.service.port,
            transport="tcp",
            family="database",
            capability="inspect_protocol",
            **metadata.model_dump(mode="json"),
            raw_response_base64=base64.b64encode(raw).decode("ascii"),
            application_bytes_sent=0 if metadata.database_type == "mysql" else 8,
            authentication_attempted=False,
            queries_sent=False,
            data_accessed=False,
            remote_mutation=False,
            tls_negotiated=False,
        ),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    evidence = Evidence(
        id=f"{context.execution_id}:database:evidence",
        source="native_database",
        origin=f"{target}:{binding.service.port}",
        artifact_reference=f"memory:{context.execution_id}:database:normalized",
        collected_at=context.collected_at,
        execution_id=context.execution_id,
        capability="inspect_protocol",
        locator=metadata.profile,
        sha256=sha256(snapshot.encode()).hexdigest(),
    )
    observation = Observation(
        id=f"{context.execution_id}:database:observation",
        kind="metadata",
        asset_id=binding.service.asset_id,
        source="native_database",
        observed_at=context.collected_at,
        execution_id=context.execution_id,
        evidence_ids=(evidence.id,),
        data=json.loads(snapshot),
    )
    errors = (
        ()
        if metadata.limitation is None
        else (
            ParserError(
                "Database metadata incomplete or unavailable under pre-authentication profile"
            ).to_error_info(),
        )
    )
    return DatabaseOutput(
        service=binding.service,
        query_target=target,
        contact_address=binding.address,
        database_type=metadata.database_type,
        profile=metadata.profile,
        status="partial" if errors else "completed",
        errors=errors,
        observations=(observation,),
        evidence=(evidence,),
    )

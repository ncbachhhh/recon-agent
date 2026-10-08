"""One numeric contact: receive-only MySQL or fixed PostgreSQL SSL support probe."""

import asyncio
import socket
from ipaddress import ip_address
from math import isfinite
from typing import Protocol

from recon_agent.tools.database_parser import MAX_RESPONSE_BYTES, mysql_payload_size

# Int32 length=8, Int32 request=80877103. No protocol/user/database/startup fields.
POSTGRESQL_SSL_REQUEST = b"\x00\x00\x00\x08\x04\xd2\x16\x2f"


class DatabaseTransport(Protocol):
    async def inspect(
        self,
        address: str,
        port: int,
        database_type: str,
        timeout_seconds: float,
        max_bytes: int,
    ) -> bytes: ...


async def _mysql_greeting(reader: asyncio.StreamReader, max_bytes: int) -> bytes:
    header = await reader.readexactly(4)
    size = mysql_payload_size(header, max_bytes)
    return header + await reader.readexactly(size)


async def _postgresql_signal(
    reader: asyncio.StreamReader, writer: asyncio.StreamWriter
) -> bytes:
    # The sole application write in this module; immutable and never remote-derived.
    writer.write(POSTGRESQL_SSL_REQUEST)
    await writer.drain()
    return await reader.readexactly(1)


class NativeDatabaseTransport:
    async def inspect(
        self,
        address: str,
        port: int,
        database_type: str,
        timeout_seconds: float,
        max_bytes: int,
    ) -> bytes:
        numeric = ip_address(address)
        if (
            str(numeric) != address
            or "%" in address
            or getattr(numeric, "ipv4_mapped", None)
            or type(port) is not int
            or not 1 <= port <= 65535
            or database_type not in ("mysql", "postgresql")
            or type(max_bytes) is not int
            or not 1 <= max_bytes <= MAX_RESPONSE_BYTES
            or (database_type == "mysql" and max_bytes < 5)
            or type(timeout_seconds) not in (int, float)
            or not isfinite(timeout_seconds)
            or timeout_seconds <= 0
        ):
            raise ValueError("unsupported database contact or allowance")
        writer: asyncio.StreamWriter | None = None
        try:
            async with asyncio.timeout(timeout_seconds):
                reader, writer = await asyncio.open_connection(
                    address,
                    port,
                    family=socket.AF_INET if numeric.version == 4 else socket.AF_INET6,
                    flags=socket.AI_NUMERICHOST | socket.AI_NUMERICSERV,
                    limit=MAX_RESPONSE_BYTES,
                )
                if database_type == "mysql":
                    return await _mysql_greeting(reader, max_bytes)
                return await _postgresql_signal(reader, writer)
        except asyncio.IncompleteReadError as cause:
            if not cause.partial:
                raise ConnectionError(
                    "Database connection closed before metadata"
                ) from cause
            raise ValueError("incomplete database metadata frame") from cause
        finally:
            if writer is not None:
                writer.close()
                writer.transport.abort()

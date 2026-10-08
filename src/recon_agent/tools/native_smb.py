"""Single fixed SMB2 negotiation over scoped numeric TCP, then abort."""

import asyncio
import socket
from ipaddress import ip_address
from math import isfinite
from typing import Protocol
from uuid import uuid4

from recon_agent.tools.smb_parser import (
    MAX_RESPONSE_BYTES,
    negotiate_request,
    response_size,
)


class SmbTransport(Protocol):
    async def negotiate(
        self, address: str, port: int, timeout_seconds: float, max_bytes: int
    ) -> bytes: ...


class NativeSmbTransport:
    async def negotiate(
        self, address: str, port: int, timeout_seconds: float, max_bytes: int
    ) -> bytes:
        numeric = ip_address(address)
        if (
            str(numeric) != address
            or "%" in address
            or getattr(numeric, "ipv4_mapped", None)
            or type(port) is not int
            or not 1 <= port <= 65535
            or port == 139
            or type(max_bytes) is not int
            or not 76 <= max_bytes <= MAX_RESPONSE_BYTES
            or type(timeout_seconds) not in (int, float)
            or not isfinite(timeout_seconds)
            or timeout_seconds <= 0
        ):
            raise ValueError("Unsupported SMB numeric contact or allowance")
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
                # Sole outbound application message. No remote input can change it.
                writer.write(negotiate_request(uuid4()))
                await writer.drain()
                header = await reader.readexactly(4)
                size = response_size(header, max_bytes)
                return header + await reader.readexactly(size)
        except asyncio.IncompleteReadError as cause:
            if not cause.partial:
                raise ConnectionError(
                    "SMB connection closed before complete response"
                ) from cause
            raise ValueError("Incomplete SMB frame") from cause
        finally:
            if writer is not None:
                writer.close()
                writer.transport.abort()

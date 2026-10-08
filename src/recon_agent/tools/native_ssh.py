"""One receive-only numeric TCP connection. No SSH client messages exist here."""

import asyncio
import socket
from ipaddress import ip_address
from math import isfinite
from typing import Protocol

from recon_agent.tools.ssh_parser import (
    MAX_GREETING_BYTES,
    MAX_IDENTIFICATION_BYTES,
    MAX_LINE_BYTES,
    MAX_PREAMBLE_LINES,
)


class SshBannerTransport(Protocol):
    async def receive(
        self, address: str, port: int, timeout_seconds: float, max_bytes: int
    ) -> bytes: ...


class NativeSshBannerTransport:
    async def receive(
        self, address: str, port: int, timeout_seconds: float, max_bytes: int
    ) -> bytes:
        # Internal defense in depth; the trusted adapter already validated scope.
        numeric = ip_address(address)
        if (
            str(numeric) != address
            or "%" in address
            or getattr(numeric, "ipv4_mapped", None)
            or type(port) is not int
            or not 1 <= port <= 65535
            or type(max_bytes) is not int
            or not 1 <= max_bytes <= MAX_GREETING_BYTES
            or type(timeout_seconds) not in (int, float)
            or not isfinite(timeout_seconds)
            or timeout_seconds <= 0
        ):
            raise ValueError("unsupported SSH numeric contact or allowance")
        writer: asyncio.StreamWriter | None = None
        captured = bytearray()
        line = bytearray()
        preamble_lines = 0
        try:
            async with asyncio.timeout(timeout_seconds):
                reader, writer = await asyncio.open_connection(
                    address,
                    port,
                    family=socket.AF_INET if numeric.version == 4 else socket.AF_INET6,
                    flags=socket.AI_NUMERICHOST | socket.AI_NUMERICSERV,
                    limit=MAX_LINE_BYTES,
                )
                while len(captured) < max_bytes:
                    # Stop at identification LF, before reading binary SSH packets.
                    chunk = await reader.read(1)
                    if not chunk:
                        if not captured:
                            raise ConnectionError(
                                "SSH connection closed before greeting"
                            )
                        return bytes(captured)
                    captured.extend(chunk)
                    line.extend(chunk)
                    identification = line.startswith(b"SSH-")
                    if len(line) > (
                        MAX_IDENTIFICATION_BYTES if identification else MAX_LINE_BYTES
                    ):
                        raise ValueError("SSH greeting line bound")
                    if chunk == b"\n":
                        if identification:
                            return bytes(captured)
                        preamble_lines += 1
                        if preamble_lines > MAX_PREAMBLE_LINES:
                            raise ValueError("SSH preamble line bound")
                        line.clear()
                raise ValueError("SSH greeting aggregate byte bound")
        finally:
            if writer is not None:
                # Synchronous abort discards unread packets; cancellation cannot
                # interrupt cleanup with a second await or unbounded wait_closed.
                writer.close()
                writer.transport.abort()

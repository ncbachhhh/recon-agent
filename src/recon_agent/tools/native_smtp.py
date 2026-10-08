"""One numeric SMTP control connection; only the immutable EHLO request is sent."""

import asyncio
import socket
from ipaddress import ip_address
from math import isfinite
from typing import Protocol

from recon_agent.tools.smtp_parser import (
    MAX_CAPTURE_BYTES,
    MAX_LINE_BYTES,
    MAX_REPLY_LINES,
    parse_reply,
    parse_reply_line,
)

# Fixed synthetic documentation-address literal: no planner/remote hostname or
# local hostname lookup. It is an inspection label, not a verified client identity.
EHLO_REQUEST = b"EHLO [192.0.2.1]\r\n"


class SmtpTransport(Protocol):
    async def inspect(
        self, address: str, port: int, timeout_seconds: float, max_bytes: int
    ) -> bytes: ...


async def _read_reply(reader: asyncio.StreamReader, allowance: int) -> bytes:
    captured = bytearray()
    line = bytearray()
    code: int | None = None
    lines = 0
    while len(captured) < allowance:
        chunk = await reader.read(1)
        if not chunk:
            return bytes(captured)
        captured.extend(chunk)
        line.extend(chunk)
        if len(line) > MAX_LINE_BYTES:
            raise ValueError("SMTP line byte bound")
        if chunk == b"\n":
            lines += 1
            if lines > MAX_REPLY_LINES:
                raise ValueError("SMTP reply line count bound")
            line_code, continuation, _ = parse_reply_line(bytes(line))
            if code is not None and line_code != code:
                raise ValueError("inconsistent SMTP reply codes")
            code = line_code
            if not continuation:
                return bytes(captured)
            line.clear()
    raise ValueError("SMTP capture byte bound")


class NativeSmtpTransport:
    async def inspect(
        self, address: str, port: int, timeout_seconds: float, max_bytes: int
    ) -> bytes:
        numeric = ip_address(address)
        if (
            str(numeric) != address
            or "%" in address
            or getattr(numeric, "ipv4_mapped", None)
            or type(port) is not int
            or not 1 <= port <= 65535
            or port == 465
            or type(max_bytes) is not int
            or not 1 <= max_bytes <= MAX_CAPTURE_BYTES
            or type(timeout_seconds) not in (int, float)
            or not isfinite(timeout_seconds)
            or timeout_seconds <= 0
        ):
            raise ValueError("unsupported SMTP numeric contact or allowance")
        writer: asyncio.StreamWriter | None = None
        try:
            async with asyncio.timeout(timeout_seconds):
                reader, writer = await asyncio.open_connection(
                    address,
                    port,
                    family=socket.AF_INET if numeric.version == 4 else socket.AF_INET6,
                    flags=socket.AI_NUMERICHOST | socket.AI_NUMERICSERV,
                    limit=MAX_LINE_BYTES,
                )
                greeting = await _read_reply(reader, max_bytes)
                if not greeting:
                    raise ConnectionError("SMTP closed before greeting")
                reply, _ = parse_reply(greeting)
                if reply.code != 220 or len(greeting) == max_bytes:
                    return greeting
                writer.write(EHLO_REQUEST)
                await writer.drain()
                # Preserve an already valid greeting for bounded malformed/EOF
                # EHLO replies. Timeouts/connection errors still fail the action.
                try:
                    extensions = await _read_reply(reader, max_bytes - len(greeting))
                except ValueError:
                    return greeting
                return greeting + extensions
        finally:
            if writer is not None:
                writer.close()
                writer.transport.abort()

"""One numeric FTP control connection; only the immutable FEAT request is sent."""

import asyncio
import socket
from ipaddress import ip_address
from math import isfinite
from typing import Protocol

from recon_agent.tools.ftp_parser import (
    MAX_CAPTURE_BYTES,
    MAX_LINE_BYTES,
    MAX_REPLY_LINES,
    parse_reply,
)

FEAT_REQUEST = b"FEAT\r\n"


class FtpTransport(Protocol):
    async def inspect(
        self, address: str, port: int, timeout_seconds: float, max_bytes: int
    ) -> bytes: ...


async def _read_reply(reader: asyncio.StreamReader, allowance: int) -> bytes:
    captured = bytearray()
    line = bytearray()
    code: bytes | None = None
    lines = 0
    while len(captured) < allowance:
        chunk = await reader.read(1)
        if not chunk:
            return bytes(captured)
        captured.extend(chunk)
        line.extend(chunk)
        if len(line) > MAX_LINE_BYTES:
            raise ValueError("FTP line byte bound")
        if chunk == b"\n":
            lines += 1
            if lines > MAX_REPLY_LINES:
                raise ValueError("FTP reply line count bound")
            if code is None:
                # Validate the first line before trusting multiline framing.
                if len(line) < 6 or not line.endswith(b"\r\n"):
                    raise ValueError("malformed FTP line")
                code = bytes(line[:3])
                if line[3:4] == b" ":
                    return bytes(captured)
                if line[3:4] != b"-" or not code.isdigit():
                    raise ValueError("malformed FTP reply prefix")
            elif line.startswith(code + b" "):
                return bytes(captured)
            line.clear()
    raise ValueError("FTP capture byte bound")


class NativeFtpTransport:
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
            or type(max_bytes) is not int
            or not 1 <= max_bytes <= MAX_CAPTURE_BYTES
            or type(timeout_seconds) not in (int, float)
            or not isfinite(timeout_seconds)
            or timeout_seconds <= 0
        ):
            raise ValueError("unsupported FTP numeric contact or allowance")
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
                    raise ConnectionError("FTP closed before greeting")
                reply, _ = parse_reply(greeting)
                if reply.code != 220 or len(greeting) == max_bytes:
                    return greeting
                writer.write(FEAT_REQUEST)
                await writer.drain()
                # Preserve an already valid greeting for bounded malformed/EOF
                # feature replies. Timeouts/connection errors still fail the action.
                try:
                    features = await _read_reply(reader, max_bytes - len(greeting))
                except ValueError:
                    return greeting
                return greeting + features
        finally:
            if writer is not None:
                writer.close()
                writer.transport.abort()

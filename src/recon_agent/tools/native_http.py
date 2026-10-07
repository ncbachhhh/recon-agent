"""Single HTTP GET over a pinned numeric socket; no DNS/proxy/redirect/retry."""

import asyncio
import ssl
from ipaddress import ip_address
from typing import Protocol
from urllib.parse import urlsplit

import h11

from recon_agent.core.errors import ParserError
from recon_agent.tools.common_files_models import HttpResponse

HEADER_LIMIT = 16_384
WIRE_OVERHEAD_LIMIT = 65_536


class HttpTransport(Protocol):
    async def get(
        self, url: str, address: str, timeout_seconds: float, max_body_bytes: int
    ) -> HttpResponse: ...


class NativeHttpTransport:
    async def get(
        self, url: str, address: str, timeout_seconds: float, max_body_bytes: int
    ) -> HttpResponse:
        # Only trusted adapter-normalized URLs and independently approved contacts.
        address = str(ip_address(address))
        parts = urlsplit(url)
        if parts.scheme not in ("http", "https") or not parts.hostname:
            raise ValueError("unsupported HTTP destination")
        response: HttpResponse | None = None
        body = bytearray()
        writer: asyncio.StreamWriter | None = None
        try:
            async with asyncio.timeout(timeout_seconds):
                reader, writer = await asyncio.open_connection(
                    address,
                    parts.port or (443 if parts.scheme == "https" else 80),
                    ssl=ssl.create_default_context()
                    if parts.scheme == "https"
                    else None,
                    server_hostname=parts.hostname if parts.scheme == "https" else None,
                    limit=HEADER_LIMIT,
                )
                connection = h11.Connection(
                    h11.CLIENT, max_incomplete_event_size=HEADER_LIMIT
                )
                request = h11.Request(
                    method="GET",
                    target=parts.path + ("?" + parts.query if parts.query else ""),
                    headers=[
                        ("Host", parts.netloc),
                        ("Connection", "close"),
                        ("Accept-Encoding", "identity"),
                        ("User-Agent", "recon-agent/0.1 common-files"),
                    ],
                )
                writer.write(connection.send(request) or b"")
                writer.write(connection.send(h11.EndOfMessage()) or b"")
                await writer.drain()
                wire_bytes = 0
                informational = 0
                eof = False
                while True:
                    event = connection.next_event()
                    if event is h11.NEED_DATA:
                        if eof:
                            raise ValueError("incomplete HTTP response")
                        chunk = await reader.read(4096)
                        eof = not chunk
                        wire_bytes += len(chunk)
                        if wire_bytes > max_body_bytes + WIRE_OVERHEAD_LIMIT:
                            raise ValueError("HTTP wire bound exceeded")
                        if response is None and wire_bytes > HEADER_LIMIT:
                            raise ValueError("HTTP header bound exceeded")
                        connection.receive_data(chunk)
                    elif isinstance(event, h11.InformationalResponse):
                        informational += 1
                        if event.status_code == 101 or informational > 4:
                            raise ValueError(
                                "unsupported HTTP upgrade/interim response"
                            )
                    elif isinstance(event, h11.Response):
                        if response is not None:
                            raise ValueError("duplicate HTTP response")
                        headers = list(event.headers)
                        if sum(len(k) + len(v) + 4 for k, v in headers) > HEADER_LIMIT:
                            raise ValueError("HTTP header bound exceeded")
                        selected: dict[str, str] = {}
                        for name, value in headers:
                            key = name.decode("ascii")
                            if key in (
                                "content-type",
                                "content-length",
                                "content-encoding",
                                "location",
                            ):
                                if key in selected:
                                    raise ValueError("ambiguous HTTP metadata")
                                selected[key] = value.decode("latin-1")
                        response = HttpResponse(
                            status_code=event.status_code,
                            content_type=selected.get("content-type"),
                            content_length=int(selected["content-length"])
                            if "content-length" in selected
                            else None,
                            content_encoding=selected.get("content-encoding"),
                            location=selected.get("location"),
                        )
                    elif isinstance(event, h11.Data):
                        if response is None:
                            raise ValueError("HTTP body without response")
                        remaining = max_body_bytes - len(body)
                        body.extend(event.data[:remaining])
                        if len(event.data) > remaining:
                            return response.model_copy(
                                update={"body": bytes(body), "truncated": True}
                            )
                    elif isinstance(event, h11.EndOfMessage):
                        if response is None:
                            raise ValueError("missing HTTP response")
                        if (
                            sum(len(k) + len(v) + 4 for k, v in event.headers)
                            > HEADER_LIMIT
                        ):
                            raise ValueError("HTTP trailer bound exceeded")
                        return response.model_copy(update={"body": bytes(body)})
                    else:
                        raise ValueError("unexpected HTTP framing")
        except h11.ProtocolError as cause:
            if response is not None:
                return response.model_copy(
                    update={
                        "body": bytes(body),
                        "truncated": True,
                        "errors": (
                            ParserError(
                                "Incomplete or malformed HTTP framing"
                            ).to_error_info(),
                        ),
                    }
                )
            raise ValueError("invalid HTTP framing") from cause
        finally:
            if writer is not None:
                # Close immediately even on repeated cancellation. Avoid unbounded
                # TLS wait_closed; transport abort discards unread excess safely.
                writer.close()
                writer.transport.abort()

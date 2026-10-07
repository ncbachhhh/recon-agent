"""Native HTTP framing via fake streams; no server, resolver or live socket."""

import asyncio
import socket
from unittest.mock import Mock

import pytest

from recon_agent.core.errors import ErrorCode
from recon_agent.tools.native_http import NativeHttpTransport


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    blocked = Mock(side_effect=AssertionError("unexpected network/DNS"))
    for name in ("getaddrinfo", "gethostbyname", "create_connection"):
        monkeypatch.setattr(socket, name, blocked)
    for name in ("connect", "connect_ex", "sendto", "bind", "listen"):
        original = getattr(socket.socket, name)

        def guarded(self, *args, _original=original, **kwargs):
            if self.family != socket.AF_UNIX:
                return blocked()
            return _original(self, *args, **kwargs)

        monkeypatch.setattr(socket.socket, name, guarded)
    yield
    blocked.assert_not_called()


class Reader:
    def __init__(self, wire, chunk_size=4096):
        self.wire = wire
        self.chunk_size = chunk_size
        self.calls = []

    async def read(self, size):
        self.calls.append(size)
        part, self.wire = (
            self.wire[: min(size, self.chunk_size)],
            self.wire[min(size, self.chunk_size) :],
        )
        return part


class Writer:
    def __init__(self):
        self.data = b""
        self.closed = False
        self.transport = Mock()

    def write(self, value):
        self.data += value

    async def drain(self):
        pass

    def close(self):
        self.closed = True


def exchange(
    monkeypatch,
    wire,
    *,
    url="https://example.test:8443/robots.txt",
    size=16384,
    chunk_size=4096,
):
    reader = Reader(wire, chunk_size)
    writer = Writer()
    calls = []

    async def connect(*args, **kwargs):
        calls.append((args, kwargs))
        return reader, writer

    monkeypatch.setattr(asyncio, "open_connection", connect)
    result = asyncio.run(NativeHttpTransport().get(url, "192.0.2.10", 0.5, size))
    assert writer.closed
    writer.transport.abort.assert_called_once()
    return result, reader, writer, calls


@pytest.mark.parametrize(
    "framing", [b"Content-Length: 5\r\n", b"Transfer-Encoding: chunked\r\n", b""]
)
def test_http_framing_and_fixed_request(monkeypatch, framing):
    body = b"5\r\nhello\r\n0\r\n\r\n" if b"chunked" in framing else b"hello"
    wire = b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n" + framing + b"\r\n" + body
    out, reader, writer, calls = exchange(monkeypatch, wire, chunk_size=7)
    assert out.status_code == 200
    assert out.body == b"hello"
    assert out.truncated is False
    assert out.content_type == "text/plain"
    assert calls[0][0] == ("192.0.2.10", 8443)
    context = calls[0][1]["ssl"]
    assert context.check_hostname
    assert calls[0][1]["server_hostname"] == "example.test"
    assert writer.data == (
        b"GET /robots.txt HTTP/1.1\r\nHost: example.test:8443\r\n"
        b"Connection: close\r\nAccept-Encoding: identity\r\nUser-Agent: recon-agent/0.1 common-files\r\n\r\n"
    )
    assert set(reader.calls) == {4096}


def test_http_plain_does_not_enable_tls_or_follow_location(monkeypatch):
    wire = b"HTTP/1.1 302 Found\r\nLocation: https://outside.test/robots.txt\r\nContent-Length: 0\r\n\r\n"
    out, _, _, calls = exchange(monkeypatch, wire, url="http://example.test/robots.txt")
    assert out.location == "https://outside.test/robots.txt"
    assert calls[0][0] == ("192.0.2.10", 80)
    assert calls[0][1]["ssl"] is None
    assert calls[0][1]["server_hostname"] is None
    assert len(calls) == 1


@pytest.mark.parametrize("chunked", [False, True])
def test_body_overflow_stops_reading_and_keeps_exact_prefix(monkeypatch, chunked):
    body = b"x" * 100000
    headers = b"Transfer-Encoding: chunked" if chunked else b"Content-Length: 100000"
    wirebody = b"186a0\r\n" + body + b"\r\n0\r\n\r\n" if chunked else body
    wire = b"HTTP/1.1 200 OK\r\n" + headers + b"\r\n\r\n" + wirebody
    out, reader, _, _ = exchange(monkeypatch, wire, size=10)
    assert out.body == b"x" * 10
    assert out.truncated
    assert len(reader.calls) == 1
    assert reader.wire


def test_exact_body_bound_is_complete(monkeypatch):
    out, _, _, _ = exchange(
        monkeypatch, b"HTTP/1.1 200 OK\r\nContent-Length: 5\r\n\r\nhello", size=5
    )
    assert out.body == b"hello"
    assert not out.truncated


def test_incomplete_framing_keeps_bounded_partial_body(monkeypatch):
    out, _, _, _ = exchange(
        monkeypatch, b"HTTP/1.1 200 OK\r\nContent-Length: 10\r\n\r\nhello"
    )
    assert out.body == b"hello"
    assert out.truncated
    assert out.errors[0].code == ErrorCode.PARSE_FAILED


@pytest.mark.parametrize(
    "wire",
    [
        b"invalid HTTP\r\n\r\n",
        b"",
        b"HTTP/1.1 101 Upgrade\r\n\r\n",
        b"HTTP/1.1 100 Continue\r\n\r\n" * 5,
        b"HTTP/1.1 200 OK\r\nX-Large: " + b"x" * 20000 + b"\r\n\r\n",
        b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Type: text/html\r\n\r\n",
        b"HTTP/1.1 200 OK\r\nContent-Length: -1\r\n\r\n",
        b"HTTP/1.1 200 OK\r\nContent-Length: 99999999999999999999\r\n\r\n",
        b"HTTP/1.1 200 OK\r\nLocation: " + b"x" * 2049 + b"\r\n\r\n",
    ],
)
def test_malformed_or_oversized_metadata_closes_transport(monkeypatch, wire):
    reader = Reader(wire)
    writer = Writer()

    async def connect(*args, **kwargs):
        return reader, writer

    monkeypatch.setattr(asyncio, "open_connection", connect)
    with pytest.raises(ValueError):
        asyncio.run(
            NativeHttpTransport().get(
                "http://example.test/robots.txt", "192.0.2.10", 0.5, 16384
            )
        )
    assert writer.closed
    writer.transport.abort.assert_called_once()


def test_wire_overhead_is_bounded_even_for_many_tiny_chunks(monkeypatch):
    wire = (
        b"HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n"
        + (b"1;" + b"x" * 9000 + b"\r\na\r\n") * 8
        + b"0\r\n\r\n"
    )
    with pytest.raises(ValueError):
        exchange(monkeypatch, wire, size=10)


def test_interim_response_and_chunk_trailers_are_not_additional_contacts(monkeypatch):
    wire = (
        b"HTTP/1.1 100 Continue\r\n\r\nHTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n"
        b"5\r\nhello\r\n0\r\nX-Trailer: untrusted\r\n\r\n"
    )
    out, _, _, calls = exchange(monkeypatch, wire)
    assert out.body == b"hello"
    assert len(calls) == 1


def test_transport_timeout_and_cancellation_abort_stream(monkeypatch):
    async def scenario(cancel):
        writer = Writer()
        entered = asyncio.Event()

        class HangingReader:
            async def read(self, size):
                entered.set()
                await asyncio.Event().wait()

        async def connect(*args, **kwargs):
            return HangingReader(), writer

        monkeypatch.setattr(asyncio, "open_connection", connect)
        task = asyncio.create_task(
            NativeHttpTransport().get(
                "http://example.test/robots.txt", "192.0.2.10", 0.01, 16384
            )
        )
        await entered.wait()
        if cancel:
            task.cancel()
        with pytest.raises(asyncio.CancelledError if cancel else TimeoutError):
            await task
        assert writer.closed
        writer.transport.abort.assert_called_once()

    asyncio.run(scenario(False))
    asyncio.run(scenario(True))


def test_complete_oversized_trailer_is_rejected_even_at_read_boundary(monkeypatch):
    wire = (
        b"HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n"
        b"1\r\na\r\n0\r\nX-Trailer: " + b"x" * 17000 + b"\r\n\r\n"
    )
    with pytest.raises(ValueError):
        exchange(monkeypatch, wire)


def test_connection_failure_and_invalid_native_destination(monkeypatch):
    async def connect(*args, **kwargs):
        raise ConnectionError

    monkeypatch.setattr(asyncio, "open_connection", connect)
    with pytest.raises(ConnectionError):
        asyncio.run(
            NativeHttpTransport().get(
                "http://example.test/robots.txt", "192.0.2.10", 0.5, 16384
            )
        )
    with pytest.raises(ValueError):
        asyncio.run(
            NativeHttpTransport().get("file:///etc/passwd", "192.0.2.10", 0.5, 16384)
        )

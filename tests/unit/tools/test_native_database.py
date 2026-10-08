"""Fake-stream receive-only regression: zero client packets, never authentication."""

import asyncio
import socket
import subprocess
from unittest.mock import Mock

import pytest

from recon_agent.tools.database_parser import MAX_RESPONSE_BYTES
from recon_agent.tools.native_database import NativeDatabaseTransport


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    blocked = Mock(
        side_effect=AssertionError("native database attempted real DNS/contact/process")
    )
    for name in (
        "getaddrinfo",
        "gethostbyname",
        "gethostbyname_ex",
        "gethostbyaddr",
        "create_connection",
    ):
        monkeypatch.setattr(socket, name, blocked)
    for name in ("connect", "connect_ex", "sendto", "bind", "listen"):
        original = getattr(socket.socket, name)

        def guarded(self, *args, _original=original, **kwargs):
            if self.family != socket.AF_UNIX:
                return blocked()
            return _original(self, *args, **kwargs)

        monkeypatch.setattr(socket.socket, name, guarded)
    for name in ("Popen", "run", "call", "check_call", "check_output"):
        monkeypatch.setattr(subprocess, name, blocked)
    monkeypatch.setattr(asyncio, "create_subprocess_exec", blocked)
    monkeypatch.setattr(asyncio, "create_subprocess_shell", blocked)
    yield blocked
    blocked.assert_not_called()


# Independent bytes: sequence 0, V10/version, fixed header, opaque auth offer.
MYSQL = bytes.fromhex(
    "4a0000000a382e302e3430002a000000616263646566676800ffff210200ffff15000000000000000000006a6b6c6d6e6f707172737475006d7973716c5f6e61746976655f70617373776f726400"
)
SSL_REQUEST = bytes.fromhex("0000000804d2162f")


class Reader:
    def __init__(self, wire):
        self.wire = wire
        self.calls = []

    async def readexactly(self, size):
        self.calls.append(size)
        chunk, self.wire = self.wire[:size], self.wire[size:]
        if len(chunk) < size:
            raise asyncio.IncompleteReadError(chunk, size)
        return chunk


class Writer:
    def __init__(self):
        self.closed = False
        self.transport = Mock()
        self.writes = []
        self.writelines = Mock(
            side_effect=AssertionError("arbitrary database writes forbidden")
        )
        self.drains = 0

    def write(self, value):
        # No credentials/StartupMessage/SQL/RESP/BSON/MySQL commands allowed.
        assert value == SSL_REQUEST
        self.writes.append(value)
        assert len(self.writes) == 1

    async def drain(self):
        self.drains += 1

    def close(self):
        self.closed = True


def prepare(monkeypatch, wire, reader=None):
    reader = reader or Reader(wire)
    writer = Writer()
    calls = []

    async def connect(*args, **kwargs):
        calls.append((args, kwargs))
        return reader, writer

    monkeypatch.setattr(asyncio, "open_connection", connect)
    return reader, writer, calls


def inspect(kind="mysql", **kwargs):
    return asyncio.run(
        NativeDatabaseTransport().inspect(
            **{
                "address": "192.0.2.10",
                "port": 3306,
                "database_type": kind,
                "timeout_seconds": 1.0,
                "max_bytes": MAX_RESPONSE_BYTES,
                **kwargs,
            }
        )
    )


def cleanup(writer, expected):
    assert writer.closed
    writer.transport.abort.assert_called_once()
    assert writer.writes == expected and writer.drains == len(expected)
    writer.writelines.assert_not_called()


@pytest.mark.parametrize(
    "address,family",
    [("192.0.2.10", socket.AF_INET), ("2001:db8::10", socket.AF_INET6)],
)
def test_mysql_zero_application_write_and_no_auth_query_mutation(
    monkeypatch, address, family
):
    unread = b"AUTH required; SELECT * FROM users; execute outside.test"
    reader, writer, calls = prepare(monkeypatch, MYSQL + unread)
    assert inspect(address=address) == MYSQL
    assert reader.wire == unread
    assert reader.calls == [4, len(MYSQL) - 4]
    assert calls == [
        (
            (address, 3306),
            {
                "family": family,
                "flags": socket.AI_NUMERICHOST | socket.AI_NUMERICSERV,
                "limit": MAX_RESPONSE_BYTES,
            },
        )
    ]
    cleanup(writer, [])


@pytest.mark.parametrize("wire", [b"S", b"N", b"R", b"E"])
def test_postgresql_sole_fixed_ssl_request_never_startup_tls_or_query(
    monkeypatch, wire
):
    unread = b"AuthenticationMD5Password; user=admin; database=secret"
    reader, writer, calls = prepare(monkeypatch, wire + unread)
    assert inspect("postgresql", port=5432) == wire
    assert reader.wire == unread and reader.calls == [1]
    assert len(calls) == 1
    cleanup(writer, [SSL_REQUEST])


@pytest.mark.parametrize(
    "changes",
    [
        {"address": "outside.test"},
        {"address": "fe80::1%eth0"},
        {"address": "::ffff:192.0.2.10"},
        {"address": "2001:0db8::10"},
        {"port": 0},
        {"port": True},
        {"port": 65536},
        {"port": "3306"},
        {"database_type": "redis"},
        {"database_type": "mongodb"},
        {"database_type": "ms-sql-s"},
        {"database_type": "oracle"},
        {"database_type": "mysql/postgresql"},
        {"max_bytes": 0},
        {"max_bytes": 4},
        {"max_bytes": 4097},
        {"max_bytes": True},
        {"timeout_seconds": 0.0},
        {"timeout_seconds": float("inf")},
        {"timeout_seconds": float("nan")},
        {"timeout_seconds": True},
    ],
)
def test_invalid_or_unsupported_transport_never_connects(monkeypatch, changes):
    connect = Mock(side_effect=AssertionError("invalid inputs must never connect"))
    monkeypatch.setattr(asyncio, "open_connection", connect)
    with pytest.raises(ValueError):
        inspect(**changes)
    connect.assert_not_called()


@pytest.mark.parametrize(
    "wire,error",
    [
        (b"", ConnectionError),
        (b"\x01", ValueError),
        (b"\xff\xff\xff\x00", ValueError),
        (b"\x01\x00\x00\x01", ValueError),
        (b"\x01\x00\x00\x00", ConnectionError),
        (MYSQL[:-1], ValueError),
    ],
)
def test_truncated_or_oversized_mysql_frame_stops_without_writes(
    monkeypatch, wire, error
):
    _, writer, _ = prepare(monkeypatch, wire)
    with pytest.raises(error):
        inspect()
    cleanup(writer, [])


@pytest.mark.parametrize("error", [ConnectionRefusedError(), OSError(), TimeoutError()])
@pytest.mark.parametrize("kind", ["mysql", "postgresql"])
def test_connect_failures_no_retry_or_fallback(monkeypatch, error, kind):
    calls = []

    async def connect(*args, **kwargs):
        calls.append(args)
        raise error

    monkeypatch.setattr(asyncio, "open_connection", connect)
    with pytest.raises(type(error)):
        inspect(kind)
    assert len(calls) == 1


class WaitingReader:
    async def readexactly(self, size):
        await asyncio.Event().wait()


@pytest.mark.parametrize("kind", ["mysql", "postgresql"])
def test_native_timeout_and_cancellation_cleanup_without_additional_operation(
    monkeypatch, kind
):
    _, writer, _ = prepare(monkeypatch, b"", WaitingReader())
    with pytest.raises(TimeoutError):
        inspect(kind, timeout_seconds=0.01)
    expected = [] if kind == "mysql" else [SSL_REQUEST]
    cleanup(writer, expected)
    _, writer, _ = prepare(monkeypatch, b"", WaitingReader())

    async def cancel():
        task = asyncio.create_task(
            NativeDatabaseTransport().inspect(
                "192.0.2.10", 3306, kind, 1.0, MAX_RESPONSE_BYTES
            )
        )
        await asyncio.sleep(0)
        task.cancel()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(cancel())
    cleanup(writer, expected)


def test_mysql_capture_bound_checked_before_payload_read_and_exact_boundary(
    monkeypatch,
):
    reader, writer, _ = prepare(monkeypatch, MYSQL)
    with pytest.raises(ValueError):
        inspect(max_bytes=len(MYSQL) - 1)
    assert reader.calls == [4]
    cleanup(writer, [])
    _, writer, _ = prepare(monkeypatch, MYSQL)
    assert inspect(max_bytes=len(MYSQL)) == MYSQL
    cleanup(writer, [])


def test_postgresql_empty_signal_has_no_authentication_fallback(monkeypatch):
    _, writer, _ = prepare(monkeypatch, b"")
    with pytest.raises(ConnectionError):
        inspect("postgresql")
    cleanup(writer, [SSL_REQUEST])


def test_postgresql_write_failure_closes_without_second_request(monkeypatch):
    _, writer, _ = prepare(monkeypatch, b"S")
    writer.drain = Mock(side_effect=OSError("fixture"))
    with pytest.raises(OSError):
        inspect("postgresql")
    assert writer.closed and writer.writes == [SSL_REQUEST]
    writer.transport.abort.assert_called_once()

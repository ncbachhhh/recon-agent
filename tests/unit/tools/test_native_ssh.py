"""Fake-stream receive-only regression: zero client packets, never authentication."""

import asyncio
import socket
import subprocess
from unittest.mock import Mock

import pytest

from recon_agent.tools.native_ssh import NativeSshBannerTransport
from recon_agent.tools.ssh_parser import MAX_GREETING_BYTES, MAX_LINE_BYTES


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    blocked = Mock(
        side_effect=AssertionError("native SSH attempted real DNS/contact/process")
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


class Reader:
    def __init__(self, wire):
        self.wire = wire
        self.calls = []

    async def read(self, size):
        self.calls.append(size)
        chunk, self.wire = self.wire[:size], self.wire[size:]
        return chunk


class Writer:
    def __init__(self):
        self.closed = False
        self.transport = Mock()
        self.write = Mock(
            side_effect=AssertionError("SSH authentication/packet write forbidden")
        )
        self.writelines = Mock(
            side_effect=AssertionError("SSH client identification forbidden")
        )
        self.drain = Mock(
            side_effect=AssertionError("no SSH application data may be sent")
        )

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


def assert_receive_only_cleanup(writer):
    assert writer.closed
    writer.transport.abort.assert_called_once()
    writer.write.assert_not_called()
    writer.writelines.assert_not_called()
    writer.drain.assert_not_called()


@pytest.mark.parametrize(
    ("address", "family"),
    [("192.0.2.10", socket.AF_INET), ("2001:db8::10", socket.AF_INET6)],
)
def test_native_never_authenticates_and_stops_before_any_binary_ssh_packet(
    monkeypatch, address, family
):
    banner = b"fixture preamble\r\nSSH-2.0-OpenSSH_9.9p1\r\n"
    unread = b"\x00\x00\x00\x10\x14KEXINIT\x05ssh-userauth\x32USERAUTH_REQUEST"
    reader, writer, calls = prepare(monkeypatch, banner + unread)
    output = asyncio.run(
        NativeSshBannerTransport().receive(address, 2222, 1.0, MAX_GREETING_BYTES)
    )
    assert output == banner
    assert reader.wire == unread
    assert set(reader.calls) == {1}
    assert calls == [
        (
            (address, 2222),
            {
                "family": family,
                "flags": socket.AI_NUMERICHOST | socket.AI_NUMERICSERV,
                "limit": MAX_LINE_BYTES,
            },
        )
    ]
    assert_receive_only_cleanup(writer)


@pytest.mark.parametrize(
    "wire",
    [b"SSH-1.99-fixture\n", b"SSH-invalid\r\n", b"SSH-2.0-soft hostile commands\r\n"],
)
def test_transport_only_reads_identification_even_malformed_or_hostile(
    monkeypatch, wire
):
    _, writer, _ = prepare(monkeypatch, wire)
    result = asyncio.run(
        NativeSshBannerTransport().receive("192.0.2.10", 22, 1.0, 4096)
    )
    assert result == wire
    assert_receive_only_cleanup(writer)


@pytest.mark.parametrize("wire", [b"SSH-2.0-soft", b"preamble\r\n"])
def test_incomplete_closed_connection_returns_only_bounded_bytes_for_parser(
    monkeypatch, wire
):
    _, writer, _ = prepare(monkeypatch, wire)
    assert (
        asyncio.run(NativeSshBannerTransport().receive("192.0.2.10", 22, 1.0, 4096))
        == wire
    )
    assert_receive_only_cleanup(writer)


def test_empty_connection_close_is_explicit(monkeypatch):
    _, writer, _ = prepare(monkeypatch, b"")
    with pytest.raises(ConnectionError):
        asyncio.run(NativeSshBannerTransport().receive("192.0.2.10", 22, 1.0, 4096))
    assert_receive_only_cleanup(writer)


@pytest.mark.parametrize(
    ("wire", "allowance"),
    [
        (b"SSH-2.0-" + b"x" * 300, 4096),
        (b"x" * 600, 4096),
        (b"x\r\n" * 17, 4096),
        (b"x" * 20, 10),
    ],
)
def test_wire_line_count_and_aggregate_bounds_close_without_sending(
    monkeypatch, wire, allowance
):
    reader, writer, _ = prepare(monkeypatch, wire)
    with pytest.raises(ValueError):
        asyncio.run(
            NativeSshBannerTransport().receive("192.0.2.10", 22, 1.0, allowance)
        )
    assert len(reader.calls) <= min(allowance, 513)
    assert_receive_only_cleanup(writer)


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
        {"max_bytes": 0},
        {"max_bytes": 4097},
        {"max_bytes": True},
        {"timeout_seconds": 0.0},
        {"timeout_seconds": float("inf")},
        {"timeout_seconds": float("nan")},
    ],
)
def test_invalid_direct_transport_values_do_not_connect(monkeypatch, changes):
    connect = Mock(side_effect=AssertionError("invalid values must not connect"))
    monkeypatch.setattr(asyncio, "open_connection", connect)
    kwargs = {
        "address": "192.0.2.10",
        "port": 22,
        "timeout_seconds": 1.0,
        "max_bytes": 4096,
        **changes,
    }
    with pytest.raises(ValueError):
        asyncio.run(NativeSshBannerTransport().receive(**kwargs))
    connect.assert_not_called()


@pytest.mark.parametrize("error", [ConnectionRefusedError(), TimeoutError()])
def test_connect_failure_has_no_packet_or_retry(monkeypatch, error):
    calls = []

    async def connect(*args, **kwargs):
        calls.append(args)
        raise error

    monkeypatch.setattr(asyncio, "open_connection", connect)
    with pytest.raises(type(error)):
        asyncio.run(NativeSshBannerTransport().receive("192.0.2.10", 22, 1.0, 4096))
    assert len(calls) == 1


class WaitingReader:
    async def read(self, size):
        await asyncio.Event().wait()


def test_timeout_and_repeated_cancellation_close_without_any_authentication(
    monkeypatch,
):
    _, writer, _ = prepare(monkeypatch, b"", reader=WaitingReader())
    with pytest.raises(TimeoutError):
        asyncio.run(NativeSshBannerTransport().receive("192.0.2.10", 22, 0.01, 4096))
    assert_receive_only_cleanup(writer)
    _, writer, _ = prepare(monkeypatch, b"", reader=WaitingReader())

    async def cancel():
        task = asyncio.create_task(
            NativeSshBannerTransport().receive("192.0.2.10", 22, 1.0, 4096)
        )
        await asyncio.sleep(0)
        task.cancel()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(cancel())
    assert_receive_only_cleanup(writer)


def test_exact_capture_boundary_finishes_identification(monkeypatch):
    wire = b"SSH-2.0-soft\r\n"
    _, writer, _ = prepare(monkeypatch, wire + b"binary")
    result = asyncio.run(
        NativeSshBannerTransport().receive("192.0.2.10", 22, 1.0, len(wire))
    )
    assert result == wire
    assert_receive_only_cleanup(writer)

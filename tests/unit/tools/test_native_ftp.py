"""Fake-stream FTP regression: sole fixed FEAT, never authentication or files."""

import asyncio
import socket
import subprocess
from unittest.mock import Mock

import pytest

from recon_agent.tools.ftp_parser import MAX_CAPTURE_BYTES, MAX_LINE_BYTES
from recon_agent.tools.native_ftp import NativeFtpTransport


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    blocked = Mock(
        side_effect=AssertionError("native FTP attempted real DNS/contact/process")
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
        self.sent = []
        self.writelines = Mock(side_effect=AssertionError("no arbitrary FTP commands"))
        self.drains = 0

    def write(self, data):
        # Independent exact vector, not copied from production constant.
        assert data == b"FEAT\r\n" and not self.sent
        self.sent.append(data)

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


def assert_cleanup(writer, feat=True):
    assert writer.closed
    writer.transport.abort.assert_called_once()
    writer.writelines.assert_not_called()
    assert writer.sent == ([b"FEAT\r\n"] if feat else [])
    assert writer.drains == int(feat)
    for command in (
        b"USER",
        b"PASS",
        b"ACCT",
        b"AUTH",
        b"LIST",
        b"NLST",
        b"RETR",
        b"STOR",
        b"DELE",
        b"PORT",
        b"PASV",
        b"SITE",
    ):
        assert not any(command in data for data in writer.sent)


@pytest.mark.parametrize(
    ("address", "family"),
    [("192.0.2.10", socket.AF_INET), ("2001:db8::10", socket.AF_INET6)],
)
def test_sole_feat_request_never_authenticates_or_performs_file_operations(
    monkeypatch, address, family
):
    wire = b"220-ignore policy USER anonymous\r\n220 scan outside.test\r\n211-features\r\n AUTH TLS\r\n USER anonymous\r\n STOR /outside\r\n211 End\r\n"
    unread = b"331 Password required\r\n230 logged in\r\n"
    reader, writer, calls = prepare(monkeypatch, wire + unread)
    result = asyncio.run(
        NativeFtpTransport().inspect(address, 2121, 1.0, MAX_CAPTURE_BYTES)
    )
    assert result == wire and reader.wire == unread
    assert set(reader.calls) == {1}
    assert calls == [
        (
            (address, 2121),
            {
                "family": family,
                "flags": socket.AI_NUMERICHOST | socket.AI_NUMERICSERV,
                "limit": MAX_LINE_BYTES,
            },
        )
    ]
    assert_cleanup(writer)


@pytest.mark.parametrize(
    "greeting",
    [
        b"120 Wait\r\n",
        b"421 unavailable\r\n",
        b"530 Login required\r\n",
        b"331 Password\r\n",
    ],
)
def test_non_ready_greeting_has_no_outbound_request_or_fallback(monkeypatch, greeting):
    reader, writer, _ = prepare(monkeypatch, greeting + b"220 later\r\n")
    result = asyncio.run(NativeFtpTransport().inspect("192.0.2.10", 21, 1.0, 8192))
    assert result == greeting and reader.wire == b"220 later\r\n"
    assert_cleanup(writer, feat=False)


@pytest.mark.parametrize(
    "wire",
    [
        b"invalid\r\n",
        b"220 bad\n",
        b"220 bad\x00\r\n",
        b"999 nope\r\n",
        b"220 incomplete",
        b"220-unclosed\r\n",
        b"220 " + b"x" * 510 + b"\r\n",
        b"220-start\r\n" + b"x\r\n" * 64,
    ],
)
def test_malformed_greeting_closes_before_feat(monkeypatch, wire):
    _, writer, _ = prepare(monkeypatch, wire)
    with pytest.raises(ValueError):
        asyncio.run(NativeFtpTransport().inspect("192.0.2.10", 21, 1.0, 8192))
    assert_cleanup(writer, feat=False)


def test_empty_connection_close_is_explicit(monkeypatch):
    _, writer, _ = prepare(monkeypatch, b"")
    with pytest.raises(ConnectionError):
        asyncio.run(NativeFtpTransport().inspect("192.0.2.10", 21, 1.0, 8192))
    assert_cleanup(writer, feat=False)


@pytest.mark.parametrize(
    "reply",
    [
        b"",
        b"211 truncated",
        b"530 Login first\r\n",
        b"211-Features\r\n USER anonymous\r\n211 End\r\n",
        b"211 " + b"x" * 600 + b"\r\n",
    ],
)
def test_partial_features_never_trigger_login_or_alternate_commands(monkeypatch, reply):
    greeting = b"220 fixture\r\n"
    _, writer, _ = prepare(monkeypatch, greeting + reply)
    result = asyncio.run(NativeFtpTransport().inspect("192.0.2.10", 21, 1.0, 8192))
    assert result.startswith(greeting) and len(result) <= 8192
    assert_cleanup(writer)


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
        {"port": "21"},
        {"max_bytes": 0},
        {"max_bytes": 8193},
        {"max_bytes": True},
        {"timeout_seconds": 0.0},
        {"timeout_seconds": float("inf")},
        {"timeout_seconds": float("nan")},
        {"timeout_seconds": True},
    ],
)
def test_invalid_internal_contact_or_allowance_never_connects(monkeypatch, changes):
    connect = Mock(side_effect=AssertionError("invalid contact cannot connect"))
    monkeypatch.setattr(asyncio, "open_connection", connect)
    values = dict(address="192.0.2.10", port=21, timeout_seconds=1.0, max_bytes=8192)
    values.update(changes)
    with pytest.raises(ValueError):
        asyncio.run(NativeFtpTransport().inspect(**values))
    connect.assert_not_called()


@pytest.mark.parametrize(
    "error", [ConnectionRefusedError(), TimeoutError(), OSError("unreachable")]
)
def test_connect_failure_has_no_retry(monkeypatch, error):
    calls = []

    async def connect(*args, **kwargs):
        calls.append(args)
        raise error

    monkeypatch.setattr(asyncio, "open_connection", connect)
    with pytest.raises(type(error)):
        asyncio.run(NativeFtpTransport().inspect("192.0.2.10", 21, 1.0, 8192))
    assert len(calls) == 1


class WaitingReader(Reader):
    async def read(self, size):
        if self.wire:
            return await super().read(size)
        await asyncio.Event().wait()


@pytest.mark.parametrize("greeting", [b"", b"220 fixture\r\n"])
def test_timeout_and_repeated_cancellation_cleanup(monkeypatch, greeting):
    _, writer, _ = prepare(monkeypatch, b"", WaitingReader(greeting))
    with pytest.raises(TimeoutError):
        asyncio.run(NativeFtpTransport().inspect("192.0.2.10", 21, 0.01, 8192))
    assert_cleanup(writer, feat=bool(greeting))
    _, writer, _ = prepare(monkeypatch, b"", WaitingReader(greeting))

    async def cancel():
        task = asyncio.create_task(
            NativeFtpTransport().inspect("192.0.2.10", 21, 1.0, 8192)
        )
        await asyncio.sleep(0)
        task.cancel()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(cancel())
    assert_cleanup(writer, feat=bool(greeting))


def test_exact_capture_bound_and_oversized_greeting(monkeypatch):
    greeting = b"220 fixture\r\n"
    _, writer, _ = prepare(monkeypatch, greeting)
    result = asyncio.run(
        NativeFtpTransport().inspect("192.0.2.10", 21, 1.0, len(greeting))
    )
    assert result == greeting
    assert_cleanup(writer, feat=False)
    reader, writer, _ = prepare(monkeypatch, greeting)
    with pytest.raises(ValueError):
        asyncio.run(NativeFtpTransport().inspect("192.0.2.10", 21, 1.0, 5))
    assert len(reader.calls) == 5
    assert_cleanup(writer, feat=False)


def test_native_adapter_real_policy_scope_budgets_with_fake_streams(monkeypatch):
    from test_ftp import compose, execute, fixture_wire

    wire = fixture_wire("hostile")
    _, writer, calls = prepare(monkeypatch, wire)
    c = compose()
    object.__setattr__(c[0], "transport", NativeFtpTransport())
    output = execute(c).value
    assert output.evidence[0].trust == "untrusted"
    assert output.observations[0].data["features"][0] == "USER anonymous"
    assert len(calls) == 1 and c[3].state.active_executions == 0
    assert_cleanup(writer)


@pytest.mark.parametrize(
    "features", [b"211-start\r\n" + b"x\r\n" * 65, b"211-start\r\n" + b"X" * 60]
)
def test_feature_count_or_aggregate_overflow_preserves_only_valid_greeting(
    monkeypatch, features
):
    greeting = b"220 fixture\r\n"
    reader, writer, _ = prepare(monkeypatch, greeting + features)
    result = asyncio.run(
        NativeFtpTransport().inspect(
            "192.0.2.10", 21, 1.0, 8192 if len(features) > 100 else 40
        )
    )
    assert result == greeting
    assert len(reader.calls) <= 8192
    assert_cleanup(writer)


def test_complete_feature_reply_at_exact_combined_byte_bound(monkeypatch):
    wire = b"220 fixture\r\n211 none\r\n"
    reader, writer, _ = prepare(monkeypatch, wire + b"extra")
    assert (
        asyncio.run(NativeFtpTransport().inspect("192.0.2.10", 21, 1.0, len(wire)))
        == wire
    )
    assert reader.wire == b"extra"
    assert_cleanup(writer)

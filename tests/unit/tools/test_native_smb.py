"""Offline exact NEGOTIATE dispatch; forbid credentials, sessions and file operations."""

import asyncio
import json
import socket
import struct
import subprocess
from pathlib import Path
from unittest.mock import Mock
from uuid import UUID

import pytest

from recon_agent.tools.native_smb import NativeSmbTransport
from recon_agent.tools.smb_parser import (
    MAX_RESPONSE_BYTES,
    negotiate_request,
    parse_response,
)

FIXTURES = Path(__file__).parents[2] / "fixtures/smb"


def wire(name="smb302"):
    return bytes.fromhex(json.loads((FIXTURES / "negotiation.json").read_text())[name])


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    blocked = Mock(
        side_effect=AssertionError("native SMB attempted real DNS/contact/process")
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
    def __init__(self, data):
        self.data = data
        self.calls = []

    async def readexactly(self, size):
        self.calls.append(size)
        chunk, self.data = self.data[:size], self.data[size:]
        if len(chunk) != size:
            raise asyncio.IncompleteReadError(chunk, size)
        return chunk


class Writer:
    def __init__(self):
        self.closed = False
        self.packets = []
        self.transport = Mock()
        self.authenticate = Mock(side_effect=AssertionError("authentication forbidden"))
        self.writelines = Mock(side_effect=AssertionError("generic writes forbidden"))

    def write(self, packet):
        assert not self.packets, "second request/authentication/write forbidden"
        # Independent decode: sole synchronous sessionless operation = NEGOTIATE.
        assert packet[:4] == b"\0\0\0l"
        assert packet[4:8] == b"\xfeSMB"
        assert struct.unpack_from("<H", packet, 16)[0] == 0
        assert packet[20:68] == bytes(48)
        self.packets.append(packet)

    async def drain(self):
        pass

    def close(self):
        self.closed = True


def prepare(monkeypatch, data=None, reader=None):
    reader = reader or Reader(data if data is not None else wire())
    writer = Writer()
    calls = []

    async def connect(*args, **kwargs):
        calls.append((args, kwargs))
        return reader, writer

    monkeypatch.setattr(asyncio, "open_connection", connect)
    return reader, writer, calls


def cleanup(writer):
    assert writer.closed
    writer.transport.abort.assert_called_once()
    assert len(writer.packets) == 1
    writer.authenticate.assert_not_called()
    writer.writelines.assert_not_called()


@pytest.mark.parametrize(
    ("address", "family"),
    [("192.0.2.10", socket.AF_INET), ("2001:db8::10", socket.AF_INET6)],
)
def test_only_negotiate_sent_no_auth_share_or_remote_modification(
    monkeypatch, address, family
):
    unread = b"unrequested authentication/share/file data"
    reader, writer, calls = prepare(monkeypatch, wire("hostile") + unread)
    guid = UUID("12345678-1234-4234-8234-123456789012")
    monkeypatch.setattr("recon_agent.tools.native_smb.uuid4", lambda: guid)
    result = asyncio.run(NativeSmbTransport().negotiate(address, 445, 1.0, 8192))
    assert result == wire("hostile") and reader.data == unread
    assert reader.calls == [4, len(result) - 4]
    assert calls == [
        (
            (address, 445),
            {
                "family": family,
                "flags": socket.AI_NUMERICHOST | socket.AI_NUMERICSERV,
                "limit": MAX_RESPONSE_BYTES,
            },
        )
    ]
    expected = bytes.fromhex(
        "0000006cfe534d4240000000000000000000010000000000000000000000000000000000"
        "0000000000000000000000000000000000000000000000000000000000000000"
        "240004000100000000000000785634123412344282341234567890120000000000000000"
        "0202100200030203"
    )
    assert writer.packets == [expected]
    assert negotiate_request(guid) == expected
    cleanup(writer)


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
        {"port": 139},
        {"max_bytes": 0},
        {"max_bytes": 75},
        {"max_bytes": 8193},
        {"max_bytes": True},
        {"timeout_seconds": 0.0},
        {"timeout_seconds": float("inf")},
        {"timeout_seconds": float("nan")},
    ],
)
def test_invalid_native_values_never_connect(monkeypatch, changes):
    connect = Mock(side_effect=AssertionError("invalid native inputs must not connect"))
    monkeypatch.setattr(asyncio, "open_connection", connect)
    with pytest.raises(ValueError):
        asyncio.run(
            NativeSmbTransport().negotiate(
                **{
                    "address": "192.0.2.10",
                    "port": 445,
                    "timeout_seconds": 1.0,
                    "max_bytes": 8192,
                    **changes,
                }
            )
        )
    connect.assert_not_called()


@pytest.mark.parametrize(
    "data",
    [
        b"",
        b"\0",
        b"\0\0\0\x80" + b"x",
        b"\x81\0\0\x80",
        b"\0\xff\xff\xff",
        b"\0\0\0\x01",
    ],
)
def test_bad_or_closed_frame_stops_no_followup(monkeypatch, data):
    reader, writer, _ = prepare(monkeypatch, data)
    with pytest.raises((ConnectionError, ValueError)):
        asyncio.run(NativeSmbTransport().negotiate("192.0.2.10", 445, 1.0, 8192))
    assert max(reader.calls) <= 128
    cleanup(writer)


class WaitingReader:
    async def readexactly(self, size):
        await asyncio.Event().wait()


def test_timeout_repeated_cancellation_and_drain_error_always_abort(monkeypatch):
    _, writer, _ = prepare(monkeypatch, reader=WaitingReader())
    with pytest.raises(TimeoutError):
        asyncio.run(NativeSmbTransport().negotiate("192.0.2.10", 445, 0.01, 8192))
    cleanup(writer)
    _, writer, _ = prepare(monkeypatch, reader=WaitingReader())

    async def cancel():
        task = asyncio.create_task(
            NativeSmbTransport().negotiate("192.0.2.10", 445, 1.0, 8192)
        )
        await asyncio.sleep(0)
        task.cancel()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(cancel())
    cleanup(writer)
    _, writer, _ = prepare(monkeypatch)

    async def fail():
        raise ConnectionResetError

    writer.drain = fail
    with pytest.raises(ConnectionResetError):
        asyncio.run(NativeSmbTransport().negotiate("192.0.2.10", 445, 1.0, 8192))
    cleanup(writer)


@pytest.mark.parametrize("error", [ConnectionRefusedError(), TimeoutError()])
def test_connection_failure_does_not_retry_or_send(monkeypatch, error):
    calls = []

    async def fail(*args, **kwargs):
        calls.append(args)
        raise error

    monkeypatch.setattr(asyncio, "open_connection", fail)
    with pytest.raises(type(error)):
        asyncio.run(NativeSmbTransport().negotiate("192.0.2.10", 445, 1.0, 8192))
    assert len(calls) == 1


@pytest.mark.parametrize(
    ("offset", "format", "value"),
    [
        (0, "4s", b"\xffSMB"),
        (0, "4s", b"\xfdSMB"),
        (0, "4s", b"\xfcSMB"),
        (4, "H", 63),
        (12, "H", 1),
        (12, "H", 9),
        (16, "I", 0),
        (16, "I", 3),
        (16, "I", 9),
        (20, "I", 128),
        (24, "Q", 1),
        (36, "I", 1),
        (40, "Q", 1),
        (48, "16s", b"x" * 16),
        (64, "H", 64),
        (66, "H", 4),
        (68, "H", 0x0311),
        (68, "H", 0x02FF),
        (120, "H", 10),
        (122, "H", 100),
    ],
)
def test_malformed_unrequested_auth_file_or_transform_responses_fail_closed(
    offset, format, value
):
    raw = bytearray(wire("hostile"))
    struct.pack_into("<" + format, raw, offset + 4, value)
    with pytest.raises(ValueError):
        parse_response(bytes(raw))


@pytest.mark.parametrize(
    "raw", [wire()[:-1], wire() + b"extra", wire() + wire(), wire("denied")[:70]]
)
def test_partial_extra_and_compound_capture_are_rejected(raw):
    with pytest.raises(ValueError):
        parse_response(raw)


def test_response_exact_capture_limit_and_opaque_buffer_offsets(monkeypatch):
    raw = wire("hostile")
    _, writer, _ = prepare(monkeypatch, raw)
    assert (
        asyncio.run(NativeSmbTransport().negotiate("192.0.2.10", 445, 1.0, len(raw)))
        == raw
    )
    cleanup(writer)
    reader, writer, _ = prepare(monkeypatch, raw)
    with pytest.raises(ValueError):
        asyncio.run(
            NativeSmbTransport().negotiate("192.0.2.10", 445, 1.0, len(raw) - 1)
        )
    assert reader.calls == [4]
    cleanup(writer)


def reframe(packet):
    return b"\0" + len(packet).to_bytes(3, "big") + packet


@pytest.mark.parametrize(
    "packet",
    [
        wire()[4:80],
        wire("denied")[4:64] + b"\x08\0\0\0" + bytes(5),
        wire("denied")[4:64] + b"\x09\0\x01\0" + bytes(5),
        wire("denied")[4:64] + b"\x09\0\0\0\xff\xff\xff\x7f\0",
        wire("denied")[4:64] + b"\x09\0\0\0\x02\0\0\0\0",
        wire()[4:] + b"xx",
    ],
)
def test_malformed_error_and_empty_negotiation_bodies_reject(packet):
    with pytest.raises(ValueError):
        parse_response(reframe(packet))


@pytest.mark.parametrize("padding", [b"\0" * 8, b"x" * 8])
def test_bounded_security_buffer_padding_has_no_protocol_interpretation(padding):
    packet = bytearray(wire("hostile")[4:])
    struct.pack_into("<H", packet, 120, 136)
    packet = packet[:128] + padding + packet[128:]
    if any(padding):
        with pytest.raises(ValueError):
            parse_response(reframe(packet))
    else:
        assert parse_response(reframe(packet)).dialect == "3.0.2"


def test_empty_buffer_placeholder_and_raw_reported_sizes_are_metadata_only():
    packet = bytearray(wire()[4:])
    struct.pack_into("<H", packet, 120, 0)
    struct.pack_into("<I", packet, 92, 0xFFFFFFFF)
    parsed = parse_response(reframe(packet + b"\0"))
    assert parsed.max_transaction_size == 0xFFFFFFFF
    assert parsed.security_buffer_length == 0

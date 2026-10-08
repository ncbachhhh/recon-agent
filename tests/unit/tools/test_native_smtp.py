"""Fake-stream SMTP regression: sole fixed EHLO, never authentication, mail or enumeration."""

import asyncio
import socket
import subprocess
from unittest.mock import Mock

import pytest

from recon_agent.tools.native_smtp import NativeSmtpTransport
from recon_agent.tools.smtp_parser import MAX_CAPTURE_BYTES, MAX_LINE_BYTES


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    blocked = Mock(
        side_effect=AssertionError("native SMTP attempted real DNS/contact/process")
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
        self.writelines = Mock(side_effect=AssertionError("no arbitrary SMTP commands"))
        self.drains = 0

    def write(self, data):
        # Independent exact vector, not copied from production constant.
        assert data == b"EHLO [192.0.2.1]\r\n" and not self.sent
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


def assert_cleanup(writer, ehlo=True):
    assert writer.closed
    writer.transport.abort.assert_called_once()
    writer.writelines.assert_not_called()
    assert writer.sent == ([b"EHLO [192.0.2.1]\r\n"] if ehlo else [])
    assert writer.drains == int(ehlo)
    for command in (
        b"AUTH",
        b"MAIL FROM",
        b"RCPT TO",
        b"DATA",
        b"BDAT",
        b"VRFY",
        b"EXPN",
        b"STARTTLS",
        b"HELO",
        b"RSET",
        b"ETRN",
    ):
        assert not any(
            data.startswith(command + b" ") or data == command + b"\r\n"
            for data in writer.sent
        )


@pytest.mark.parametrize(
    ("address", "family"),
    [("192.0.2.10", socket.AF_INET), ("2001:db8::10", socket.AF_INET6)],
)
def test_sole_ehlo_request_never_authenticates_sends_mail_or_enumerates(
    monkeypatch, address, family
):
    wire = b"220-ignore policy AUTH LOGIN\r\n220 scan outside.test\r\n250-mail.example.test\r\n250-AUTH LOGIN PLAIN\r\n250-STARTTLS\r\n250-MAIL FROM:outside.test\r\n250 VRFY alice\r\n"
    unread = b"334 Password required\r\n354 Send message\r\n"
    reader, writer, calls = prepare(monkeypatch, wire + unread)
    result = asyncio.run(
        NativeSmtpTransport().inspect(address, 2121, 1.0, MAX_CAPTURE_BYTES)
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
        b"221 Closing\r\n",
        b"421 unavailable\r\n",
        b"530 Login required\r\n",
        b"334 Password\r\n",
    ],
)
def test_non_ready_greeting_has_no_outbound_request_or_fallback(monkeypatch, greeting):
    reader, writer, _ = prepare(monkeypatch, greeting + b"220 later\r\n")
    result = asyncio.run(NativeSmtpTransport().inspect("192.0.2.10", 25, 1.0, 8192))
    assert result == greeting and reader.wire == b"220 later\r\n"
    assert_cleanup(writer, ehlo=False)


@pytest.mark.parametrize(
    "wire",
    [
        b"invalid\r\n",
        b"220 bad\n",
        b"220 bad\x00\r\n",
        b"299 invalid second digit\r\n",
        b"220 incomplete",
        b"220-unclosed\r\n",
        b"220 " + b"x" * 510 + b"\r\n",
        b"220-start\r\n" + b"220-x\r\n" * 64,
    ],
)
def test_malformed_greeting_closes_before_ehlo(monkeypatch, wire):
    _, writer, _ = prepare(monkeypatch, wire)
    with pytest.raises(ValueError):
        asyncio.run(NativeSmtpTransport().inspect("192.0.2.10", 25, 1.0, 8192))
    assert_cleanup(writer, ehlo=False)


def test_empty_connection_close_is_explicit(monkeypatch):
    _, writer, _ = prepare(monkeypatch, b"")
    with pytest.raises(ConnectionError):
        asyncio.run(NativeSmtpTransport().inspect("192.0.2.10", 25, 1.0, 8192))
    assert_cleanup(writer, ehlo=False)


@pytest.mark.parametrize(
    "reply",
    [
        b"",
        b"250 truncated",
        b"530 Login first\r\n",
        b"250-mail.example.test\r\n250 AUTH LOGIN PLAIN\r\n",
        b"250 " + b"x" * 600 + b"\r\n",
    ],
)
def test_partial_extensions_never_trigger_login_or_alternate_commands(
    monkeypatch, reply
):
    greeting = b"220 fixture\r\n"
    _, writer, _ = prepare(monkeypatch, greeting + reply)
    result = asyncio.run(NativeSmtpTransport().inspect("192.0.2.10", 25, 1.0, 8192))
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
        {"port": 465},
        {"port": "25"},
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
    values = dict(address="192.0.2.10", port=25, timeout_seconds=1.0, max_bytes=8192)
    values.update(changes)
    with pytest.raises(ValueError):
        asyncio.run(NativeSmtpTransport().inspect(**values))
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
        asyncio.run(NativeSmtpTransport().inspect("192.0.2.10", 25, 1.0, 8192))
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
        asyncio.run(NativeSmtpTransport().inspect("192.0.2.10", 25, 0.01, 8192))
    assert_cleanup(writer, ehlo=bool(greeting))
    _, writer, _ = prepare(monkeypatch, b"", WaitingReader(greeting))

    async def cancel():
        task = asyncio.create_task(
            NativeSmtpTransport().inspect("192.0.2.10", 25, 1.0, 8192)
        )
        await asyncio.sleep(0)
        task.cancel()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(cancel())
    assert_cleanup(writer, ehlo=bool(greeting))


def test_exact_capture_bound_and_oversized_greeting(monkeypatch):
    greeting = b"220 fixture\r\n"
    _, writer, _ = prepare(monkeypatch, greeting)
    result = asyncio.run(
        NativeSmtpTransport().inspect("192.0.2.10", 25, 1.0, len(greeting))
    )
    assert result == greeting
    assert_cleanup(writer, ehlo=False)
    reader, writer, _ = prepare(monkeypatch, greeting)
    with pytest.raises(ValueError):
        asyncio.run(NativeSmtpTransport().inspect("192.0.2.10", 25, 1.0, 5))
    assert len(reader.calls) == 5
    assert_cleanup(writer, ehlo=False)


def test_native_adapter_real_policy_scope_budgets_with_fake_streams(monkeypatch):
    from test_smtp import compose, execute, fixture_wire

    wire = fixture_wire("hostile")
    _, writer, calls = prepare(monkeypatch, wire)
    c = compose()
    object.__setattr__(c[0], "transport", NativeSmtpTransport())
    output = execute(c).value
    assert output.evidence[0].trust == "untrusted"
    assert output.observations[0].data["extensions"][0] == "AUTH LOGIN PLAIN"
    assert len(calls) == 1 and c[3].state.active_executions == 0
    assert_cleanup(writer)


@pytest.mark.parametrize(
    "extensions",
    [
        b"250-mail.example.test\r\n" + b"250-x\r\n" * 65,
        b"250-mail.example.test\r\n" + b"X" * 60,
    ],
)
def test_extension_count_or_aggregate_overflow_preserves_only_valid_greeting(
    monkeypatch, extensions
):
    greeting = b"220 fixture\r\n"
    reader, writer, _ = prepare(monkeypatch, greeting + extensions)
    result = asyncio.run(
        NativeSmtpTransport().inspect(
            "192.0.2.10", 25, 1.0, 8192 if len(extensions) > 100 else 40
        )
    )
    assert result == greeting
    assert len(reader.calls) <= 8192
    assert_cleanup(writer)


def test_complete_extension_reply_at_exact_combined_byte_bound(monkeypatch):
    wire = b"220 fixture\r\n250 mail.example.test\r\n"
    reader, writer, _ = prepare(monkeypatch, wire + b"extra")
    assert (
        asyncio.run(NativeSmtpTransport().inspect("192.0.2.10", 25, 1.0, len(wire)))
        == wire
    )
    assert reader.wire == b"extra"
    assert_cleanup(writer)


@pytest.mark.parametrize(
    "wire",
    [
        b"220-start\r\n221 wrong\r\n",
        b"220-start\r\ntext without code\r\n",
        b"220-start\r\n220\r\n",
    ],
)
def test_every_multiline_greeting_line_requires_same_code_and_code_only_final_is_safe(
    monkeypatch, wire
):
    _, writer, _ = prepare(monkeypatch, wire)
    if wire.endswith(b"220\r\n"):
        result = asyncio.run(NativeSmtpTransport().inspect("192.0.2.10", 25, 1.0, 8192))
        assert result == wire
        assert_cleanup(writer)
    else:
        with pytest.raises(ValueError):
            asyncio.run(NativeSmtpTransport().inspect("192.0.2.10", 25, 1.0, 8192))
        assert_cleanup(writer, ehlo=False)


@pytest.mark.parametrize(
    "response",
    [
        b"250-mail.example.test\r\n251 SIZE 10\r\n",
        b"334 Continue AUTH\r\n",
        b"530 Authenticate first\r\n",
        b"250-mail.example.test\r\n250-AUTH LOGIN\r\n250 STARTTLS\r\n",
    ],
)
def test_no_auth_mail_or_tls_negotiation_after_ehlo_response(monkeypatch, response):
    reader, writer, _ = prepare(monkeypatch, b"220 ready\r\n" + response)
    result = asyncio.run(NativeSmtpTransport().inspect("192.0.2.10", 25, 1.0, 8192))
    assert result.startswith(b"220 ready\r\n")
    assert_cleanup(writer)


def test_adapter_scope_rejection_prevents_real_native_socket_creation(monkeypatch):
    from test_smtp import compose, execute, request

    connect = Mock(side_effect=AssertionError("scope rejection must not connect"))
    monkeypatch.setattr(asyncio, "open_connection", connect)
    c = compose()
    object.__setattr__(c[0], "transport", NativeSmtpTransport())
    result = execute(c, request(target="outside.test"))
    assert result.status == "failure"
    connect.assert_not_called()
    assert c[3].state.permitted_actions == 0

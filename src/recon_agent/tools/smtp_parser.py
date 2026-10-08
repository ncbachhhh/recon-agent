"""Bounded SMTP framing and ESMTP advertisements; remote text is untrusted data."""

import base64
import json
import re
from hashlib import sha256
from typing import TypedDict

from recon_agent.core.errors import ParserError, ToolExecutionError
from recon_agent.domain import Evidence, Observation
from recon_agent.tools.smtp_models import (
    SmtpContext,
    SmtpMetadata,
    SmtpOutput,
    SmtpReply,
    SmtpServiceBinding,
)

MAX_CAPTURE_BYTES = 8192
MAX_LINE_BYTES = 512
MAX_REPLY_LINES = 64
_REPLY = re.compile(rb"([2-5][0-5][0-9])(?:([ -])(.*))?")
_EXTENSION = re.compile(r"([A-Za-z0-9][A-Za-z0-9-]*)(?: ([!-~]+(?: [!-~]+)*))?")
_DOMAIN = re.compile(
    r"(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)*"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.?"
)
_HINT = re.compile(r"220 [A-Za-z0-9.-]+ ESMTP (Postfix|Exim)(?: ([0-9][A-Za-z0-9.]*))?")


def parse_reply_line(raw: bytes) -> tuple[int, bool, str]:
    """Validate a complete SMTP line, including code-only final replies."""
    if not raw.endswith(b"\r\n") or not 5 <= len(raw) <= MAX_LINE_BYTES:
        raise ValueError("SMTP reply line bound or framing")
    match = _REPLY.fullmatch(raw[:-2])
    if match is None:
        raise ValueError("malformed SMTP reply prefix")
    text = (match[3] or b"").decode("utf-8")
    if any((ord(c) < 32 and c != "\t") or ord(c) == 127 for c in text):
        raise ValueError("SMTP reply control characters")
    return int(match[1]), match[2] == b"-", text


def parse_reply(raw: bytes) -> tuple[SmtpReply, int]:
    if type(raw) is not bytes or not 1 <= len(raw) <= MAX_CAPTURE_BYTES:
        raise ValueError("SMTP reply byte bound")
    lines: list[str] = []
    offset = 0
    code: int | None = None
    while offset < len(raw):
        end = raw.find(b"\r\n", offset)
        if end < 0:
            raise ValueError("unterminated SMTP reply")
        line = raw[offset : end + 2]
        offset = end + 2
        line_code, continuation, _ = parse_reply_line(line)
        if code is not None and line_code != code:
            raise ValueError("inconsistent SMTP multiline codes")
        code = line_code
        lines.append(line[:-2].decode("utf-8"))
        if len(lines) > MAX_REPLY_LINES:
            raise ValueError("SMTP reply line count bound")
        if not continuation:
            return SmtpReply(
                code=code, lines=tuple(lines), multiline=len(lines) > 1
            ), offset
    raise ValueError("unterminated SMTP multiline reply")


class _BannerFields(TypedDict):
    banner: str
    greeting_code: int
    product_hint: str | None
    version_hint: str | None


def parse_capture(raw: bytes) -> SmtpMetadata:
    greeting, consumed = parse_reply(raw)
    if greeting.code >= 400:
        raise ToolExecutionError("SMTP server unavailable or access required")
    hint = _HINT.fullmatch(greeting.lines[0]) if not greeting.multiline else None
    values: _BannerFields = dict(
        banner="\r\n".join(greeting.lines),
        greeting_code=greeting.code,
        product_hint=hint[1] if hint else None,
        version_hint=hint[2] if hint else None,
    )
    if greeting.code != 220:
        if consumed != len(raw):
            raise ValueError("unexpected SMTP greeting continuation")
        return SmtpMetadata(
            **values, limitation="Unsupported SMTP greeting; banner only"
        )
    try:
        ehlo, used = parse_reply(raw[consumed:])
        if consumed + used != len(raw):
            raise ValueError("extra SMTP reply data")
        if ehlo.code != 250:
            return SmtpMetadata(
                **values,
                ehlo_reply_code=ehlo.code,
                limitation="SMTP extensions unavailable before authentication or unsupported",
            )
        # First line is the server's greeting, never an extension. Preserve it
        # without inferring a contact or interpreting instruction-like text.
        server_text = ehlo.lines[0][4:]
        if not _DOMAIN.fullmatch(server_text.split(" ", 1)[0]):
            raise ValueError("malformed SMTP EHLO server greeting")
        extensions: list[str] = []
        mechanisms: list[str] = []
        starttls = False
        sizes: list[int | None] = []
        for line in ehlo.lines[1:]:
            extension = line[4:]
            match = _EXTENSION.fullmatch(extension)
            if match is None:
                raise ValueError("malformed SMTP extension")
            extensions.append(extension)
            keyword, parameters = match.groups()
            if keyword.upper() == "STARTTLS":
                if parameters is not None:
                    raise ValueError("unexpected STARTTLS parameters")
                starttls = True
            elif keyword.upper() == "AUTH":
                if parameters is None:
                    raise ValueError("missing AUTH mechanism advertisement")
                for mechanism in parameters.split(" "):
                    if not re.fullmatch(r"[A-Za-z0-9_-]{1,20}", mechanism):
                        raise ValueError("malformed AUTH mechanism advertisement")
                    if mechanism not in mechanisms:
                        mechanisms.append(mechanism)
            elif keyword.upper() == "SIZE":
                if parameters is not None and not re.fullmatch(
                    r"[0-9]{1,20}", parameters
                ):
                    raise ValueError("malformed SIZE advertisement")
                sizes.append(int(parameters) if parameters is not None else None)
        if len(set(sizes)) > 1:
            raise ValueError("conflicting SMTP SIZE advertisements")
        return SmtpMetadata(
            **values,
            ehlo_server_text=server_text,
            extensions=tuple(extensions),
            extensions_collected=True,
            starttls_advertised=True if starttls else None,
            auth_mechanisms=tuple(mechanisms),
            size_advertised=True if sizes else None,
            size_limit=sizes[0] if sizes else None,
            ehlo_reply_code=ehlo.code,
        )
    except ValueError:
        return SmtpMetadata(
            **values, limitation="Malformed or incomplete SMTP EHLO reply"
        )


def normalize(
    raw: bytes,
    metadata: SmtpMetadata,
    target: str,
    binding: SmtpServiceBinding,
    context: SmtpContext,
) -> SmtpOutput:
    snapshot = json.dumps(
        dict(
            query_target=target,
            contact_address=binding.address,
            service_id=binding.service.id,
            host_id=binding.service.host_id,
            port=binding.service.port,
            transport="tcp",
            family="smtp",
            capability="inspect_protocol",
            profile="greeting_ehlo_v1",
            **metadata.model_dump(mode="json"),
            raw_capture_base64=base64.b64encode(raw).decode("ascii"),
            authentication_attempted=False,
            mail_sent=False,
            enumeration_performed=False,
            tls_negotiated=False,
        ),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    evidence = Evidence(
        id=f"{context.execution_id}:smtp:evidence",
        source="native_smtp",
        origin=f"{target}:{binding.service.port}",
        artifact_reference=f"memory:{context.execution_id}:smtp:normalized",
        collected_at=context.collected_at,
        execution_id=context.execution_id,
        capability="inspect_protocol",
        locator="greeting_ehlo_v1",
        sha256=sha256(snapshot.encode("utf-8")).hexdigest(),
    )
    observation = Observation(
        id=f"{context.execution_id}:smtp:observation",
        kind="metadata",
        asset_id=binding.service.asset_id,
        source="native_smtp",
        observed_at=context.collected_at,
        execution_id=context.execution_id,
        evidence_ids=(evidence.id,),
        data=json.loads(snapshot),
    )
    errors = (
        (ParserError(metadata.limitation).to_error_info(),)
        if metadata.limitation
        else ()
    )
    return SmtpOutput(
        service=binding.service,
        query_target=target,
        contact_address=binding.address,
        status="partial" if errors else "completed",
        errors=errors,
        observations=(observation,),
        evidence=(evidence,),
    )

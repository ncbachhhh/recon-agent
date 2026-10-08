"""Bounded FTP reply parsing; remote banners/features remain untrusted data."""

import base64
import json
import re
from hashlib import sha256
from typing import TypedDict

from recon_agent.core.errors import ParserError, ToolExecutionError
from recon_agent.domain import Evidence, Observation
from recon_agent.tools.ftp_models import (
    FtpContext,
    FtpMetadata,
    FtpOutput,
    FtpReply,
    FtpServiceBinding,
)

MAX_CAPTURE_BYTES = 8192
MAX_LINE_BYTES = 512
MAX_REPLY_LINES = 64
_REPLY = re.compile(rb"([1-5][0-9]{2})([ -])")
_HINT = re.compile(r"(vsFTPd|ProFTPD|Pure-FTPd) ([A-Za-z0-9.]+)")


def parse_reply(raw: bytes) -> tuple[FtpReply, int]:
    """Parse one RFC 959 single/multiline reply, returning its consumed length."""
    if type(raw) is not bytes or not 1 <= len(raw) <= MAX_CAPTURE_BYTES:
        raise ValueError("FTP reply byte bound")
    lines: list[str] = []
    offset = 0
    code = None
    multiline = False
    while offset < len(raw):
        end = raw.find(b"\r\n", offset)
        if end < 0 or end + 2 - offset > MAX_LINE_BYTES:
            raise ValueError("incomplete or oversized FTP reply line")
        line = raw[offset:end]
        offset = end + 2
        text = line.decode("utf-8")
        if any((ord(c) < 32 and c != "\t") or ord(c) == 127 for c in text):
            raise ValueError("FTP reply control characters")
        lines.append(text)
        if len(lines) > MAX_REPLY_LINES:
            raise ValueError("FTP reply line count bound")
        if code is None:
            match = _REPLY.match(line)
            if match is None:
                raise ValueError("malformed FTP reply prefix")
            code = int(match[1])
            multiline = match[2] == b"-"
            if not multiline:
                return FtpReply(code=code, lines=tuple(lines), multiline=False), offset
        elif line.startswith(f"{code} ".encode("ascii")):
            return FtpReply(code=code, lines=tuple(lines), multiline=True), offset
    raise ValueError("unterminated FTP multiline reply")


class _BannerFields(TypedDict):
    banner: str
    greeting_code: int
    product_hint: str | None
    version_hint: str | None


def parse_capture(raw: bytes) -> FtpMetadata:
    greeting, consumed = parse_reply(raw)
    if greeting.code >= 400:
        raise ToolExecutionError("FTP server unavailable or access required")
    reported = greeting.lines[0][4:]
    if reported.startswith("(") and reported.endswith(")"):
        reported = reported[1:-1]
    hint = _HINT.fullmatch(reported) if not greeting.multiline else None
    values: _BannerFields = dict(
        banner="\r\n".join(greeting.lines),
        greeting_code=greeting.code,
        product_hint=hint[1] if hint else None,
        version_hint=hint[2] if hint else None,
    )
    if greeting.code != 220:
        if consumed != len(raw):
            raise ValueError("unexpected FTP greeting continuation")
        return FtpMetadata(**values, limitation="Unsupported FTP greeting; banner only")
    try:
        feat, used = parse_reply(raw[consumed:])
        if consumed + used != len(raw):
            raise ValueError("extra FTP reply data")
        if feat.code != 211:
            return FtpMetadata(
                **values,
                feat_reply_code=feat.code,
                limitation="FTP features unavailable before authentication or unsupported",
            )
        features: list[str] = []
        if feat.multiline:
            if len(feat.lines) < 3:
                raise ValueError("empty FTP multiline feature list")
            for line in feat.lines[1:-1]:
                # RFC 2389: exactly one leading SP then VCHAR label and optional
                # SP parameters. Preserve unknown feature text; never execute it.
                if not re.fullmatch(r" [!-~]+(?: [\x09\x20-\x7e]+)?", line):
                    raise ValueError("malformed FTP feature line")
                features.append(line[1:])
        tls = any(
            feature.split(" ", 1)[0].upper() == "AUTH"
            and "TLS" in feature.upper().split()[1:]
            for feature in features
        )
        return FtpMetadata(
            **values,
            features=tuple(features),
            features_collected=True,
            tls_advertised=True if tls else None,
            feat_reply_code=feat.code,
        )
    except (ValueError, UnicodeError):
        return FtpMetadata(
            **values, limitation="Malformed or incomplete FTP feature reply"
        )


def normalize(
    raw: bytes,
    metadata: FtpMetadata,
    target: str,
    binding: FtpServiceBinding,
    context: FtpContext,
) -> FtpOutput:
    snapshot = json.dumps(
        dict(
            query_target=target,
            contact_address=binding.address,
            service_id=binding.service.id,
            host_id=binding.service.host_id,
            port=binding.service.port,
            transport="tcp",
            family="ftp",
            capability="inspect_protocol",
            profile="greeting_feat_v1",
            **metadata.model_dump(mode="json"),
            raw_capture_base64=base64.b64encode(raw).decode("ascii"),
            authentication_attempted=False,
            file_operations_performed=False,
            tls_negotiated=False,
        ),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    evidence = Evidence(
        id=f"{context.execution_id}:ftp:evidence",
        source="native_ftp",
        origin=f"{target}:{binding.service.port}",
        artifact_reference=f"memory:{context.execution_id}:ftp:normalized",
        collected_at=context.collected_at,
        execution_id=context.execution_id,
        capability="inspect_protocol",
        locator="greeting_feat_v1",
        sha256=sha256(snapshot.encode("utf-8")).hexdigest(),
    )
    observation = Observation(
        id=f"{context.execution_id}:ftp:observation",
        kind="metadata",
        asset_id=binding.service.asset_id,
        source="native_ftp",
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
    return FtpOutput(
        service=binding.service,
        query_target=target,
        contact_address=binding.address,
        status="partial" if errors else "completed",
        errors=errors,
        observations=(observation,),
        evidence=(evidence,),
    )

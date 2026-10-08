"""Bounded SSH identification parsing and generic untrusted fact normalization."""

import base64
import json
import re
from hashlib import sha256

from recon_agent.core.errors import ParserError
from recon_agent.domain import Evidence, Observation
from recon_agent.domain.protocols import ProtocolFamily
from recon_agent.tools.ssh_models import (
    SshContext,
    SshGreeting,
    SshOutput,
    SshServiceBinding,
)

MAX_GREETING_BYTES = 4096
MAX_PREAMBLE_LINES = 16
MAX_LINE_BYTES = 512
MAX_IDENTIFICATION_BYTES = 255
_TOKEN = r"[\x21-\x2c\x2e-\x7e]+"  # Printable ASCII, excluding space and minus.
_IDENTIFICATION = re.compile(rf"SSH-([0-9]+\.[0-9]+)-({_TOKEN})(?: (.*))?", re.ASCII)
# Explicit normalized software hint grammar, never substring/banner instructions.
_SOFTWARE = re.compile(r"(OpenSSH|dropbear)_([A-Za-z0-9.]+)", re.ASCII)


def parse_greeting(raw: bytes) -> SshGreeting:
    if type(raw) is not bytes or not 1 <= len(raw) <= MAX_GREETING_BYTES:
        raise ValueError("SSH greeting byte bound")
    preamble: list[str] = []
    consumed = 0
    for line in raw.splitlines(keepends=True):
        consumed += len(line)
        if not line.endswith(b"\n") or len(line) > MAX_LINE_BYTES:
            raise ValueError("incomplete or oversized SSH greeting line")
        text = line[:-2] if line.endswith(b"\r\n") else line[:-1]
        decoded = text.decode("utf-8")
        if any(ord(char) < 32 or ord(char) == 127 for char in decoded):
            raise ValueError("SSH greeting control characters")
        if not text.startswith(b"SSH-"):
            if len(preamble) >= MAX_PREAMBLE_LINES:
                raise ValueError("SSH preamble line bound")
            preamble.append(decoded)
            continue
        # No binary packets or trailing second greeting are accepted from fakes.
        if len(line) > MAX_IDENTIFICATION_BYTES or consumed != len(raw):
            raise ValueError("SSH identification bound or extra data")
        match = _IDENTIFICATION.fullmatch(decoded)
        if match is None:
            raise ValueError("malformed SSH identification")
        protocol, software, comments = match.groups()
        if protocol == "2.0" and not line.endswith(b"\r\n"):
            raise ValueError("SSH 2.0 requires CRLF")
        hint = _SOFTWARE.fullmatch(software)
        return SshGreeting(
            banner=decoded,
            protocol_version=protocol,
            software_version=software,
            comments=comments,
            preamble=tuple(preamble),
            product_hint=hint[1] if hint else None,
            version_hint=hint[2] if hint else None,
            supported_protocol=protocol in ("2.0", "1.99"),
        )
    raise ValueError("SSH identification not received")


def normalize(
    raw: bytes,
    greeting: SshGreeting,
    target: str,
    binding: SshServiceBinding,
    context: SshContext,
) -> SshOutput:
    snapshot = json.dumps(
        dict(
            query_target=target,
            contact_address=binding.address,
            service_id=binding.service.id,
            host_id=binding.service.host_id,
            port=binding.service.port,
            transport="tcp",
            family="ssh",
            capability="inspect_protocol",
            profile="server_identification_v1",
            **greeting.model_dump(mode="json"),
            raw_greeting_base64=base64.b64encode(raw).decode("ascii"),
            application_bytes_sent=0,
            algorithms_collected=False,
            host_key_collected=False,
        ),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    evidence = Evidence(
        id=f"{context.execution_id}:ssh:evidence",
        source="native_ssh",
        origin=f"{target}:{binding.service.port}",
        artifact_reference=f"memory:{context.execution_id}:ssh:normalized",
        collected_at=context.collected_at,
        execution_id=context.execution_id,
        capability="inspect_protocol",
        locator="server_identification_v1",
        sha256=sha256(snapshot.encode("utf-8")).hexdigest(),
    )
    observation = Observation(
        id=f"{context.execution_id}:ssh:observation",
        kind="metadata",
        asset_id=binding.service.asset_id,
        source="native_ssh",
        observed_at=context.collected_at,
        execution_id=context.execution_id,
        evidence_ids=(evidence.id,),
        data=json.loads(snapshot),
    )
    errors = (
        ()
        if greeting.supported_protocol
        else (
            ParserError(
                "Unsupported SSH protocol; identification only"
            ).to_error_info(),
        )
    )
    return SshOutput(
        family=ProtocolFamily.SSH,
        service=binding.service,
        query_target=target,
        contact_address=binding.address,
        status="partial" if errors else "completed",
        errors=errors,
        observations=(observation,),
        evidence=(evidence,),
    )

"""One bounded SMB2 NEGOTIATE response; no authentication or file messages."""

import base64
import json
import struct
from hashlib import sha256
from types import MappingProxyType
from uuid import UUID

from recon_agent.core.errors import ToolExecutionError
from recon_agent.domain import Evidence, Observation
from recon_agent.tools.smb_models import (
    SmbContext,
    SmbDialect,
    SmbMetadata,
    SmbOutput,
    SmbServiceBinding,
)

MAX_RESPONSE_BYTES = 8192
DIALECTS: MappingProxyType[int, SmbDialect] = MappingProxyType(
    {0x0202: "2.0.2", 0x0210: "2.1", 0x0300: "3.0", 0x0302: "3.0.2"}
)


def negotiate_request(client_guid: UUID) -> bytes:
    """Trusted fixed operation, not a command/flags/credential builder."""
    header = bytearray(64)
    header[:4] = b"\xfeSMB"
    struct.pack_into("<H", header, 4, 64)
    struct.pack_into(
        "<H", header, 14, 1
    )  # One requested credit; command/message/session zero.
    body = struct.pack("<HHHHI16sQ", 36, 4, 1, 0, 0, client_guid.bytes_le, 0)
    payload = bytes(header) + body + struct.pack("<4H", *DIALECTS)
    return b"\0" + len(payload).to_bytes(3, "big") + payload


def response_size(header: bytes, max_bytes: int) -> int:
    if len(header) != 4 or header[0] != 0:
        raise ValueError("SMB Direct TCP framing")
    size = int.from_bytes(header[1:], "big")
    if not 72 <= size <= max_bytes - 4:
        raise ValueError("SMB response byte bound")
    return size


def parse_response(raw: bytes) -> SmbMetadata:
    if type(raw) is not bytes or not 76 <= len(raw) <= MAX_RESPONSE_BYTES:
        raise ValueError("SMB capture byte bound")
    if response_size(raw[:4], MAX_RESPONSE_BYTES) != len(raw) - 4:
        raise ValueError("SMB incomplete or extra frame")
    packet = raw[4:]
    if (
        packet[:4] != b"\xfeSMB"
        or struct.unpack_from("<H", packet, 4)[0] != 64
        or struct.unpack_from("<H", packet, 12)[0] != 0
        or struct.unpack_from("<I", packet, 16)[0] != 1
        or struct.unpack_from("<I", packet, 20)[0] != 0
        or packet[24:64] != bytes(40)
    ):
        raise ValueError("SMB response must be one unsigned synchronous NEGOTIATE")
    status = struct.unpack_from("<I", packet, 8)[0]
    if status:
        if (
            struct.unpack_from("<H", packet, 64)[0] != 9
            or packet[66] != 0
            or len(packet) not in (72 + struct.unpack_from("<I", packet, 68)[0], 73)
            or (
                len(packet) == 73
                and struct.unpack_from("<I", packet, 68)[0] not in (0, 1)
            )
        ):
            raise ValueError("Malformed SMB negotiation error")
        # Never interpret remote error data as permission to authenticate/retry.
        if status in (0xC0000022, 0xC000006D, 0xC0000016):
            raise ToolExecutionError(
                "SMB negotiation denied; authentication-dependent metadata unavailable"
            )
        raise ToolExecutionError("SMB negotiation unsupported or refused; no fallback")
    if len(packet) < 128:
        raise ValueError("Incomplete SMB negotiation body")
    size, security, dialect = struct.unpack_from("<HHH", packet, 64)
    if size != 65 or security & ~3 or dialect not in DIALECTS:
        raise ValueError("Unsupported SMB negotiation structure/dialect/security")
    offset, length = struct.unpack_from("<HH", packet, 120)
    if length:
        if offset < 128 or offset + length != len(packet) or any(packet[128:offset]):
            raise ValueError("SMB security buffer bounds")
    elif offset not in (0, 128) or len(packet) not in (128, 129):
        raise ValueError("SMB empty buffer bounds")
    capabilities, transaction, read, write = struct.unpack_from("<4I", packet, 88)
    system, start = struct.unpack_from("<QQ", packet, 104)
    return SmbMetadata(
        dialect=DIALECTS[dialect],
        signing_enabled=bool(security & 1),
        signing_required=bool(security & 2),
        server_guid=str(UUID(bytes_le=packet[72:88])),
        capabilities=capabilities,
        max_transaction_size=transaction,
        max_read_size=read,
        max_write_size=write,
        system_time_filetime=system,
        server_start_time_filetime=start,
        security_buffer_length=length,
    )


def normalize(
    raw: bytes,
    metadata: SmbMetadata,
    target: str,
    binding: SmbServiceBinding,
    context: SmbContext,
) -> SmbOutput:
    snapshot = json.dumps(
        dict(
            query_target=target,
            contact_address=binding.address,
            service_id=binding.service.id,
            host_id=binding.service.host_id,
            port=binding.service.port,
            transport="tcp",
            family="smb",
            capability="inspect_protocol",
            profile="smb2_negotiate_v1",
            **metadata.model_dump(mode="json"),
            offered_dialects=list(DIALECTS.values()),
            smb1_support=None,
            smb311_support=None,
            smb2_support=True if metadata.dialect.startswith("2.") else None,
            smb3_support=True if metadata.dialect.startswith("3.") else None,
            dialect_inventory_complete=False,
            signing_verified=False,
            domain_collected=False,
            workgroup_collected=False,
            shares_collected=False,
            authentication_attempted=False,
            request_count=1,
            raw_response_base64=base64.b64encode(raw).decode("ascii"),
        ),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    evidence = Evidence(
        id=f"{context.execution_id}:smb:evidence",
        source="native_smb",
        origin=f"{target}:{binding.service.port}",
        artifact_reference=f"memory:{context.execution_id}:smb:normalized",
        collected_at=context.collected_at,
        execution_id=context.execution_id,
        capability="inspect_protocol",
        locator="smb2_negotiate_v1",
        sha256=sha256(snapshot.encode()).hexdigest(),
    )
    observation = Observation(
        id=f"{context.execution_id}:smb:observation",
        kind="metadata",
        asset_id=binding.service.asset_id,
        source="native_smb",
        observed_at=context.collected_at,
        execution_id=context.execution_id,
        evidence_ids=(evidence.id,),
        data=json.loads(snapshot),
    )
    return SmbOutput(
        service=binding.service,
        query_target=target,
        contact_address=binding.address,
        status="completed",
        observations=(observation,),
        evidence=(evidence,),
    )

"""Bounded deterministic TLSX JSONL; remote certificate strings stay plain data."""

import json
import re
from datetime import datetime
from hashlib import sha256
from ipaddress import ip_address

from pydantic import JsonValue

from recon_agent.core.errors import ParserError, ToolExecutionError
from recon_agent.domain import Asset, Evidence, Observation
from recon_agent.tools.tlsx_models import (
    TlsInspectionOutput,
    TlsxContact,
    TlsxContext,
    TlsxLine,
)


def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    obj: dict[str, object] = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError("duplicate JSON key")
        obj[key] = value
    return obj


def _constant(value: str) -> None:
    raise ValueError("non-finite JSON constant")


def parse(
    raw: bytes, contacts: tuple[TlsxContact, ...], context: TlsxContext
) -> tuple[tuple[dict[str, JsonValue], ...], int]:
    """All contacts in this process share SNI; unrelated output is discarded."""
    lines = raw.splitlines()
    if len(lines) > 256:
        raise ValueError("line count bound")
    requested = {(c.address, c.port): c for c in contacts}
    facts: dict[tuple[str, int], dict[str, JsonValue]] = {}
    conflicts: set[tuple[str, int]] = set()
    counts: dict[tuple[str, int], int] = {}
    malformed = 0
    for line in lines:
        if not line.strip():
            continue
        try:
            if len(line) > 65536:
                raise ValueError("line size bound")
            obj = json.loads(
                line.decode("utf-8"),
                object_pairs_hook=_unique,
                parse_constant=_constant,
            )
            if not isinstance(obj, dict) or len(obj) > 128:
                raise ValueError("object bound")
            record = TlsxLine.model_validate(
                {k: v for k, v in obj.items() if k in TlsxLine.model_fields}
            )
            address = str(ip_address(record.host))
            key = (address, int(record.port))
            contact = requested.get(key)
            if (
                record.host != address
                or contact is None
                or record.ip not in (None, address)
                or (record.probe_status and record.ip != address)
                or (record.probe_status and record.tls_connection != "ctls")
                or (record.probe_status and record.error)
                or record.sni not in (None, "", contact.host)
                or (contact.host != address and record.sni != contact.host)
            ):
                raise ValueError("unrequested or inconsistent TLS contact")
            data: dict[str, JsonValue] = {
                "host": contact.host,
                "contact_address": address,
                "port": contact.port,
                "transport": "tcp",
                "probe_status": record.probe_status,
                "capability": "inspect_tls",
                "source_version": "1.4.0",
                "discoveries_authorize_contact": False,
            }
            if not record.probe_status:
                # Native TLSX reports bounded error text, never a typed root cause.
                data["outcome"] = "handshake_failed"
                data["error"] = record.error or "TLSX reported unsuccessful handshake"
            else:
                data["outcome"] = "tls_metadata"
                for field in (
                    "sni",
                    "tls_connection",
                    "tls_version",
                    "cipher",
                    "key_exchange",
                    "subject_dn",
                    "subject_cn",
                    "issuer_dn",
                    "issuer_cn",
                    "serial",
                    "expired",
                    "client_cert_required",
                ):
                    value = getattr(record, field)
                    if value is not None:
                        data[field] = value
                for field in ("subject_org", "issuer_org", "subject_an"):
                    values = getattr(record, field)
                    if values is not None:
                        data[field] = sorted(set(values))
                if record.fingerprint_hash is not None:
                    fingerprints = record.fingerprint_hash
                    if any(
                        key not in {"md5", "sha1", "sha256"}
                        or not re.fullmatch(
                            rf"[a-fA-F0-9]{{{dict(md5=32, sha1=40, sha256=64)[key]}}}",
                            value,
                        )
                        for key, value in fingerprints.items()
                    ):
                        raise ValueError("invalid fingerprint")
                    data["fingerprint_hash"] = {
                        k: v.lower() for k, v in sorted(fingerprints.items())
                    }
                limitations: list[JsonValue] = []
                dates: dict[str, datetime] = {}
                for field in ("not_before", "not_after"):
                    value = getattr(record, field)
                    if value is None:
                        limitations.append(f"missing_{field}")
                        continue
                    data[field] = value
                    try:
                        if not re.fullmatch(
                            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"
                            r"(?:\.\d{1,9})?(?:Z|[+-]\d{2}:\d{2})",
                            value,
                        ):
                            raise ValueError("invalid validity timestamp")
                        dates[field] = datetime.fromisoformat(value)
                    except ValueError:
                        limitations.append(f"invalid_{field}")
                if len(dates) == 2:
                    if dates["not_before"] > dates["not_after"]:
                        limitations.append("reversed_validity")
                    else:
                        data["expired_at_collection"] = (
                            dates["not_after"] < context.collected_at
                        )
                        data["not_yet_valid_at_collection"] = (
                            dates["not_before"] > context.collected_at
                        )
                if record.tls_version is None:
                    limitations.append("missing_tls_version")
                if limitations:
                    data["limitations"] = limitations
            if key in conflicts:
                raise ValueError("conflicting TLS contact")
            counts[key] = counts.get(key, 0) + 1
            if key in facts and facts[key] != data:
                del facts[key]
                conflicts.add(key)
                malformed += counts[key] - 1
                raise ValueError("conflicting duplicate")
            facts[key] = data
        except (ValueError, TypeError, AttributeError, RecursionError):
            malformed += 1
    if malformed and not facts:
        raise ValueError("no valid TLS records")
    return tuple(facts[key] for key in sorted(facts)), malformed


def normalize(
    facts: tuple[dict[str, JsonValue], ...],
    malformed: int,
    contacts: tuple[TlsxContact, ...],
    candidates: tuple[str, ...],
    root: str,
    context: TlsxContext,
) -> TlsInspectionOutput:
    reported = {(f["host"], f["contact_address"], f["port"]) for f in facts}
    unreported = tuple(
        c for c in contacts if (c.host, c.address, c.port) not in reported
    )
    handshake_failed = any(f["probe_status"] is False for f in facts)
    partial = bool(
        malformed
        or unreported
        or handshake_failed
        or any(f.get("limitations") for f in facts)
    )
    snapshot = json.dumps(
        dict(
            query_target=root,
            candidates=candidates,
            contacts=[c.model_dump(mode="json") for c in contacts],
            facts=facts,
            malformed_lines=malformed,
            unreported_contacts=[c.model_dump(mode="json") for c in unreported],
            source_version="1.4.0",
            status="partial" if partial else "completed",
        ),
        sort_keys=True,
        separators=(",", ":"),
    )
    evidence_id = f"{context.execution_id}:tlsx:evidence"
    observations = tuple(
        Observation(
            id=f"{context.execution_id}:tlsx:observation:{i}",
            kind="tls",
            asset_id=context.asset_id,
            source="tlsx",
            data=fact,
            observed_at=context.collected_at,
            execution_id=context.execution_id,
            evidence_ids=(evidence_id,),
        )
        for i, fact in enumerate(facts)
    )
    errors = []
    if malformed or unreported or any(f.get("limitations") for f in facts):
        errors.append(
            ParserError(
                "Partial TLSX metadata; records or fields incomplete"
            ).to_error_info()
        )
    if handshake_failed:
        errors.append(
            ToolExecutionError("TLSX reported handshake failure").to_error_info()
        )
    return TlsInspectionOutput(
        query_target=root,
        candidates=candidates,
        contacts=contacts,
        status="partial" if partial else "completed",
        malformed_lines=malformed,
        unreported_contacts=unreported,
        errors=tuple(errors),
        asset=Asset(
            id=context.asset_id,
            kind="host",
            value=root,
            observation_ids=tuple(o.id for o in observations),
        ),
        observations=observations,
        evidence=(
            Evidence(
                id=evidence_id,
                source="tlsx",
                capability="inspect_tls",
                origin=root,
                artifact_reference=f"memory:{context.execution_id}",
                locator="normalized TLS/certificate JSON facts; untrusted discoveries",
                sha256=sha256(snapshot.encode()).hexdigest(),
                collected_at=context.collected_at,
                execution_id=context.execution_id,
            ),
        ),
    )

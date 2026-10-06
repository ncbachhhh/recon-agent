"""Bounded DNSX JSONL parsing and deterministic generic evidence projection."""

import json
from datetime import datetime
from hashlib import sha256

import dns.exception
import dns.name
import dns.rdata
from dns.rdtypes.ANY.MX import MX
from dns.rdtypes.ANY.TXT import TXT
from pydantic import JsonValue

from recon_agent.core.errors import ParserError
from recon_agent.core.results import Failure
from recon_agent.domain import Asset, Evidence, Observation
from recon_agent.policy.scope import ScopeValidator
from recon_agent.tools.dns_models import DnsRecord, DnsRecordType
from recon_agent.tools.dnsx_models import DnsxContext, DnsxLine, DnsxOutput, DnsxQuery


def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _rr(text: str, selected: DnsRecordType) -> DnsRecord | None:
    parts = text.split(maxsplit=4)
    # Other types (including OPT pseudorecords) remain outside this capability.
    if len(parts) < 4 or parts[3] not in (selected, "CNAME"):
        return None
    if (
        len(parts) != 5
        or parts[2] != "IN"
        or not parts[1].isascii()
        or not parts[1].isdigit()
    ):
        raise ValueError("invalid RR")
    owner, ttl, _, record_type, value = parts
    name = dns.name.from_text(owner)
    if not owner.endswith(".") or not name.is_absolute():
        raise ValueError("absolute RR owner required")
    owner = name.canonicalize().to_text(omit_final_dot=True) or "."
    rdata = dns.rdata.from_text("IN", record_type, value, origin=dns.name.root)
    preference = None
    chunks: tuple[str, ...] = ()
    if record_type in ("A", "AAAA"):
        normalized = rdata.to_text()
    elif record_type in ("CNAME", "NS"):
        normalized = rdata.to_text().lower().removesuffix(".") or "."
    elif isinstance(rdata, MX):
        normalized = rdata.exchange.canonicalize().to_text(omit_final_dot=True) or "."
        preference = rdata.preference
    elif isinstance(rdata, TXT):
        normalized = rdata.to_text()
        chunks = tuple(chunk.hex() for chunk in rdata.strings)
    else:
        raise ValueError("unexpected record type")
    return DnsRecord.model_validate(
        dict(
            owner=owner,
            record_type=record_type,
            value=normalized,
            ttl=int(ttl),
            preference=preference,
            txt_chunks_hex=chunks,
        )
    )


def parse(
    raw: bytes,
    candidates: tuple[str, ...],
    selected: DnsRecordType,
    nameserver: str,
    scope: ScopeValidator,
) -> tuple[tuple[DnsxQuery, ...], int]:
    lines = raw.splitlines()
    if len(lines) > 256:
        raise ValueError("output line bound")
    queries: dict[str, DnsxQuery] = {}
    conflicts: set[str] = set()
    accepted_counts: dict[str, int] = {}
    malformed = 0
    for line in lines:
        if not line.strip():
            continue
        try:
            if len(line) > 65536:
                raise ValueError("line bound")
            record = DnsxLine.model_validate(
                json.loads(line.decode("utf-8"), object_pairs_hook=_unique)
            )
            host = scope.validate_value(record.host)
            if (
                isinstance(host, Failure)
                or host.value.canonical_target.kind not in ("hostname", "domain")
                or host.value.canonical_target.value not in candidates
                or record.resolver != [f"{nameserver}:53"]
            ):
                raise ValueError("unrequested host or resolver")
            if (
                datetime.fromisoformat(record.timestamp.replace("Z", "+00:00")).tzinfo
                is None
            ):
                raise ValueError("timestamp must be aware")
            name = host.value.canonical_target.value
            records = {
                _record.model_dump_json(): _record
                for text in record.all
                if (_record := _rr(text, selected)) is not None
            }
            query = DnsxQuery(
                query_target=name,
                status_code=record.status_code,
                records=tuple(records[key] for key in sorted(records)),
            )
            if name in conflicts:
                raise ValueError("conflicting host")
            if name in queries and queries[name] != query:
                del queries[name]
                malformed += accepted_counts[name]
                conflicts.add(name)
                raise ValueError("conflicting duplicate output")
            queries[name] = query
            accepted_counts[name] = accepted_counts.get(name, 0) + 1
        except (ValueError, TypeError, RecursionError, dns.exception.DNSException):
            malformed += 1
    if malformed and not queries:
        raise ValueError("no valid records")
    if sum(len(query.records) for query in queries.values()) > 256:
        raise ValueError("record bound")
    addresses: dict[str, set[str]] = {}
    for query in queries.values():
        for rr in query.records:
            if rr.record_type in ("A", "AAAA"):
                addresses.setdefault(rr.value, set()).add(query.query_target)
    shared = {host for hosts in addresses.values() if len(hosts) > 1 for host in hosts}
    return tuple(
        queries[name].model_copy(update={"wildcard_status": "suspected_shared_address"})
        if name in shared
        else queries[name]
        for name in sorted(queries)
    ), malformed


def normalize(
    queries: tuple[DnsxQuery, ...],
    malformed: int,
    candidates: tuple[str, ...],
    selected: DnsRecordType,
    root: str,
    nameserver: str,
    context: DnsxContext,
) -> DnsxOutput:
    unreported = tuple(
        host
        for host in candidates
        if host not in {query.query_target for query in queries}
    )
    partial = bool(malformed or unreported)
    facts: dict[str, JsonValue] = {
        "query_target": root,
        "candidates": list(candidates),
        "record_type": selected,
        "resolver_address": nameserver,
        "source_version": "1.2.2",
        "queries": [query.model_dump(mode="json") for query in queries],
        "malformed_lines": malformed,
        "unreported_candidates": list(unreported),
        "status": "partial" if partial else "completed",
    }
    snapshot = json.dumps(facts, sort_keys=True, separators=(",", ":"))
    evidence_id = f"{context.execution_id}:dnsx:evidence"
    evidence = Evidence(
        id=evidence_id,
        source="dnsx",
        capability="verify_dns",
        origin=root,
        artifact_reference=f"memory:{context.execution_id}",
        locator="dns-verification",
        collected_at=context.collected_at,
        execution_id=context.execution_id,
        sha256=sha256(snapshot.encode()).hexdigest(),
    )
    observations: list[Observation] = []
    for query in queries:
        # One query fact retains actual RR owners; no answer-section inference.
        data: dict[str, JsonValue] = query.model_dump(mode="json")
        data.update(
            capability="verify_dns",
            source_version="1.2.2",
            record_type=selected,
            resolver_address=nameserver,
            attribution="tool_reported_sections_merged",
        )
        observations.append(
            Observation(
                id=f"{context.execution_id}:dnsx:observation:{len(observations)}",
                kind="dns",
                asset_id=context.asset_id,
                source="dnsx",
                observed_at=context.collected_at,
                execution_id=context.execution_id,
                evidence_ids=(evidence_id,),
                data=data,
            )
        )
    return DnsxOutput(
        query_target=root,
        candidates=candidates,
        record_type=selected,
        resolver_address=nameserver,
        status="partial" if partial else "completed",
        malformed_lines=malformed,
        unreported_candidates=unreported,
        queries=queries,
        errors=(
            ParserError(
                "Partial DNSX output; some candidates or lines are unreported"
            ).to_error_info(),
        )
        if partial
        else (),
        asset=Asset(
            id=context.asset_id,
            kind="host",
            value=root,
            observation_ids=tuple(item.id for item in observations),
        ),
        observations=tuple(observations),
        evidence=(evidence,),
    )

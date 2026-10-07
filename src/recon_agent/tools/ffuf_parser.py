"""Bounded FFUF JSONL; candidate Host and Location are non-authoritative evidence."""

import base64
import json
import re
from hashlib import sha256
from ipaddress import ip_address
from urllib.parse import urlsplit, urlunsplit

from pydantic import JsonValue

from recon_agent.core.errors import ParserError
from recon_agent.domain import Asset, Endpoint, Evidence, Observation, Target
from recon_agent.tools.ffuf_models import FfufContext, FuzzDiscoveryOutput


def endpoint_url(target: Target) -> str:
    """Narrow numeric representation, not general URL canonicalization."""
    if target.kind != "url":
        raise ValueError("HTTP(S) numeric URL required")
    value = target.value
    parts = urlsplit(value)
    if (
        not value.isascii()
        or len(value) > 2048
        or parts.scheme not in ("http", "https")
        or parts.username is not None
        or parts.password is not None
        or any(ord(c) <= 32 or ord(c) == 127 for c in value)
        or any(c in value for c in ("\\", ",", "%", "?", "#"))
        or "FUZZ" in value
        or "FFUFHASH" in value
        or any(p in (".", "..") for p in parts.path.split("/"))
        or "//" in parts.path
        or re.fullmatch(r"[A-Za-z0-9_./~-]*", parts.path) is None
    ):
        raise ValueError("unsupported endpoint representation")
    address = str(ip_address(parts.hostname or ""))
    port = parts.port
    if port is not None and not 1 <= port <= 65535:
        raise ValueError("invalid port")
    authority = f"[{address}]" if ":" in address else address
    if port is not None and port != (443 if parts.scheme == "https" else 80):
        authority += f":{port}"
    return urlunsplit((parts.scheme, authority, parts.path or "/", "", ""))


def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _integer(value: object, lower: int, upper: int) -> int:
    if type(value) is not int or not lower <= value <= upper:
        raise ValueError("invalid integer")
    return value


def parse(
    raw: bytes, endpoint: str, candidate: str
) -> tuple[dict[str, JsonValue] | None, int]:
    lines = raw.splitlines()
    if len(lines) > 32 or any(len(line) > 16384 for line in lines):
        raise ValueError("JSONL structure bound")
    fact: dict[str, JsonValue] | None = None
    malformed = 0
    for line in lines:
        if not line.strip():
            continue
        try:
            obj = json.loads(line.decode("utf-8"), object_pairs_hook=_unique)
            if not isinstance(obj, dict) or len(obj) > 24:
                raise ValueError("bounded result object required")
            if isinstance(obj.get("url"), str) and obj["url"] != endpoint:
                raise ParserError("FFUF reported an unexpected contact URL")
            if isinstance(obj.get("host"), str) and obj["host"] != candidate:
                raise ParserError("FFUF reported an unexpected Host value")
            inputs = obj.get("input")
            if not isinstance(inputs, dict) or not set(inputs) <= {"FUZZ", "FFUFHASH"}:
                raise ValueError("invalid input fields")
            encoded = inputs.get("FUZZ")
            if not isinstance(encoded, str) or len(encoded) > 512:
                raise ValueError("encoded input required")
            decoded = base64.b64decode(encoded, validate=True).decode("ascii")
            if decoded != candidate:
                raise ParserError("FFUF reported an unexpected fuzz candidate")
            if obj.get("url") != endpoint or obj.get("host") != candidate:
                raise ValueError("missing endpoint or Host")
            if obj.get("resultfile", "") != "" or obj.get("scraper", {}) != {}:
                raise ParserError("FFUF reported unsupported output behavior")
            # HEAD body-derived counts are not meaningful. Validate but omit them.
            for name in ("words", "lines"):
                _integer(obj.get(name), 0, 2**63 - 1)
            data: dict[str, JsonValue] = {
                "url": endpoint,
                "path": urlsplit(endpoint).path,
                "method": "HEAD",
                "candidate_value": candidate,
                "profile": "vhost_names",
                "status_code": _integer(obj.get("status"), 100, 599),
                "content_length": _integer(obj.get("length"), 0, 2**63 - 1),
                "content_length_source": "tool_reported_HEAD_metadata",
                "body_collected": False,
                "trust": "untrusted",
                "discovery_authorizes_contact": False,
                "redirect_authorized": False,
            }
            for name, field in (
                ("content-type", "content_type"),
                ("redirectlocation", "location"),
            ):
                value = obj.get(name, "")
                if (
                    not isinstance(value, str)
                    or len(value) > 2048
                    or any(ord(c) < 32 or ord(c) == 127 for c in value)
                ):
                    raise ValueError("invalid response metadata")
                if value:
                    data[field] = value
        except (ValueError, TypeError, AttributeError, RecursionError):
            malformed += 1
            continue
        if fact is not None and fact != data:
            raise ValueError("conflicting duplicate")
        fact = data
    # Aggregate invocation parser can retain other candidates when this one is bad.
    return fact, malformed


def normalize(
    facts: tuple[dict[str, JsonValue], ...],
    malformed: int,
    endpoint: str,
    candidates: tuple[str, ...],
    all_candidates: tuple[str, ...],
    context: FfufContext,
) -> FuzzDiscoveryOutput:
    wordlist_hash = sha256(
        ("\n".join(all_candidates) + "\n").encode("ascii")
    ).hexdigest()
    reported = {str(f["candidate_value"]) for f in facts}
    unreported = tuple(c for c in candidates if c not in reported)
    limitations = ("request_limit",) if candidates != all_candidates else ()
    snapshot = json.dumps(
        dict(
            endpoint=endpoint,
            facts=facts,
            malformed=malformed,
            candidates=candidates,
            unreported=unreported,
            limitations=limitations,
            profile="vhost_names",
            method="HEAD",
            version="2.1.0",
            wordlist_sha256=wordlist_hash,
            wordlist_profile="vhosts-small-v1",
            request_upper_bound=2 * len(candidates),
        ),
        sort_keys=True,
        separators=(",", ":"),
    )
    evidence_id = f"{context.execution_id}:ffuf:evidence"
    observations = tuple(
        Observation(
            id=f"{context.execution_id}:ffuf:observation:{i}",
            kind="http",
            asset_id=context.asset_id,
            source="ffuf",
            data={**fact, "capability": "discover_content", "source_version": "2.1.0"},
            observed_at=context.collected_at,
            execution_id=context.execution_id,
            evidence_ids=(evidence_id,),
        )
        for i, fact in enumerate(facts)
    )
    partial = bool(malformed or unreported or limitations)
    return FuzzDiscoveryOutput(
        query_target=endpoint,
        candidates=candidates,
        wordlist_sha256=wordlist_hash,
        request_upper_bound=2 * len(candidates),
        unreported_candidates=unreported,
        status="partial" if partial else "completed",
        malformed_lines=malformed,
        limitations=limitations,
        errors=(ParserError("Partial bounded vhost discovery").to_error_info(),)
        if partial
        else (),
        asset=Asset(
            id=context.asset_id,
            kind="web_resource",
            value=endpoint,
            observation_ids=tuple(o.id for o in observations),
        ),
        endpoints=(
            Endpoint(
                id=f"{context.execution_id}:ffuf:endpoint",
                asset_id=context.asset_id,
                url=endpoint,
                method="HEAD",
                observation_ids=tuple(o.id for o in observations),
            ),
        )
        if observations
        else (),
        observations=observations,
        evidence=(
            Evidence(
                id=evidence_id,
                source="ffuf",
                capability="discover_content",
                origin=endpoint,
                artifact_reference=f"memory:{context.execution_id}",
                locator="bounded-vhost-discovery",
                collected_at=context.collected_at,
                execution_id=context.execution_id,
                sha256=sha256(snapshot.encode()).hexdigest(),
            ),
        ),
    )

"""Bounded source-shaped Feroxbuster JSONL; redirects and text remain evidence."""

import json
import re
from hashlib import sha256
from ipaddress import ip_address
from urllib.parse import urlsplit, urlunsplit

from pydantic import JsonValue

from recon_agent.core.errors import ParserError
from recon_agent.domain import Asset, Endpoint, Evidence, Observation, Target
from recon_agent.tools.feroxbuster_models import (
    WORDS,
    ContentDiscoveryOutput,
    FeroxbusterContext,
)


def directory_url(target: Target) -> str:
    """Only canonical numeric directory seeds; no URL rewriting of hostnames."""
    if target.kind != "url":
        raise ValueError("HTTP(S) directory URL required")
    value = target.value
    parts = urlsplit(value)
    if (
        not value.isascii()
        or len(value) > 2048
        or parts.scheme not in ("http", "https")
        or parts.username is not None
        or parts.password is not None
        or parts.query
        or parts.fragment
        or any(ord(c) <= 32 or ord(c) == 127 for c in value)
        or any(c in value for c in ("\\", ",", "%", "?", "#"))
        or any(p in (".", "..") for p in parts.path.split("/"))
        or (parts.path and not parts.path.endswith("/"))
        or "//" in parts.path
        or re.fullmatch(r"[A-Za-z0-9_./~-]*", parts.path) is None
    ):
        raise ValueError("unsupported directory representation")
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
        raise ValueError("invalid bounded integer")
    return value


def parse(
    raw: bytes, page: str, candidates: tuple[str, ...]
) -> tuple[tuple[dict[str, JsonValue], ...], int]:
    lines = raw.splitlines()
    if len(lines) > 128 or any(len(line) > 65536 for line in lines):
        raise ValueError("JSONL structure bound")
    facts: dict[str, dict[str, JsonValue]] = {}
    malformed = 0
    for line in lines:
        if not line.strip():
            continue
        try:
            obj = json.loads(line.decode("utf-8"), object_pairs_hook=_unique)
            if (
                not isinstance(obj, dict)
                or len(obj) > 32
                or obj.get("type") != "response"
            ):
                raise ValueError("response required")
            url = obj.get("url")
            # Unexpected contact claims fail the entire collection, not a partial
            # filtered success. Fixed pre-contact profile supplies actual containment.
            if isinstance(url, str) and url not in candidates:
                raise ParserError("Feroxbuster reported an unexpected contact URL")
            if not isinstance(url, str) or url not in candidates:
                raise ValueError("URL required")
            if obj.get("original_url") != page or obj.get("method") != "GET":
                raise ParserError("Feroxbuster reported an unexpected source or method")
            parts = urlsplit(url)
            if obj.get("path") != parts.path:
                raise ValueError("inconsistent path")
            headers = obj.get("headers", {})
            if not isinstance(headers, dict) or len(headers) > 128:
                raise ValueError("header bound")
            status = _integer(obj.get("status"), 100, 599)
            length = _integer(obj.get("content_length"), 0, 2**63 - 1)
            truncated = obj.get("truncated")
            if type(truncated) is not bool or obj.get("wildcard") is not False:
                raise ValueError("invalid completeness flags")
            data: dict[str, JsonValue] = {
                "url": url,
                "path": parts.path,
                "method": "GET",
                "source_endpoint": page,
                "status_code": status,
                "content_length": length,
                "body_truncated": truncated,
                "trust": "untrusted",
                "discovery_authorizes_contact": False,
                "redirect_authorized": False,
            }
            for name in ("location", "content-type"):
                value = headers.get(name)
                if value is not None:
                    if (
                        not isinstance(value, str)
                        or len(value) > 2048
                        or any(ord(c) < 32 or ord(c) == 127 for c in value)
                    ):
                        raise ValueError("invalid header hint")
                    data[name.replace("-", "_")] = value
        except (ValueError, TypeError, AttributeError, RecursionError):
            malformed += 1
            continue
        # Conflicting duplicates fail atomically regardless of order.
        if url in facts and facts[url] != data:
            raise ValueError("conflicting duplicate")
        facts[url] = data
    if malformed and not facts:
        raise ValueError("no valid response records")
    return tuple(facts[k] for k in sorted(facts)), malformed


def normalize(
    facts: tuple[dict[str, JsonValue], ...],
    malformed: int,
    scanned: tuple[str, ...],
    request_bound: int,
    unreported: tuple[str, ...],
    limitations: tuple[str, ...],
    root: str,
    context: FeroxbusterContext,
) -> ContentDiscoveryOutput:
    wordlist_hash = sha256(("\n".join(WORDS) + "\n").encode("ascii")).hexdigest()
    snapshot = json.dumps(
        dict(
            root=root,
            facts=facts,
            scanned=scanned,
            request_upper_bound=request_bound,
            unreported=unreported,
            limitations=limitations,
            malformed=malformed,
            version="2.13.1",
            wordlist_profile="small-v1",
            wordlist_sha256=wordlist_hash,
        ),
        sort_keys=True,
        separators=(",", ":"),
    )
    evidence_id = f"{context.execution_id}:feroxbuster:evidence"
    observations = tuple(
        Observation(
            id=f"{context.execution_id}:feroxbuster:observation:{i}",
            kind="http",
            asset_id=context.asset_id,
            source="feroxbuster",
            data={**fact, "capability": "discover_content", "source_version": "2.13.1"},
            observed_at=context.collected_at,
            execution_id=context.execution_id,
            evidence_ids=(evidence_id,),
        )
        for i, fact in enumerate(facts)
    )
    refs: dict[str, list[str]] = {}
    for obs in observations:
        refs.setdefault(str(obs.data["url"]), []).append(obs.id)
    endpoints = tuple(
        Endpoint(
            id=f"{context.execution_id}:feroxbuster:endpoint:{i}",
            asset_id=context.asset_id,
            url=url,
            method="GET",
            observation_ids=tuple(ids),
        )
        for i, (url, ids) in enumerate(sorted(refs.items()))
    )
    partial = bool(malformed or limitations or unreported)
    return ContentDiscoveryOutput(
        query_target=root,
        status="partial" if partial else "completed",
        wordlist_sha256=wordlist_hash,
        scanned_directories=scanned,
        request_upper_bound=request_bound,
        unreported_urls=unreported,
        malformed_lines=malformed,
        limitations=limitations,
        errors=(ParserError("Partial bounded content discovery").to_error_info(),)
        if partial
        else (),
        asset=Asset(
            id=context.asset_id,
            kind="web_resource",
            value=root,
            observation_ids=tuple(o.id for o in observations),
        ),
        endpoints=endpoints,
        observations=observations,
        evidence=(
            Evidence(
                id=evidence_id,
                source="feroxbuster",
                capability="discover_content",
                origin=root,
                artifact_reference=f"memory:{context.execution_id}",
                locator="bounded-content-discovery",
                collected_at=context.collected_at,
                execution_id=context.execution_id,
                sha256=sha256(snapshot.encode()).hexdigest(),
            ),
        ),
    )

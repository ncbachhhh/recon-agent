"""Bounded JSONL normalization; redirects and technology remain untrusted facts."""

import json
from hashlib import sha256
from urllib.parse import urljoin, urlsplit, urlunsplit

from pydantic import JsonValue

from recon_agent.core.errors import ParserError
from recon_agent.core.results import Failure
from recon_agent.domain import Asset, Endpoint, Evidence, Observation, Target
from recon_agent.policy.scope import ScopeValidator
from recon_agent.tools.httpx_models import HttpProbeOutput, HttpxContext, HttpxLine


def probe_url(target: Target) -> str:
    """Scope has already canonicalized authority; constrain HTTPX input grammar."""
    if target.kind == "url":
        value = target.value
    elif target.kind in ("hostname", "domain", "ip"):
        authority = f"[{target.value}]" if ":" in target.value else target.value
        value = f"https://{authority}/"
    else:
        raise ValueError("HTTP probing requires hostname, IP or URL")
    parts = urlsplit(value)
    if (
        not value.isascii()
        or any(char in value for char in (",", "\\"))
        or parts.fragment
        or len(value) > 2048
    ):
        raise ValueError("unsupported HTTPX URL representation")
    host = parts.hostname
    assert host is not None
    authority = f"[{host}]" if ":" in host else host
    port = parts.port or (443 if parts.scheme == "https" else 80)
    if port != (443 if parts.scheme == "https" else 80):
        authority += f":{port}"
    return urlunsplit((parts.scheme, authority, parts.path or "/", parts.query, ""))


def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _checked_url(value: str, scope: ScopeValidator) -> str:
    checked = scope.validate_value(value)
    if isinstance(checked, Failure) or checked.value.canonical_target.kind != "url":
        raise ValueError("invalid or unauthorized URL")
    return probe_url(checked.value.canonical_target)


def parse(
    raw: bytes,
    candidates: tuple[str, ...],
    addresses: tuple[str, ...],
    scope: ScopeValidator,
) -> tuple[tuple[dict[str, JsonValue], ...], int]:
    lines = raw.splitlines()
    if len(lines) > 256:
        raise ValueError("output line bound")
    facts: dict[str, dict[str, JsonValue]] = {}
    conflicts: set[str] = set()
    accepted_counts: dict[str, int] = {}
    malformed = 0
    for line in lines:
        if not line.strip():
            continue
        try:
            if len(line) > 65536:
                raise ValueError("line bound")
            obj = json.loads(line.decode("utf-8"), object_pairs_hook=_unique)
            if not isinstance(obj, dict) or len(obj) > 128:
                raise ValueError("object bound")
            # Extra version-dependent JSON bookkeeping is not domain metadata.
            # No whole response/header/body is retained or interpreted as instructions.
            record = HttpxLine.model_validate(
                {
                    key: value
                    for key, value in obj.items()
                    if key in HttpxLine.model_fields
                }
            )
            url = _checked_url(record.url, scope)
            original = _checked_url(record.input, scope)
            if original not in candidates or url != original:
                raise ValueError("unrequested or followed URL")
            if record.final_url and _checked_url(record.final_url, scope) != url:
                raise ValueError("redirect following is unsupported")
            if obj.get("chain") or len(obj.get("chain_status_codes", [])) > 1:
                raise ValueError("unexpected redirect chain")
            address = scope.validate_value(record.host_ip)
            if (
                isinstance(address, Failure)
                or address.value.canonical_target.kind != "ip"
                or address.value.canonical_target.value not in addresses
            ):
                raise ValueError("unapproved contact address")
            parts = urlsplit(url)
            port = parts.port or (443 if parts.scheme == "https" else 80)
            if (
                record.scheme is not None
                and record.scheme != parts.scheme
                or record.host is not None
                and record.host != parts.hostname
                or record.port is not None
                and int(record.port) != port
            ):
                raise ValueError("inconsistent URL metadata")
            data: dict[str, JsonValue] = {
                "url": url,
                "final_url": url,
                "scheme": parts.scheme,
                "host": parts.hostname,
                "port": port,
                "method": "GET",
                "status_code": record.status_code,
                "contact_address": address.value.canonical_target.value,
                "redirect_followed": False,
                "body_read_limit": 65536,
                "metadata_completeness": "tool_reported_body_bounded",
            }
            for key, value in (
                ("title", record.title),
                ("server", record.webserver),
                ("content_type", record.content_type),
                ("content_length", record.content_length),
            ):
                if value is not None:
                    data[key] = value
            if record.tech is not None:
                data["technologies"] = [tech for tech in sorted(set(record.tech))]
            if record.location:
                # Validate for later use only. This check does not fetch, schedule,
                # mutate scope, or turn a hostname match into IP authorization.
                destination = urljoin(url, record.location)
                redirect = scope.validate_value(destination)
                data["redirect_location"] = record.location
                data["redirect_target"] = (
                    redirect.value.canonical_target.value
                    if not isinstance(redirect, Failure)
                    else destination
                )
                data["redirect_scope_status"] = (
                    "rejected" if isinstance(redirect, Failure) else "allowed"
                )
                data["redirect_authorized"] = False
            if url in conflicts:
                raise ValueError("conflicting URL")
            if url in facts and facts[url] != data:
                del facts[url]
                malformed += accepted_counts[url]
                conflicts.add(url)
                raise ValueError("conflicting duplicate")
            facts[url] = data
            accepted_counts[url] = accepted_counts.get(url, 0) + 1
        except (ValueError, TypeError, AttributeError, RecursionError):
            malformed += 1
    if malformed and not facts:
        raise ValueError("no valid records")
    return tuple(facts[url] for url in sorted(facts)), malformed


def normalize(
    facts: tuple[dict[str, JsonValue], ...],
    malformed: int,
    candidates: tuple[str, ...],
    addresses: tuple[str, ...],
    resolver: str,
    root: str,
    context: HttpxContext,
) -> HttpProbeOutput:
    unreported = tuple(
        url for url in candidates if url not in {f["url"] for f in facts}
    )
    partial = bool(malformed or unreported)
    snapshot = json.dumps(
        dict(
            query_target=root,
            candidates=candidates,
            contact_addresses=addresses,
            resolver_address=resolver,
            source_version="1.9.0",
            facts=facts,
            malformed_lines=malformed,
            unreported_candidates=unreported,
            status="partial" if partial else "completed",
        ),
        sort_keys=True,
        separators=(",", ":"),
    )
    evidence_id = f"{context.execution_id}:httpx:evidence"
    observations = tuple(
        Observation(
            id=f"{context.execution_id}:httpx:observation:{index}",
            kind="http",
            asset_id=context.asset_id,
            source="httpx",
            data={**data, "capability": "probe_http", "source_version": "1.9.0"},
            observed_at=context.collected_at,
            execution_id=context.execution_id,
            evidence_ids=(evidence_id,),
        )
        for index, data in enumerate(facts)
    )
    endpoints = tuple(
        Endpoint(
            id=f"{context.execution_id}:httpx:endpoint:{index}",
            asset_id=context.asset_id,
            url=str(data["url"]),
            method="GET",
            observation_ids=(observations[index].id,),
        )
        for index, data in enumerate(facts)
    )
    return HttpProbeOutput(
        query_target=root,
        candidates=candidates,
        contact_addresses=addresses,
        resolver_address=resolver,
        status="partial" if partial else "completed",
        malformed_lines=malformed,
        unreported_candidates=unreported,
        errors=(
            ParserError(
                "Partial HTTPX output; candidates or lines unreported"
            ).to_error_info(),
        )
        if partial
        else (),
        asset=Asset(
            id=context.asset_id,
            kind="host" if "://" not in root else "web_resource",
            value=root,
            observation_ids=tuple(item.id for item in observations),
        ),
        endpoints=endpoints,
        observations=observations,
        evidence=(
            Evidence(
                id=evidence_id,
                source="httpx",
                capability="probe_http",
                origin=root,
                artifact_reference=f"memory:{context.execution_id}",
                locator="http-probing",
                collected_at=context.collected_at,
                execution_id=context.execution_id,
                sha256=sha256(snapshot.encode()).hexdigest(),
            ),
        ),
    )

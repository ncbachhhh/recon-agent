"""Bounded Katana JSONL; remote URL/method/form/JS metadata is data only."""

import json
import re
from hashlib import sha256
from ipaddress import ip_address
from urllib.parse import urlsplit, urlunsplit

from pydantic import JsonValue

from recon_agent.core.errors import ParserError
from recon_agent.domain import Asset, Endpoint, Evidence, Observation, Target
from recon_agent.tools.katana_models import CrawlOutput, KatanaContext


def url_data(value: object) -> str:
    """Structural evidence check only. This function grants no authorization."""
    if (
        not isinstance(value, str)
        or not value.isascii()
        or len(value) > 2048
        or any(ord(c) <= 32 or ord(c) == 127 for c in value)
        or any(c in value for c in ("\\", ","))
    ):
        raise ValueError("unsupported URL representation")
    parts = urlsplit(value)
    if (
        parts.scheme not in ("http", "https")
        or not parts.hostname
        or parts.username is not None
        or parts.password is not None
        or parts.fragment
    ):
        raise ValueError("unsupported HTTP URL")
    port = parts.port or (443 if parts.scheme == "https" else 80)
    if not 1 <= port <= 65535:
        raise ValueError("invalid port")
    return urlunsplit((parts.scheme, parts.netloc, parts.path or "/", parts.query, ""))


def numeric_url(target: Target) -> str:
    if target.kind != "url":
        raise ValueError("crawl requires a numeric HTTP endpoint URL")
    value = url_data(target.value)
    parts = urlsplit(value)
    address = str(ip_address(parts.hostname or ""))
    authority = f"[{address}]" if ":" in address else address
    port = parts.port
    if port is not None and port != (443 if parts.scheme == "https" else 80):
        authority += f":{port}"
    return urlunsplit((parts.scheme, authority, parts.path, parts.query, ""))


def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _text(value: object, limit: int = 256) -> str:
    if not isinstance(value, str) or len(value) > limit or "\x00" in value:
        raise ValueError("bounded text required")
    return value


def _forms(value: object) -> list[JsonValue]:
    if not isinstance(value, list) or len(value) > 32:
        raise ValueError("form bound")
    result: list[JsonValue] = []
    for form in value:
        if not isinstance(form, dict) or len(form) > 8:
            raise ValueError("invalid form")
        data: dict[str, JsonValue] = {}
        for key in ("method", "action", "enctype"):
            if key in form:
                data[key] = _text(form[key], 2048 if key == "action" else 256)
        parameters = form.get("parameters", [])
        if not isinstance(parameters, list) or len(parameters) > 64:
            raise ValueError("form parameter bound")
        data["parameters"] = [_text(p) for p in sorted({_text(p) for p in parameters})]
        data["submitted"] = False
        result.append(data)
    # Exact local duplicate/order normalization, no generic web canonicalization.
    return [
        json.loads(s) for s in sorted({json.dumps(f, sort_keys=True) for f in result})
    ]


def parse(raw: bytes, page: str) -> tuple[tuple[dict[str, JsonValue], ...], int]:
    lines = raw.splitlines()
    if len(lines) > 512:
        raise ValueError("JSONL line bound")
    facts: dict[str, dict[str, JsonValue]] = {}
    malformed = 0
    for line in lines:
        if not line.strip():
            continue
        try:
            if len(line) > 65536:
                raise ValueError("JSONL record bound")
            obj = json.loads(line.decode("utf-8"), object_pairs_hook=_unique)
            if not isinstance(obj, dict) or len(obj) > 16:
                raise ValueError("JSON object bound")
            req = obj.get("request")
            if not isinstance(req, dict) or len(req) > 16:
                raise ValueError("missing request")
            url = url_data(req.get("endpoint"))
            method = _text(req.get("method"), 32)
            if re.fullmatch(r"[!#$%&'*+.^_`|~0-9A-Za-z-]+", method) is None:
                raise ValueError("invalid method")
            response = obj.get("response")
            contacted = response is not None
            if contacted and (url != page or method != "GET"):
                raise ValueError("unexpected internal follow or method")
            source = req.get("source", page)
            if url_data(source) != page:
                raise ValueError("unexpected source page")
            parts = urlsplit(url)
            data: dict[str, JsonValue] = {
                "url": url,
                "method": method,
                "source_page": page,
                "path": parts.path,
                "query_present": bool(parts.query),
                "tag": _text(req.get("tag", "")),
                "attribute": _text(req.get("attribute", "")),
                "contacted": contacted,
                "discovery_type": "page"
                if contacted
                else (
                    "javascript_endpoint"
                    if (req.get("tag"), req.get("attribute"))
                    in (("js", "regex"), ("script", "text"))
                    else "resource"
                    if (req.get("tag"), req.get("attribute")) == ("script", "src")
                    else "html_endpoint"
                ),
                "trust": "untrusted",
                "discovery_authorizes_contact": False,
            }
            if contacted:
                if not isinstance(response, dict) or len(response) > 32:
                    raise ValueError("invalid response")
                status = response.get("status_code")
                if type(status) is not int or not 100 <= status <= 599:
                    raise ValueError("invalid status")
                data["status_code"] = status
                headers = response.get("headers", {})
                if not isinstance(headers, dict) or len(headers) > 128:
                    raise ValueError("header bound")
                for name in ("content-type", "location"):
                    if name in headers:
                        data[name.replace("-", "_")] = _text(headers[name], 2048)
                if "forms" in response:
                    data["forms"] = _forms(response["forms"])
            if "error" in obj:
                # Fixed depth-limited discoveries are expected, not crawl failures.
                data["tool_error"] = _text(obj["error"], 4096)
            key = json.dumps(data, sort_keys=True, separators=(",", ":"))
            facts[key] = data
        except (ValueError, TypeError, AttributeError, RecursionError):
            malformed += 1
    if malformed and not facts:
        raise ValueError("no valid crawl records")
    return tuple(facts[k] for k in sorted(facts)), malformed


def followable(fact: dict[str, JsonValue]) -> bool:
    # Explicit read-only hyperlink and script-resource profile only. JS extracted
    # endpoints, htmx, forms, refresh/base/doctype and all redirects stay data.
    return (
        fact["method"] == "GET"
        and not fact["contacted"]
        and (fact["tag"], fact["attribute"]) in (("a", "href"), ("script", "src"))
    )


def normalize(
    facts: tuple[dict[str, JsonValue], ...],
    malformed: int,
    contacted: tuple[str, ...],
    limitations: tuple[str, ...],
    root: str,
    context: KatanaContext,
) -> CrawlOutput:
    snapshot = json.dumps(
        dict(
            root=root,
            facts=facts,
            contacted=contacted,
            limitations=limitations,
            malformed=malformed,
            version="1.8.0",
        ),
        sort_keys=True,
        separators=(",", ":"),
    )
    evidence_id = f"{context.execution_id}:katana:evidence"
    observations = tuple(
        Observation(
            id=f"{context.execution_id}:katana:observation:{index}",
            kind="http",
            asset_id=context.asset_id,
            source="katana",
            data={**data, "capability": "crawl_web", "source_version": "1.8.0"},
            observed_at=context.collected_at,
            execution_id=context.execution_id,
            evidence_ids=(evidence_id,),
        )
        for index, data in enumerate(facts)
    )
    endpoint_refs: dict[tuple[str, str], list[str]] = {}
    for observation in observations:
        key = (str(observation.data["url"]), str(observation.data["method"]))
        endpoint_refs.setdefault(key, []).append(observation.id)
    endpoints = tuple(
        Endpoint(
            id=f"{context.execution_id}:katana:endpoint:{i}",
            asset_id=context.asset_id,
            url=url,
            method=method,
            observation_ids=tuple(refs),
        )
        for i, ((url, method), refs) in enumerate(sorted(endpoint_refs.items()))
    )
    partial = bool(malformed or limitations)
    return CrawlOutput(
        query_target=root,
        status="partial" if partial else "completed",
        contacted_urls=contacted,
        malformed_lines=malformed,
        limitations=limitations,
        errors=(ParserError("Partial bounded crawl collection").to_error_info(),)
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
                source="katana",
                capability="crawl_web",
                origin=root,
                artifact_reference=f"memory:{context.execution_id}",
                locator="bounded-crawl",
                collected_at=context.collected_at,
                execution_id=context.execution_id,
                sha256=sha256(snapshot.encode()).hexdigest(),
            ),
        ),
    )

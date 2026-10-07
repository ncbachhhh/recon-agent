"""Bounded text/XML extraction with no remote instruction or contact semantics."""

import base64
import re
from hashlib import sha256
from xml.etree import ElementTree

from recon_agent.core.errors import ParserError
from recon_agent.domain import Asset, Evidence, Observation
from recon_agent.tools.common_files_models import (
    CommonFileFact,
    CommonFilesContext,
    CommonFilesOutput,
    CommonPath,
    HttpResponse,
    RedirectFact,
)


def sitemap_urls(text: str) -> tuple[str, ...]:
    # UTF-8 decoding has already rejected alternate encodings/NUL. Reject every
    # DTD/entity declaration BEFORE stdlib parsing, including internal subsets.
    if "\x00" in text or re.search(r"<!\s*(DOCTYPE|ENTITY)\b", text, re.I):
        raise ValueError("XML declarations are forbidden")
    declaration = re.match(r"\s*<\?xml\b[^?]*\?>", text)
    if declaration:
        encoding = re.search(r"encoding\s*=\s*['\"]([^'\"]+)['\"]", declaration[0])
        if encoding and encoding[1].lower() not in ("utf-8", "utf8"):
            raise ValueError("unsupported XML encoding")
    root = ElementTree.fromstring(text)
    namespace = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
    if root.tag not in (
        "urlset",
        "sitemapindex",
        namespace + "urlset",
        namespace + "sitemapindex",
    ):
        raise ValueError("unsupported sitemap root")
    prefix = namespace if root.tag.startswith(namespace) else ""
    child_name = "sitemap" if root.tag.endswith("sitemapindex") else "url"
    nodes = 0
    pending = [(root, 0)]
    while pending:
        node, depth = pending.pop()
        nodes += 1
        if nodes > 2048 or depth > 16:
            raise ValueError("sitemap structure bound exceeded")
        pending.extend((child, depth + 1) for child in node)
    urls: set[str] = set()
    if len(root) > 256:
        raise ValueError("sitemap URL bound exceeded")
    for child in root:
        if child.tag != prefix + child_name:
            raise ValueError("unsupported sitemap entry")
        locations = [node for node in child if node.tag == prefix + "loc"]
        if len(locations) != 1 or len(locations[0]):
            raise ValueError("invalid sitemap location")
        url = (locations[0].text or "").strip()
        if not 1 <= len(url) <= 2048 or not url.startswith(("http://", "https://")):
            raise ValueError("unsupported sitemap URL")
        urls.add(url)
    return tuple(sorted(urls))


def response_fact(
    path: CommonPath,
    requested_url: str,
    final_url: str,
    address: str | None,
    response: HttpResponse | None,
    redirects: tuple[RedirectFact, ...],
) -> CommonFileFact:
    if response is None:
        return CommonFileFact(
            path=path,
            requested_url=requested_url,
            final_url=final_url,
            contact_address=address,
            retained_bytes=0,
            body_base64="",
            redirects=redirects,
        )
    errors = list(response.errors)
    text = None
    robots: list[dict[str, str]] = []
    security: list[dict[str, str]] = []
    discovered: tuple[str, ...] = ()
    if response.truncated:
        errors.append(
            ParserError(
                "Common-file response body incomplete or exceeds bound"
            ).to_error_info()
        )
    elif response.status_code == 200:
        media = (response.content_type or "").split(";", 1)[0].strip().lower()
        allowed = (
            ("application/xml", "text/xml")
            if path == "/sitemap.xml"
            else ("text/plain",)
        )
        try:
            if media not in allowed or response.content_encoding not in (
                None,
                "identity",
            ):
                raise ValueError("unsupported common-file content")
            text = response.body.decode("utf-8-sig")
            if "\x00" in text:
                raise ValueError("unsupported text encoding")
            if path == "/sitemap.xml":
                discovered = sitemap_urls(text)
            elif path == "/.well-known/security.txt":
                for line in text.splitlines():
                    name, sep, value = line.split("#", 1)[0].partition(":")
                    if sep and name.strip().lower() in (
                        "contact",
                        "expires",
                        "encryption",
                        "acknowledgments",
                        "preferred-languages",
                        "canonical",
                        "policy",
                        "hiring",
                    ):
                        if len(security) >= 256 or len(value.strip()) > 2048:
                            raise ValueError("security metadata bound exceeded")
                        security.append(
                            {"field": name.strip().lower(), "value": value.strip()}
                        )
            elif path == "/robots.txt":
                for line in text.splitlines():
                    directive, separator, value = line.split("#", 1)[0].partition(":")
                    directive = directive.strip().lower()
                    value = value.strip()
                    if separator and directive in (
                        "user-agent",
                        "allow",
                        "disallow",
                        "sitemap",
                    ):
                        if len(robots) >= 256 or len(value) > 2048:
                            raise ValueError("robots directive bound exceeded")
                        robots.append({"directive": directive, "value": value})
                discovered = tuple(
                    sorted(
                        {
                            item["value"]
                            for item in robots
                            if item["directive"] == "sitemap"
                            and item["value"].startswith(("http://", "https://"))
                        }
                    )
                )
        except (ValueError, UnicodeError, ElementTree.ParseError):
            # Keep exact raw bytes and valid decoded text; parsed facts are atomic.
            robots = []
            security = []
            discovered = ()
            errors.append(
                ParserError(
                    "Unsupported or malformed common-file content"
                ).to_error_info()
            )
    return CommonFileFact(
        path=path,
        requested_url=requested_url,
        final_url=final_url,
        contact_address=address,
        status_code=response.status_code,
        content_type=response.content_type,
        content_length=response.content_length,
        retained_bytes=len(response.body),
        body_base64=base64.b64encode(response.body).decode("ascii"),
        body_text=text,
        truncated=response.truncated,
        redirects=redirects,
        robots=tuple(robots),
        security=tuple(security),
        discovered_urls=discovered,
        errors=tuple(errors),
    )


def normalize(
    target: str, files: tuple[CommonFileFact, ...], context: CommonFilesContext
) -> CommonFilesOutput:
    observations = []
    evidence = []
    for index, fact in enumerate(files):
        evidence_id = f"{context.execution_id}:common:evidence:{index}"
        evidence.append(
            Evidence(
                id=evidence_id,
                source="native_common_files",
                capability="inspect_common_files",
                origin=fact.requested_url,
                artifact_reference=f"memory:{context.execution_id}",
                locator=f"files/{index}",
                collected_at=context.collected_at,
                execution_id=context.execution_id,
                sha256=sha256(fact.model_dump_json().encode()).hexdigest(),
                truncated=fact.truncated,
            )
        )
        observations.append(
            Observation(
                id=f"{context.execution_id}:common:observation:{index}",
                kind="http",
                asset_id=context.asset_id,
                source="native_common_files",
                data={
                    **fact.model_dump(mode="json"),
                    "source_capability": "inspect_common_files",
                },
                observed_at=context.collected_at,
                evidence_ids=(evidence_id,),
                execution_id=context.execution_id,
            )
        )
    errors = tuple(error for fact in files for error in fact.errors)
    return CommonFilesOutput(
        query_target=target,
        status="partial" if errors else "completed",
        files=files,
        errors=errors,
        asset=Asset(
            id=context.asset_id,
            kind="web_resource",
            value=target,
            observation_ids=tuple(item.id for item in observations),
        ),
        observations=tuple(observations),
        evidence=tuple(evidence),
    )

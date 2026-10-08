"""Pure HTTP contact identity. Parsing never checks scope or performs I/O."""

import re
from ipaddress import IPv6Address, ip_address
from typing import Literal
from urllib.parse import urlsplit

from pydantic import field_validator

from recon_agent.domain._base import NonEmptyText, Record
from recon_agent.domain.identity import canonical_json

_LABEL = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\Z")
_METHOD = re.compile(r"[!#$%&'*+.^_`|~0-9A-Za-z-]+\Z")
_PATH = re.compile(r"(?:[A-Za-z0-9._~!$&'()*+,;=:@/-]|%[0-9A-Fa-f]{2})*\Z")
_QUERY = re.compile(r"(?:[A-Za-z0-9._~!$&'()*+,;=:@/?-]|%[0-9A-Fa-f]{2})*\Z")


def _host(value: str) -> str:
    if not value or not value.isascii() or "%" in value:
        raise ValueError("Unsupported web host")
    try:
        address = ip_address(value)
    except ValueError:
        host = value.lower().removesuffix(".")
        labels = host.split(".")
        if (
            len(host) > 253
            or any(
                not _LABEL.fullmatch(label) or label.startswith("xn--")
                for label in labels
            )
            or all(
                label.isdecimal() or re.fullmatch(r"0x[0-9a-f]+", label)
                for label in labels
            )
        ):
            raise ValueError("Unsupported web host") from None
        return host
    if isinstance(address, IPv6Address) and address.ipv4_mapped is not None:
        raise ValueError("Mapped IPv6 is unsupported")
    return str(address)


def canonical_web_url(value: str) -> str:
    """Canonical HTTP(S) contact URL; malformed/ambiguous input raises ValueError.

    Preserve path and query bytes (including an empty query delimiter). Validate
    fragments before omitting them. No decoding, dot removal, query sorting, DNS,
    scope lookup or transport is involved. See docs/web-identity.md.
    """
    if (
        type(value) is not str
        or not 1 <= len(value) <= 2048
        or not value.isascii()
        or any(ord(char) <= 32 or ord(char) == 127 for char in value)
        or "\\" in value
    ):
        raise ValueError("Unsupported web URL")
    try:
        parts = urlsplit(value)
        if parts.scheme not in ("http", "https") or not parts.netloc:
            raise ValueError("Unsupported web URL")
        authority = parts.netloc
        if "@" in authority or "%" in authority:
            raise ValueError("Ambiguous web authority")
        if authority.startswith("["):
            match = re.fullmatch(r"\[([^\]]+)\](?::([0-9]+))?", authority)
            if match is None or not isinstance(ip_address(match[1]), IPv6Address):
                raise ValueError("Invalid IPv6 authority")
            host, port_text = _host(match[1]), match[2]
            authority = f"[{host}]"
        else:
            match = re.fullmatch(r"([^:\[\]]+)(?::([0-9]+))?", authority)
            if match is None:
                raise ValueError("Ambiguous web authority")
            authority, port_text = _host(match[1]), match[2]
        port = int(port_text) if port_text is not None else None
        if port is not None:
            if not 1 <= port <= 65535:
                raise ValueError("Invalid web port")
            if port != (443 if parts.scheme == "https" else 80):
                authority += f":{port}"
        if (
            not _PATH.fullmatch(parts.path)
            or not _QUERY.fullmatch(parts.query)
            or not _QUERY.fullmatch(parts.fragment)
        ):
            raise ValueError("Unsupported web URL encoding")
        query = "?" + parts.query if "?" in value.split("#", 1)[0] else ""
        return f"{parts.scheme}://{authority}{parts.path or '/'}{query}"
    except ValueError:
        # Diagnostics never echo userinfo, query secrets or remote text.
        raise ValueError("Malformed or unsupported web URL") from None


class WebAssetIdentity(Record):
    """Contact resource identity; method case and explicit Host variants matter."""

    version: Literal["web-v1"] = "web-v1"
    url: NonEmptyText
    method: NonEmptyText = "GET"
    host_header: NonEmptyText | None = None

    @field_validator("url")
    @classmethod
    def canonical_url(cls, value: str) -> str:
        return canonical_web_url(value)

    @field_validator("method")
    @classmethod
    def valid_method(cls, value: str) -> str:
        if not _METHOD.fullmatch(value):
            raise ValueError("Invalid HTTP method")
        return value

    @field_validator("host_header")
    @classmethod
    def canonical_host_header(cls, value: str | None) -> str | None:
        # Current explicit Host variants are FFUF DNS candidates, not ports/SNI.
        if value is not None:
            host = _host(value)
            if ":" in host:
                raise ValueError("Unsupported Host variant")
            return host
        return None

    @property
    def key(self) -> str:
        return canonical_json(self.model_dump(mode="json"))


class WebAssetDiscovery(Record):
    """Derived deduplicated view retaining all references, never permission."""

    identity: WebAssetIdentity
    endpoint_ids: tuple[NonEmptyText, ...] = ()
    observation_ids: tuple[NonEmptyText, ...] = ()
    evidence_ids: tuple[NonEmptyText, ...] = ()
    contacted_observation_ids: tuple[NonEmptyText, ...] = ()

    @property
    def contacted(self) -> bool:
        """At least one source reported a response; no inference from discovery."""
        return bool(self.contacted_observation_ids)

"""Local declaration membership only; no contact, authority inference or logging."""

import re
from dataclasses import dataclass, field
from ipaddress import (
    IPv4Address,
    IPv4Network,
    IPv6Address,
    IPv6Network,
    ip_address,
    ip_network,
)
from typing import Literal
from urllib.parse import urlsplit, urlunsplit

from pydantic import BaseModel, ConfigDict, ValidationError

from recon_agent.core.errors import (
    ErrorContext,
    ScopeRejectedError,
    ScopeRejectionReason,
)
from recon_agent.core.results import Failure, OperationResult, Success
from recon_agent.domain import Scope, Target

_Address = IPv4Address | IPv6Address
_Network = IPv4Network | IPv6Network
_PRIVATE = (
    IPv4Network("10.0.0.0/8"),
    IPv4Network("172.16.0.0/12"),
    IPv4Network("192.168.0.0/16"),
    IPv6Network("fc00::/7"),
)
_LABEL = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", re.ASCII)


class ScopeMatch(BaseModel):
    """Traceable membership result, not an executable approval token."""

    model_config = ConfigDict(
        extra="forbid", strict=True, frozen=True, revalidate_instances="always"
    )
    canonical_target: Target
    matched_rule: Target


@dataclass(frozen=True)
class _Parsed:
    target: Target
    host: str | None = None
    address: _Address | None = None
    network: _Network | None = None

    @property
    def authority(self) -> str:
        # URLs report only their host, never paths/query strings in error context.
        return self.host if self.host is not None else self.target.value


def _hostname(value: str) -> str:
    if not value.isascii():
        raise ValueError("unsupported hostname encoding")
    host = value.lower().removesuffix(".")
    labels = host.split(".")
    if len(host) > 253 or any(
        not _LABEL.fullmatch(label) or label.startswith("xn--") for label in labels
    ):
        raise ValueError("invalid or unsupported hostname")
    # Reject numeric address spellings rather than treating them as DNS names.
    if all(
        label.isdecimal() or re.fullmatch(r"0x[0-9a-f]+", label) for label in labels
    ):
        raise ValueError("address is not a hostname")
    return host


def _address(value: str) -> _Address:
    if "%" in value:
        raise ValueError("scoped IPv6 is unsupported")
    address = ip_address(value)
    if isinstance(address, IPv6Address) and address.ipv4_mapped is not None:
        raise ValueError("mapped IPv6 is unsupported")
    return address


def _parse(target: Target) -> _Parsed:
    value = target.value
    if not value or any(c.isspace() or ord(c) < 32 or ord(c) == 127 for c in value):
        raise ValueError("whitespace or control characters are unsupported")
    if target.kind in ("domain", "hostname"):
        host = _hostname(value)
        return _Parsed(target.model_copy(update={"value": host}), host=host)
    if target.kind == "ip":
        address = _address(value)
        return _Parsed(
            target.model_copy(update={"value": str(address)}), address=address
        )
    if target.kind == "cidr":
        if "/" not in value:
            raise ValueError("CIDR prefix required")
        _address(value.split("/", 1)[0])
        network = ip_network(value, strict=True)
        # Prefix length syntax only; dotted masks are deliberately unsupported.
        if (
            not value.split("/", 1)[1].isascii()
            or not value.split("/", 1)[1].isdecimal()
        ):
            raise ValueError("invalid prefix length")
        return _Parsed(
            target.model_copy(update={"value": str(network)}), network=network
        )
    if target.kind != "url":
        raise ValueError("unsupported target kind")
    if "\\" in value:
        raise ValueError("ambiguous URL separators")
    url = urlsplit(value)
    if url.scheme not in ("http", "https") or not url.netloc or not url.hostname:
        raise ValueError("unsupported or incomplete URL")
    if url.username is not None or url.password is not None or "@" in url.netloc:
        raise ValueError("userinfo is unsupported")
    if "[" in url.netloc and not re.fullmatch(r"\[[^\]]+\](?::[0-9]+)?", url.netloc):
        raise ValueError("invalid bracketed authority suffix")
    port = url.port  # Raises for malformed/out-of-range port text.
    if url.netloc.endswith(":") or port == 0:
        raise ValueError("invalid port")
    url_address: _Address | None = None
    try:
        url_address = _address(url.hostname)
    except ValueError:
        host = _hostname(url.hostname)
    else:
        host = str(url_address)
    # Brackets are for IPv6 only; urllib also accepts IPvFuture authorities.
    if "[" in url.netloc and not isinstance(url_address, IPv6Address):
        raise ValueError("invalid bracketed authority")
    authority = f"[{host}]" if isinstance(url_address, IPv6Address) else host
    if port is not None:
        authority += f":{port}"
    canonical = urlunsplit((url.scheme, authority, url.path, url.query, url.fragment))
    return _Parsed(
        target.model_copy(update={"value": canonical}), host=host, address=url_address
    )


def _matches(rule: _Parsed, candidate: _Parsed, descendants: bool) -> bool:
    if rule.network is not None:
        if candidate.address is not None:
            return candidate.address.version == rule.network.version and (
                candidate.address in rule.network
            )
        if candidate.network is not None:
            return candidate.network.version == rule.network.version and (
                int(candidate.network.network_address)
                >= int(rule.network.network_address)
                and int(candidate.network.broadcast_address)
                <= int(rule.network.broadcast_address)
            )
        return False
    if rule.address is not None:
        return candidate.address == rule.address
    if candidate.address is not None or candidate.network is not None:
        return False
    return candidate.host == rule.host or (
        descendants
        and rule.target.kind == "domain"
        and candidate.host is not None
        and rule.host is not None
        and candidate.host.endswith("." + rule.host)
    )


def _excluded(rule: _Parsed, candidate: _Parsed) -> bool:
    if rule.network is not None and candidate.network is not None:
        return (
            rule.network.version == candidate.network.version
            and rule.network.overlaps(candidate.network)
        )
    if rule.address is not None and candidate.network is not None:
        return rule.address.version == candidate.network.version and (
            rule.address in candidate.network
        )
    return _matches(rule, candidate, descendants=True)


def _private(candidate: _Parsed) -> bool:
    if candidate.address is not None:
        return any(
            candidate.address.version == network.version
            and candidate.address in network
            for network in _PRIVATE
        )
    if candidate.network is not None:
        return any(
            candidate.network.version == network.version
            and candidate.network.overlaps(network)
            for network in _PRIVATE
        )
    return False


def _rule_order(rule: _Parsed) -> tuple[int, int, str, str, str]:
    # Exact authorities precede domains, then most-specific CIDRs. Stable ties
    # depend on canonical data/opaque ID, never declaration order.
    rank = 2 if rule.network is not None else int(rule.target.kind == "domain")
    specificity = (
        rule.network.prefixlen
        if rule.network is not None
        else (rule.host or "").count(".")
    )
    return rank, -specificity, rule.target.kind, rule.target.value, rule.target.id


def _rejection(
    reason: ScopeRejectionReason, candidate: _Parsed | None = None
) -> ScopeRejectedError:
    return ScopeRejectedError(
        "Scope validation rejected the target.",
        context=ErrorContext(
            scope_reason=reason,
            target_kind=candidate.target.kind if candidate is not None else None,
            normalized_candidate=candidate.authority if candidate is not None else None,
        ),
    )


@dataclass(frozen=True)
class ScopeValidator:
    """Immutable compiled scope snapshot; validate each introduced target anew.

    Effective options come from Scope, never global application configuration.
    Malformed declarations fail construction rather than being silently ignored.
    """

    scope: Scope
    _roots: tuple[_Parsed, ...] = field(init=False, repr=False)
    _exclusions: tuple[_Parsed, ...] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        try:
            snapshot = Scope.model_validate(self.scope)
            roots = tuple(sorted((_parse(t) for t in snapshot.roots), key=_rule_order))
            exclusions = tuple(_parse(t) for t in snapshot.exclusions)
        except (ValueError, TypeError):
            raise _rejection(ScopeRejectionReason.INVALID_SCOPE) from None
        object.__setattr__(self, "scope", snapshot)
        object.__setattr__(self, "_roots", roots)
        object.__setattr__(self, "_exclusions", exclusions)

    def validate(self, candidate: Target) -> OperationResult[ScopeMatch]:
        """Return canonical matched declaration or canonical structured failure."""
        try:
            parsed = _parse(Target.model_validate(candidate))
        except (ValueError, TypeError, ValidationError):
            return Failure(
                error=_rejection(ScopeRejectionReason.INVALID_TARGET).to_error_info()
            )
        if any(_excluded(rule, parsed) for rule in self._exclusions):
            reason = ScopeRejectionReason.EXCLUDED
        elif not self.scope.allow_private_ips and _private(parsed):
            reason = ScopeRejectionReason.PRIVATE_IP_NOT_ALLOWED
        else:
            for rule in self._roots:
                if _matches(rule, parsed, self.scope.allow_subdomains):
                    return Success[ScopeMatch](
                        value=ScopeMatch(
                            canonical_target=parsed.target, matched_rule=rule.target
                        )
                    )
            reason = ScopeRejectionReason.NOT_IN_SCOPE
        return Failure(error=_rejection(reason, parsed).to_error_info())

    def validate_value(self, value: str) -> OperationResult[ScopeMatch]:
        """Classify untyped action target text locally, then use the same parser.

        Delimiters select URL/CIDR/address syntax, never a permissive fallback
        after parsing fails. Ordinary names use hostname (not domain-root) kind.
        """
        kind: Literal["url", "cidr", "ip", "hostname"]
        try:
            if "://" in value:
                kind = "url"
            elif "/" in value:
                kind = "cidr"
            elif ":" in value or value.replace(".", "").isdecimal():
                kind = "ip"
            else:
                kind = "hostname"
            candidate = Target(id="action-target", kind=kind, value=value)
        except (ValueError, TypeError):
            return Failure(
                error=_rejection(ScopeRejectionReason.INVALID_TARGET).to_error_info()
            )
        return self.validate(candidate)

    def require_allowed(self, candidate: Target) -> ScopeMatch:
        """Raise the canonical policy exception on rejection, without side effects."""
        result = self.validate(candidate)
        if result.status == "failure":
            raise ScopeRejectedError(result.error.message, context=result.error.context)
        return result.value


__all__ = ["ScopeMatch", "ScopeValidator"]

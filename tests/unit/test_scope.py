"""Offline implementation tests; the broader independent corpus belongs to M1-T02."""

from dataclasses import FrozenInstanceError
from unittest.mock import Mock

import pytest
from pydantic import TypeAdapter, ValidationError

from recon_agent.core.config.models import ScopeConfig
from recon_agent.core.errors import ErrorCode, ErrorContext, ScopeRejectedError
from recon_agent.core.results import OperationResult
from recon_agent.domain import Scope, Target
from recon_agent.policy import ScopeMatch, ScopeRejectionReason, ScopeValidator
from recon_agent.policy import scope as scope_module


def target(value: str, kind: str = "domain", identity: str = "target") -> Target:
    return Target.model_validate({"id": identity, "kind": kind, "value": value})


def validator(
    *roots: Target,
    subdomains: bool = False,
    private: bool = False,
    exclusions: tuple[Target, ...] = (),
) -> ScopeValidator:
    return ScopeValidator(
        Scope(
            id="scope",
            roots=roots,
            exclusions=exclusions,
            allow_subdomains=subdomains,
            allow_private_ips=private,
        )
    )


@pytest.mark.parametrize(
    ("value", "allowed"),
    [
        ("example.com", True),
        ("EXAMPLE.COM", True),
        ("Example.Com.", True),
        ("api.example.com", False),
        ("notexample.com", False),
        ("example.com.attacker.test", False),
        ("fake-example.com", False),
    ],
)
def test_scope_exact_domains(value: str, allowed: bool) -> None:
    result = validator(target("example.com")).validate(target(value))
    assert (result.status == "success") == allowed
    if allowed:
        assert result.status == "success"
        assert result.value.canonical_target.value == "example.com"


@pytest.mark.parametrize(
    ("value", "allowed"),
    [
        ("example.com", True),
        ("api.example.com", True),
        ("a.b.example.com", True),
        ("example.com.attacker.test", False),
        ("notexample.com", False),
        ("fake-example.com", False),
    ],
)
def test_scope_explicit_domain_descendants(value: str, allowed: bool) -> None:
    assert (
        validator(target("example.com"), subdomains=True).validate(target(value)).status
        == "success"
    ) == allowed


@pytest.mark.parametrize("kind", ["hostname", "url"])
def test_scope_hostname_and_url_roots_remain_exact(kind: str) -> None:
    root = "https://example.com/root" if kind == "url" else "example.com"
    policy = validator(target(root, kind), subdomains=True)
    assert policy.validate(target("example.com", "hostname")).status == "success"
    assert policy.validate(target("api.example.com", "hostname")).status == "failure"


def test_scope_independently_declared_subdomain_and_stable_match() -> None:
    root = target("example.com", identity="root")
    exact = target("api.example.com", "hostname", "exact")
    candidate = target("API.EXAMPLE.COM.", "hostname")
    a = validator(root, exact, subdomains=True)
    b = validator(exact, root, subdomains=True)
    assert a.validate(candidate) == b.validate(candidate) == a.validate(candidate)
    assert a.require_allowed(candidate).matched_rule == exact
    assert validator(root, exact).validate(candidate).status == "success"


@pytest.mark.parametrize(
    ("root", "candidate", "allowed"),
    [
        ("192.0.2.10", "192.0.2.10", True),
        ("192.0.2.10", "192.0.2.11", False),
        ("2001:db8::1", "2001:0db8:0:0::1", True),
        ("2001:db8::1", "2001:db8::2", False),
    ],
)
def test_scope_exact_ips(root: str, candidate: str, allowed: bool) -> None:
    assert (
        validator(target(root, "ip")).validate(target(candidate, "ip")).status
        == "success"
    ) == allowed


@pytest.mark.parametrize(
    ("root", "candidate", "kind", "allowed"),
    [
        ("192.0.2.0/24", "192.0.2.0", "ip", True),
        ("192.0.2.0/24", "192.0.2.255", "ip", True),
        ("192.0.2.0/24", "192.0.3.0", "ip", False),
        ("192.0.2.0/24", "192.0.2.128/25", "cidr", True),
        ("192.0.2.0/24", "192.0.2.0/23", "cidr", False),
        ("2001:db8::/32", "2001:db8::", "ip", True),
        ("2001:db8::/32", "2001:db8:ffff:ffff:ffff:ffff:ffff:ffff", "ip", True),
        ("2001:db8::/32", "2001:db9::", "ip", False),
        ("2001:db8::/32", "2001:db8:1::/48", "cidr", True),
        ("2001:db8::/32", "2001:db8::/31", "cidr", False),
        ("2001:db8::/32", "192.0.2.1", "ip", False),
        ("192.0.2.0/24", "2001:db8::/32", "cidr", False),
        ("192.0.2.0/24", "example.com", "domain", False),
    ],
)
def test_scope_cidr_membership(
    root: str, candidate: str, kind: str, allowed: bool
) -> None:
    assert (
        validator(target(root, "cidr")).validate(target(candidate, kind)).status
        == "success"
    ) == allowed


@pytest.mark.parametrize(
    ("value", "allowed"),
    [
        ("https://example.com/", True),
        ("http://EXAMPLE.COM.:8080/Admin?Q=X#F", True),
        ("https://api.example.com/path", True),
        ("https://evil.test/example.com", False),
        ("https://example.com@evil.test/", False),
        ("https://example.com.evil.test/", False),
    ],
)
def test_scope_url_authority(value: str, allowed: bool) -> None:
    assert (
        validator(target("example.com"), subdomains=True)
        .validate(target(value, "url"))
        .status
        == "success"
    ) == allowed


def test_scope_url_preserves_path_query_case_and_parses_ip_literals() -> None:
    policy = validator(
        target("example.com"), target("192.0.2.10", "ip"), target("2001:db8::1", "ip")
    )
    url = "HTTP://EXAMPLE.COM.:8080/Admin?Q=X#F"
    match = policy.require_allowed(target(url, "url"))
    assert match.canonical_target.value == "http://example.com:8080/Admin?Q=X#F"
    for url in ("http://192.0.2.10/", "http://[2001:0db8::1]:443/"):
        assert policy.validate(target(url, "url")).status == "success"
    assert policy.validate(target("192.0.2.10", "hostname")).status == "failure"


@pytest.mark.parametrize(
    ("kind", "value"),
    [
        ("domain", " example.com"),
        ("domain", "example.com "),
        ("domain", "example..com"),
        ("domain", ".example.com"),
        ("domain", "example.com.."),
        ("hostname", "-example.com"),
        ("hostname", "example-.com"),
        ("hostname", "a" * 64 + ".com"),
        ("hostname", ".".join(["a" * 63] * 4)),
        ("hostname", "exa_mple.com"),
        ("hostname", "example.com:443"),
        ("hostname", "0x7f000001"),
        ("hostname", "0x7f.0.0.1"),
        ("hostname", "https://example.com"),
        ("domain", "*.example.com"),
        ("domain", "bücher.test"),
        ("domain", "xn--bcher-kva.test"),
        ("ip", "192.0.2.999"),
        ("ip", "192.000.2.10"),
        ("ip", "2001:db8:::1"),
        ("ip", "::ffff:192.0.2.10"),
        ("ip", "fe80::1%eth0"),
        ("cidr", "192.0.2.1/24"),
        ("cidr", "192.0.2.0/33"),
        ("cidr", "192.0.2.0/255.255.255.0"),
        ("cidr", "2001:db8::/129"),
        ("cidr", "192.0.2.1"),
        ("cidr", "192.0.2.0/a"),
        ("url", "http://"),
        ("url", "https:///"),
        ("url", "//example.com/"),
        ("url", "ftp://example.com/"),
        ("url", "https://example.com:/"),
        ("url", "https://example.com:0/"),
        ("url", "https://example.com:65536/"),
        ("url", "https://example.com:bad/"),
        ("url", "https://example.com@evil.test/"),
        ("url", "https://evil.test@example.com/"),
        ("url", "https://example.com\\@evil.test/"),
        ("url", "https://example.com\n.evil.test/"),
        ("url", "https://[::ffff:192.0.2.10]/"),
        ("url", "https://[v1.example.com]/"),
        ("url", "https://[2001:db8::1]evil.test/"),
        ("url", "https://[2001:db8::1/"),
        ("url", "https://%65xample.com/"),
        ("url", "http://192.0.2.999/"),
    ],
)
def test_scope_malformed_targets_and_declarations_fail_closed(
    kind: str, value: str
) -> None:
    result = validator(target("example.com")).validate(target(value, kind))
    assert result.status == "failure"
    assert result.error.context.scope_reason == ScopeRejectionReason.INVALID_TARGET
    assert result.error.context.normalized_candidate is None
    for exclusions in (False, True):
        with pytest.raises(ScopeRejectedError) as caught:
            validator(
                *(() if exclusions else (target(value, kind),)),
                exclusions=(target(value, kind),) if exclusions else (),
            )
        assert caught.value.context.scope_reason == ScopeRejectionReason.INVALID_SCOPE


@pytest.mark.parametrize("value", ["", " "])
def test_scope_empty_values_fail_at_structural_boundary(value: str) -> None:
    with pytest.raises(ValidationError):
        target(value)


@pytest.mark.parametrize(
    ("allow_private", "candidate", "allowed"),
    [
        (True, "10.10.10.5", True),
        (True, "10.20.20.5", False),
        (False, "10.10.10.5", False),
        (True, "fd00::1", True),
        (True, "fd01::1", False),
        (False, "fd00::1", False),
    ],
)
def test_scope_private_option_never_grants_membership(
    allow_private: bool,
    candidate: str,
    allowed: bool,
) -> None:
    policy = validator(
        target("10.10.10.0/24", "cidr"),
        target("fd00::/64", "cidr"),
        private=allow_private,
    )
    result = policy.validate(target(candidate, "ip"))
    assert (result.status == "success") == allowed
    if not allow_private:
        assert result.status == "failure"
        assert (
            result.error.context.scope_reason
            == ScopeRejectionReason.PRIVATE_IP_NOT_ALLOWED
        )


def test_scope_private_range_and_url_gate() -> None:
    policy = validator(target("0.0.0.0/0", "cidr"))
    assert policy.validate(target("0.0.0.0/0", "cidr")).status == "failure"
    assert policy.validate(target("http://10.10.10.5/", "url")).status == "failure"
    assert policy.validate(target("192.0.2.1", "ip")).status == "success"
    # Documentation/loopback/etc are membership data, not RFC1918/ULA flags.
    assert (
        validator(target("127.0.0.1", "ip")).validate(target("127.0.0.1", "ip")).status
        == "success"
    )


@pytest.mark.parametrize(
    ("exclusion", "kind", "candidate", "candidate_kind"),
    [
        ("api.example.com", "domain", "a.api.example.com", "hostname"),
        ("api.example.com", "hostname", "api.example.com", "domain"),
        (
            "https://api.example.com/path",
            "url",
            "http://api.example.com:8080/else",
            "url",
        ),
        ("192.0.2.128/25", "cidr", "192.0.2.200", "ip"),
        ("192.0.2.128/25", "cidr", "192.0.2.0/24", "cidr"),
        ("192.0.2.200", "ip", "192.0.2.0/24", "cidr"),
        ("2001:db8:1::/48", "cidr", "2001:db8::/32", "cidr"),
    ],
)
def test_scope_exclusions_always_win(
    exclusion: str,
    kind: str,
    candidate: str,
    candidate_kind: str,
) -> None:
    policy = validator(
        target("example.com"),
        target("192.0.2.0/24", "cidr"),
        target("2001:db8::/32", "cidr"),
        subdomains=True,
        exclusions=(target(exclusion, kind),),
    )
    result = policy.validate(target(candidate, candidate_kind))
    assert result.status == "failure"
    assert result.error.context.scope_reason == ScopeRejectionReason.EXCLUDED


def test_scope_exclusion_boundaries() -> None:
    policy = validator(
        target("example.com"),
        subdomains=True,
        exclusions=(target("api.example.com", "hostname"),),
    )
    assert policy.validate(target("a.api.example.com")).status == "success"
    policy = validator(
        target("192.0.2.0/24", "cidr"),
        exclusions=(target("2001:db8::/32", "cidr"), target("192.0.3.1", "ip")),
    )
    assert policy.validate(target("192.0.2.0/24", "cidr")).status == "success"
    assert (
        validator(target("192.0.2.1", "ip")).validate(target("example.com")).status
        == "failure"
    )


def test_scope_redirect_and_discovery_do_not_expand_authority() -> None:
    policy = validator(target("example.com"))
    assert policy.validate(target("https://example.com/", "url")).status == "success"
    assert (
        policy.validate(target("https://example.com/next", "url")).status == "success"
    )
    for value, kind in (
        ("https://evil.test/", "url"),
        ("api.example.com", "hostname"),
        ("192.0.2.10", "ip"),
    ):
        assert policy.validate(target(value, kind)).status == "failure"
    assert len(policy.scope.roots) == 1


def test_scope_results_errors_roundtrip_and_safe_diagnostics() -> None:
    policy = validator(target("example.com"))
    candidate = target("https://evil.test/private?token=synthetic", "url")
    result = policy.validate(candidate)
    assert result.status == "failure"
    assert result.error.code == ErrorCode.SCOPE_REJECTED
    assert result.error.context.scope_reason == ScopeRejectionReason.NOT_IN_SCOPE
    assert result.error.context.normalized_candidate == "evil.test"
    assert "synthetic" not in result.model_dump_json()
    with pytest.raises(ScopeRejectedError) as caught:
        policy.require_allowed(candidate)
    assert caught.value.to_error_info() == result.error
    adapter = TypeAdapter[OperationResult[ScopeMatch]](OperationResult[ScopeMatch])
    for outcome in (result, policy.validate(target("example.com"))):
        assert adapter.validate_json(adapter.dump_json(outcome)) == outcome
    assert (
        ErrorContext.model_validate_json(result.error.context.model_dump_json())
        == result.error.context
    )


def test_scope_no_mutation_and_no_global_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = ScopeConfig(allow_subdomains=True, allow_private_ips=True)
    declared = Scope(id="scope", roots=(target("EXAMPLE.COM."),))
    candidate = target("Example.Com.")
    before = (declared.model_dump(), candidate.model_dump(), config.model_dump())
    monkeypatch.setattr("socket.getaddrinfo", Mock(side_effect=AssertionError("DNS")))
    monkeypatch.setattr("socket.socket", Mock(side_effect=AssertionError("network")))
    policy = ScopeValidator(declared)
    assert policy.require_allowed(candidate).canonical_target.value == "example.com"
    assert before == (
        declared.model_dump(),
        candidate.model_dump(),
        config.model_dump(),
    )
    assert policy.validate(target("api.example.com")).status == "failure"
    with pytest.raises(FrozenInstanceError):
        policy.scope = Scope(id="replacement")


def test_scope_empty_and_invalid_structural_inputs() -> None:
    assert validator().validate(target("example.com")).status == "failure"
    malformed = Target.model_construct(id="bad", kind="unknown", value="example.com")
    assert validator(target("example.com")).validate(malformed).status == "failure"
    bad_scope = Scope.model_construct(id="scope", roots=(malformed,))
    with pytest.raises(ScopeRejectedError):
        ScopeValidator(bad_scope)


def test_scope_parser_failure_is_never_allowed(monkeypatch: pytest.MonkeyPatch) -> None:
    policy = validator(target("example.com"))
    monkeypatch.setattr(
        scope_module, "_parse", Mock(side_effect=ValueError("untrusted"))
    )
    result = policy.validate(target("example.com"))
    assert result.status == "failure"
    assert "untrusted" not in result.model_dump_json()

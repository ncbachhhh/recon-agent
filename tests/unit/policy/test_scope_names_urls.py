"""Independent adversarial corpus for the documented name/URL boundary."""

from itertools import product
from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from recon_agent.core.errors import ErrorCode, ScopeRejectedError
from recon_agent.domain import Scope, Target
from recon_agent.policy import ScopeRejectionReason, ScopeValidator


def target(value: str, kind: str = "domain", identity: str = "candidate") -> Target:
    return Target.model_validate({"id": identity, "kind": kind, "value": value})


@pytest.mark.parametrize("kind", ["domain", "hostname"])
@pytest.mark.parametrize("value", ["example.com", "EXAMPLE.COM", "Example.Com."])
def test_scope_exact_names_have_one_canonical_identity(kind: str, value: str) -> None:
    root = target("EXAMPLE.COM.", identity="root")
    policy = ScopeValidator(Scope(id="scope", roots=(root,)))
    match = policy.require_allowed(target(value, kind))
    assert match.canonical_target == target("example.com", kind)
    assert match.matched_rule == target("example.com", identity="root")
    assert root.value == "EXAMPLE.COM."


@pytest.mark.parametrize("subdomains", [False, True])
@pytest.mark.parametrize(
    "value",
    [
        "notexample.com",
        "fake-example.com",
        "example.com.attacker.test",
        "example.comm",
        "example.comevil.test",
        "aexample.com",
        "badexample.com",
        "fooexample.com",
        "examplecom",
        "api.example.com.attacker.test",
    ],
)
def test_scope_domain_suffix_confusion_does_not_authorize_lookalikes(
    subdomains: bool, value: str
) -> None:
    policy = ScopeValidator(
        Scope(id="scope", roots=(target("example.com"),), allow_subdomains=subdomains)
    )
    result = policy.validate(target(value))
    assert result.status == "failure"
    assert result.error.context.scope_reason == ScopeRejectionReason.NOT_IN_SCOPE


@pytest.mark.parametrize(
    "value", ["api.example.com", "a.b.example.com", "deep.a.b.example.com"]
)
@pytest.mark.parametrize("subdomains", [False, True])
def test_scope_descendants_require_a_flag_or_independent_declaration(
    value: str, subdomains: bool
) -> None:
    policy = ScopeValidator(
        Scope(id="scope", roots=(target("example.com"),), allow_subdomains=subdomains)
    )
    assert (policy.validate(target(value)).status == "success") == subdomains
    explicit = ScopeValidator(
        Scope(id="explicit", roots=(target("example.com"), target(value, "hostname")))
    )
    assert explicit.validate(target(value)).status == "success"


def test_scope_generated_prefixes_require_a_label_boundary() -> None:
    policy = ScopeValidator(
        Scope(id="scope", roots=(target("example.com"),), allow_subdomains=True)
    )
    # Exhaust a small reproducible alphabet; no random seed or new dependency.
    for size in range(1, 4):
        for letters in product("az09-", repeat=size):
            prefix = "".join(letters)
            result = policy.validate(target(prefix + "example.com"))
            assert result.status == "failure", prefix
            if prefix[0] != "-" and prefix[-1] != "-":
                assert (
                    policy.validate(target(prefix + ".example.com")).status == "success"
                )


@pytest.mark.parametrize(
    "value",
    [
        ".",
        "..",
        "/",
        ":",
        "@",
        ".example.com",
        "example..com",
        "example.com..",
        "-example.com",
        "example-.com",
        "exa_mple.com",
        "*.example.com",
        "example.com:443",
        "https://example.com/",
        "bücher.example.com",
        "exаmple.com",
        "example。com",
        "ｅxample.com",
        "xn--bcher-kva.example.com",
        "XN--bcher-kva.example.com",
        "api.xn--example.com",
        "a" * 64 + ".example.com",
        ".".join(["a" * 63] * 4),
    ],
)
@pytest.mark.parametrize("kind", ["domain", "hostname"])
def test_scope_malformed_or_unsupported_names_cannot_be_candidates_or_rules(
    value: str, kind: str
) -> None:
    malformed = target(value, kind)
    good = target("example.com")
    policy = ScopeValidator(Scope(id="scope", roots=(good,), allow_subdomains=True))
    result = policy.validate(malformed)
    assert result.status == "failure"
    assert result.error.context.scope_reason == ScopeRejectionReason.INVALID_TARGET
    assert result.error.context.normalized_candidate is None
    for scope in (
        Scope(id="scope", roots=(good, malformed)),
        Scope(id="scope", roots=(good,), exclusions=(malformed,)),
    ):
        with pytest.raises(ScopeRejectedError) as caught:
            ScopeValidator(scope)
        assert caught.value.code == ErrorCode.SCOPE_REJECTED
        assert caught.value.context.scope_reason == ScopeRejectionReason.INVALID_SCOPE


@pytest.mark.parametrize(
    "character", [" ", "\t", "\n", "\r", "\x00", "\x1f", "\x7f", "\u00a0"]
)
@pytest.mark.parametrize("position", ["before", "after", "embedded"])
@pytest.mark.parametrize("kind", ["hostname", "url"])
def test_scope_whitespace_and_controls_are_never_implicitly_stripped(
    character: str, position: str, kind: str
) -> None:
    value = "example.com" if kind == "hostname" else "https://example.com/"
    value = {
        "before": character + value,
        "after": value + character,
        "embedded": value.replace("example", "exa" + character + "mple"),
    }[position]
    result = ScopeValidator(Scope(id="scope", roots=(target("example.com"),))).validate(
        target(value, kind)
    )
    assert result.status == "failure"
    assert result.error.context.scope_reason == ScopeRejectionReason.INVALID_TARGET


def test_scope_dns_length_limits_accept_valid_boundary_names() -> None:
    for value in ("a" * 63 + ".test", ".".join(["a" * 63] * 3 + ["a" * 61])):
        policy = ScopeValidator(Scope(id="scope", roots=(target(value),)))
        assert (
            policy.require_allowed(target(value.upper() + ".")).canonical_target.value
            == value
        )


@pytest.mark.parametrize(
    "value",
    [
        "https://example.com/",
        "http://example.com/path",
        "https://example.com:443/",
        "http://example.com:8080/",
        "https://example.com:1/",
        "https://example.com:65535/",
        "HTTPS://EXAMPLE.COM./Path?next=https://evil.test/#evil.test",
        "https://example.com/%2f%00?q=%20#ordinary",
    ],
)
def test_scope_url_path_query_fragment_and_valid_ports_do_not_change_host_membership(
    value: str,
) -> None:
    policy = ScopeValidator(Scope(id="scope", roots=(target("example.com"),)))
    assert policy.validate(target(value, "url")).status == "success"


@pytest.mark.parametrize(
    "value",
    [
        "https://evil.test/example.com/",
        "https://example.com.evil.test/",
        "https://notexample.com/",
        "https://evil.test/?next=https://example.com",
        "https://evil.test/#example.com",
        "https://evil.test:443/example.com",
    ],
)
def test_scope_url_authority_controls_authorization_even_when_other_components_match(
    value: str,
) -> None:
    policy = ScopeValidator(Scope(id="scope", roots=(target("example.com"),)))
    result = policy.validate(target(value, "url"))
    assert result.status == "failure"
    assert result.error.context.scope_reason == ScopeRejectionReason.NOT_IN_SCOPE


@pytest.mark.parametrize(
    "value",
    [
        "https://example.com@evil.test/",
        "https://user:pass@example.com@evil.test/",
        "https://user@example.com/",
        "https://user:pass@example.com/",
        "https://@example.com/",
        "https://example.com%40evil.test/",
    ],
)
def test_scope_url_userinfo_never_authorizes_even_an_independently_scoped_actual_host(
    value: str,
) -> None:
    policy = ScopeValidator(
        Scope(id="scope", roots=(target("example.com"), target("evil.test")))
    )
    result = policy.validate(target(value, "url"))
    assert result.status == "failure"
    assert result.error.context.scope_reason == ScopeRejectionReason.INVALID_TARGET
    assert result.error.context.normalized_candidate is None
    assert "pass" not in result.model_dump_json()


@pytest.mark.parametrize(
    "value",
    [
        "http://",
        "https:///",
        "http://@",
        "https://:443/",
        "//example.com/",
        "ftp://example.com/",
        "file:///etc/passwd",
        "javascript:example.com",
        "data:text/plain,example.com",
        "https:example.com",
        "https:/example.com",
        "https://example.com:abc/",
        "https://example.com:99999/",
        "https://example.com:0/",
        "https://example.com:/",
        "https://example.com:-1/",
        "https://example.com:443:80/",
        "https://example%2Ecom/",
        "https://example.com%00.evil.test/",
        "https://%65xample.com/",
        "https://example.com\\@evil.test/",
        "https:\\example.com",
        "https://example.com/path\\evil",
        "http://[::1",
        "https://[example.com]/",
        "https://[2001:db8::1]evil.test/",
        "https://[2001:db8::1]:abc/",
        "https://2001:db8::1/",
        "https://example.com]/",
        "https://[v1.example.com]/",
        "https://bücher.example.com/",
        "https://xn--bcher-kva.example.com/",
    ],
)
def test_scope_url_malformed_authority_encoding_and_schemes_fail_closed(
    value: str,
) -> None:
    policy = ScopeValidator(
        Scope(id="scope", roots=(target("example.com"), target("2001:db8::1", "ip")))
    )
    result = policy.validate(target(value, "url"))
    assert result.status == "failure"
    assert result.error.context.scope_reason == ScopeRejectionReason.INVALID_TARGET


@pytest.mark.parametrize("subdomains", [False, True])
@pytest.mark.parametrize(
    ("destination", "requires_subdomains", "independently_allowed"),
    [
        ("https://example.com/next", False, True),
        ("https://api.example.com/", True, True),
        ("https://evil.test/", False, False),
        ("https://example.com.evil.test/", False, False),
        ("https://example.com@evil.test/", False, False),
        ("http://192.0.2.10/", False, False),
    ],
)
def test_scope_redirect_destinations_are_revalidated_before_fake_contact(
    subdomains: bool,
    destination: str,
    requires_subdomains: bool,
    independently_allowed: bool,
) -> None:
    policy = ScopeValidator(
        Scope(id="scope", roots=(target("example.com"),), allow_subdomains=subdomains)
    )
    assert policy.validate(target("https://example.com/", "url")).status == "success"
    contact = Mock()
    candidate = target(destination, "url")
    allowed = independently_allowed and (not requires_subdomains or subdomains)
    # A test-only consumer of the existing boundary, not an execution subsystem.
    if allowed:
        contact(policy.require_allowed(candidate).canonical_target)
        contact.assert_called_once_with(
            policy.require_allowed(candidate).canonical_target
        )
    else:
        with pytest.raises(ScopeRejectedError):
            contact(policy.require_allowed(candidate).canonical_target)
        contact.assert_not_called()
    assert len(policy.scope.roots) == 1


@pytest.mark.parametrize(
    "source", ["tls_san", "dns_record", "robots.txt", "javascript", "scanner_output"]
)
@pytest.mark.parametrize(
    ("value", "kind", "allowed"),
    [
        ("example.com", "hostname", True),
        ("api.example.com", "hostname", False),
        ("evil.test", "hostname", False),
        ("192.0.2.10", "ip", False),
    ],
)
def test_scope_discovery_source_labels_cannot_expand_authorization(
    source: str, value: str, kind: str, allowed: bool
) -> None:
    declared = Scope(id="scope", roots=(target("example.com"),))
    before = declared.model_dump()
    policy = ScopeValidator(declared)
    direct = target(value, kind)
    # Provenance is data outside Target; the public validator has no source override.
    evidence = {"source": source, "candidate": direct}
    discovered = evidence["candidate"]
    assert discovered == direct
    result = policy.validate(direct)
    assert policy.validate(discovered) == result
    assert (result.status == "success") == allowed
    contact = Mock()
    if allowed:
        contact(policy.require_allowed(discovered).canonical_target)
        contact.assert_called_once_with(policy.require_allowed(direct).canonical_target)
    else:
        with pytest.raises(ScopeRejectedError):
            contact(policy.require_allowed(discovered).canonical_target)
        contact.assert_not_called()
    assert policy.scope.model_dump() == before == declared.model_dump()


def test_scope_redirect_ip_requires_its_own_declaration_even_after_allowed_origin() -> (
    None
):
    roots = (target("example.com"), target("192.0.2.10", "ip"))
    policy = ScopeValidator(Scope(id="scope", roots=roots))
    policy.require_allowed(target("https://example.com/", "url"))
    contact = Mock()
    match = policy.require_allowed(target("http://192.0.2.10/", "url"))
    contact(match.canonical_target)
    contact.assert_called_once_with(target("http://192.0.2.10/", "url"))
    assert match.matched_rule == roots[1]


@pytest.mark.parametrize("value", ["", " ", "\t", "\n"])
def test_scope_empty_candidates_are_rejected_before_policy(value: str) -> None:
    with pytest.raises(ValidationError):
        target(value)

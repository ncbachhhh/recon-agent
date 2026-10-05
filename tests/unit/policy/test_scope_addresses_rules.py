"""Address boundaries, exclusion precedence and stable public scope outcomes."""

from ipaddress import ip_address, ip_network
from itertools import permutations
from unittest.mock import Mock

import pytest
from pydantic import TypeAdapter, ValidationError

from recon_agent.core.errors import ErrorCode, ScopeRejectedError
from recon_agent.core.results import OperationResult
from recon_agent.domain import Scope, Target
from recon_agent.policy import ScopeMatch, ScopeRejectionReason, ScopeValidator
from recon_agent.policy import scope as scope_module


def target(value: str, kind: str = "ip", identity: str = "candidate") -> Target:
    return Target.model_validate({"id": identity, "kind": kind, "value": value})


@pytest.mark.parametrize("value", ["192.0.2.10", "198.51.100.20", "203.0.113.30"])
def test_scope_ipv4_exact_membership_rejects_both_neighbors(value: str) -> None:
    policy = ScopeValidator(Scope(id="scope", roots=(target(value),)))
    assert policy.require_allowed(target(value)).canonical_target.value == value
    for offset in (-1, 1):
        result = policy.validate(
            target(str(ip_address(int(ip_address(value)) + offset)))
        )
        assert result.status == "failure"
        assert result.error.context.scope_reason == ScopeRejectionReason.NOT_IN_SCOPE


@pytest.mark.parametrize(
    "value", ["2001:db8::1", "2001:0db8:0:0:0:0:0:1", "2001:DB8:0000::0001"]
)
@pytest.mark.parametrize("as_url", [False, True])
def test_scope_ipv6_equivalents_and_bracketed_urls_use_parsed_identity(
    value: str, as_url: bool
) -> None:
    policy = ScopeValidator(Scope(id="scope", roots=(target("2001:db8::1"),)))
    candidate = target(
        f"https://[{value}]:443/" if as_url else value, "url" if as_url else "ip"
    )
    match = policy.require_allowed(candidate)
    expected = "https://[2001:db8::1]:443/" if as_url else "2001:db8::1"
    assert match.canonical_target.value == expected
    assert policy.validate(target("2001:db8::2")).status == "failure"


@pytest.mark.parametrize(
    ("network", "members", "nonmembers"),
    [
        (
            "192.0.2.0/24",
            ("192.0.2.0", "192.0.2.1", "192.0.2.128", "192.0.2.255"),
            ("192.0.1.255", "192.0.3.0"),
        ),
        ("192.0.2.10/32", ("192.0.2.10",), ("192.0.2.9", "192.0.2.11")),
        ("192.0.2.10/31", ("192.0.2.10", "192.0.2.11"), ("192.0.2.9", "192.0.2.12")),
        (
            "2001:db8::/32",
            ("2001:db8::", "2001:db8::1", "2001:db8:ffff:ffff:ffff:ffff:ffff:ffff"),
            ("2001:db7:ffff:ffff:ffff:ffff:ffff:ffff", "2001:db9::"),
        ),
        ("2001:db8::/127", ("2001:db8::", "2001:db8::1"), ("2001:db8::2",)),
        ("2001:db8::1/128", ("2001:db8::1",), ("2001:db8::", "2001:db8::2")),
    ],
)
def test_scope_cidr_membership_includes_network_and_last_address(
    network: str, members: tuple[str, ...], nonmembers: tuple[str, ...]
) -> None:
    policy = ScopeValidator(Scope(id="scope", roots=(target(network, "cidr"),)))
    for value in members:
        assert policy.validate(target(value)).status == "success", value
    for value in nonmembers:
        result = policy.validate(target(value))
        assert result.status == "failure", value
        assert result.error.context.scope_reason == ScopeRejectionReason.NOT_IN_SCOPE


@pytest.mark.parametrize("network", ["0.0.0.0/0", "::/0"])
def test_scope_zero_prefix_has_same_family_membership_and_still_obeys_private_gate(
    network: str,
) -> None:
    ipv4 = network == "0.0.0.0/0"
    policy = ScopeValidator(
        Scope(id="scope", roots=(target(network, "cidr"),), allow_private_ips=True)
    )
    for value in (
        ("0.0.0.0", "255.255.255.255")
        if ipv4
        else ("::", "ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff")
    ):
        assert policy.validate(target(value)).status == "success"
    assert (
        policy.validate(target("2001:db8::1" if ipv4 else "192.0.2.1")).status
        == "failure"
    )
    gated = ScopeValidator(Scope(id="scope", roots=(target(network, "cidr"),)))
    result = gated.validate(target(network, "cidr"))
    assert result.status == "failure"
    assert (
        result.error.context.scope_reason == ScopeRejectionReason.PRIVATE_IP_NOT_ALLOWED
    )


def test_scope_generated_cidr_decisions_match_mathematical_membership() -> None:
    # Exhaust each IPv4 prefix wholly inside the documentation /24 and its neighbors.
    for prefix in range(24, 33):
        network = ip_network(f"192.0.2.0/{prefix}")
        policy = ScopeValidator(
            Scope(id="scope", roots=(target(str(network), "cidr"),))
        )
        for offset in range(-1, 257):
            address = ip_address(int(ip_address("192.0.2.0")) + offset)
            result = policy.validate(target(str(address)))
            assert (result.status == "success") == (address in network), (
                network,
                address,
            )
    for prefix in (32, 48, 64, 96, 127, 128):
        network = ip_network(f"2001:db8::/{prefix}")
        policy = ScopeValidator(
            Scope(id="scope", roots=(target(str(network), "cidr"),))
        )
        for number in (
            int(network.network_address) - 1,
            int(network.network_address),
            int(network.network_address) + 1,
            int(network.broadcast_address),
            int(network.broadcast_address) + 1,
        ):
            address = ip_address(number)
            assert (policy.validate(target(str(address))).status == "success") == (
                address in network
            )


@pytest.mark.parametrize(
    "value",
    [
        "192.168.001.001",
        "127.1",
        "2130706433",
        "0x7f000001",
        "0177.0.0.1",
        "192.0.2.256",
        "192.0.2.-1",
        "192.0.2.1.",
        "2001:db8:::1",
        "2001:db8::g",
        "[2001:db8::1]",
        "::ffff:192.0.2.10",
        "::ffff:c000:20a",
        "fe80::1%eth0",
        "fe80::1%25eth0",
    ],
)
@pytest.mark.parametrize("kind", ["ip", "url"])
def test_scope_nonstandard_ip_and_unsupported_ipv6_forms_fail_closed(
    value: str, kind: str
) -> None:
    policy = ScopeValidator(
        Scope(
            id="scope",
            roots=(target("0.0.0.0/0", "cidr"), target("::/0", "cidr")),
            allow_private_ips=True,
        )
    )
    url_host = f"[{value}]" if ":" in value else value
    result = policy.validate(
        target(f"http://{url_host}/" if kind == "url" else value, kind)
    )
    assert result.status == "failure"
    assert result.error.context.scope_reason == ScopeRejectionReason.INVALID_TARGET


@pytest.mark.parametrize(
    "value", ["127.1", "2130706433", "0x7f000001", "192.168.001.001"]
)
def test_scope_alternate_ipv4_cannot_fall_back_to_authorized_hostname(
    value: str,
) -> None:
    with pytest.raises(ScopeRejectedError) as caught:
        ScopeValidator(Scope(id="scope", roots=(target(value, "hostname"),)))
    assert caught.value.context.scope_reason == ScopeRejectionReason.INVALID_SCOPE


@pytest.mark.parametrize(
    "value",
    [
        "192.0.2.1/24",
        "192.0.2.0/-1",
        "192.0.2.0/33",
        "192.0.2.0/",
        "192.0.2.0/255.255.255.0",
        "192.0.2.0/0.0.0.255",
        "192.0.2.0/abc",
        "192.0.2.0/24/24",
        "2001:db8::1/64",
        "2001:db8::/129",
        "2001:db8::/-1",
        "::ffff:192.0.2.0/120",
        "fe80::%eth0/64",
    ],
)
def test_scope_invalid_cidr_cannot_partially_compile_with_valid_rules(
    value: str,
) -> None:
    good = target("192.0.2.0/24", "cidr")
    bad = target(value, "cidr")
    policy = ScopeValidator(Scope(id="scope", roots=(good,)))
    result = policy.validate(bad)
    assert result.status == "failure"
    assert result.error.context.scope_reason == ScopeRejectionReason.INVALID_TARGET
    for roots, exclusions in (((good, bad), ()), ((good,), (bad,))):
        with pytest.raises(ScopeRejectedError) as caught:
            ScopeValidator(Scope(id="scope", roots=roots, exclusions=exclusions))
        assert caught.value.context.scope_reason == ScopeRejectionReason.INVALID_SCOPE


@pytest.mark.parametrize(
    ("root", "member", "unrelated"),
    [
        ("10.10.10.0/24", "10.10.10.5", "10.20.20.5"),
        ("172.16.1.0/24", "172.16.1.1", "172.31.1.1"),
        ("192.168.1.0/24", "192.168.1.1", "192.168.2.1"),
        ("fd00::/64", "fd00::1", "fc00::1"),
    ],
)
@pytest.mark.parametrize("private", [False, True])
def test_scope_private_ip_flag_does_not_expand_declared_scope(
    root: str, member: str, unrelated: str, private: bool
) -> None:
    policy = ScopeValidator(
        Scope(id="scope", roots=(target(root, "cidr"),), allow_private_ips=private)
    )
    result = policy.validate(target(member))
    assert (result.status == "success") == private
    rejected = policy.validate(target(unrelated))
    assert rejected.status == "failure"
    expected = (
        ScopeRejectionReason.NOT_IN_SCOPE
        if private
        else ScopeRejectionReason.PRIVATE_IP_NOT_ALLOWED
    )
    assert rejected.error.context.scope_reason == expected
    if not private:
        assert result.status == "failure"
        assert result.error.context.scope_reason == expected


@pytest.mark.parametrize(
    ("private", "nonprivate"),
    [
        ("10.0.0.0", "9.255.255.255"),
        ("10.255.255.255", "11.0.0.0"),
        ("172.16.0.0", "172.15.255.255"),
        ("172.31.255.255", "172.32.0.0"),
        ("192.168.0.0", "192.167.255.255"),
        ("192.168.255.255", "192.169.0.0"),
        ("fc00::", "fbff:ffff:ffff:ffff:ffff:ffff:ffff:ffff"),
        ("fdff:ffff:ffff:ffff:ffff:ffff:ffff:ffff", "fe00::"),
    ],
)
def test_scope_private_gate_uses_explicit_rfc1918_and_ula_boundaries(
    private: str, nonprivate: str
) -> None:
    policy = ScopeValidator(
        Scope(id="scope", roots=(target(private), target(nonprivate)))
    )
    result = policy.validate(target(private))
    assert result.status == "failure"
    assert (
        result.error.context.scope_reason == ScopeRejectionReason.PRIVATE_IP_NOT_ALLOWED
    )
    assert policy.validate(target(nonprivate)).status == "success"


@pytest.mark.parametrize(
    "value",
    [
        "127.0.0.1",
        "::1",
        "169.254.0.0",
        "169.254.255.255",
        "fe80::1",
        "0.0.0.0",
        "::",
        "224.0.0.1",
        "ff02::1",
    ],
)
def test_scope_special_addresses_require_explicit_membership_without_invented_private_gates(
    value: str,
) -> None:
    assert ScopeValidator(Scope(id="empty")).validate(target(value)).status == "failure"
    policy = ScopeValidator(Scope(id="scope", roots=(target(value),)))
    assert policy.validate(target(value)).status == "success"


@pytest.mark.parametrize("allow_subdomains", [False, True])
@pytest.mark.parametrize("exclusion_kind", ["domain", "hostname", "url"])
def test_scope_exclusion_subtree_semantics_depend_on_rule_kind_not_allow_flag(
    allow_subdomains: bool, exclusion_kind: str
) -> None:
    roots = tuple(
        target(v, "domain", v)
        for v in (
            "example.com",
            "admin.example.com",
            "x.admin.example.com",
            "api.example.com",
        )
    )
    exclusion = target(
        "https://admin.example.com/path"
        if exclusion_kind == "url"
        else "admin.example.com",
        exclusion_kind,
    )
    policy = ScopeValidator(
        Scope(
            id="scope",
            roots=roots,
            exclusions=(exclusion,),
            allow_subdomains=allow_subdomains,
        )
    )
    excluded = policy.validate(target("admin.example.com", "hostname"))
    assert excluded.status == "failure"
    assert excluded.error.context.scope_reason == ScopeRejectionReason.EXCLUDED
    assert policy.validate(target("api.example.com", "hostname")).status == "success"
    deeper = policy.validate(target("x.admin.example.com", "hostname"))
    assert (deeper.status == "success") == (exclusion_kind != "domain")


@pytest.mark.parametrize(
    ("exclusion", "kind", "denied", "allowed"),
    [
        (
            "10.10.20.0/24",
            "cidr",
            ("10.10.20.0", "10.10.20.255"),
            ("10.10.19.255", "10.10.21.0"),
        ),
        ("10.10.20.5", "ip", ("10.10.20.5",), ("10.10.20.4", "10.10.20.6")),
        (
            "2001:db8:1::/48",
            "cidr",
            ("2001:db8:1::", "2001:db8:1:ffff:ffff:ffff:ffff:ffff"),
            ("2001:db8::1", "2001:db8:2::"),
        ),
    ],
)
def test_scope_address_exclusions_win_at_both_boundaries(
    exclusion: str, kind: str, denied: tuple[str, ...], allowed: tuple[str, ...]
) -> None:
    roots = (target("10.10.0.0/16", "cidr"), target("2001:db8::/32", "cidr"))
    policy = ScopeValidator(
        Scope(
            id="scope",
            roots=roots,
            exclusions=(target(exclusion, kind),),
            allow_private_ips=True,
        )
    )
    for value in denied:
        result = policy.validate(target(value))
        assert result.status == "failure"
        assert result.error.context.scope_reason == ScopeRejectionReason.EXCLUDED
    for value in allowed:
        assert policy.validate(target(value)).status == "success"


def test_scope_candidate_ranges_cannot_union_roots_or_subtract_excluded_addresses() -> (
    None
):
    halves = (target("192.0.2.0/25", "cidr"), target("192.0.2.128/25", "cidr"))
    policy = ScopeValidator(Scope(id="scope", roots=halves))
    assert policy.validate(target("192.0.2.0/24", "cidr")).status == "failure"
    for excluded in (target("192.0.2.128/25", "cidr"), target("192.0.2.255")):
        policy = ScopeValidator(
            Scope(
                id="scope",
                roots=(target("192.0.2.0/24", "cidr"),),
                exclusions=(excluded,),
            )
        )
        result = policy.validate(target("192.0.2.0/24", "cidr"))
        assert result.status == "failure"
        assert result.error.context.scope_reason == ScopeRejectionReason.EXCLUDED
        assert policy.validate(target("192.0.2.0/25", "cidr")).status == "success"


@pytest.mark.parametrize(
    ("root", "contained", "larger"),
    [
        ("192.0.2.0/24", "192.0.2.128/25", "192.0.2.0/23"),
        ("2001:db8::/32", "2001:db8:1::/48", "2001:db8::/31"),
    ],
)
def test_scope_candidate_cidr_requires_full_containment_in_one_root(
    root: str, contained: str, larger: str
) -> None:
    policy = ScopeValidator(Scope(id="scope", roots=(target(root, "cidr"),)))
    assert policy.validate(target(root, "cidr")).status == "success"
    assert policy.validate(target(contained, "cidr")).status == "success"
    rejected = policy.validate(target(larger, "cidr"))
    assert rejected.status == "failure"
    assert rejected.error.context.scope_reason == ScopeRejectionReason.NOT_IN_SCOPE


@pytest.mark.parametrize(
    "value", ["10.0.0.0/7", "172.0.0.0/11", "192.168.0.0/15", "f800::/5"]
)
def test_scope_partial_private_cidr_overlap_blocks_the_entire_candidate(
    value: str,
) -> None:
    root = target(value, "cidr")
    rejected = ScopeValidator(Scope(id="scope", roots=(root,))).validate(root)
    assert rejected.status == "failure"
    assert (
        rejected.error.context.scope_reason
        == ScopeRejectionReason.PRIVATE_IP_NOT_ALLOWED
    )
    allowed = ScopeValidator(Scope(id="scope", roots=(root,), allow_private_ips=True))
    assert allowed.validate(root).status == "success"


def test_scope_exclusion_reason_precedes_private_gate_and_missing_allow_membership() -> (
    None
):
    excluded = target("10.10.20.0/24", "cidr")
    policy = ScopeValidator(Scope(id="scope", exclusions=(excluded,)))
    result = policy.validate(target("10.10.20.5"))
    assert result.status == "failure"
    assert result.error.context.scope_reason == ScopeRejectionReason.EXCLUDED


def test_scope_canonical_duplicate_rules_use_stable_ids_for_match_ties() -> None:
    roots = (
        target("EXAMPLE.COM.", "domain", "z"),
        target("example.com", "domain", "a"),
    )
    for ordered in permutations(roots):
        match = ScopeValidator(Scope(id="scope", roots=ordered)).require_allowed(
            target("Example.Com", "hostname")
        )
        assert match.matched_rule == target("example.com", "domain", "a")


def test_scope_rule_permutations_duplicates_and_repeated_results_are_stable() -> None:
    roots = (
        target("EXAMPLE.COM.", "domain", "root"),
        target("api.example.com", "domain", "specific"),
        target("API.EXAMPLE.COM.", "hostname", "exact"),
    )
    exclusions = (
        target("admin.example.com", "domain", "admin"),
        target("evil.test", "hostname", "evil"),
    )
    candidates = tuple(
        target(v, "hostname")
        for v in (
            "example.com",
            "api.example.com",
            "a.api.example.com",
            "x.admin.example.com",
            "evil.test",
        )
    )
    baseline = ScopeValidator(
        Scope(id="scope", roots=roots, exclusions=exclusions, allow_subdomains=True)
    )
    outcomes = tuple(baseline.validate(candidate) for candidate in candidates)
    assert baseline.require_allowed(candidates[1]).matched_rule.id == "exact"
    assert baseline.require_allowed(candidates[2]).matched_rule.id == "specific"
    for ordered_roots in permutations(roots):
        for ordered_exclusions in permutations(exclusions):
            policy = ScopeValidator(
                Scope(
                    id="scope",
                    roots=ordered_roots + (roots[0],),
                    exclusions=ordered_exclusions + (exclusions[0],),
                    allow_subdomains=True,
                )
            )
            for candidate, expected in zip(candidates, outcomes, strict=True):
                assert (
                    policy.validate(candidate) == expected == policy.validate(candidate)
                )


def test_scope_overlapping_ip_rules_report_most_specific_match_in_any_order() -> None:
    roots = (
        target("192.0.2.0/24", "cidr", "wide"),
        target("192.0.2.10/32", "cidr", "narrow"),
        target("192.0.2.10", "ip", "exact"),
    )
    for ordered in permutations(roots):
        policy = ScopeValidator(Scope(id="scope", roots=ordered))
        assert policy.require_allowed(target("192.0.2.10")).matched_rule.id == "exact"
        assert (
            policy.require_allowed(target("192.0.2.10/32", "cidr")).matched_rule.id
            == "narrow"
        )


@pytest.mark.parametrize("kind", ["domain", "hostname", "ip", "cidr", "url"])
def test_scope_empty_roots_deny_every_supported_kind(kind: str) -> None:
    values = {
        "domain": "example.com",
        "hostname": "example.com",
        "ip": "192.0.2.1",
        "cidr": "192.0.2.0/24",
        "url": "https://example.com/",
    }
    result = ScopeValidator(
        Scope(id="scope", allow_private_ips=True, allow_subdomains=True)
    ).validate(target(values[kind], kind))
    assert result.status == "failure"
    assert result.error.context.scope_reason == ScopeRejectionReason.NOT_IN_SCOPE


@pytest.mark.parametrize("kind", ["unknown", "DOMAIN", "", None])
def test_scope_unknown_kinds_have_no_hostname_fallback(kind: str | None) -> None:
    data = {"id": "candidate", "kind": kind, "value": "example.com"}
    with pytest.raises(ValidationError):
        Target.model_validate(data)
    forged = Target.model_construct(**data)
    policy = ScopeValidator(Scope(id="scope", roots=(target("example.com", "domain"),)))
    result = policy.validate(forged)
    assert result.status == "failure"
    assert result.error.context.scope_reason == ScopeRejectionReason.INVALID_TARGET
    with pytest.raises(ScopeRejectedError):
        ScopeValidator(Scope.model_construct(id="scope", roots=(forged,)))


def test_scope_misspelled_authorization_and_match_fields_are_rejected() -> None:
    candidate = target("example.com", "hostname")
    with pytest.raises(ValidationError):
        Target.model_validate({**candidate.model_dump(), "hostnme": "evil.test"})
    with pytest.raises(ValidationError):
        Scope.model_validate(
            {"id": "scope", "roots": (candidate,), "allow_subdoman": True}
        )
    match = ScopeValidator(Scope(id="scope", roots=(candidate,))).require_allowed(
        candidate
    )
    with pytest.raises(ValidationError):
        ScopeMatch.model_validate({**match.model_dump(), "allowed": True})


@pytest.mark.parametrize(
    ("candidate", "reason", "normalized"),
    [
        (
            "https://example.com.evil.test/private?token=synthetic#data",
            "not_in_scope",
            "example.com.evil.test",
        ),
        (
            "https://admin.example.com/private?token=synthetic",
            "excluded",
            "admin.example.com",
        ),
        (
            "http://10.10.10.5/private?token=synthetic",
            "private_ip_not_allowed",
            "10.10.10.5",
        ),
        ("https://user:synthetic@example.com/", "invalid_target", None),
    ],
)
def test_scope_rejections_keep_canonical_codes_safe_context_and_error_parity(
    candidate: str, reason: str, normalized: str | None
) -> None:
    policy = ScopeValidator(
        Scope(
            id="scope",
            roots=(target("example.com", "domain"), target("10.10.10.0/24", "cidr")),
            exclusions=(target("admin.example.com", "domain"),),
            allow_subdomains=True,
        )
    )
    supplied = target(candidate, "url")
    result = policy.validate(supplied)
    assert result.status == "failure"
    assert result.error.code.value == "scope_rejected"
    assert result.error.context.scope_reason is not None
    assert result.error.context.scope_reason.value == reason
    assert result.error.context.normalized_candidate == normalized
    assert result.error.context.target_kind == (
        None if reason == "invalid_target" else "url"
    )
    assert not result.error.retryable
    assert "synthetic" not in result.model_dump_json()
    with pytest.raises(ScopeRejectedError) as caught:
        policy.require_allowed(supplied)
    assert caught.value.to_error_info() == result.error
    adapter = TypeAdapter[OperationResult[ScopeMatch]](OperationResult[ScopeMatch])
    for outcome in (result, policy.validate(target("EXAMPLE.COM.", "hostname"))):
        assert adapter.validate_json(adapter.dump_json(outcome)) == outcome


@pytest.mark.parametrize("error_type", [ValueError, TypeError])
def test_scope_parser_failures_cannot_return_allow_or_leak_raw_diagnostics(
    monkeypatch: pytest.MonkeyPatch, error_type: type[Exception]
) -> None:
    policy = ScopeValidator(Scope(id="scope", roots=(target("example.com", "domain"),)))
    monkeypatch.setattr(
        scope_module,
        "_parse",
        Mock(side_effect=error_type("synthetic raw parser data")),
    )
    result = policy.validate(target("example.com", "hostname"))
    assert result.status == "failure"
    assert result.error.code == ErrorCode.SCOPE_REJECTED
    assert result.error.context.scope_reason == ScopeRejectionReason.INVALID_TARGET
    assert "synthetic" not in result.model_dump_json()
    with pytest.raises(ScopeRejectedError) as caught:
        ScopeValidator(Scope(id="scope", roots=(target("example.com", "domain"),)))
    assert caught.value.context.scope_reason == ScopeRejectionReason.INVALID_SCOPE

"""Offline canonical contact identity and evidence-preserving state projection."""

import asyncio
import json
import socket
import subprocess
from datetime import UTC, datetime
from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from recon_agent.core.results import Failure, Success
from recon_agent.domain import (
    Asset,
    Endpoint,
    Evidence,
    Observation,
    ReconState,
    ReconStateMachine,
    Scope,
    Target,
    WebAssetIdentity,
    canonical_web_url,
)
from recon_agent.execution import AsyncProcessRunner
from recon_agent.policy import ScopeValidator
from recon_agent.tools import (
    common_files_parser,
    feroxbuster_parser,
    ffuf_parser,
    httpx_parser,
    katana_parser,
)
from recon_agent.tools.common_files_models import CommonFileFact, CommonFilesContext
from recon_agent.tools.feroxbuster_models import FeroxbusterContext
from recon_agent.tools.ffuf_models import FfufContext
from recon_agent.tools.httpx_models import HttpxContext
from recon_agent.tools.katana_models import KatanaContext

WHEN = datetime(2026, 10, 8, tzinfo=UTC)


@pytest.fixture(autouse=True)
def inert(monkeypatch):
    forbidden = Mock(
        side_effect=AssertionError("Identity must have no runtime effects")
    )
    for name in (
        "socket",
        "getaddrinfo",
        "gethostbyname",
        "gethostbyname_ex",
        "gethostbyaddr",
        "getnameinfo",
        "create_connection",
    ):
        monkeypatch.setattr(socket, name, forbidden)
    for name in ("Popen", "run", "call", "check_call", "check_output"):
        monkeypatch.setattr(subprocess, name, forbidden)
    for name in (
        "open_connection",
        "create_subprocess_exec",
        "create_subprocess_shell",
    ):
        monkeypatch.setattr(asyncio, name, forbidden)
    monkeypatch.setattr(AsyncProcessRunner, "run", forbidden)
    yield forbidden
    forbidden.assert_not_called()


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("HTTPS://EXAMPLE.test", "https://example.test/"),
        ("https://example.test:443/", "https://example.test/"),
        ("http://example.test:00080", "http://example.test/"),
        ("https://example.test:8443", "https://example.test:8443/"),
        ("http://example.test:443/", "http://example.test:443/"),
        ("https://EXAMPLE.test./a", "https://example.test/a"),
        ("https://192.0.2.10:443", "https://192.0.2.10/"),
        ("http://[2001:0DB8:0:0::10]:080", "http://[2001:db8::10]/"),
        ("https://[::1]:00443/?a=1#two", "https://[::1]/?a=1"),
        ("https://example.test#one", "https://example.test/"),
        ("https://example.test/?#two", "https://example.test/?"),
        ("https://example.test/a//b/../c", "https://example.test/a//b/../c"),
        (
            "https://example.test/%7e/%2F?q=%41&a=1&a=2",
            "https://example.test/%7e/%2F?q=%41&a=1&a=2",
        ),
    ],
)
def test_canonical_table_and_idempotence(raw, expected):
    assert canonical_web_url(raw) == expected
    assert canonical_web_url(expected) == expected
    assert WebAssetIdentity(url=raw).url == expected


@pytest.mark.parametrize(
    "left,right",
    [
        ("http://example.test/", "https://example.test/"),
        ("https://example.test:8443/", "https://example.test:9443/"),
        ("https://example.test/A", "https://example.test/a"),
        ("https://example.test/a", "https://example.test/a/"),
        ("https://example.test/a//b", "https://example.test/a/b"),
        ("https://example.test/a/../b", "https://example.test/b"),
        ("https://example.test/a", "https://example.test/b"),
        ("https://example.test/", "https://example.test/?"),
        ("https://example.test/?a=1&b=2", "https://example.test/?b=2&a=1"),
        ("https://example.test/?a=1&a=2", "https://example.test/?a=2&a=1"),
        ("https://example.test/?a=1&a=1", "https://example.test/?a=1"),
        ("https://example.test/?a", "https://example.test/?a="),
        ("https://example.test/?q=+", "https://example.test/?q=%20"),
        ("https://example.test/%41", "https://example.test/A"),
        ("https://example.test/%2f", "https://example.test/%2F"),
        ("https://example.test/a%2Fb", "https://example.test/a/b"),
        ("https://example.test/%252F", "https://example.test/%2F"),
        ("https://example.test/?q=%26", "https://example.test/?q=&"),
        ("https://example.test/", "https://example.test.evil.test/"),
    ],
)
def test_meaningful_distinctions(left, right):
    assert canonical_web_url(left) != canonical_web_url(right)


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "example.test",
        "/a",
        "//example.test/",
        "ftp://example.test/",
        "https:///a",
        "https://",
        "https://example.test@evil.test/",
        "https://user:password@example.test/",
        "https://example.test%40evil.test/",
        "https://%65xample.test/",
        "https://example.test\\@evil.test/",
        "https://example.test:\\443/",
        "https://example.test:/",
        "https://example.test:0/",
        "https://example.test:-1/",
        "https://example.test:65536/",
        "https://example.test:four/",
        "https://example.test:443:80/",
        "https://example.test\n/",
        " https://example.test/",
        "https://example.test/a b",
        "https://example.test/\x00",
        "https://example.test/a%",
        "https://example.test/?q=%GG",
        "https://example.test/#bad%1",
        "https://éxample.test/",
        "https://xn--test.test/",
        "https://example..test/",
        "https://-example.test/",
        "https://127.1/",
        "https://0177.0.0.1/",
        "https://2130706433/",
        "https://0x7f000001/",
        "https://[2001:db8::1/",
        "https://[2001:db8::1]suffix/",
        "https://[192.0.2.1]/",
        "https://2001:db8::1/",
        "https://[::ffff:192.0.2.1]/",
        "https://[fe80::1%25eth0]/",
        "https://[v1.foo]/",
        "https://example.test/[x]",
        "https://example.test/" + "a" * 2048,
    ],
)
def test_malformed_fails_closed_without_echoing_input(raw):
    with pytest.raises(ValueError) as error:
        canonical_web_url(raw)
    assert "password" not in str(error.value)
    with pytest.raises(ValidationError):
        WebAssetIdentity(url=raw)


@pytest.mark.parametrize("method", ["", "GET POST", "GET\n", "GÉT"])
def test_invalid_method(method):
    with pytest.raises(ValidationError):
        WebAssetIdentity(url="https://example.test/", method=method)


def test_methods_host_variants_and_serialization():
    one = WebAssetIdentity(url="HTTPS://EXAMPLE.test:443#one")
    two = WebAssetIdentity(url="https://example.test/#two")
    assert one.key == two.key
    assert json.loads(one.key) == one.model_dump(mode="json")
    assert WebAssetIdentity.model_validate_json(one.model_dump_json()) == one
    assert (
        len(
            {
                WebAssetIdentity(url=one.url, method=m).key
                for m in ("GET", "get", "HEAD", "POST")
            }
        )
        == 4
    )
    assert (
        WebAssetIdentity(url=one.url, host_header="API.EXAMPLE.test").host_header
        == "api.example.test"
    )
    assert one != WebAssetIdentity(url=one.url, host_header="api.example.test")
    for bad in ("example.test@evil.test", "example.test:443", "[::1]", "::1"):
        with pytest.raises(ValidationError):
            WebAssetIdentity(url=one.url, host_header=bad)


@pytest.mark.parametrize(
    "outside",
    [
        "https://EXAMPLE.test.evil.test:443/#one",
        "https://evil.test/",
        "https://192.0.2.1/",
    ],
)
def test_canonicalization_never_authorizes_outside(outside):
    scope = ScopeValidator(
        Scope(
            id="scope",
            roots=(Target(id="root", kind="hostname", value="example.test"),),
        )
    )
    before = scope.scope.model_dump_json()
    assert isinstance(scope.validate_value(outside), Failure)
    canonical = canonical_web_url(outside)
    assert isinstance(scope.validate_value(canonical), Failure)
    assert scope.scope.model_dump_json() == before


def outputs():
    """Actual five adapter normalizers, with deliberately varied URL spellings."""
    url = "https://192.0.2.10/robots.txt"
    variants = (url, "HTTPS://192.0.2.10:443/robots.txt", url + "#one", url, url)
    contexts = [
        dict(asset_id=f"asset-{i}", execution_id=f"exec-{i}", collected_at=WHEN)
        for i in range(5)
    ]
    fact = dict(url=variants[0], method="GET", status_code=200)
    http = httpx_parser.normalize(
        (fact,),
        0,
        (url,),
        ("192.0.2.10",),
        "192.0.2.53",
        url,
        HttpxContext(**contexts[0]),
    )
    common = common_files_parser.normalize(
        url,
        (
            CommonFileFact(
                path="/robots.txt",
                requested_url=variants[1],
                final_url=variants[1],
                status_code=200,
                retained_bytes=0,
                body_base64="",
                discovered_urls=(url + "#two", "https://outside.test/a"),
            ),
        ),
        CommonFilesContext(**contexts[1]),
    )
    katana = katana_parser.normalize(
        (dict(url=variants[2], method="GET", contacted=False),),
        0,
        (),
        (),
        url,
        KatanaContext(**contexts[2]),
    )
    ferox = feroxbuster_parser.normalize(
        (dict(url=variants[3], method="GET", status_code=200),),
        0,
        (url,),
        4,
        (),
        (),
        url,
        FeroxbusterContext(**contexts[3]),
    )
    ffuf = ffuf_parser.normalize(
        (
            dict(
                url=url,
                method="HEAD",
                status_code=200,
                candidate_value="api.example.test",
                profile="vhost_names",
            ),
        ),
        0,
        url,
        ("api.example.test",),
        ("api.example.test",),
        FfufContext(**contexts[4]),
    )
    return http, common, katana, ferox, ffuf


def test_cross_adapter_dedup_preserves_evidence_state_and_host_methods():
    results = outputs()
    originals = tuple(result.model_dump_json() for result in results)
    owner = ReconStateMachine()
    for result in results:
        assert isinstance(
            owner.record_facts(
                assets=(result.asset,),
                endpoints=getattr(result, "endpoints", ()),
                observations=result.observations,
                evidence=result.evidence,
            ),
            Success,
        )
    state = owner.state
    before = state.model_dump_json()
    discovered = state.find_web_asset("https://192.0.2.10:443/robots.txt#three")
    assert discovered and discovered.contacted
    assert len(discovered.observation_ids) == 4
    assert len(discovered.evidence_ids) == 4
    assert len(discovered.endpoint_ids) == 3
    assert len(discovered.contacted_observation_ids) == 3
    head = state.find_web_asset(discovered.identity.url, method="HEAD")
    assert head and not head.contacted  # Endpoint alone cannot prove contact.
    variant = state.find_web_asset(
        discovered.identity.url, method="HEAD", host_header="api.example.test"
    )
    assert variant and variant.contacted
    assert state.find_web_asset(discovered.identity.url, method="POST") is None
    outside = state.find_web_asset("https://outside.test/a")
    assert outside and not outside.contacted
    assert state.model_dump_json() == before
    assert tuple(result.model_dump_json() for result in results) == originals
    restored = ReconState.model_validate_json(before)
    assert restored.web_assets == state.web_assets
    reversed_state = ReconState(
        assets=state.assets[::-1],
        endpoints=state.endpoints[::-1],
        observations=state.observations[::-1],
        evidence=state.evidence[::-1],
    )
    assert reversed_state.web_assets == state.web_assets
    # Derived records are portable, detached and absent from stored raw snapshots.
    assert "web_assets" not in state.model_dump()
    for item in state.web_assets:
        assert type(item).model_validate_json(item.model_dump_json()) == item
    assert owner.state.model_dump_json() == before


def test_discovery_alone_and_malformed_index_fail_closed():
    asset = Asset(id="a", kind="web_resource", value="https://example.test/")
    evidence = Evidence(
        id="e",
        source="katana",
        origin="test",
        artifact_reference="memory:test",
        collected_at=WHEN,
    )
    obs = Observation(
        id="o",
        kind="http",
        asset_id="a",
        source="katana",
        evidence_ids=("e",),
        observed_at=WHEN,
        data={
            "url": "https://example.test/a",
            "method": "GET",
            "contacted": False,
            "status_code": 200,
        },
    )
    endpoint = Endpoint(
        id="p", asset_id="a", url="https://EXAMPLE.test:443/a#f", observation_ids=("o",)
    )
    state = ReconState(
        assets=(asset,),
        observations=(obs,),
        evidence=(evidence,),
        endpoints=(endpoint,),
    )
    assert endpoint.web_identity.url == "https://example.test/a"
    assert not state.web_assets[0].contacted
    bad = obs.model_copy(update={"data": {"url": "https://example.test@evil.test/"}})
    state = ReconState(assets=(asset,), observations=(bad,), evidence=(evidence,))
    before = state.model_dump_json()
    with pytest.raises(ValueError):
        _ = state.web_assets
    assert state.model_dump_json() == before


def test_common_redirect_contact_and_unknown_source_are_only_evidence():
    url = "https://example.test/robots.txt"
    output = common_files_parser.normalize(
        url,
        (
            CommonFileFact(
                path="/robots.txt",
                requested_url=url,
                final_url="https://example.test/final",
                retained_bytes=0,
                body_base64="",
                redirects=(
                    {
                        "url": url,
                        "status_code": 302,
                        "location": "https://outside.test/",
                        "destination": "https://outside.test/",
                        "outcome": "rejected",
                    },
                ),
            ),
        ),
        CommonFilesContext(asset_id="a", execution_id="x", collected_at=WHEN),
    )
    unknown = Observation(
        id="unknown",
        kind="http",
        asset_id="a",
        source="remote_banner",
        data={
            "url": "https://example.test/claim",
            "status_code": 200,
            "contacted": True,
        },
        observed_at=WHEN,
        evidence_ids=(output.evidence[0].id,),
    )
    state = ReconState(
        assets=(output.asset,),
        observations=(*output.observations, unknown),
        evidence=output.evidence,
    )
    assert state.find_web_asset(url).contacted
    assert not state.find_web_asset("https://example.test/final").contacted
    assert not state.find_web_asset("https://example.test/claim").contacted
    assert state.find_web_asset("https://outside.test/") is None


@pytest.mark.parametrize(
    "data",
    [
        {
            "requested_url": "https://example.test/",
            "final_url": "https://example.test/",
            "discovered_urls": 1,
        },
        {
            "requested_url": "https://example.test/",
            "final_url": "https://example.test/",
            "redirects": [1],
        },
        {"url": 123},
        {"url": "https://example.test/", "method": False},
    ],
)
def test_malformed_discovery_fields_fail_entire_lookup(data):
    source = "native_common_files" if "requested_url" in data else "katana"
    obs = Observation(
        id="o",
        kind="http",
        asset_id="a",
        source=source,
        data=data,
        observed_at=WHEN,
        evidence_ids=("e",),
    )
    evidence = Evidence(
        id="e",
        source=source,
        origin="fixture",
        artifact_reference="memory:fixture",
        collected_at=WHEN,
    )
    state = ReconState(
        assets=(Asset(id="a", kind="web_resource", value="seed"),),
        observations=(obs,),
        evidence=(evidence,),
    )
    before = state.model_dump_json()
    with pytest.raises(ValueError):
        state.find_web_asset("https://example.test/")
    assert state.model_dump_json() == before


@pytest.mark.parametrize("raw", [None, 1, True, b"https://example.test/"])
def test_non_string_url_fails_closed(raw):
    with pytest.raises(ValueError):
        canonical_web_url(raw)


def test_identity_never_calls_scope_validator(monkeypatch):
    blocked = Mock(side_effect=AssertionError("Identity is not authorization"))
    monkeypatch.setattr(ScopeValidator, "validate", blocked)
    monkeypatch.setattr(ScopeValidator, "validate_value", blocked)
    assert (
        WebAssetIdentity(url="https://OUTSIDE.test:443/#f").url
        == "https://outside.test/"
    )
    blocked.assert_not_called()

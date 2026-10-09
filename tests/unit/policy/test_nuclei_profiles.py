"""Pure profile/behavior/provenance tables; policy eligibility never enables scans."""

import asyncio
import json
import socket
import subprocess
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from recon_agent.core.config.models import ExecutionConfig
from recon_agent.core.errors import ConfigurationError, ErrorCode
from recon_agent.core.results import Failure, Success
from recon_agent.domain import ActionRequest, ReconStateMachine, Scope, Target
from recon_agent.domain.capabilities import CapabilityId, RiskClass
from recon_agent.domain.nuclei_policy import (
    NucleiProfile,
    TemplateBehavior,
    TemplateClassRule,
    TemplateIdentity,
    TemplatePolicyAssessment,
    TemplatePolicyCandidate,
    TemplateReview,
)
from recon_agent.policy import (
    ActionCanonicalizer,
    ActionDeduplicator,
    ActionPolicyConfig,
    ActionPolicyValidator,
    BudgetController,
    ExecutionBudget,
    ScopeValidator,
)
from recon_agent.policy.nuclei_profiles import (
    DEFAULT_PROFILE,
    NucleiProfileCatalog,
    classify_template,
    nuclei_profiles,
    template_class_rules,
)
from recon_agent.tools import AdapterAvailability, AdapterRegistration, ToolRegistry
from recon_agent.tools.nuclei import NucleiAdapter
from recon_agent.tools.nuclei_models import NucleiContext, NucleiInput

FIXTURE = (
    Path(__file__).parents[2] / "fixtures/nuclei_policy/reviews.json"
).read_text()
REVIEWS = tuple(
    TemplateReview.model_validate_json(json.dumps(item)) for item in json.loads(FIXTURE)
)
WHEN = datetime(2026, 10, 10, tzinfo=UTC)
ALLOWED = ("http_response_metadata", "http_security_header_presence")
PROHIBITED = (
    "exploit",
    "credential_attack",
    "destructive",
    "out_of_band",
    "payload_fuzzing",
    "remote_mutation",
    "code_execution",
)
UNREVIEWED = (
    "http_body_exposure",
    "http_path_discovery",
    "tls_checks",
    "dns_checks",
    "network_checks",
    "headless",
    "file",
    "workflow",
    "javascript",
    "custom",
    "unknown",
)
PROFILES = {
    "safe": ALLOWED,
    "http_metadata": (ALLOWED[0],),
    "http_headers": (ALLOWED[1],),
}
FEATURES = (
    "redirects",
    "host_redirects",
    "cookies",
    "payloads",
    "fuzzing",
    "oast",
    "interactsh",
    "credentials",
    "mutation",
    "code",
    "workflow",
    "headless",
    "filesystem",
    "secondary_contacts",
    "custom_headers",
    "request_body",
    "raw_http",
    "dsl",
    "dynamic_extractors",
    "helper_files",
    "unknown_feature",
)


@pytest.fixture(autouse=True)
def no_runtime(monkeypatch):
    forbidden = Mock(
        side_effect=AssertionError("policy must not contact/start runtime")
    )
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    for name in (
        "getaddrinfo",
        "gethostbyname",
        "gethostbyname_ex",
        "gethostbyaddr",
        "create_connection",
    ):
        monkeypatch.setattr(socket, name, forbidden)
    for name in (
        "connect",
        "connect_ex",
        "send",
        "sendall",
        "sendto",
        "bind",
        "listen",
    ):
        original = getattr(socket.socket, name)

        def guarded(self, *args, _original=original, **kwargs):
            if self.family != socket.AF_UNIX:
                return forbidden()
            return _original(self, *args, **kwargs)

        monkeypatch.setattr(socket.socket, name, guarded)
    for name in ("Popen", "run", "call", "check_call", "check_output"):
        monkeypatch.setattr(subprocess, name, forbidden)
    for name in (
        "create_subprocess_exec",
        "create_subprocess_shell",
        "open_connection",
    ):
        monkeypatch.setattr(asyncio, name, forbidden)
    monkeypatch.setattr("recon_agent.execution.AsyncProcessRunner.run", forbidden)
    monkeypatch.setattr("recon_agent.tools.nuclei.shutil.which", forbidden)
    yield
    forbidden.assert_not_called()


def candidate(review=REVIEWS[0], **changes):
    values = {
        name: getattr(review, name) for name in TemplatePolicyCandidate.model_fields
    }
    values.update(changes)
    return TemplatePolicyCandidate(**values)


def test_catalog_tables_are_exact_reviewable_sorted_and_inert():
    rules = template_class_rules()
    assert tuple(rule.name for rule in rules) == tuple(
        sorted(ALLOWED + PROHIBITED + UNREVIEWED)
    )
    assert {rule.name: rule.classification for rule in rules} == (
        {name: "allowed" for name in ALLOWED}
        | {name: "prohibited" for name in PROHIBITED}
        | {name: "unreviewed" for name in UNREVIEWED}
    )
    for rule in rules:
        if rule.name in ALLOWED:
            assert rule.risk_class is RiskClass.ACTIVE_SAFE
            assert rule.behavior.model_dump() == dict(
                protocol="http",
                method="HEAD",
                destination="target_root",
                request_count=1,
                response_parts=("headers", "status"),
                features=(),
            )
        else:
            assert rule.risk_class is None and rule.behavior is None
    profiles = nuclei_profiles()
    assert {p.name: p.allowed_classes for p in profiles} == PROFILES
    assert tuple(p.name for p in profiles) == tuple(sorted(PROFILES))
    assert [p.name for p in profiles if p.is_default] == [DEFAULT_PROFILE] == ["safe"]
    assert all(p.execution_authorized is False for p in profiles)
    assert not NucleiProfileCatalog().reviews
    assert not ToolRegistry().catalog()
    assert isinstance(
        NucleiProfileCatalog().assess(DEFAULT_PROFILE, candidate()), Failure
    )


@pytest.mark.parametrize("profile", PROFILES)
@pytest.mark.parametrize("review", REVIEWS, ids=ALLOWED)
def test_named_profile_subsets_and_provenance(profile, review):
    catalog = NucleiProfileCatalog(REVIEWS)
    result = catalog.assess(profile, candidate(review))
    if review.template_class not in PROFILES[profile]:
        assert isinstance(result, Failure)
        return
    assert isinstance(result, Success)
    assessment = result.value
    assert assessment.identity == review.identity
    assert assessment.review_reference == review.review_reference
    assert assessment.reviewed_at == WHEN
    assert (
        assessment.profile == profile
        and assessment.template_class == review.template_class
    )
    assert assessment.risk_class is RiskClass.ACTIVE_SAFE
    assert assessment.execution_authorized is False
    assert (
        TemplatePolicyAssessment.model_validate_json(assessment.model_dump_json())
        == assessment
    )
    assert catalog.assess(profile, candidate(review)) == result


@pytest.mark.parametrize("template_class", ALLOWED)
def test_classification_requires_complete_reviewed_behavior(template_class):
    result = classify_template(template_class, REVIEWS[0].behavior)
    assert isinstance(result, Success) and result.value.name == template_class


@pytest.mark.parametrize("profile", PROFILES)
@pytest.mark.parametrize(
    "template_class",
    PROHIBITED
    + UNREVIEWED
    + ("missing-class", "HTTP_RESPONSE_METADATA", "../allowed", "safe;id"),
)
def test_all_profiles_exclude_prohibited_unreviewed_and_unknown_classes(
    profile, template_class
):
    catalog = NucleiProfileCatalog(REVIEWS)
    result = catalog.assess(
        profile, candidate().model_copy(update={"template_class": template_class})
    )
    assert (
        isinstance(result, Failure)
        and result.error.code is ErrorCode.PLANNER_VALIDATION_FAILED
    )
    assert isinstance(classify_template(template_class, REVIEWS[0].behavior), Failure)


@pytest.mark.parametrize("feature", FEATURES)
@pytest.mark.parametrize("template_class", ALLOWED)
def test_labels_cannot_override_additional_or_unknown_behavior(feature, template_class):
    behavior = REVIEWS[0].behavior.model_copy(update={"features": (feature,)})
    assert isinstance(classify_template(template_class, behavior), Failure)
    review = REVIEWS[0].model_copy(
        update={"template_class": template_class, "behavior": behavior}
    )
    with pytest.raises(ConfigurationError):
        NucleiProfileCatalog((review,))


@pytest.mark.parametrize(
    "changes",
    [
        {"protocol": "ssl"},
        {"protocol": "dns"},
        {"protocol": "tcp"},
        {"protocol": "javascript"},
        {"protocol": "headless"},
        {"protocol": "code"},
        {"protocol": "file"},
        {"protocol": "http-unknown"},
        {"method": "GET"},
        {"method": "POST"},
        {"method": "PUT"},
        {"method": "DELETE"},
        {"method": "head"},
        {"destination": "target_path"},
        {"destination": "absolute"},
        {"destination": "derived"},
        {"destination": "unknown"},
        {"request_count": 2},
        {"request_count": 256},
        {"response_parts": ("body",)},
        {"response_parts": ("raw",)},
        {"response_parts": ("headers", "status", "body")},
    ],
)
@pytest.mark.parametrize("template_class", ALLOWED)
def test_exact_single_head_root_response_only_envelope(changes, template_class):
    behavior = REVIEWS[0].behavior.model_copy(update=changes)
    assert isinstance(classify_template(template_class, behavior), Failure)
    assert isinstance(
        NucleiProfileCatalog(REVIEWS).assess("safe", candidate(behavior=behavior)),
        Failure,
    )


@pytest.mark.parametrize(
    "changes",
    [
        {"source_repository": "other/templates"},
        {"source_revision": "1" * 40},
        {"package_version": "1.0.0"},
        {"engine_version": "3.4.11"},
        {"content_sha256": "1" * 64},
        {"template_id": "new-template"},
    ],
)
@pytest.mark.parametrize("profile", PROFILES)
def test_each_changed_identity_field_denies_until_explicit_review(changes, profile):
    identity = REVIEWS[0].identity.model_copy(update=changes)
    constructed = TemplatePolicyCandidate.model_construct(
        identity=identity, template_class=ALLOWED[0], behavior=REVIEWS[0].behavior
    )
    result = NucleiProfileCatalog(REVIEWS).assess(profile, constructed)
    assert isinstance(result, Failure)
    assert result.error.code is ErrorCode.PLANNER_VALIDATION_FAILED


@pytest.mark.parametrize(
    "profile",
    [
        "",
        "default",
        "SAFE",
        "safe ",
        " safe",
        "/tmp/safe.yaml",
        "../safe",
        "-t",
        "safe;id",
        "https://example.test/templates",
        None,
        1,
        True,
    ],
)
def test_unknown_profile_no_alias_or_permissive_fallback(profile):
    catalog = NucleiProfileCatalog(REVIEWS)
    assert isinstance(catalog.select(profile), Failure)
    assert isinstance(catalog.assess(profile, candidate()), Failure)


@pytest.mark.parametrize("template_class", [None, 1, True])
def test_nonstring_classes_are_canonical_denials(template_class):
    assert isinstance(classify_template(template_class, REVIEWS[0].behavior), Failure)


@pytest.mark.parametrize("field", TemplateBehavior.model_fields)
def test_missing_effective_behavior_is_not_assumed_safe(field):
    data = REVIEWS[0].behavior.model_dump()
    del data[field]
    with pytest.raises(ValidationError):
        TemplateBehavior.model_validate(data)
    assert isinstance(
        classify_template(ALLOWED[0], TemplateBehavior.model_construct(**data)), Failure
    )


@pytest.mark.parametrize(
    "changes",
    [
        {"protocol": 1},
        {"method": None},
        {"request_count": 0},
        {"request_count": True},
        {"response_parts": ()},
        {"response_parts": ("headers", "headers")},
        {"features": ("oast", "oast")},
        {"features": ("x",) * 65},
        {"features": ("../file",)},
        {"features": ("unknown",) * 65},
    ],
)
def test_malformed_behavior_and_constructed_copies_revalidate(changes):
    behavior = REVIEWS[0].behavior.model_copy(update=changes)
    assert isinstance(classify_template(ALLOWED[0], behavior), Failure)
    with pytest.raises(ConfigurationError):
        NucleiProfileCatalog((REVIEWS[0].model_copy(update={"behavior": behavior}),))


@pytest.mark.parametrize(
    "changes",
    [
        {"template_id": "../template"},
        {"source_revision": "main"},
        {"source_revision": "A" * 40},
        {"source_revision": "0" * 39},
        {"package_version": "latest"},
        {"package_version": "0.0.0-beta"},
        {"engine_version": ""},
        {"content_sha256": "0" * 63},
        {"content_sha256": "G" * 64},
        {"content_sha256": None},
    ],
)
def test_malformed_provenance_never_becomes_trusted_review(changes):
    identity = REVIEWS[0].identity.model_copy(update=changes)
    with pytest.raises(ConfigurationError):
        NucleiProfileCatalog((REVIEWS[0].model_copy(update={"identity": identity}),))
    assert isinstance(
        NucleiProfileCatalog(REVIEWS).assess(
            "safe",
            TemplatePolicyCandidate.model_construct(
                identity=identity,
                template_class=ALLOWED[0],
                behavior=REVIEWS[0].behavior,
            ),
        ),
        Failure,
    )


@pytest.mark.parametrize(
    "field",
    [
        "template_path",
        "template_url",
        "flags",
        "approved",
        "tags",
        "severity",
        "executable",
        "signature",
    ],
)
def test_operator_or_candidate_extras_cannot_authorize_or_select_files(field):
    for model, data in (
        (TemplateIdentity, REVIEWS[0].identity.model_dump()),
        (TemplateReview, REVIEWS[0].model_dump()),
        (TemplatePolicyCandidate, candidate().model_dump()),
    ):
        data[field] = "untrusted-override"
        with pytest.raises(ValidationError):
            model.model_validate(data)


def test_order_canonicalization_repetition_and_immutable_snapshots():
    before = tuple(r.model_dump_json() for r in REVIEWS)
    first = NucleiProfileCatalog(REVIEWS)
    second = NucleiProfileCatalog(tuple(reversed(REVIEWS)))
    assert first.reviews == second.reviews
    behavior = REVIEWS[0].behavior.model_copy(
        update={"response_parts": ("status", "headers")}
    )
    assert first.assess("safe", candidate(behavior=behavior)) == first.assess(
        "safe", candidate()
    )
    assert tuple(r.model_dump_json() for r in REVIEWS) == before
    assert first.reviews[0] is not REVIEWS[0]
    assert first.reviews[0].identity is not REVIEWS[0].identity
    with pytest.raises(FrozenInstanceError):
        first._reviews = {}
    with pytest.raises(TypeError):
        first._reviews["new"] = REVIEWS[0]
    with pytest.raises(ValidationError):
        nuclei_profiles()[0].allowed_classes = ("exploit",)
    with pytest.raises(ValidationError):
        first.reviews[0].identity.package_version = "1.0.0"
    for profile in nuclei_profiles():
        assert NucleiProfile.model_validate_json(profile.model_dump_json()) == profile
    for rule in template_class_rules():
        assert TemplateClassRule.model_validate_json(rule.model_dump_json()) == rule


def test_duplicates_mixed_packages_unreviewed_engine_and_review_bound_reject():
    for reviews in ((REVIEWS[0], REVIEWS[0]), REVIEWS * 65, list(REVIEWS)):
        with pytest.raises(ConfigurationError):
            NucleiProfileCatalog(reviews)
    for change in (
        {"source_revision": "1" * 40},
        {"package_version": "1.0.0"},
        {"engine_version": "3.4.11"},
    ):
        updated = REVIEWS[1].model_copy(
            update={"identity": REVIEWS[1].identity.model_copy(update=change)}
        )
        with pytest.raises(ConfigurationError):
            NucleiProfileCatalog((REVIEWS[0], updated))
    unsupported = REVIEWS[0].model_copy(
        update={
            "identity": REVIEWS[0].identity.model_copy(
                update={"engine_version": "3.4.11"}
            )
        }
    )
    with pytest.raises(ConfigurationError):
        NucleiProfileCatalog((unsupported,))
    for change in (
        {"review_reference": ""},
        {"reviewed_at": WHEN.replace(tzinfo=None)},
    ):
        with pytest.raises(ConfigurationError):
            NucleiProfileCatalog((REVIEWS[0].model_copy(update=change),))


def test_explicit_rereview_updates_pins_without_broadening_or_mutating_old_catalog():
    original = NucleiProfileCatalog(REVIEWS)
    changed = candidate(
        identity=REVIEWS[0].identity.model_copy(
            update={
                "content_sha256": "2" * 64,
                "source_revision": "2" * 40,
                "package_version": "1.0.0",
            }
        )
    )
    assert isinstance(original.assess("safe", changed), Failure)
    reviewed = TemplateReview(
        **changed.model_dump(), review_reference="explicit-new-review", reviewed_at=WHEN
    )
    replacement = NucleiProfileCatalog((reviewed,))
    assert isinstance(replacement.assess("safe", changed), Success)
    assert isinstance(original.assess("safe", changed), Failure)
    assert isinstance(replacement.assess("safe", candidate()), Failure)
    unsafe = reviewed.model_copy(
        update={
            "behavior": reviewed.behavior.model_copy(
                update={"features": ("secondary_contacts",)}
            )
        }
    )
    with pytest.raises(ConfigurationError):
        NucleiProfileCatalog((unsafe,))
    assert nuclei_profiles() == tuple(
        NucleiProfile.model_validate_json(p.model_dump_json())
        for p in nuclei_profiles()
    )


def test_pure_policy_cannot_touch_scope_registry_budgets_state_or_adapters(monkeypatch):
    forbidden = Mock(
        side_effect=AssertionError("classification/assessment must remain pure")
    )
    for cls, name in (
        (ScopeValidator, "validate_value"),
        (ToolRegistry, "resolve"),
        (ActionPolicyValidator, "validate"),
        (BudgetController, "check"),
        (BudgetController, "reserve"),
        (ReconStateMachine, "record_facts"),
        (NucleiAdapter, "execute"),
        (NucleiAdapter, "detect"),
    ):
        monkeypatch.setattr(cls, name, forbidden)
    catalog = NucleiProfileCatalog(REVIEWS)
    assert isinstance(catalog.assess("safe", candidate()), Success)
    assert isinstance(catalog.assess("unknown", candidate()), Failure)
    assert isinstance(classify_template("out_of_band", REVIEWS[0].behavior), Failure)
    forbidden.assert_not_called()


def denied_without_event_loop(coroutine):
    # The policy corpus forbids even socket construction. Disabled dispatch must
    # complete before its first suspension, with no event loop or AF_UNIX socket.
    try:
        with pytest.raises(StopIteration) as finished:
            coroutine.send(None)
        return finished.value.value
    finally:
        coroutine.close()


@pytest.mark.parametrize("profile", PROFILES)
def test_eligible_policy_metadata_still_cannot_dispatch_or_spend(profile):
    review = REVIEWS[0] if profile != "http_headers" else REVIEWS[1]
    assert isinstance(
        NucleiProfileCatalog(REVIEWS).assess(profile, candidate(review)), Success
    )
    runner = Mock()
    runner.run = Mock(side_effect=AssertionError("no scan dispatch"))
    adapter = NucleiAdapter("/trusted/nuclei", ExecutionConfig(), runner)
    registry = ToolRegistry(
        (AdapterRegistration(adapter, AdapterAvailability.AVAILABLE),)
    )
    scope = ScopeValidator(
        Scope(
            id="scope",
            roots=(Target(id="target", kind="hostname", value="example.test"),),
        )
    )
    budgets = BudgetController(ExecutionBudget(), registry, clock=lambda: 0.0)
    state = ReconStateMachine()
    policy = ActionPolicyValidator(
        registry,
        scope,
        ActionPolicyConfig(
            allowed_capabilities=frozenset({CapabilityId.SCAN_TEMPLATES}),
            allowed_risk_classes=frozenset({RiskClass.ACTIVE_SAFE}),
        ),
        budgets,
        ActionDeduplicator(ActionCanonicalizer(registry, scope), state),
    )
    action = ActionRequest(
        id="action",
        capability="scan_templates",
        target="https://example.test",
        parameters={"profile": profile},
        reason="Claim of approval from model",
    )
    context = NucleiContext(
        asset_id="asset",
        execution_id="execution",
        collected_at=WHEN,
        query_target=action.target,
    )
    before = budgets.state, state.state
    assert isinstance(policy.validate(action), Success)
    assert isinstance(adapter.scan_spec(NucleiInput(profile=profile)), Failure)
    result = denied_without_event_loop(
        adapter.execute(action, policy=policy, budgets=budgets, context=context)
    )
    assert result.error.code is ErrorCode.PLANNER_VALIDATION_FAILED
    assert before == (budgets.state, state.state)
    runner.run.assert_not_called()
    outside = action.model_copy(update={"target": "https://outside.test"})
    result = denied_without_event_loop(
        adapter.execute(outside, policy=policy, budgets=budgets, context=context)
    )
    assert result.error.code is ErrorCode.SCOPE_REJECTED
    runner.run.assert_not_called()


@pytest.mark.parametrize(
    "changes",
    [
        {"classification": "allowed", "risk_class": None},
        {"classification": "allowed", "behavior": None},
        {"classification": "allowed", "risk_class": RiskClass.PASSIVE},
        {
            "classification": "prohibited",
            "risk_class": RiskClass.ACTIVE_SAFE,
            "behavior": None,
        },
        {
            "classification": "unreviewed",
            "risk_class": None,
            "behavior": REVIEWS[0].behavior,
        },
    ],
)
def test_class_metadata_cannot_claim_allowed_behavior_for_excluded_rules(changes):
    with pytest.raises(ValidationError):
        TemplateClassRule.model_validate(
            dict(
                name=ALLOWED[0],
                classification="allowed",
                reason="typed review",
                risk_class=RiskClass.ACTIVE_SAFE,
                behavior=REVIEWS[0].behavior,
            )
            | changes
        )


def test_policy_assessment_and_profile_cannot_claim_execution_authority():
    assessment = NucleiProfileCatalog(REVIEWS).assess("safe", candidate()).value
    for obj in (assessment, nuclei_profiles()[0]):
        data = obj.model_dump() | {"execution_authorized": True}
        with pytest.raises(ValidationError):
            type(obj).model_validate(data)


def test_matching_profile_cannot_relabel_a_reviewed_template_as_other_allowed_class():
    result = NucleiProfileCatalog(REVIEWS).assess(
        "safe", candidate(template_class=ALLOWED[1])
    )
    assert result.error.code is ErrorCode.PLANNER_VALIDATION_FAILED


def test_source_reads_are_forbidden_during_policy_operations(monkeypatch):
    forbidden = Mock(side_effect=AssertionError("no filesystem source/manifest reads"))
    with monkeypatch.context() as patch:
        for method in ("read_bytes", "read_text", "open", "glob", "rglob"):
            patch.setattr(Path, method, forbidden)
        patch.setattr("builtins.open", forbidden)
        catalog = NucleiProfileCatalog(REVIEWS)
        assert isinstance(catalog.assess("safe", candidate()), Success)
        assert isinstance(catalog.assess("unsafe", candidate()), Failure)
        assert (
            classify_template(ALLOWED[0], REVIEWS[0].behavior).value.name == ALLOWED[0]
        )
    forbidden.assert_not_called()

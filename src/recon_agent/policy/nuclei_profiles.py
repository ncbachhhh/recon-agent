"""Finite inert Nuclei policy catalog; runtime enforcement belongs to M5-T03."""

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from recon_agent.core.errors import ConfigurationError, PlannerValidationError
from recon_agent.core.results import Failure, OperationResult, Success
from recon_agent.domain.capabilities import RiskClass
from recon_agent.domain.nuclei_policy import (
    NucleiProfile,
    TemplateBehavior,
    TemplateClassRule,
    TemplatePolicyAssessment,
    TemplatePolicyCandidate,
    TemplateReview,
)

DEFAULT_PROFILE = "safe"
REVIEWED_ENGINE_VERSION = "3.4.10"
_HEAD_ROOT = TemplateBehavior(
    protocol="http",
    method="HEAD",
    destination="target_root",
    request_count=1,
    response_parts=("headers", "status"),
    features=(),
)
_ALLOWED = (
    TemplateClassRule(
        name="http_response_metadata",
        classification="allowed",
        reason="One root HEAD; collect reported status and response headers only",
        risk_class=RiskClass.ACTIVE_SAFE,
        behavior=_HEAD_ROOT,
    ),
    TemplateClassRule(
        name="http_security_header_presence",
        classification="allowed",
        reason="One root HEAD; report header presence/absence without vulnerability verification",
        risk_class=RiskClass.ACTIVE_SAFE,
        behavior=_HEAD_ROOT,
    ),
)
_PROHIBITED = (
    "exploit",
    "credential_attack",
    "destructive",
    "out_of_band",
    "payload_fuzzing",
    "remote_mutation",
    "code_execution",
)
_UNREVIEWED = (
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
_CLASSES = tuple(
    sorted(
        (
            *_ALLOWED,
            *(
                TemplateClassRule(
                    name=name,
                    classification="prohibited",
                    reason="Excluded by repository security policy",
                )
                for name in _PROHIBITED
            ),
            *(
                TemplateClassRule(
                    name=name,
                    classification="unreviewed",
                    reason="Effective behavior/containment has no approved class contract",
                )
                for name in _UNREVIEWED
            ),
        ),
        key=lambda rule: rule.name,
    )
)
_PROFILES = (
    NucleiProfile(
        name="http_headers",
        is_default=False,
        allowed_classes=("http_security_header_presence",),
    ),
    NucleiProfile(
        name="http_metadata",
        is_default=False,
        allowed_classes=("http_response_metadata",),
    ),
    NucleiProfile(
        name=DEFAULT_PROFILE,
        is_default=True,
        allowed_classes=tuple(rule.name for rule in _ALLOWED),
    ),
)


def _deny(message: str) -> Failure:
    return Failure(error=PlannerValidationError(message).to_error_info())


def template_class_rules() -> tuple[TemplateClassRule, ...]:
    """Reviewable immutable table; unknown labels have no permissive fallback."""
    return _CLASSES


def nuclei_profiles() -> tuple[NucleiProfile, ...]:
    """Finite named safe/default profiles, independent of installed templates."""
    return _PROFILES


def classify_template(
    template_class: str, behavior: TemplateBehavior
) -> OperationResult[TemplateClassRule]:
    """Class name AND complete effective behavior must match the reviewed envelope."""
    try:
        behavior = TemplateBehavior.model_validate(behavior)
    except (ValueError, TypeError):
        return _deny("Invalid or incomplete template behavior")
    if type(template_class) is not str:
        return _deny("Unknown template class")
    rule = next((rule for rule in _CLASSES if rule.name == template_class), None)
    if rule is None or rule.classification != "allowed":
        return _deny("Template class is prohibited, unreviewed or unknown")
    if behavior != rule.behavior:
        return _deny("Template behavior exceeds the reviewed class envelope")
    return Success[TemplateClassRule](value=rule)


@dataclass(frozen=True, slots=True, init=False)
class NucleiProfileCatalog:
    """Trusted operator reviews within immutable repository classes/profiles.

    Default has zero approved concrete templates. A matching assessment grants
    no scope, budget, byte authenticity, process or scan authority. No loader,
    YAML parser, file read, template installation/update or adapter integration.
    """

    _reviews: Mapping[str, TemplateReview]

    def __init__(self, reviews: tuple[TemplateReview, ...] = ()) -> None:
        try:
            if type(reviews) is not tuple or len(reviews) > 128:
                raise ValueError("bounded explicit review tuple required")
            copied: dict[str, TemplateReview] = {}
            package: tuple[str, str, str, str] | None = None
            for raw in reviews:
                review = TemplateReview.model_validate(raw)
                identity = review.identity
                current = (
                    identity.source_repository,
                    identity.source_revision,
                    identity.package_version,
                    identity.engine_version,
                )
                if (
                    identity.engine_version != REVIEWED_ENGINE_VERSION
                    or identity.template_id in copied
                    or (package is not None and current != package)
                    or isinstance(
                        classify_template(review.template_class, review.behavior),
                        Failure,
                    )
                ):
                    raise ValueError("unreviewed or conflicting template review")
                package = current
                copied[identity.template_id] = review
        except (ValueError, TypeError) as cause:
            raise ConfigurationError("Invalid trusted Nuclei review catalog") from cause
        object.__setattr__(self, "_reviews", MappingProxyType(copied))

    @property
    def reviews(self) -> tuple[TemplateReview, ...]:
        return tuple(self._reviews[key] for key in sorted(self._reviews))

    def select(self, profile: str) -> OperationResult[NucleiProfile]:
        """Exact finite profile name; no aliases, override options or auto-default."""
        if type(profile) is not str:
            return _deny("Unknown Nuclei policy profile")
        selected = next((item for item in _PROFILES if item.name == profile), None)
        if selected is None:
            return _deny("Unknown Nuclei policy profile")
        return Success[NucleiProfile](value=selected)

    def assess(
        self, profile: str, candidate: TemplatePolicyCandidate
    ) -> OperationResult[TemplatePolicyAssessment]:
        """Exact current review/identity/behavior match, never an execution token."""
        selected = self.select(profile)
        if isinstance(selected, Failure):
            return selected
        try:
            candidate = TemplatePolicyCandidate.model_validate(candidate)
        except (ValueError, TypeError):
            return _deny("Invalid template policy candidate")
        rule = classify_template(candidate.template_class, candidate.behavior)
        if isinstance(rule, Failure):
            return rule
        review = self._reviews.get(candidate.identity.template_id)
        if review is None:
            return _deny("Template has no current trusted review")
        if (
            candidate.identity != review.identity
            or candidate.template_class != review.template_class
            or candidate.behavior != review.behavior
        ):
            return _deny(
                "Template provenance, version, content or behavior changed; new review required"
            )
        if candidate.template_class not in selected.value.allowed_classes:
            return _deny("Template class is excluded from the selected profile")
        return Success[TemplatePolicyAssessment](
            value=TemplatePolicyAssessment(
                profile=selected.value.name,
                template_class=candidate.template_class,
                identity=review.identity,
                review_reference=review.review_reference,
                reviewed_at=review.reviewed_at,
                risk_class=RiskClass.ACTIVE_SAFE,
            )
        )

"""Pure template review/profile data; never scanner input or execution authority."""

from typing import Annotated, Literal, Self

from pydantic import Field, StringConstraints, field_validator, model_validator

from recon_agent.domain._base import Record, Timestamp
from recon_agent.domain.capabilities import RiskClass

PolicyName = Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9_-]{0,63}$")]
Version = Annotated[
    str, StringConstraints(max_length=64, pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
]
ResponsePart = Literal["status", "headers", "body", "raw"]


class TemplateBehavior(Record):
    """Explicit effective behavior attested by trusted review, not template tags.

    No omitted safety fields/defaults. Features enumerate every additional behavior
    (redirects, cookies, payloads, OAST, code, helpers, secondary contacts, etc.).
    Only an empty feature set is eligible; unknown features fail closed.
    """

    protocol: PolicyName
    method: Annotated[str, Field(min_length=1, max_length=16)]
    destination: Literal["target_root", "target_path", "absolute", "derived", "unknown"]
    request_count: int = Field(ge=1, le=256)
    response_parts: tuple[ResponsePart, ...] = Field(min_length=1, max_length=4)
    features: tuple[PolicyName, ...] = Field(max_length=64)

    @field_validator("response_parts", "features")
    @classmethod
    def unique_sorted(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if len(set(values)) != len(values):
            raise ValueError("duplicate behavior entry")
        return tuple(sorted(values))


class TemplateClassRule(Record):
    name: PolicyName
    classification: Literal["allowed", "prohibited", "unreviewed"]
    reason: Annotated[str, Field(min_length=1, max_length=512)]
    risk_class: RiskClass | None = None
    behavior: TemplateBehavior | None = None

    @model_validator(mode="after")
    def classification_fields(self) -> Self:
        if (self.classification == "allowed") != (
            self.risk_class is RiskClass.ACTIVE_SAFE and self.behavior is not None
        ):
            raise ValueError("only allowed classes have reviewed behavior/risk")
        if self.classification != "allowed" and (
            self.risk_class is not None or self.behavior is not None
        ):
            raise ValueError("excluded classes cannot carry allowed behavior/risk")
        return self


class NucleiProfile(Record):
    """Finite profile metadata; even the default does not enable scan dispatch."""

    name: PolicyName
    is_default: bool
    allowed_classes: tuple[PolicyName, ...] = Field(min_length=1, max_length=2)
    execution_authorized: Literal[False] = False


class TemplateIdentity(Record):
    """Trusted content/provenance pins; no template path, URL or CLI option.

    Values alone do not verify local bytes, upstream authenticity or contact
    containment. The enforcement task must establish these before execution.
    """

    template_id: PolicyName
    source_repository: Literal["projectdiscovery/nuclei-templates"]
    source_revision: Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{40}$")]
    package_version: Version
    engine_version: Version
    content_sha256: Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")]


class TemplatePolicyCandidate(Record):
    """Metadata from trusted inspection, never a scanner-emitted self-attestation."""

    identity: TemplateIdentity
    template_class: PolicyName
    behavior: TemplateBehavior


class TemplateReview(TemplatePolicyCandidate):
    """Operator-owned manual review pinned to all effective template content."""

    review_reference: PolicyName
    reviewed_at: Timestamp


class TemplatePolicyAssessment(Record):
    """Eligible review metadata, explicitly not an ApprovedAction/ProcessSpec."""

    profile: PolicyName
    template_class: PolicyName
    identity: TemplateIdentity
    review_reference: PolicyName
    reviewed_at: Timestamp
    risk_class: RiskClass
    execution_authorized: Literal[False] = False

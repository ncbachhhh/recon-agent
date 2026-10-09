"""Strict Nuclei foundation contracts; candidates are unverified reported data."""

from typing import Annotated, Literal

from pydantic import ConfigDict, Field, StringConstraints

from recon_agent.core.errors import ErrorInfo
from recon_agent.domain import Evidence, Observation
from recon_agent.domain._base import NonEmptyText, Record, Timestamp

ProfileName = Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9_-]{0,63}$")]
Text = Annotated[str, Field(max_length=4096)]
Reference = Annotated[str, Field(min_length=1, max_length=2048, pattern=r"\S")]
Severity = Literal["unknown", "info", "low", "medium", "high", "critical"]


class NucleiInput(Record):
    """Explicit semantic name only; no default, paths, flags or template selectors."""

    profile: ProfileName


class NucleiContext(Record):
    """Trusted caller provenance for already captured output, not authorization."""

    asset_id: NonEmptyText
    execution_id: NonEmptyText
    collected_at: Timestamp
    query_target: Reference
    # A result event does not establish the scanner or template version.
    scanner_version: Literal["3.4.10"] | None = None


class NucleiInfo(Record):
    name: Text | None = None
    description: Text | None = None
    severity: Severity | None = None
    reference: list[Reference] = Field(default_factory=list, max_length=64)


class NucleiEvent(Record):
    """Selected ResultEvent fields; all other fields remain in raw evidence."""

    model_config = ConfigDict(validate_by_name=True)

    template_id: Reference = Field(alias="template-id")
    template: Text | None = None
    template_url: Text | None = Field(default=None, alias="template-url")
    template_path: Text | None = Field(default=None, alias="template-path")
    info: NucleiInfo
    type: Reference
    host: Reference
    matched_at: Reference = Field(alias="matched-at")
    url: Reference | None = None
    ip: Reference | None = None
    matcher_name: Text | None = Field(default=None, alias="matcher-name")
    extractor_name: Text | None = Field(default=None, alias="extractor-name")
    extracted_results: list[Text] = Field(
        default_factory=list, max_length=64, alias="extracted-results"
    )
    timestamp: Text | None = None
    matcher_status: Literal[True] = Field(alias="matcher-status")


class NucleiCandidate(Record):
    """A scanner claim, never a Finding or verified vulnerability.

    Template paths/URLs/references are inert reported text, not trusted provenance.
    Repeated/conflicting records remain separate until the owning later tasks.
    """

    source: Literal["nuclei"] = "nuclei"
    verification: Literal["unverified"] = "unverified"
    execution_id: NonEmptyText
    observation_id: NonEmptyText
    evidence_ids: tuple[NonEmptyText, ...] = Field(min_length=1)
    source_line: int = Field(ge=1, le=256)
    record_sha256: Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")]
    reported: NucleiEvent


class NucleiOutput(Record):
    """Offline result ingestion; completed means parsing, not a successful scan."""

    query_target: Reference
    format_version: Literal["nuclei-result-event-3.4.10"] = "nuclei-result-event-3.4.10"
    scanner_version: Literal["3.4.10"] | None
    status: Literal["completed", "partial", "failed"]
    malformed_lines: int = Field(ge=0)
    errors: tuple[ErrorInfo, ...] = ()
    candidates: tuple[NucleiCandidate, ...]
    observations: tuple[Observation, ...]
    evidence: tuple[Evidence, ...]
    # Exact retained bytes including malformed/unknown fields and stderr.
    stdout_base64: str = Field(repr=False)
    stderr_base64: str = Field(repr=False)

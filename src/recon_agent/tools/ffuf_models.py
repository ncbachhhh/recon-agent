"""Restricted FFUF profile; wordlists and bounds belong to trusted composition."""

from typing import Literal, Self

from pydantic import Field, model_validator

from recon_agent.core.errors import ErrorInfo, ScopeRejectedError
from recon_agent.domain import Asset, Endpoint, Evidence, Observation, Scope, Target
from recon_agent.domain._base import Record
from recon_agent.policy.scope import ScopeValidator
from recon_agent.tools.dns_models import DnsContext

# Application-owned labels, never AI-selected paths, credentials or remote text.
LABELS = ("www", "api", "static", "dev")
WORDLIST_PROFILE = "vhosts-small-v1"


class FfufInput(Record):
    """Only one explicitly requested semantic profile; no FFUF syntax."""

    profile: Literal["vhost_names"]


class FfufSettings(Record):
    """Operator selects a DNS suffix, not an arbitrary file or request template."""

    vhost_suffix: str = Field(min_length=1, max_length=240)
    wordlist_profile: Literal["vhosts-small-v1"] = "vhosts-small-v1"
    max_requests: int = Field(default=8, ge=2, le=8)
    request_rate: int = Field(default=1, ge=1, le=4)
    concurrency: int = Field(default=1, ge=1, le=1)

    @model_validator(mode="after")
    def canonical_suffix(self) -> Self:
        # Central syntax validation only, not operational authorization.
        try:
            validator = ScopeValidator(
                Scope(
                    id="ffuf-syntax",
                    roots=(
                        Target(
                            id="ffuf-suffix", kind="hostname", value=self.vhost_suffix
                        ),
                    ),
                )
            )
            target = validator.require_allowed(
                Target(id="ffuf-suffix", kind="hostname", value=self.vhost_suffix)
            ).canonical_target.value
        except ScopeRejectedError:
            raise ValueError("canonical dotted ASCII suffix required") from None
        if target != self.vhost_suffix or "." not in target or "FUZZ" in target:
            raise ValueError("canonical dotted ASCII suffix required")
        return self

    @property
    def candidates(self) -> tuple[str, ...]:
        return tuple(f"{label}.{self.vhost_suffix}" for label in LABELS)


class FfufContext(DnsContext):
    """Caller owns identities, lifecycle, time and snapshot retention."""


class FuzzDiscoveryOutput(Record):
    query_target: str
    profile: Literal["vhost_names"] = "vhost_names"
    source_version: Literal["2.1.0"] = "2.1.0"
    wordlist_profile: Literal["vhosts-small-v1"] = "vhosts-small-v1"
    wordlist_sha256: str
    candidates: tuple[str, ...]
    request_upper_bound: int = Field(ge=2, le=8)
    unreported_candidates: tuple[str, ...]
    status: Literal["completed", "partial"]
    malformed_lines: int = Field(ge=0)
    limitations: tuple[str, ...]
    errors: tuple[ErrorInfo, ...]
    asset: Asset
    endpoints: tuple[Endpoint, ...]
    observations: tuple[Observation, ...]
    evidence: tuple[Evidence, ...]

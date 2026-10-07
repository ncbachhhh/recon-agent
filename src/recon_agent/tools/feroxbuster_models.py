"""Strict operator-only content discovery limits and generic output contracts."""

from typing import Literal

from pydantic import Field

from recon_agent.core.errors import ErrorInfo
from recon_agent.domain import Asset, Endpoint, Evidence, Observation
from recon_agent.domain._base import Record
from recon_agent.tools.dns_models import DnsContext

# Reviewed application policy, not an external file or remote wordlist.
WORDS = ("admin/", "api/", "assets/", "index.html")
WORDLIST_PROFILE = "small-v1"


class FeroxbusterInput(Record):
    """Planner selects the capability and primary target only."""


class FeroxbusterSettings(Record):
    """Root depth is zero; limits never mean unlimited."""

    wordlist_profile: Literal["small-v1"] = "small-v1"
    max_depth: int = Field(default=1, ge=0, le=3)
    max_directories: int = Field(default=4, ge=1, le=8)
    max_requests: int = Field(default=28, ge=4, le=56)
    request_rate: int = Field(default=1, ge=1, le=4)
    concurrency: int = Field(default=1, ge=1, le=2)


class FeroxbusterContext(DnsContext):
    """Caller owns time/identity/lifecycle and normalized snapshot retention."""


class ContentDiscoveryOutput(Record):
    query_target: str
    source_version: Literal["2.13.1"] = "2.13.1"
    wordlist_profile: Literal["small-v1"] = "small-v1"
    wordlist_sha256: str
    status: Literal["completed", "partial"]
    scanned_directories: tuple[str, ...]
    request_upper_bound: int = Field(ge=0, le=56)
    unreported_urls: tuple[str, ...]
    malformed_lines: int = Field(ge=0)
    limitations: tuple[str, ...]
    errors: tuple[ErrorInfo, ...]
    asset: Asset
    endpoints: tuple[Endpoint, ...]
    observations: tuple[Observation, ...]
    evidence: tuple[Evidence, ...]

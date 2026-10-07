"""Strict crawl composition; discoveries use existing generic domain contracts."""

from typing import Literal

from pydantic import Field

from recon_agent.core.errors import ErrorInfo
from recon_agent.domain import Asset, Endpoint, Evidence, Observation
from recon_agent.domain._base import Record
from recon_agent.tools.dns_models import DnsContext


class KatanaInput(Record):
    """Planner selects only the primary semantic capability, never crawl controls."""


class KatanaSettings(Record):
    """Operator-only finite graph limits. Root has depth zero and counts as a page."""

    max_depth: int = Field(default=2, ge=0, le=3)
    max_pages: int = Field(default=8, ge=1, le=16)
    max_discoveries: int = Field(default=256, ge=1, le=256)


class KatanaContext(DnsContext):
    """Caller supplies identities/time and owns lifecycle/snapshot retention."""


class CrawlOutput(Record):
    query_target: str
    source_version: Literal["1.8.0"] = "1.8.0"
    status: Literal["completed", "partial"]
    contacted_urls: tuple[str, ...]
    malformed_lines: int = Field(ge=0)
    limitations: tuple[str, ...]
    errors: tuple[ErrorInfo, ...]
    asset: Asset
    endpoints: tuple[Endpoint, ...]
    observations: tuple[Observation, ...]
    evidence: tuple[Evidence, ...]

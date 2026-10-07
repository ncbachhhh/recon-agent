"""Fixed-file contracts. All remote fields remain untrusted evidence."""

from typing import Literal

from pydantic import Field

from recon_agent.core.errors import ErrorInfo
from recon_agent.domain import Asset, Evidence, Observation
from recon_agent.domain._base import Record
from recon_agent.tools.dns_models import DnsContext

CommonPath = Literal["/robots.txt", "/sitemap.xml", "/.well-known/security.txt"]
COMMON_PATHS: tuple[CommonPath, ...] = (
    "/robots.txt",
    "/sitemap.xml",
    "/.well-known/security.txt",
)


class CommonFilesInput(Record):
    """No planner paths, headers, URLs or transport controls."""


class CommonFilesContext(DnsContext):
    """Caller owns identity, collection time, lifecycle and snapshot retention."""


class ContactBinding(Record):
    """Operator-selected canonical hostname/numeric contact, never a DNS claim."""

    host: str = Field(min_length=1, max_length=254)
    address: str = Field(min_length=1, max_length=45)


class HttpResponse(Record):
    """Transport result with selected metadata and an exact bounded body prefix."""

    status_code: int = Field(ge=200, le=599)
    content_type: str | None = Field(default=None, max_length=1024)
    content_length: int | None = Field(default=None, ge=0, le=2**63 - 1)
    content_encoding: str | None = Field(default=None, max_length=256)
    location: str | None = Field(default=None, max_length=2048)
    errors: tuple[ErrorInfo, ...] = ()
    body: bytes = Field(default=b"", exclude=True, repr=False)
    truncated: bool = False


class RedirectFact(Record):
    url: str
    status_code: int
    location: str
    destination: str | None
    rejection_error: ErrorInfo | None = None
    outcome: Literal["followed", "rejected", "limit", "loop"]


class CommonFileFact(Record):
    path: CommonPath
    requested_url: str
    final_url: str
    contact_address: str | None = None
    status_code: int | None = None
    content_type: str | None = None
    content_length: int | None = None
    retained_bytes: int = Field(ge=0)
    body_base64: str
    body_text: str | None = None
    truncated: bool = False
    redirects: tuple[RedirectFact, ...] = ()
    # robots group context is preserved; directives are observations, not ACLs.
    robots: tuple[dict[str, str], ...] = ()
    security: tuple[dict[str, str], ...] = ()
    discovered_urls: tuple[str, ...] = ()
    errors: tuple[ErrorInfo, ...] = ()
    trust: Literal["untrusted"] = "untrusted"
    discovery_authorizes_contact: Literal[False] = False


class CommonFilesOutput(Record):
    query_target: str
    source_capability: Literal["inspect_common_files"] = "inspect_common_files"
    status: Literal["completed", "partial"]
    files: tuple[CommonFileFact, ...]
    errors: tuple[ErrorInfo, ...]
    asset: Asset
    observations: tuple[Observation, ...]
    evidence: tuple[Evidence, ...]

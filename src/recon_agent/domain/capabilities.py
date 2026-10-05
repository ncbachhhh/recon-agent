"""Finite semantic identities and planner-safe metadata, without implementations."""

from enum import StrEnum
from typing import Annotated

from pydantic import StringConstraints

from recon_agent.domain._base import Record


class CapabilityId(StrEnum):
    RESOLVE_DNS = "resolve_dns"
    ENUMERATE_SUBDOMAINS = "enumerate_subdomains"
    DISCOVER_PORTS = "discover_ports"
    FINGERPRINT_SERVICES = "fingerprint_services"
    PROBE_HTTP = "probe_http"
    INSPECT_TLS = "inspect_tls"
    CRAWL_WEB = "crawl_web"
    DISCOVER_CONTENT = "discover_content"
    INSPECT_PROTOCOL = "inspect_protocol"
    SCAN_TEMPLATES = "scan_templates"


class RiskClass(StrEnum):
    """Reported classification only; action policy owns permission."""

    PASSIVE = "passive"
    ACTIVE_SAFE = "active_safe"


class CapabilityDescriptor(Record):
    """Explicit trusted semantic text; never derive it from executable metadata."""

    capability: CapabilityId
    description: Annotated[
        str, StringConstraints(min_length=1, max_length=1024, pattern=r"\S")
    ]
    risk_class: RiskClass

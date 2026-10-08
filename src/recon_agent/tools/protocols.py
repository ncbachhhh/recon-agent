"""Finite service relevance contracts, independent of operational registration."""

from dataclasses import dataclass
from types import MappingProxyType

from pydantic import ValidationError

from recon_agent.domain.assets import Service
from recon_agent.domain.capabilities import (
    CapabilityDescriptor,
    CapabilityId,
    RiskClass,
)
from recon_agent.domain.protocols import (
    ProtocolFamily,
    ProtocolMetadataInput,
    ProtocolMetadataOutput,
)


@dataclass(frozen=True, slots=True)
class ProtocolCapabilityContract:
    """Known semantic contract, never an adapter or an availability declaration.

    Schema classes are internal trusted code. Only descriptor is planner-facing;
    actual adapter definitions/availability remain owned by ToolRegistry.
    """

    family: ProtocolFamily
    descriptor: CapabilityDescriptor
    input_schema: type[ProtocolMetadataInput] = ProtocolMetadataInput
    output_schema: type[ProtocolMetadataOutput] = ProtocolMetadataOutput
    parameter_target_fields: tuple[str, ...] = ()


_CONTRACTS = tuple(
    ProtocolCapabilityContract(
        family=family,
        descriptor=CapabilityDescriptor(
            capability=CapabilityId.INSPECT_PROTOCOL,
            description=f"Collect non-authentication {family.value} service metadata.",
            risk_class=RiskClass.ACTIVE_SAFE,
        ),
    )
    for family in sorted(ProtocolFamily)
)
_BY_FAMILY = MappingProxyType({item.family: item for item in _CONTRACTS})

# Exact ASCII case-insensitive normalized identities only, never banner searches.
# Values retain database identity to reject conflicting database product hints too.
_SERVICE_IDENTITIES = MappingProxyType(
    {
        "ssh": (ProtocolFamily.SSH, "ssh"),
        "smb": (ProtocolFamily.SMB, "smb"),
        "microsoft-ds": (ProtocolFamily.SMB, "smb"),
        "netbios-ssn": (ProtocolFamily.SMB, "smb"),
        "ftp": (ProtocolFamily.FTP, "ftp"),
        "smtp": (ProtocolFamily.SMTP, "smtp"),
        "smtps": (ProtocolFamily.SMTP, "smtp"),
        "submission": (ProtocolFamily.SMTP, "smtp"),
        "mysql": (ProtocolFamily.DATABASE, "mysql"),
        "mariadb": (ProtocolFamily.DATABASE, "mysql"),
        "postgresql": (ProtocolFamily.DATABASE, "postgresql"),
        "postgres": (ProtocolFamily.DATABASE, "postgresql"),
        "ms-sql-s": (ProtocolFamily.DATABASE, "ms-sql-s"),
        "mongodb": (ProtocolFamily.DATABASE, "mongodb"),
        "redis": (ProtocolFamily.DATABASE, "redis"),
    }
)
_PRODUCT_IDENTITIES = MappingProxyType(
    {
        "openssh": "ssh",
        "dropbear": "ssh",
        "samba": "smb",
        "vsftpd": "ftp",
        "proftpd": "ftp",
        "pure-ftpd": "ftp",
        "postfix": "smtp",
        "exim": "smtp",
        "mysql": "mysql",
        "mariadb": "mysql",
        "postgresql": "postgresql",
        "microsoft sql server": "ms-sql-s",
        "mongodb": "mongodb",
        "redis": "redis",
    }
)


def protocol_capability_contracts() -> tuple[ProtocolCapabilityContract, ...]:
    """Sorted known contracts, including families without any implementation."""
    return _CONTRACTS


def select_protocol_capability(service: Service) -> ProtocolCapabilityContract | None:
    """Return one relevance candidate or None, without runtime/policy side effects.

    Explicit recognized TCP identity is mandatory. Port never supplies identity;
    products only veto recognized conflicts, never rescue an unknown identity.
    Malformed constructed/copied records fail closed like unknown services.
    """
    try:
        normalized = Service.model_validate(service)
    except (ValidationError, TypeError, ValueError):
        return None
    name = normalized.protocol
    if normalized.transport != "tcp" or name is None or not name.isascii():
        return None
    identity = _SERVICE_IDENTITIES.get(name.lower())
    if identity is None:
        return None
    product = normalized.product
    if product is not None and product.isascii():
        hint = _PRODUCT_IDENTITIES.get(product.lower())
        if hint is not None and hint != identity[1]:
            return None
    return _BY_FAMILY[identity[0]]

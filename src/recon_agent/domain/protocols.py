"""Protocol metadata data contracts; no exchanges, authorization or inference."""

from enum import StrEnum
from typing import Literal, Self

from pydantic import Field, model_validator

from recon_agent.domain._base import Port, Record
from recon_agent.domain.assets import Service
from recon_agent.domain.observations import Evidence, Observation


class ProtocolFamily(StrEnum):
    SSH = "ssh"
    SMB = "smb"
    FTP = "ftp"
    SMTP = "smtp"
    DATABASE = "database"


class ProtocolMetadataInput(Record):
    """Semantic parameters only; ActionRequest.target remains the scoped host.

    Future adapters must verify these claims against the observed service and
    their reviewed supported profile. Construction cannot authorize contact.
    """

    family: Literal["ssh", "smb", "ftp", "smtp", "database"]
    port: Port
    transport: Literal["tcp"]


class ProtocolMetadataOutput(Record):
    """Common future metadata envelope with explicit existing evidence lineage.

    No facts are generated here. ActionResult owns terminal/partial/error status;
    ReconState continues to own whole-session identity/lifecycle validation.
    """

    family: ProtocolFamily
    service: Service
    observations: tuple[Observation, ...] = Field(default=(), max_length=128)
    evidence: tuple[Evidence, ...] = Field(default=(), max_length=256)

    @model_validator(mode="after")
    def metadata_lineage(self) -> Self:
        evidence = {item.id: item for item in self.evidence}
        if len(evidence) != len(self.evidence) or len(
            {item.id for item in self.observations}
        ) != len(self.observations):
            raise ValueError("protocol metadata requires unique record identities")
        if any(item.capability != "inspect_protocol" for item in self.evidence):
            raise ValueError("protocol evidence requires capability attribution")
        for observation in self.observations:
            if (
                observation.kind != "metadata"
                or observation.asset_id != self.service.asset_id
            ):
                raise ValueError("protocol metadata must belong to the service asset")
            for reference in observation.evidence_ids:
                origin = evidence.get(reference)
                if (
                    origin is None
                    or origin.source != observation.source
                    or origin.execution_id != observation.execution_id
                ):
                    raise ValueError("protocol metadata requires matching evidence")
        return self

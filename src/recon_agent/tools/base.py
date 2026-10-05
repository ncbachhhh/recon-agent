"""Minimum trusted adapter interface; capability implementations live separately."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum
from typing import Annotated, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    model_validator,
)

from recon_agent.domain.capabilities import CapabilityDescriptor

AdapterId = Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9_-]{0,63}$")]


class AdapterDefinition(BaseModel):
    """Internal definition; schema classes are trusted code, not planner data."""

    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        frozen=True,
        validate_default=True,
        revalidate_instances="always",
        hide_input_in_errors=True,
    )

    adapter_id: AdapterId
    descriptor: CapabilityDescriptor
    input_schema: type[BaseModel] = Field(exclude=True, repr=False)
    output_schema: type[BaseModel] = Field(exclude=True, repr=False)
    # None means target semantics are unestablished; () explicitly declares that
    # this schema introduces no secondary network targets.
    parameter_target_fields: tuple[str, ...] | None = None

    @model_validator(mode="after")
    def strict_schemas(self) -> Self:
        fields = self.parameter_target_fields
        if fields is not None and (
            len(set(fields)) != len(fields)
            or any(name not in self.input_schema.model_fields for name in fields)
        ):
            raise ValueError("parameter target fields must name unique input fields")
        for schema in (self.input_schema, self.output_schema):
            if (
                schema.model_config.get("extra") != "forbid"
                or schema.model_config.get("strict") is not True
            ):
                raise ValueError(
                    "adapter schemas must be strict and forbid extra fields"
                )
        return self


class ToolAdapter(ABC):
    """Trusted application code supplied explicitly by the composition root.

    Capability-specific implementations own execution and normalization; the
    base exposes metadata only. Native DNS uses no process runner. Later external
    adapters own availability probing, ProcessSpec construction and runner use.
    """

    @property
    @abstractmethod
    def definition(self) -> AdapterDefinition:
        """Stable adapter identity, semantic metadata and input/output contracts."""


class AdapterAvailability(StrEnum):
    """Explicit trusted snapshot, not a registry probe or authorization."""

    NOT_CHECKED = "not_checked"
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True, slots=True)
class AdapterRegistration:
    """Composition input; external data must never construct adapter instances."""

    adapter: ToolAdapter
    availability: AdapterAvailability = AdapterAvailability.NOT_CHECKED


class CapabilityCatalogEntry(CapabilityDescriptor):
    """Planner-safe projection; no adapter identity, schema class or runtime object."""

    availability: AdapterAvailability

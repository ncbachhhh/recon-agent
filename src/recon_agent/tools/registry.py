"""Immutable explicit composition and local lookup; never authorizes or executes."""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from types import MappingProxyType

from pydantic import InstanceOf, ValidationError

from recon_agent.core.errors import (
    ConfigurationError,
    ErrorContext,
    PlannerValidationError,
    ToolUnavailableError,
)
from recon_agent.core.results import Failure, OperationResult, Success
from recon_agent.domain.capabilities import CapabilityId
from recon_agent.tools.base import (
    AdapterAvailability,
    AdapterDefinition,
    AdapterRegistration,
    CapabilityCatalogEntry,
    ToolAdapter,
)


@dataclass(frozen=True, slots=True)
class _Binding:
    adapter: ToolAdapter
    definition: AdapterDefinition
    availability: AdapterAvailability


@dataclass(frozen=True, slots=True, init=False)
class ToolRegistry:
    """One explicitly selected adapter per capability, fixed at construction.

    All names in CapabilityId are conceptual. Only supplied trusted registrations
    have implementations, and only declared AVAILABLE registrations resolve.
    """

    _capabilities: Mapping[CapabilityId, _Binding]
    _adapters: Mapping[str, _Binding]

    def __init__(self, registrations: Iterable[AdapterRegistration] = ()) -> None:
        capabilities: dict[CapabilityId, _Binding] = {}
        adapters: dict[str, _Binding] = {}
        for registration in registrations:
            if (
                not isinstance(registration, AdapterRegistration)
                or not isinstance(registration.adapter, ToolAdapter)
                or not isinstance(registration.availability, AdapterAvailability)
            ):
                raise ConfigurationError("Invalid trusted adapter registration")
            try:
                definition = AdapterDefinition.model_validate(
                    registration.adapter.definition
                )
            except ValidationError as cause:
                raise ConfigurationError(
                    "Invalid trusted adapter definition"
                ) from cause
            if definition.adapter_id in adapters:
                raise ConfigurationError(
                    "Duplicate adapter identity",
                    context=ErrorContext(tool=definition.adapter_id),
                )
            capability = definition.descriptor.capability
            if capability in capabilities:
                raise ConfigurationError(
                    "Conflicting capability registration",
                    context=ErrorContext(capability=capability),
                )
            binding = _Binding(
                registration.adapter, definition, registration.availability
            )
            adapters[definition.adapter_id] = binding
            capabilities[capability] = binding
        object.__setattr__(self, "_capabilities", MappingProxyType(capabilities))
        object.__setattr__(self, "_adapters", MappingProxyType(adapters))

    @staticmethod
    def is_known_capability(capability: str) -> bool:
        """Conceptual catalog membership, independent of registration/availability."""
        return capability in CapabilityId

    def has_capability(self, capability: str) -> bool:
        """Registration only; does not mean enabled, available or authorized."""
        return capability in self._capabilities

    def has_adapter(self, adapter_id: str) -> bool:
        return adapter_id in self._adapters

    def list_capabilities(self) -> tuple[CapabilityId, ...]:
        return tuple(sorted(self._capabilities))

    def list_adapters(self) -> tuple[str, ...]:
        return tuple(sorted(self._adapters))

    def catalog(self) -> tuple[CapabilityCatalogEntry, ...]:
        return tuple(
            CapabilityCatalogEntry(
                **binding.definition.descriptor.model_dump(),
                availability=binding.availability,
            )
            for capability in self.list_capabilities()
            for binding in (self._capabilities[capability],)
        )

    def definition(self, adapter_id: str) -> OperationResult[AdapterDefinition]:
        """Internal schema/identity lookup; never interprets an ID as a program."""
        binding = self._adapters.get(adapter_id)
        if binding is None:
            return Failure(
                error=ToolUnavailableError("Adapter is not registered").to_error_info()
            )
        return Success[AdapterDefinition](value=binding.definition)

    def resolve(self, capability: str) -> OperationResult[InstanceOf[ToolAdapter]]:
        """Select trusted code, with canonical failures and no execution side effects."""
        if not self.is_known_capability(capability):
            return Failure(
                error=PlannerValidationError(
                    "Unknown capability requested"
                ).to_error_info()
            )
        binding = self._capabilities.get(CapabilityId(capability))
        if binding is None:
            return Failure(
                error=ToolUnavailableError(
                    "Capability has no registered adapter",
                    context=ErrorContext(capability=capability),
                ).to_error_info()
            )
        if binding.availability is not AdapterAvailability.AVAILABLE:
            return Failure(
                error=ToolUnavailableError(
                    "Registered adapter availability is not confirmed",
                    context=ErrorContext(
                        capability=capability, tool=binding.definition.adapter_id
                    ),
                ).to_error_info()
            )
        return Success[InstanceOf[ToolAdapter]](value=binding.adapter)

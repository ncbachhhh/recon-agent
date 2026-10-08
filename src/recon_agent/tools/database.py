"""Operational database identification metadata under current policy/scope/resources."""

import asyncio
from dataclasses import dataclass, field
from ipaddress import ip_address

from recon_agent.core.config.models import ExecutionConfig
from recon_agent.core.errors import (
    ConfigurationError,
    ParserError,
    PlannerValidationError,
    ToolExecutionError,
    ToolTimeoutError,
    ToolUnavailableError,
)
from recon_agent.core.results import Failure, OperationResult, Success
from recon_agent.domain import ActionRequest
from recon_agent.domain.budgets import ReservationOutcome
from recon_agent.domain.capabilities import CapabilityId
from recon_agent.domain.protocols import ProtocolFamily
from recon_agent.execution.lifecycle import ExecutionStart, notify_execution_start
from recon_agent.policy.actions import ActionPolicyValidator
from recon_agent.policy.budgets import BudgetController
from recon_agent.tools import AdapterDefinition, ToolAdapter
from recon_agent.tools.database_models import (
    DatabaseContext,
    DatabaseInput,
    DatabaseOutput,
    DatabaseServiceBinding,
    database_type,
)
from recon_agent.tools.database_parser import (
    MAX_RESPONSE_BYTES,
    normalize,
    parse_metadata,
)
from recon_agent.tools.native_database import DatabaseTransport, NativeDatabaseTransport
from recon_agent.tools.protocols import select_protocol_capability


def _invalid(message: str) -> Failure:
    return Failure(error=PlannerValidationError(message).to_error_info())


@dataclass(frozen=True, slots=True)
class DatabaseAdapter(ToolAdapter):
    """One current observed service and numeric contact per permitted attempt.

    Only reviewed pre-authentication profiles run. No authentication, query,
    database driver, data operation, process or authenticated session API exists.
    """

    bindings: tuple[DatabaseServiceBinding, ...] = field(repr=False)
    config: ExecutionConfig = field(repr=False)
    transport: DatabaseTransport = field(
        default_factory=NativeDatabaseTransport, repr=False
    )
    _timeout: float = field(init=False, repr=False)
    _output_limit: int = field(init=False, repr=False)

    def __post_init__(self) -> None:
        try:
            config = ExecutionConfig.model_validate(self.config.model_dump())
            if (
                not isinstance(self.bindings, tuple)
                or not 1 <= len(self.bindings) <= 64
            ):
                raise ValueError("finite observed database bindings required")
            bindings = tuple(
                DatabaseServiceBinding.model_validate(item) for item in self.bindings
            )
            if len({(item.host, item.service.port) for item in bindings}) != len(
                bindings
            ):
                raise ValueError("ambiguous database host/port binding")
            for item in bindings:
                address = ip_address(item.address)
                candidate = select_protocol_capability(item.service)
                if (
                    str(address) != item.address
                    or "%" in item.address
                    or getattr(address, "ipv4_mapped", None)
                    or item.host != item.host.lower()
                    or item.host.endswith(".")
                    or candidate is None
                    or candidate.family is not ProtocolFamily.DATABASE
                ):
                    raise ValueError(
                        "normalized database service/numeric contact required"
                    )
            object.__setattr__(self, "bindings", bindings)
        except (ValueError, TypeError, AttributeError) as cause:
            raise ConfigurationError(
                "Invalid trusted database metadata settings"
            ) from cause
        object.__setattr__(self, "_timeout", config.default_timeout_seconds)
        object.__setattr__(self, "_output_limit", config.max_output_bytes)

    @property
    def definition(self) -> AdapterDefinition:
        candidate = select_protocol_capability(self.bindings[0].service)
        assert candidate is not None
        return AdapterDefinition(
            adapter_id="native_database",
            descriptor=candidate.descriptor,
            input_schema=DatabaseInput,
            output_schema=DatabaseOutput,
            parameter_target_fields=candidate.parameter_target_fields,
        )

    async def execute(
        self,
        request: ActionRequest,
        *,
        policy: ActionPolicyValidator,
        budgets: BudgetController,
        context: DatabaseContext,
        on_started: ExecutionStart | None = None,
    ) -> OperationResult[DatabaseOutput]:
        try:
            request = ActionRequest.model_validate(request)
            context = DatabaseContext.model_validate(context)
        except (ValueError, TypeError):
            return _invalid("Malformed database request or context")
        if (
            request.capability != CapabilityId.INSPECT_PROTOCOL
            or policy.budget_eligibility is not budgets
        ):
            return _invalid("database execution composition does not match request")
        selected = policy.registry.resolve(request.capability)
        if isinstance(selected, Failure):
            return selected
        if selected.value is not self:
            return _invalid("database adapter is not the current registry binding")
        approved = policy.validate(request)
        if isinstance(approved, Failure):
            return approved
        # Revalidate specialized input even if trusted registry metadata was wrong.
        try:
            parameters = DatabaseInput.model_validate(request.parameters)
        except (ValueError, TypeError):
            return _invalid("Unsupported database metadata parameters")
        subject = approved.value.scope_match
        if subject.canonical_target.kind not in ("ip", "hostname"):
            return _invalid("database metadata requires an explicit host or IP")
        host = subject.host_identity
        binding = next(
            (
                item
                for item in self.bindings
                if item.host == host and item.service.port == parameters.port
            ),
            None,
        )
        if binding is None:
            return _invalid("database request has no observed service/contact binding")
        if request.asset_id not in (None, binding.service.asset_id):
            return _invalid("database service subject does not match request")
        candidate = select_protocol_capability(binding.service)
        if candidate is None or candidate.family is not ProtocolFamily.DATABASE:
            return _invalid("Observed service is not an unambiguous database candidate")
        if parameters.database_type != database_type(binding.service):
            return _invalid("Database type does not match observed service")
        contact = policy.scope_validator.validate_value(binding.address)
        if isinstance(contact, Failure):
            return contact
        # Numeric subjects cannot silently bind to a different address.
        if subject.canonical_target.kind == "ip" and host != binding.address:
            return _invalid("Numeric database subject must equal the contact address")
        if parameters.database_type not in ("mysql", "postgresql"):
            return Failure(
                error=ToolUnavailableError(
                    "Database profile has no approved pre-authentication metadata exchange"
                ).to_error_info()
            )
        reserved = budgets.reserve(
            approved.value.model_copy(
                update={
                    "parameter_scope_matches": (
                        *approved.value.parameter_scope_matches,
                        contact.value,
                    ),
                }
            )
        )
        if isinstance(reserved, Failure):
            return reserved
        with reserved.value as permit:
            started = notify_execution_start(on_started)
            if isinstance(started, Failure):
                permit.release(ReservationOutcome.ABORTED)
                return started
            # Trusted start notification can change current facts. Recheck scope
            # and registry immediately before contact, without double reservation.
            selected = policy.registry.resolve(request.capability)
            if isinstance(selected, Failure):
                permit.release(ReservationOutcome.ABORTED)
                return selected
            if selected.value is not self:
                permit.release(ReservationOutcome.ABORTED)
                return _invalid("database registry binding changed before contact")
            for value in (request.target, binding.address):
                scoped = policy.scope_validator.validate_value(value)
                if isinstance(scoped, Failure):
                    permit.release(ReservationOutcome.ABORTED)
                    return scoped
            timeout = min(self._timeout, budgets.state.remaining_seconds)
            if timeout <= 0:
                permit.release(ReservationOutcome.TIMEOUT)
                return Failure(
                    error=ToolTimeoutError("database deadline reached").to_error_info()
                )
            output_limit = min(self._output_limit, budgets.limits.max_output_bytes)
            try:
                async with asyncio.timeout(timeout):
                    raw = await self.transport.inspect(
                        binding.address,
                        parameters.port,
                        parameters.database_type,
                        timeout,
                        min(MAX_RESPONSE_BYTES, output_limit),
                    )
                    if type(raw) is not bytes or len(raw) > min(
                        MAX_RESPONSE_BYTES, output_limit
                    ):
                        raise ValueError("database capture bound")
                    greeting = parse_metadata(raw, parameters.database_type)
                    output = normalize(
                        raw, greeting, subject.canonical_target.value, binding, context
                    )
                    if len(output.model_dump_json().encode("utf-8")) > output_limit:
                        raise ValueError("database normalized output bound")
                    if budgets.state.remaining_seconds <= 0:
                        raise TimeoutError
                    permit.release(
                        ReservationOutcome.FAILED
                        if output.errors
                        else ReservationOutcome.COMPLETED
                    )
                    return Success(value=output)
            except TimeoutError:
                permit.release(ReservationOutcome.TIMEOUT)
                return Failure(
                    error=ToolTimeoutError(
                        "database metadata timed out"
                    ).to_error_info()
                )
            except ToolExecutionError as cause:
                permit.release(ReservationOutcome.FAILED)
                return Failure(error=cause.to_error_info())
            except OSError:
                permit.release(ReservationOutcome.FAILED)
                return Failure(
                    error=ToolExecutionError(
                        "database connection failed or closed"
                    ).to_error_info()
                )
            except (ValueError, TypeError, AttributeError):
                permit.release(ReservationOutcome.FAILED)
                return Failure(
                    error=ParserError(
                        "Malformed or oversized database metadata"
                    ).to_error_info()
                )

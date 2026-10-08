"""Operational SMB negotiation metadata under current policy/scope/resources."""

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
from recon_agent.tools.native_smb import NativeSmbTransport, SmbTransport
from recon_agent.tools.protocols import select_protocol_capability
from recon_agent.tools.smb_models import (
    SmbContext,
    SmbInput,
    SmbOutput,
    SmbServiceBinding,
)
from recon_agent.tools.smb_parser import MAX_RESPONSE_BYTES, normalize, parse_response


def _invalid(message: str) -> Failure:
    return Failure(error=PlannerValidationError(message).to_error_info())


@dataclass(frozen=True, slots=True)
class SmbAdapter(ToolAdapter):
    """One current observed service and numeric contact per permitted attempt.

    Only one fixed SMB2 NEGOTIATE is sent. No session setup, authentication,
    share/file operation, command, generic packet writer or process API exists.
    """

    bindings: tuple[SmbServiceBinding, ...] = field(repr=False)
    config: ExecutionConfig = field(repr=False)
    transport: SmbTransport = field(default_factory=NativeSmbTransport, repr=False)
    _timeout: float = field(init=False, repr=False)
    _output_limit: int = field(init=False, repr=False)

    def __post_init__(self) -> None:
        try:
            config = ExecutionConfig.model_validate(self.config.model_dump())
            if (
                not isinstance(self.bindings, tuple)
                or not 1 <= len(self.bindings) <= 64
            ):
                raise ValueError("finite observed SMB bindings required")
            bindings = tuple(
                SmbServiceBinding.model_validate(item) for item in self.bindings
            )
            if len({(item.host, item.service.port) for item in bindings}) != len(
                bindings
            ):
                raise ValueError("ambiguous SMB host/port binding")
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
                    or candidate.family is not ProtocolFamily.SMB
                    or item.service.port == 139
                    or item.service.protocol is None
                    or item.service.protocol.lower() == "netbios-ssn"
                ):
                    raise ValueError("normalized SMB service/numeric contact required")
            object.__setattr__(self, "bindings", bindings)
        except (ValueError, TypeError, AttributeError) as cause:
            raise ConfigurationError("Invalid trusted SMB metadata settings") from cause
        object.__setattr__(self, "_timeout", config.default_timeout_seconds)
        object.__setattr__(self, "_output_limit", config.max_output_bytes)

    @property
    def definition(self) -> AdapterDefinition:
        candidate = select_protocol_capability(self.bindings[0].service)
        assert candidate is not None
        return AdapterDefinition(
            adapter_id="native_smb",
            descriptor=candidate.descriptor,
            input_schema=SmbInput,
            output_schema=SmbOutput,
            parameter_target_fields=candidate.parameter_target_fields,
        )

    async def execute(
        self,
        request: ActionRequest,
        *,
        policy: ActionPolicyValidator,
        budgets: BudgetController,
        context: SmbContext,
        on_started: ExecutionStart | None = None,
    ) -> OperationResult[SmbOutput]:
        try:
            request = ActionRequest.model_validate(request)
            context = SmbContext.model_validate(context)
        except (ValueError, TypeError):
            return _invalid("Malformed SMB request or context")
        if (
            request.capability != CapabilityId.INSPECT_PROTOCOL
            or policy.budget_eligibility is not budgets
        ):
            return _invalid("SMB execution composition does not match request")
        selected = policy.registry.resolve(request.capability)
        if isinstance(selected, Failure):
            return selected
        if selected.value is not self:
            return _invalid("SMB adapter is not the current registry binding")
        approved = policy.validate(request)
        if isinstance(approved, Failure):
            return approved
        # Revalidate specialized input even if trusted registry metadata was wrong.
        try:
            parameters = SmbInput.model_validate(request.parameters)
        except (ValueError, TypeError):
            return _invalid("Unsupported SMB metadata parameters")
        subject = approved.value.scope_match
        if subject.canonical_target.kind not in ("ip", "hostname"):
            return _invalid("SMB metadata requires an explicit host or IP")
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
            return _invalid("SMB request has no observed service/contact binding")
        if request.asset_id not in (None, binding.service.asset_id):
            return _invalid("SMB service subject does not match request")
        candidate = select_protocol_capability(binding.service)
        if candidate is None or candidate.family is not ProtocolFamily.SMB:
            return _invalid("Observed service is not an unambiguous SMB candidate")
        contact = policy.scope_validator.validate_value(binding.address)
        if isinstance(contact, Failure):
            return contact
        # Numeric subjects cannot silently bind to a different address.
        if subject.canonical_target.kind == "ip" and host != binding.address:
            return _invalid("Numeric SMB subject must equal the contact address")
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
                return _invalid("SMB registry binding changed before contact")
            for value in (request.target, binding.address):
                scoped = policy.scope_validator.validate_value(value)
                if isinstance(scoped, Failure):
                    permit.release(ReservationOutcome.ABORTED)
                    return scoped
            timeout = min(self._timeout, budgets.state.remaining_seconds)
            if timeout <= 0:
                permit.release(ReservationOutcome.TIMEOUT)
                return Failure(
                    error=ToolTimeoutError("SMB deadline reached").to_error_info()
                )
            output_limit = min(self._output_limit, budgets.limits.max_output_bytes)
            try:
                async with asyncio.timeout(timeout):
                    raw = await self.transport.negotiate(
                        binding.address,
                        parameters.port,
                        timeout,
                        min(MAX_RESPONSE_BYTES, output_limit),
                    )
                    if type(raw) is not bytes or len(raw) > min(
                        MAX_RESPONSE_BYTES, output_limit
                    ):
                        raise ValueError("SMB capture bound")
                    metadata = parse_response(raw)
                    output = normalize(
                        raw, metadata, subject.canonical_target.value, binding, context
                    )
                    if len(output.model_dump_json().encode("utf-8")) > output_limit:
                        raise ValueError("SMB normalized output bound")
                    if budgets.state.remaining_seconds <= 0:
                        raise TimeoutError
                    permit.release(ReservationOutcome.COMPLETED)
                    return Success(value=output)
            except ToolExecutionError as cause:
                permit.release(ReservationOutcome.FAILED)
                return Failure(error=cause.to_error_info())
            except TimeoutError:
                permit.release(ReservationOutcome.TIMEOUT)
                return Failure(
                    error=ToolTimeoutError("SMB metadata timed out").to_error_info()
                )
            except OSError:
                permit.release(ReservationOutcome.FAILED)
                return Failure(
                    error=ToolExecutionError(
                        "SMB connection failed or closed"
                    ).to_error_info()
                )
            except (ValueError, TypeError, AttributeError):
                permit.release(ReservationOutcome.FAILED)
                return Failure(
                    error=ParserError(
                        "Malformed or oversized SMB negotiation metadata"
                    ).to_error_info()
                )

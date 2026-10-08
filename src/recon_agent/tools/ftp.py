"""Operational FTP metadata under current policy/scope/resources."""

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
from recon_agent.tools.ftp_models import (
    FtpContext,
    FtpInput,
    FtpOutput,
    FtpServiceBinding,
)
from recon_agent.tools.ftp_parser import MAX_CAPTURE_BYTES, normalize, parse_capture
from recon_agent.tools.native_ftp import FtpTransport, NativeFtpTransport
from recon_agent.tools.protocols import select_protocol_capability


def _invalid(message: str) -> Failure:
    return Failure(error=PlannerValidationError(message).to_error_info())


@dataclass(frozen=True, slots=True)
class FtpAdapter(ToolAdapter):
    """One current observed service and numeric contact per permitted attempt.

    Only the greeting and a fixed FEAT reply are read. No authentication,
    file/data operation, arbitrary command, process or session API exists.
    """

    bindings: tuple[FtpServiceBinding, ...] = field(repr=False)
    config: ExecutionConfig = field(repr=False)
    transport: FtpTransport = field(default_factory=NativeFtpTransport, repr=False)
    _timeout: float = field(init=False, repr=False)
    _output_limit: int = field(init=False, repr=False)

    def __post_init__(self) -> None:
        try:
            config = ExecutionConfig.model_validate(self.config.model_dump())
            if (
                not isinstance(self.bindings, tuple)
                or not 1 <= len(self.bindings) <= 64
            ):
                raise ValueError("finite observed FTP bindings required")
            bindings = tuple(
                FtpServiceBinding.model_validate(item) for item in self.bindings
            )
            if len({(item.host, item.service.port) for item in bindings}) != len(
                bindings
            ):
                raise ValueError("ambiguous FTP host/port binding")
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
                    or candidate.family is not ProtocolFamily.FTP
                ):
                    raise ValueError("normalized FTP service/numeric contact required")
            object.__setattr__(self, "bindings", bindings)
        except (ValueError, TypeError, AttributeError) as cause:
            raise ConfigurationError("Invalid trusted FTP metadata settings") from cause
        object.__setattr__(self, "_timeout", config.default_timeout_seconds)
        object.__setattr__(self, "_output_limit", config.max_output_bytes)

    @property
    def definition(self) -> AdapterDefinition:
        candidate = select_protocol_capability(self.bindings[0].service)
        assert candidate is not None
        return AdapterDefinition(
            adapter_id="native_ftp",
            descriptor=candidate.descriptor,
            input_schema=FtpInput,
            output_schema=FtpOutput,
            parameter_target_fields=candidate.parameter_target_fields,
        )

    async def execute(
        self,
        request: ActionRequest,
        *,
        policy: ActionPolicyValidator,
        budgets: BudgetController,
        context: FtpContext,
        on_started: ExecutionStart | None = None,
    ) -> OperationResult[FtpOutput]:
        try:
            request = ActionRequest.model_validate(request)
            context = FtpContext.model_validate(context)
        except (ValueError, TypeError):
            return _invalid("Malformed FTP request or context")
        if (
            request.capability != CapabilityId.INSPECT_PROTOCOL
            or policy.budget_eligibility is not budgets
        ):
            return _invalid("FTP execution composition does not match request")
        selected = policy.registry.resolve(request.capability)
        if isinstance(selected, Failure):
            return selected
        if selected.value is not self:
            return _invalid("FTP adapter is not the current registry binding")
        approved = policy.validate(request)
        if isinstance(approved, Failure):
            return approved
        # Revalidate specialized input even if trusted registry metadata was wrong.
        try:
            parameters = FtpInput.model_validate(request.parameters)
        except (ValueError, TypeError):
            return _invalid("Unsupported FTP metadata parameters")
        subject = approved.value.scope_match
        if subject.canonical_target.kind not in ("ip", "hostname"):
            return _invalid("FTP metadata requires an explicit host or IP")
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
            return _invalid("FTP request has no observed service/contact binding")
        if request.asset_id not in (None, binding.service.asset_id):
            return _invalid("FTP service subject does not match request")
        candidate = select_protocol_capability(binding.service)
        if candidate is None or candidate.family is not ProtocolFamily.FTP:
            return _invalid("Observed service is not an unambiguous FTP candidate")
        contact = policy.scope_validator.validate_value(binding.address)
        if isinstance(contact, Failure):
            return contact
        # Numeric subjects cannot silently bind to a different address.
        if subject.canonical_target.kind == "ip" and host != binding.address:
            return _invalid("Numeric FTP subject must equal the contact address")
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
                return _invalid("FTP registry binding changed before contact")
            for value in (request.target, binding.address):
                scoped = policy.scope_validator.validate_value(value)
                if isinstance(scoped, Failure):
                    permit.release(ReservationOutcome.ABORTED)
                    return scoped
            timeout = min(self._timeout, budgets.state.remaining_seconds)
            if timeout <= 0:
                permit.release(ReservationOutcome.TIMEOUT)
                return Failure(
                    error=ToolTimeoutError("FTP deadline reached").to_error_info()
                )
            output_limit = min(self._output_limit, budgets.limits.max_output_bytes)
            try:
                async with asyncio.timeout(timeout):
                    raw = await self.transport.inspect(
                        binding.address,
                        parameters.port,
                        timeout,
                        min(MAX_CAPTURE_BYTES, output_limit),
                    )
                    if type(raw) is not bytes or len(raw) > min(
                        MAX_CAPTURE_BYTES, output_limit
                    ):
                        raise ValueError("FTP capture bound")
                    metadata = parse_capture(raw)
                    output = normalize(
                        raw, metadata, subject.canonical_target.value, binding, context
                    )
                    if len(output.model_dump_json().encode("utf-8")) > output_limit:
                        raise ValueError("FTP normalized output bound")
                    if budgets.state.remaining_seconds <= 0:
                        raise TimeoutError
                    permit.release(
                        ReservationOutcome.FAILED
                        if output.errors
                        else ReservationOutcome.COMPLETED
                    )
                    return Success(value=output)
            except ToolExecutionError as cause:
                permit.release(ReservationOutcome.FAILED)
                return Failure(error=cause.to_error_info())
            except TimeoutError:
                permit.release(ReservationOutcome.TIMEOUT)
                return Failure(
                    error=ToolTimeoutError("FTP metadata timed out").to_error_info()
                )
            except OSError:
                permit.release(ReservationOutcome.FAILED)
                return Failure(
                    error=ToolExecutionError(
                        "FTP connection failed or closed"
                    ).to_error_info()
                )
            except (ValueError, TypeError, AttributeError):
                permit.release(ReservationOutcome.FAILED)
                return Failure(
                    error=ParserError(
                        "Malformed or oversized FTP metadata"
                    ).to_error_info()
                )

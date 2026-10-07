"""Fixed common-file inspection through current registry/policy/scope/budgets."""

import asyncio
from dataclasses import dataclass, field
from ipaddress import ip_address
from time import monotonic
from typing import Literal
from urllib.parse import urljoin, urlsplit, urlunsplit

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
from recon_agent.domain.capabilities import (
    CapabilityDescriptor,
    CapabilityId,
    RiskClass,
)
from recon_agent.execution.lifecycle import ExecutionStart, notify_execution_start
from recon_agent.policy.actions import ActionPolicyValidator
from recon_agent.policy.budgets import BudgetController
from recon_agent.policy.scope import ScopeMatch
from recon_agent.tools.base import AdapterDefinition, ToolAdapter
from recon_agent.tools.common_files_models import (
    COMMON_PATHS,
    CommonFileFact,
    CommonFilesContext,
    CommonFilesInput,
    CommonFilesOutput,
    CommonPath,
    ContactBinding,
    HttpResponse,
    RedirectFact,
)
from recon_agent.tools.common_files_parser import normalize, response_fact
from recon_agent.tools.native_http import HttpTransport, NativeHttpTransport

MAX_REDIRECTS = 2
MAX_BODY_BYTES = 16_384


def _invalid(message: str) -> Failure:
    return Failure(error=PlannerValidationError(message).to_error_info())


def _url(value: str) -> str:
    # Centralized scope parsing happens first at each caller. This profile removes
    # unsupported wire representations; it supplies no separate membership rules.
    if len(value) > 2048 or any(ord(c) < 33 or ord(c) > 126 for c in value):
        raise ValueError("unsupported URL representation")
    parts = urlsplit(value)
    if parts.scheme not in ("http", "https") or not parts.hostname:
        raise ValueError("HTTP endpoint required")
    if (
        parts.username is not None
        or parts.password is not None
        or parts.fragment
        or "\\" in value
    ):
        raise ValueError("unsupported URL representation")
    host = parts.hostname
    authority = f"[{host}]" if ":" in host else host
    if parts.port and parts.port != (443 if parts.scheme == "https" else 80):
        authority += f":{parts.port}"
    return urlunsplit((parts.scheme, authority, parts.path or "/", parts.query, ""))


@dataclass(frozen=True, slots=True)
class CommonFilesAdapter(ToolAdapter):
    """Operator bindings pin contacts. Planner input is strictly empty.

    One action reserves all finite possible binding hosts/addresses once. Its at
    most nine GETs are sequential and paced; no discovered URL becomes a request.
    The caller retains returned memory evidence and records lifecycle/subjects.
    """

    bindings: tuple[ContactBinding, ...] = field(repr=False)
    config: ExecutionConfig = field(repr=False)
    transport: HttpTransport = field(default_factory=NativeHttpTransport, repr=False)
    _timeout: float = field(init=False, repr=False)
    _output_limit: int = field(init=False, repr=False)

    def __post_init__(self) -> None:
        try:
            snapshot = ExecutionConfig.model_validate(self.config.model_dump())
            if (
                not isinstance(self.bindings, tuple)
                or not 1 <= len(self.bindings) <= 64
            ):
                raise ValueError("finite contact bindings required")
            bindings = tuple(
                ContactBinding.model_validate(item) for item in self.bindings
            )
            if len({item.host for item in bindings}) != len(bindings):
                raise ValueError("duplicate contact binding")
            for item in bindings:
                address = ip_address(item.address)
                if (
                    str(address) != item.address
                    or "%" in item.address
                    or getattr(address, "ipv4_mapped", None)
                ):
                    raise ValueError("canonical numeric contacts required")
                if (
                    item.host != item.host.lower()
                    or item.host.endswith(".")
                    or "://" in item.host
                ):
                    raise ValueError("canonical host bindings required")
            object.__setattr__(self, "bindings", bindings)
        except (ValueError, TypeError, AttributeError) as cause:
            raise ConfigurationError("Invalid trusted common-file settings") from cause
        object.__setattr__(self, "_timeout", snapshot.default_timeout_seconds)
        object.__setattr__(self, "_output_limit", snapshot.max_output_bytes)

    @property
    def definition(self) -> AdapterDefinition:
        return AdapterDefinition(
            adapter_id="native_common_files",
            descriptor=CapabilityDescriptor(
                capability=CapabilityId.INSPECT_COMMON_FILES,
                description="Inspect fixed common web files as bounded untrusted metadata",
                risk_class=RiskClass.ACTIVE_SAFE,
            ),
            input_schema=CommonFilesInput,
            output_schema=CommonFilesOutput,
            parameter_target_fields=(),
        )

    def _contact(
        self, url: str, policy: ActionPolicyValidator
    ) -> OperationResult[tuple[str, str, tuple[ScopeMatch, ...]]]:
        scoped = policy.scope_validator.validate_value(url)
        if isinstance(scoped, Failure):
            return scoped
        try:
            canonical = _url(scoped.value.canonical_target.value)
            host = urlsplit(canonical).hostname
            try:
                address = str(ip_address(host or ""))
                if not any(
                    item.host == host and item.address == address
                    for item in self.bindings
                ):
                    return _invalid(
                        "Numeric HTTP endpoint has no trusted contact binding"
                    )
            except ValueError:
                binding = next(
                    (item for item in self.bindings if item.host == host), None
                )
                if binding is None:
                    return _invalid("HTTP endpoint has no trusted numeric binding")
                address = binding.address
        except (ValueError, TypeError):
            return _invalid("Unsupported common-file HTTP endpoint")
        contact = policy.scope_validator.validate_value(address)
        if isinstance(contact, Failure):
            return contact
        return Success(value=(canonical, address, (scoped.value, contact.value)))

    async def execute(
        self,
        request: ActionRequest,
        *,
        policy: ActionPolicyValidator,
        budgets: BudgetController,
        context: CommonFilesContext,
        on_started: ExecutionStart | None = None,
    ) -> OperationResult[CommonFilesOutput]:
        try:
            request = ActionRequest.model_validate(request)
            context = CommonFilesContext.model_validate(context)
        except (ValueError, TypeError):
            return _invalid("Malformed common-file request or context")
        if (
            request.capability != CapabilityId.INSPECT_COMMON_FILES
            or policy.budget_eligibility is not budgets
            or request.asset_id not in (None, context.asset_id)
        ):
            return _invalid("Common-file execution composition does not match request")
        selected = policy.registry.resolve(request.capability)
        if isinstance(selected, Failure):
            return selected
        if selected.value is not self:
            return _invalid("Common-file adapter is not the current registry binding")
        approved = policy.validate(request)
        if isinstance(approved, Failure):
            return approved
        initial = self._contact(
            approved.value.scope_match.canonical_target.value, policy
        )
        if isinstance(initial, Failure):
            return initial
        endpoint = urlsplit(initial.value[0])
        origin = urlunsplit((endpoint.scheme, endpoint.netloc, "", "", ""))
        matches = list(initial.value[2])
        # Charge possible redirect contacts before execution, including unused ones.
        for binding in self.bindings:
            for value in (binding.host, binding.address):
                match = policy.scope_validator.validate_value(value)
                if isinstance(match, Failure):
                    return match
                if match.value.host_identity != value:
                    return _invalid("Unsupported trusted HTTP host binding")
                matches.append(match.value)
        reserved = budgets.reserve(
            approved.value.model_copy(
                update={
                    "parameter_scope_matches": tuple(matches),
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
            timeout = min(self._timeout, budgets.state.remaining_seconds)
            if timeout <= 0:
                permit.release(ReservationOutcome.TIMEOUT)
                return Failure(
                    error=ToolTimeoutError(
                        "Common-file deadline reached"
                    ).to_error_info()
                )
            deadline = monotonic() + timeout
            interval = max(
                1.0,
                budgets.limits.capability_rate_window_seconds
                / budgets.limits.capability_rate_actions,
            )
            next_request = 0.0
            files: list[CommonFileFact] = []
            try:
                async with asyncio.timeout(timeout):
                    for path in COMMON_PATHS:
                        # The typed constant tuple is the ONLY initial path source.
                        inspected = await self._inspect(
                            path,
                            origin + path,
                            policy,
                            budgets,
                            deadline,
                            interval,
                            next_request,
                        )
                        if isinstance(inspected, Failure):
                            permit.release(ReservationOutcome.ABORTED)
                            return inspected
                        fact, next_request = inspected
                        files.append(fact)
                    output = normalize(initial.value[0], tuple(files), context)
                    if len(output.model_dump_json().encode()) > min(
                        self._output_limit, budgets.limits.max_output_bytes
                    ):
                        raise ValueError("normalized output bound exceeded")
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
                        "Common-file deadline reached"
                    ).to_error_info()
                )
            except (ValueError, TypeError, AttributeError):
                permit.release(ReservationOutcome.FAILED)
                return Failure(
                    error=ParserError(
                        "Malformed or oversized common-file output"
                    ).to_error_info()
                )

    async def _inspect(
        self,
        path: CommonPath,
        requested: str,
        policy: ActionPolicyValidator,
        budgets: BudgetController,
        deadline: float,
        interval: float,
        next_request: float,
    ) -> tuple[CommonFileFact, float] | Failure:
        current = requested
        redirects: list[RedirectFact] = []
        seen = {current}
        response: HttpResponse | None = None
        address = None
        errors = []
        body_limit = min(
            MAX_BODY_BYTES,
            self._output_limit // 3,
            budgets.limits.max_output_bytes // 3,
        )
        if body_limit < 1:
            return Failure(
                error=ParserError(
                    "Common-file body allowance unavailable"
                ).to_error_info()
            )
        for hop in range(MAX_REDIRECTS + 1):
            if next_request > monotonic():
                await asyncio.sleep(next_request - monotonic())
            # Scope/address rechecks occur after pacing immediately before contact.
            contact = self._contact(current, policy)
            if isinstance(contact, Failure):
                return contact
            current, address, _ = contact.value
            remaining = min(
                deadline - monotonic(), budgets.state.remaining_seconds, 10.0
            )
            if remaining <= 0:
                raise TimeoutError
            response = None
            try:
                async with asyncio.timeout(remaining):
                    response = HttpResponse.model_validate(
                        await self.transport.get(
                            current, address, remaining, body_limit
                        )
                    )
                next_request = monotonic() + interval
                if len(response.body) > body_limit:
                    response = response.model_copy(
                        update={
                            "body": response.body[:body_limit],
                            "truncated": True,
                        }
                    )
            except TimeoutError:
                errors.append(
                    ToolTimeoutError("Common-file request timed out").to_error_info()
                )
                break
            except OSError:
                errors.append(
                    ToolExecutionError("Common-file connection failed").to_error_info()
                )
                break
            except (ValueError, TypeError):
                errors.append(ParserError("Malformed HTTP response").to_error_info())
                break
            finally:
                next_request = monotonic() + interval
            if budgets.state.remaining_seconds <= 0:
                raise TimeoutError
            if (
                response.truncated
                or response.status_code not in (301, 302, 303, 307, 308)
                or response.location is None
            ):
                break
            destination = None
            rejection = None
            try:
                destination = urljoin(current, response.location)
                checked = self._contact(destination, policy)
                if isinstance(checked, Failure):
                    rejection = checked.error
                else:
                    destination = checked.value[0]
                    parts = urlsplit(destination)
                    if (
                        parts.path != path
                        or parts.query
                        or (
                            urlsplit(current).scheme == "https"
                            and parts.scheme == "http"
                        )
                    ):
                        rejection = PlannerValidationError(
                            "Redirect leaves the trusted common-file profile"
                        ).to_error_info()
            except (ValueError, TypeError):
                rejection = ParserError(
                    "Malformed common-file redirect"
                ).to_error_info()
            outcome: Literal["followed", "rejected", "limit", "loop"] = (
                "rejected"
                if rejection
                else "loop"
                if destination in seen
                else "limit"
                if hop == MAX_REDIRECTS
                else "followed"
            )
            redirects.append(
                RedirectFact(
                    url=current,
                    status_code=response.status_code,
                    location=response.location,
                    destination=destination,
                    outcome=outcome,
                    rejection_error=rejection,
                )
            )
            if outcome != "followed":
                errors.append(
                    ParserError(
                        "Common-file redirect rejected, loop or limit reached"
                    ).to_error_info()
                )
                break
            assert destination is not None
            seen.add(destination)
            current = destination
        fact = response_fact(
            path, requested, current, address, response, tuple(redirects)
        )
        if errors:
            fact = fact.model_copy(update={"errors": fact.errors + tuple(errors)})
        return fact, next_request

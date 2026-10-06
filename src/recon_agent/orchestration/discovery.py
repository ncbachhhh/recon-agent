"""Finite M2 integration proof. No provider, planner, retry or autonomous loop."""

import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Annotated, Literal

from pydantic import Field, JsonValue

from recon_agent.core.audit import AuditEvent, AuditEventType
from recon_agent.core.errors import (
    CancelledError,
    ErrorCode,
    ErrorInfo,
    PlannerValidationError,
    StateTransitionError,
)
from recon_agent.core.results import Failure, OperationResult, Success
from recon_agent.domain import (
    ActionRequest,
    ActionResult,
    ReconState,
    ReconStateMachine,
)
from recon_agent.domain._base import Record
from recon_agent.domain.budgets import BudgetSnapshot
from recon_agent.domain.capabilities import CapabilityId
from recon_agent.domain.observations import Observation
from recon_agent.policy import (
    ActionCanonicalizer,
    ActionDeduplicator,
    ActionPolicyConfig,
    ActionPolicyValidator,
    BudgetController,
    ScopeValidator,
)
from recon_agent.tools import AdapterRegistration, ToolRegistry
from recon_agent.tools.dns import DnsAdapter
from recon_agent.tools.dns_models import DnsContext, DnsOutput
from recon_agent.tools.dnsx import DnsxAdapter
from recon_agent.tools.dnsx_models import DnsxContext, DnsxOutput
from recon_agent.tools.httpx import HttpxAdapter
from recon_agent.tools.httpx_models import HttpProbeOutput, HttpxContext
from recon_agent.tools.naabu import NaabuAdapter
from recon_agent.tools.naabu_models import NaabuContext, PortDiscoveryOutput
from recon_agent.tools.nmap import NmapAdapter
from recon_agent.tools.nmap_models import (
    DiscoveredPortSelection,
    NmapContext,
    ServiceFingerprintOutput,
)
from recon_agent.tools.subfinder import SubfinderAdapter
from recon_agent.tools.subfinder_models import SubdomainOutput, SubfinderContext

DiscoveryOutput = (
    DnsOutput
    | SubdomainOutput
    | DnsxOutput
    | HttpProbeOutput
    | PortDiscoveryOutput
    | ServiceFingerprintOutput
)
_Identity = Annotated[
    str, Field(min_length=1, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$")
]
_FATAL = frozenset(
    {
        ErrorCode.BUDGET_EXHAUSTED,
        ErrorCode.SCOPE_REJECTED,
        ErrorCode.PLANNER_VALIDATION_FAILED,
        ErrorCode.STATE_TRANSITION_INVALID,
        ErrorCode.CONFIGURATION_INVALID,
    }
)


class DiscoveryRequest(Record):
    """Explicit one-root workflow input; unique run IDs identify attempts only."""

    run_id: _Identity
    session_id: _Identity
    target: Annotated[str, Field(min_length=1, max_length=254)]


@dataclass(frozen=True, slots=True)
class DiscoveryReport:
    state: ReconState
    outputs: tuple[DiscoveryOutput, ...]
    audit_events: tuple[AuditEvent, ...]
    skipped_action_ids: tuple[str, ...]


@dataclass(slots=True)
class DiscoveryWorkflow:
    """Single-owner sequential workflow over explicitly composed trusted services.

    Adapters retain reservation/contact/runner ownership. Only their post-reservation
    callback records STARTED. A fatal Failure leaves inspectable state and events;
    ordinary tool failures remain terminal records and independent stages continue.
    """

    registry: ToolRegistry
    scope_validator: ScopeValidator
    budgets: BudgetController
    state_machine: ReconStateMachine
    policy_config: ActionPolicyConfig
    now: Callable[[], datetime] = field(default=lambda: datetime.now(UTC), repr=False)
    _events: list[AuditEvent] = field(default_factory=list, init=False, repr=False)
    _outputs: list[DiscoveryOutput] = field(
        default_factory=list, init=False, repr=False
    )
    _skipped: list[str] = field(default_factory=list, init=False, repr=False)
    _running: bool = field(default=False, init=False, repr=False)

    @property
    def report(self) -> DiscoveryReport:
        """Detached in-memory evidence snapshots, including after a fatal stop."""
        return DiscoveryReport(
            self.state_machine.state,
            tuple(o.model_copy(deep=True) for o in self._outputs),
            tuple(e.model_copy(deep=True) for e in self._events),
            tuple(self._skipped),
        )

    def _event(
        self,
        run: DiscoveryRequest,
        kind: AuditEventType,
        *,
        action_id: str | None = None,
        execution_id: str | None = None,
        error: ErrorInfo | None = None,
    ) -> None:
        self._events.append(
            AuditEvent(
                event_id=f"{run.run_id}:event:{len(self._events)}",
                event_type=kind,
                timestamp=self.now(),
                session_id=run.session_id,
                action_id=action_id,
                execution_id=execution_id,
                message="Deterministic discovery workflow outcome",
                error=error,
            )
        )

    def _policy(
        self, registry: ToolRegistry
    ) -> tuple[ActionPolicyValidator, ActionDeduplicator]:
        dedup = ActionDeduplicator(
            ActionCanonicalizer(registry, self.scope_validator),
            self.state_machine,
        )
        return ActionPolicyValidator(
            registry,
            self.scope_validator,
            self.policy_config,
            self.budgets,
            dedup,
        ), dedup

    async def _dispatch(
        self,
        run: DiscoveryRequest,
        capability: CapabilityId,
        target: str,
        parameters: dict[str, JsonValue],
        *,
        registry: ToolRegistry | None = None,
    ) -> OperationResult[None]:
        registry = registry or self.registry
        policy, dedup = self._policy(registry)
        action_id = f"{run.run_id}:action:{len(self._events)}"
        execution_id = f"{action_id}:execution"
        asset_id = f"{execution_id}:asset"
        request = ActionRequest(
            id=action_id,
            capability=capability.value,
            target=target,
            parameters=parameters,
            reason="Explicit deterministic M2 discovery stage",
        )
        approved = policy.validate(request)
        inspected = dedup.inspect(request)
        if isinstance(inspected, Success) and not inspected.value.eligible:
            self._skipped.append(action_id)
            self._event(
                run,
                AuditEventType.POLICY_ACTION_REJECTED,
                action_id=action_id,
                error=PlannerValidationError(
                    "Equivalent discovery action skipped"
                ).to_error_info(),
            )
            return Success[None](value=None)
        if isinstance(approved, Failure):
            recorded = self.state_machine.record_action_requested(
                request, recorded_at=self.now()
            )
        else:
            recorded = dedup.record_request(request, recorded_at=self.now())
        if isinstance(recorded, Failure):
            return recorded
        if isinstance(approved, Failure):
            return self._reject(run, request, approved.error)
        marked = self.state_machine.mark_action_approved(
            action_id,
            policy_reference=f"{action_id}:policy",
            recorded_at=self.now(),
        )
        if isinstance(marked, Failure):
            return marked
        self._event(run, AuditEventType.POLICY_ACTION_APPROVED, action_id=action_id)
        selected = registry.resolve(capability)
        if isinstance(selected, Failure):
            return self._reject(run, request, selected.error)
        started = False

        def on_started() -> OperationResult[None]:
            nonlocal started
            changed = self.state_machine.mark_action_started(
                action_id,
                execution_id=execution_id,
                recorded_at=self.now(),
            )
            if isinstance(changed, Failure):
                return changed
            started = True
            self._event(
                run,
                AuditEventType.TOOL_EXECUTION_STARTED,
                action_id=action_id,
                execution_id=execution_id,
            )
            return Success[None](value=None)

        context = DnsContext(
            asset_id=asset_id, execution_id=execution_id, collected_at=self.now()
        )
        adapter = selected.value
        try:
            if capability is CapabilityId.RESOLVE_DNS and isinstance(
                adapter, DnsAdapter
            ):
                result: (
                    Success[DnsOutput]
                    | Success[SubdomainOutput]
                    | Success[DnsxOutput]
                    | Success[HttpProbeOutput]
                    | Success[PortDiscoveryOutput]
                    | Success[ServiceFingerprintOutput]
                    | Failure
                ) = await adapter.execute(
                    request,
                    policy=policy,
                    budgets=self.budgets,
                    context=context,
                    on_started=on_started,
                )
            elif capability is CapabilityId.ENUMERATE_SUBDOMAINS and isinstance(
                adapter, SubfinderAdapter
            ):
                result = await adapter.execute(
                    request,
                    policy=policy,
                    budgets=self.budgets,
                    context=SubfinderContext(**context.model_dump()),
                    on_started=on_started,
                )
            elif capability is CapabilityId.VERIFY_DNS and isinstance(
                adapter, DnsxAdapter
            ):
                result = await adapter.execute(
                    request,
                    policy=policy,
                    budgets=self.budgets,
                    context=DnsxContext(**context.model_dump()),
                    on_started=on_started,
                )
            elif capability is CapabilityId.PROBE_HTTP and isinstance(
                adapter, HttpxAdapter
            ):
                result = await adapter.execute(
                    request,
                    policy=policy,
                    budgets=self.budgets,
                    context=HttpxContext(**context.model_dump()),
                    on_started=on_started,
                )
            elif capability is CapabilityId.DISCOVER_PORTS and isinstance(
                adapter, NaabuAdapter
            ):
                result = await adapter.execute(
                    request,
                    policy=policy,
                    budgets=self.budgets,
                    context=NaabuContext(**context.model_dump()),
                    on_started=on_started,
                )
            elif capability is CapabilityId.FINGERPRINT_SERVICES and isinstance(
                adapter, NmapAdapter
            ):
                result = await adapter.execute(
                    request,
                    policy=policy,
                    budgets=self.budgets,
                    context=NmapContext(**context.model_dump()),
                    on_started=on_started,
                )
            else:
                result = Failure(
                    error=PlannerValidationError(
                        "Unsupported M2 adapter binding"
                    ).to_error_info()
                )
        except asyncio.CancelledError:
            changed = self.state_machine.record_action_result(
                ActionResult(
                    id=f"{action_id}:result",
                    action_id=action_id,
                    status="cancelled",
                    recorded_at=self.now(),
                    execution_ids=(execution_id,) if started else (),
                    error=CancelledError("Discovery cancelled").to_error_info(),
                )
            )
            if isinstance(changed, Failure):
                self._event(run, AuditEventType.SESSION_FAILED, error=changed.error)
            raise
        if isinstance(result, Failure):
            if result.error.code is ErrorCode.STATE_TRANSITION_INVALID:
                return result
            if not started:
                return self._reject(run, request, result.error)
            status: Literal[
                "completed", "partial", "failed", "timeout", "cancelled"
            ] = "timeout" if result.error.code is ErrorCode.TOOL_TIMEOUT else "failed"
            # Policy denial after reservation is an abort, never a failed tool fact.
            if result.error.code in (
                ErrorCode.SCOPE_REJECTED,
                ErrorCode.BUDGET_EXHAUSTED,
                ErrorCode.PLANNER_VALIDATION_FAILED,
            ):
                status = "cancelled"
                error = CancelledError(
                    "Discovery execution aborted by policy"
                ).to_error_info()
            else:
                error = result.error
            terminal = ActionResult(
                id=f"{action_id}:result",
                action_id=action_id,
                status=status,
                recorded_at=self.now(),
                execution_ids=(execution_id,),
                error=error,
            )
            committed = self.state_machine.record_action_result(terminal)
        else:
            if not started:
                return Failure(
                    error=StateTransitionError(
                        "Adapter did not record execution start"
                    ).to_error_info()
                )
            output = result.value
            status = (
                output.status
                if isinstance(
                    output,
                    (
                        DnsxOutput,
                        HttpProbeOutput,
                        PortDiscoveryOutput,
                        ServiceFingerprintOutput,
                    ),
                )
                else "completed"
            )
            errors = (
                output.errors
                if isinstance(
                    output,
                    (
                        DnsxOutput,
                        HttpProbeOutput,
                        PortDiscoveryOutput,
                        ServiceFingerprintOutput,
                    ),
                )
                else ()
            )
            terminal = ActionResult(
                id=f"{action_id}:result",
                action_id=action_id,
                status=status,
                recorded_at=self.now(),
                execution_ids=(execution_id,),
                observations=output.observations,
                evidence=output.evidence,
                error=errors[0] if errors else None,
            )
            committed = self.state_machine.record_action_result(
                terminal,
                assets=(output.asset,),
                hosts=output.hosts
                if isinstance(output, (PortDiscoveryOutput, ServiceFingerprintOutput))
                else (),
                services=output.services
                if isinstance(output, (PortDiscoveryOutput, ServiceFingerprintOutput))
                else (),
                endpoints=output.endpoints
                if isinstance(output, HttpProbeOutput)
                else (),
            )
            if isinstance(committed, Success):
                self._outputs.append(output)
        if isinstance(committed, Failure):
            return committed
        self._event(
            run,
            AuditEventType.TOOL_EXECUTION_COMPLETED
            if terminal.status == "completed"
            else AuditEventType.TOOL_EXECUTION_FAILED,
            action_id=action_id,
            execution_id=execution_id,
            error=result.error if isinstance(result, Failure) else terminal.error,
        )
        sampled = self.state_machine.record_budget_snapshot(
            BudgetSnapshot(
                id=f"{action_id}:budget",
                recorded_at=self.now(),
                state=self.budgets.state,
            )
        )
        if isinstance(sampled, Failure):
            return sampled
        return (
            result
            if isinstance(result, Failure) and result.error.code in _FATAL
            else Success[None](value=None)
        )

    def _reject(
        self, run: DiscoveryRequest, request: ActionRequest, error: ErrorInfo
    ) -> OperationResult[None]:
        committed = self.state_machine.record_action_result(
            ActionResult(
                id=f"{request.id}:result",
                action_id=request.id,
                status="rejected",
                recorded_at=self.now(),
                error=error,
            )
        )
        if isinstance(committed, Failure):
            return committed
        self._event(
            run,
            AuditEventType.POLICY_ACTION_REJECTED,
            action_id=request.id,
            error=error,
        )
        if error.code is ErrorCode.BUDGET_EXHAUSTED:
            self._event(
                run, AuditEventType.BUDGET_EXHAUSTED, action_id=request.id, error=error
            )
        return (
            Failure(error=error) if error.code in _FATAL else Success[None](value=None)
        )

    def _observations(
        self,
        root: str,
        capability: CapabilityId,
        source: str,
    ) -> tuple[Observation, ...]:
        state = self.state_machine.state
        assets = {a.id for a in state.assets if a.value == root}
        requests = {
            a.id for a in state.action_requests if a.capability == capability.value
        }
        return tuple(
            o
            for result in state.action_results
            if result.action_id in requests
            and result.status in ("completed", "partial")
            for o in result.observations
            if o.asset_id in assets and o.source == source
        )

    def _candidates(
        self, run: DiscoveryRequest, root: str
    ) -> OperationResult[tuple[str, ...]]:
        names = {root}
        for observation in self._observations(
            root, CapabilityId.ENUMERATE_SUBDOMAINS, "subfinder"
        ):
            host = observation.data.get("hostname")
            if isinstance(host, str):
                checked = self.scope_validator.validate_value(host)
                if isinstance(checked, Success):
                    names.add(checked.value.canonical_target.value)
                else:
                    self._event(
                        run, AuditEventType.POLICY_ACTION_REJECTED, error=checked.error
                    )
        if len(names) > 64:
            return Failure(
                error=PlannerValidationError(
                    "Discovery candidate bound exceeded"
                ).to_error_info()
            )
        return Success(value=tuple(sorted(names)))

    def _selections(
        self, root: str
    ) -> OperationResult[tuple[DiscoveredPortSelection, ...]]:
        ports: dict[str, set[int]] = {}
        evidence: dict[str, set[str]] = {}
        for observation in self._observations(
            root, CapabilityId.DISCOVER_PORTS, "naabu"
        ):
            address, port = observation.data.get("host"), observation.data.get("port")
            if (
                isinstance(address, str)
                and type(port) is int
                and observation.data.get("state") == "open"
            ):
                ports.setdefault(address, set()).add(port)
                evidence.setdefault(address, set()).update(observation.evidence_ids)
        if len(ports) > 64 or any(
            len(values) > 128 or len(evidence[address]) > 128
            for address, values in ports.items()
        ):
            return Failure(
                error=PlannerValidationError(
                    "Fingerprint selection bound exceeded"
                ).to_error_info()
            )
        return Success(
            value=tuple(
                DiscoveredPortSelection(
                    address=address,
                    ports=tuple(sorted(values)),
                    evidence_ids=tuple(sorted(evidence[address])),
                )
                for address, values in sorted(ports.items())
            )
        )

    async def run(self, request: DiscoveryRequest) -> OperationResult[DiscoveryReport]:
        """Resolve, enumerate, verify, probe, discover, then fingerprint finite ports.

        Independent tool failures continue; policy/resource/state failures stop.
        Reusing a run ID is forbidden; semantic repeats use a new ID and are skipped.
        """
        try:
            request = DiscoveryRequest.model_validate(request)
        except (ValueError, TypeError):
            return Failure(
                error=PlannerValidationError(
                    "Invalid discovery request"
                ).to_error_info()
            )
        if self._running or any(
            a.id.startswith(f"{request.run_id}:action:")
            for a in self.state_machine.state.action_requests
        ):
            return Failure(
                error=StateTransitionError(
                    "Discovery run is active or reused"
                ).to_error_info()
            )
        self._running = True
        self._events.clear()
        self._outputs.clear()
        self._skipped.clear()
        try:
            self._event(request, AuditEventType.SESSION_STARTED)
            for capability in (
                CapabilityId.RESOLVE_DNS,
                CapabilityId.ENUMERATE_SUBDOMAINS,
            ):
                result = await self._dispatch(request, capability, request.target, {})
                if isinstance(result, Failure):
                    return self._stop(request, result)
            matched = self.scope_validator.validate_value(request.target)
            if isinstance(matched, Failure):
                return self._stop(request, matched)
            root = matched.value.canonical_target.value
            candidates = self._candidates(request, root)
            if isinstance(candidates, Failure):
                return self._stop(request, candidates)
            for capability in (
                CapabilityId.VERIFY_DNS,
                CapabilityId.PROBE_HTTP,
                CapabilityId.DISCOVER_PORTS,
            ):
                result = await self._dispatch(
                    request, capability, root, {"candidates": list(candidates.value)}
                )
                if isinstance(result, Failure):
                    return self._stop(request, result)
            selections = self._selections(root)
            if isinstance(selections, Failure):
                return self._stop(request, selections)
            if selections.value:
                selected = self.registry.resolve(CapabilityId.FINGERPRINT_SERVICES)
                registry = self.registry
                if isinstance(selected, Success) and isinstance(
                    selected.value, NmapAdapter
                ):
                    adapter = selected.value.with_selections(selections.value)
                    registrations = []
                    for entry in self.registry.catalog():
                        binding = self.registry.resolve(entry.capability)
                        if isinstance(binding, Success):
                            registrations.append(
                                AdapterRegistration(
                                    adapter
                                    if entry.capability
                                    is CapabilityId.FINGERPRINT_SERVICES
                                    else binding.value,
                                    entry.availability,
                                )
                            )
                    registry = ToolRegistry(registrations)
                for selection in selections.value:
                    result = await self._dispatch(
                        request,
                        CapabilityId.FINGERPRINT_SERVICES,
                        selection.address,
                        {"ports": list(selection.ports)},
                        registry=registry,
                    )
                    if isinstance(result, Failure):
                        return self._stop(request, result)
            self._event(request, AuditEventType.SESSION_COMPLETED)
            return Success(value=self.report)
        except asyncio.CancelledError:
            self._event(request, AuditEventType.SESSION_CANCELLED)
            raise
        finally:
            self._running = False

    def _stop(self, request: DiscoveryRequest, failure: Failure) -> Failure:
        self._event(request, AuditEventType.SESSION_STOPPED, error=failure.error)
        return failure

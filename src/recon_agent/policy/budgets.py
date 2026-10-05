"""Local atomic resource reservations; no execution, waiting or authorization."""

from __future__ import annotations

from asyncio import CancelledError
from collections.abc import Callable
from dataclasses import dataclass, field
from math import isfinite
from threading import Lock
from time import monotonic
from types import TracebackType
from typing import Self

from pydantic import BaseModel, ConfigDict, InstanceOf, ValidationError

from recon_agent.core.config.models import (
    ExecutionConfig,
    PositiveInt,
    PositiveSeconds,
)
from recon_agent.core.errors import BudgetExhaustedError, ConfigurationError
from recon_agent.core.results import Failure, OperationResult, Success
from recon_agent.domain.budgets import BudgetState, ReservationOutcome
from recon_agent.domain.capabilities import CapabilityId
from recon_agent.policy.actions import ApprovedAction
from recon_agent.tools import ToolRegistry


class ExecutionBudget(BaseModel):
    """Trusted immutable session limits, separate from consumed resource state."""

    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        frozen=True,
        validate_default=True,
        revalidate_instances="always",
        hide_input_in_errors=True,
    )
    max_actions: PositiveInt = 100
    max_concurrency: PositiveInt = 1
    max_actions_per_host: PositiveInt = 10
    capability_rate_actions: PositiveInt = 1
    capability_rate_window_seconds: PositiveSeconds = 1.0
    max_duration_seconds: PositiveSeconds = 600.0
    max_output_bytes: PositiveInt = 1_048_576
    max_session_output_bytes: PositiveInt = 16_777_216

    @classmethod
    def from_config(cls, config: ExecutionConfig) -> Self:
        validated = ExecutionConfig.model_validate(config.model_dump())
        return cls.model_validate(
            {name: getattr(validated, name) for name in cls.model_fields}
        )


@dataclass(slots=True)
class _Usage:
    started: float
    last_time: float
    clock_failed: bool = False
    actions: int = 0
    output_bytes: int = 0
    hosts: dict[str, int] = field(default_factory=dict)
    rates: dict[CapabilityId, tuple[float, ...]] = field(default_factory=dict)
    active: set[object] = field(default_factory=set)
    entered: set[object] = field(default_factory=set)
    outcomes: dict[ReservationOutcome, int] = field(default_factory=dict)


def _denied(message: str) -> Failure:
    return Failure(error=BudgetExhaustedError(message).to_error_info())


def _clock_value(clock: Callable[[], float]) -> float:
    value = clock()
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not isfinite(value)
    ):
        raise ValueError("Invalid monotonic clock")
    return float(value)


@dataclass(frozen=True, slots=True, init=False)
class BudgetController:
    """One session-local locked ledger, explicitly composed by trusted code.

    check is advisory and consumes nothing. reserve repeats all limits atomically.
    Every granted reservation spends an attempt, host/rate counts and worst-case
    output allowance permanently, even if aborted/failed/cancelled/timed out.
    Only concurrency is released. There is no refund, reset or limit-update API.
    """

    _limits: ExecutionBudget
    _clock: Callable[[], float]
    _lock: Lock
    _usage: _Usage

    def __init__(
        self,
        limits: ExecutionBudget,
        registry: ToolRegistry,
        *,
        clock: Callable[[], float] = monotonic,
    ) -> None:
        try:
            validated = ExecutionBudget.model_validate(limits)
            started = _clock_value(clock)
        except Exception as cause:
            raise ConfigurationError("Invalid execution budget or clock") from cause
        object.__setattr__(self, "_limits", validated)
        object.__setattr__(self, "_clock", clock)
        object.__setattr__(self, "_lock", Lock())
        object.__setattr__(
            self,
            "_usage",
            _Usage(
                started=started,
                last_time=started,
                rates={capability: () for capability in registry.list_capabilities()},
            ),
        )

    @property
    def limits(self) -> ExecutionBudget:
        return self._limits

    def _now(self) -> float:
        # A broken clock fails closed permanently rather than extending the session.
        usage = self._usage
        try:
            now = _clock_value(self._clock)
            if now < usage.last_time:
                raise ValueError("Monotonic clock regressed")
        except Exception:
            usage.clock_failed = True
            return usage.last_time
        usage.last_time = now
        return now

    def _remaining_seconds(self, now: float) -> float:
        if self._usage.clock_failed:
            return 0.0
        return max(0.0, self._limits.max_duration_seconds - (now - self._usage.started))

    def _window(self, capability: CapabilityId, now: float) -> tuple[float, ...]:
        return tuple(
            stamp
            for stamp in self._usage.rates[capability]
            if now - stamp < self._limits.capability_rate_window_seconds
        )

    @property
    def state(self) -> BudgetState:
        with self._lock:
            now = self._now()
            usage, limits = self._usage, self._limits
            return BudgetState(
                permitted_actions=usage.actions,
                remaining_actions=limits.max_actions - usage.actions,
                active_executions=len(usage.active),
                reserved_output_bytes=usage.output_bytes,
                remaining_output_bytes=limits.max_session_output_bytes
                - usage.output_bytes,
                remaining_seconds=self._remaining_seconds(now),
                host_actions=tuple(sorted(usage.hosts.items())),
                capability_window_actions=tuple(
                    (capability, len(self._window(capability, now)))
                    for capability in sorted(usage.rates)
                ),
                outcomes=tuple(sorted(usage.outcomes.items())),
            )

    def _hosts(self, action: object) -> tuple[str, ...] | Failure:
        if not isinstance(action, ApprovedAction):
            return _denied("Budget target semantics are not established")
        try:
            approved = ApprovedAction.model_validate(action)
            if approved.capability not in self._usage.rates:
                return _denied("Capability budget is not established")
            hosts = set()
            for match in (approved.scope_match, *approved.parameter_scope_matches):
                host = match.host_identity
                if host is None:
                    return _denied("Target has no single-host budget identity")
                hosts.add(host)
            return tuple(sorted(hosts))
        except (ValidationError, TypeError, ValueError, AttributeError):
            return _denied("Budget target semantics are not established")

    def _check(
        self, action: ApprovedAction, hosts: tuple[str, ...], now: float
    ) -> Failure | None:
        usage, limits = self._usage, self._limits
        if self._remaining_seconds(now) == 0.0:
            return _denied("Session time budget exhausted")
        if usage.actions >= limits.max_actions:
            return _denied("Session action budget exhausted")
        if len(usage.active) >= limits.max_concurrency:
            return _denied("Concurrency budget exhausted")
        if any(
            usage.hosts.get(host, 0) >= limits.max_actions_per_host for host in hosts
        ):
            return _denied("Host action budget exhausted")
        if len(self._window(action.capability, now)) >= limits.capability_rate_actions:
            return _denied("Capability rate limit reached")
        if (
            usage.output_bytes + 2 * limits.max_output_bytes
            > limits.max_session_output_bytes
        ):
            return _denied("Session output allowance exhausted")
        return None

    def check(self, action: ApprovedAction) -> OperationResult[None]:
        """Policy eligibility seam: all normalized targets, no consumption."""
        with self._lock:
            hosts = self._hosts(action)
            if isinstance(hosts, Failure):
                return hosts
            failure = self._check(action, hosts, self._now())
            return failure if failure is not None else Success[None](value=None)

    def reserve(
        self, action: ApprovedAction
    ) -> OperationResult[InstanceOf[BudgetPermit]]:
        """Acquire without waiting. This is resource availability, not authorization.

        Future dispatch must first revalidate the original ActionRequest with current
        policy; neither an old nor a forged ApprovedAction skips that obligation.
        """
        with self._lock:
            hosts = self._hosts(action)
            if isinstance(hosts, Failure):
                return hosts
            now = self._now()
            failure = self._check(action, hosts, now)
            if failure is not None:
                return failure
            token = object()
            permit = BudgetPermit(self, token)
            result = Success[InstanceOf[BudgetPermit]](value=permit)
            usage = self._usage
            usage.actions += 1
            usage.output_bytes += 2 * self._limits.max_output_bytes
            for host in hosts:
                usage.hosts[host] = usage.hosts.get(host, 0) + 1
            usage.rates[action.capability] = (
                *self._window(action.capability, now),
                now,
            )
            usage.active.add(token)
            return result

    def _release(self, token: object, outcome: ReservationOutcome) -> None:
        if not isinstance(outcome, ReservationOutcome):
            raise ValueError("Invalid reservation outcome")
        with self._lock:
            if token in self._usage.active:
                self._usage.active.remove(token)
                self._usage.entered.discard(token)
                self._usage.outcomes[outcome] = self._usage.outcomes.get(outcome, 0) + 1

    def _enter(self, token: object) -> None:
        with self._lock:
            if token not in self._usage.active or token in self._usage.entered:
                raise ValueError("Reservation is released or already entered")
            self._usage.entered.add(token)

    def _is_active(self, token: object) -> bool:
        with self._lock:
            return token in self._usage.active


@dataclass(frozen=True, slots=True)
class BudgetPermit:
    """Synchronous context manager, including around awaits; cleanup never awaits.

    Use immediately after acquisition with no intervening await. Explicit release
    is idempotent. Abandoned ownership is a caller error; there is no GC refund.
    """

    _controller: BudgetController = field(repr=False)
    _token: object = field(repr=False)

    @property
    def active(self) -> bool:
        return self._controller._is_active(self._token)

    def release(self, outcome: ReservationOutcome = ReservationOutcome.ABORTED) -> None:
        self._controller._release(self._token, outcome)

    def __enter__(self) -> Self:
        self._controller._enter(self._token)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if exc_type is None:
            outcome = ReservationOutcome.COMPLETED
        elif issubclass(exc_type, CancelledError):
            outcome = ReservationOutcome.CANCELLED
        elif issubclass(exc_type, TimeoutError):
            outcome = ReservationOutcome.TIMEOUT
        else:
            outcome = ReservationOutcome.FAILED
        self.release(outcome)


__all__ = [
    "BudgetController",
    "BudgetPermit",
    "BudgetState",
    "ExecutionBudget",
    "ReservationOutcome",
]

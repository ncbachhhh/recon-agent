"""Pure operational failure contracts; no logging, recovery or subsystem activity."""

from enum import StrEnum
from typing import Annotated, ClassVar, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator


class ErrorCategory(StrEnum):
    CONFIGURATION = "configuration"
    POLICY = "policy"
    TOOL = "tool"
    PROVIDER = "provider"
    PLANNER = "planner"
    CANCELLATION = "cancellation"
    STATE = "state"


class ScopeRejectionReason(StrEnum):
    INVALID_SCOPE = "invalid_scope"
    INVALID_TARGET = "invalid_target"
    NOT_IN_SCOPE = "not_in_scope"
    EXCLUDED = "excluded"
    PRIVATE_IP_NOT_ALLOWED = "private_ip_not_allowed"


class ErrorCode(StrEnum):
    CONFIGURATION_INVALID = "configuration_invalid"
    SCOPE_REJECTED = "scope_rejected"
    TOOL_UNAVAILABLE = "tool_unavailable"
    TOOL_TIMEOUT = "tool_timeout"
    TOOL_EXECUTION_FAILED = "tool_execution_failed"
    PARSE_FAILED = "parse_failed"
    PROVIDER_FAILED = "provider_failed"
    PLANNER_VALIDATION_FAILED = "planner_validation_failed"
    BUDGET_EXHAUSTED = "budget_exhausted"
    CANCELLED = "cancelled"
    STATE_TRANSITION_INVALID = "state_transition_invalid"

    @property
    def category(self) -> ErrorCategory:
        """Category is derived from the code, never a contradictory input field."""
        if self is ErrorCode.CONFIGURATION_INVALID:
            return ErrorCategory.CONFIGURATION
        if self in (ErrorCode.SCOPE_REJECTED, ErrorCode.BUDGET_EXHAUSTED):
            return ErrorCategory.POLICY
        if self in (
            ErrorCode.TOOL_UNAVAILABLE,
            ErrorCode.TOOL_TIMEOUT,
            ErrorCode.TOOL_EXECUTION_FAILED,
            ErrorCode.PARSE_FAILED,
        ):
            return ErrorCategory.TOOL
        if self is ErrorCode.PROVIDER_FAILED:
            return ErrorCategory.PROVIDER
        if self is ErrorCode.PLANNER_VALIDATION_FAILED:
            return ErrorCategory.PLANNER
        if self is ErrorCode.STATE_TRANSITION_INVALID:
            return ErrorCategory.STATE
        return ErrorCategory.CANCELLATION


class _Contract(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        frozen=True,
        validate_default=True,
        revalidate_instances="always",
        hide_input_in_errors=True,
        allow_inf_nan=False,
    )


# Diagnostics carry references and short operator-authored messages, not raw output.
_Reference = Annotated[
    str, StringConstraints(min_length=1, max_length=256, pattern=r"\S")
]
_Message = Annotated[
    str, StringConstraints(min_length=1, max_length=1024, pattern=r"\S")
]


class ErrorContext(_Contract):
    """Allowlisted scalar metadata; never pass credentials or source/output dumps.

    References and messages are caller-sanitized text, not automatic redaction.
    """

    action_id: _Reference | None = None
    target_id: _Reference | None = None
    capability: _Reference | None = None
    tool: _Reference | None = None
    provider: _Reference | None = None
    timeout_seconds: Annotated[float, Field(gt=0)] | None = None
    exit_code: int | None = None
    configuration_source: Literal["file", "environment", "validation"] | None = None
    scope_reason: ScopeRejectionReason | None = None
    target_kind: Literal["domain", "hostname", "ip", "cidr", "url"] | None = None
    normalized_candidate: _Reference | None = None


class ErrorInfo(_Contract):
    """Portable failure data, excluding exceptions, traceback and raw source inputs."""

    code: ErrorCode
    message: _Message
    retryable: bool = False
    context: ErrorContext = Field(default_factory=ErrorContext)

    @property
    def category(self) -> ErrorCategory:
        return self.code.category

    @model_validator(mode="after")
    def retry_requires_operational_failure(self) -> Self:
        if self.retryable and self.category in (
            ErrorCategory.CONFIGURATION,
            ErrorCategory.POLICY,
            ErrorCategory.PLANNER,
            ErrorCategory.CANCELLATION,
            ErrorCategory.STATE,
        ):
            raise ValueError(
                "rejection, invalid input or cancellation is not retryable"
            )
        return self


class ReconAgentError(Exception):
    """Catch boundary for project failures; instantiate a concrete category.

    All retry defaults are conservative (False). An operational boundary may set
    retryable=True when a transient tool/provider failure is known; this neither
    schedules a retry nor authorizes execution. Chain lower-level causes explicitly.
    """

    _code: ClassVar[ErrorCode | None] = None

    def __init__(
        self,
        message: str,
        *,
        context: ErrorContext | None = None,
        retryable: bool = False,
    ) -> None:
        if self._code is None:
            raise TypeError("instantiate a concrete project error category")
        self._info = ErrorInfo(
            code=self._code,
            message=message,
            context=context if context is not None else ErrorContext(),
            retryable=retryable,
        )
        super().__init__(self._info.message)

    @property
    def code(self) -> ErrorCode:
        return self._info.code

    @property
    def category(self) -> ErrorCategory:
        return self._info.category

    @property
    def message(self) -> str:
        return self._info.message

    @property
    def retryable(self) -> bool:
        return self._info.retryable

    @property
    def context(self) -> ErrorContext:
        return self._info.context

    def to_error_info(self) -> ErrorInfo:
        """Copy only the stable contract; chained causes are never serialized."""
        return self._info


class ConfigurationError(ReconAgentError):
    """Explicit configuration source or effective settings failed."""

    _code = ErrorCode.CONFIGURATION_INVALID


class PolicyError(ReconAgentError):
    """Catch boundary for deterministic policy rejection/exhaustion."""


class ScopeRejectedError(PolicyError):
    _code = ErrorCode.SCOPE_REJECTED


class BudgetExhaustedError(PolicyError):
    _code = ErrorCode.BUDGET_EXHAUSTED


class ToolError(ReconAgentError):
    """Catch boundary for tool availability, execution and normalization failures."""


class ToolUnavailableError(ToolError):
    _code = ErrorCode.TOOL_UNAVAILABLE


class ToolTimeoutError(ToolError):
    _code = ErrorCode.TOOL_TIMEOUT


class ToolExecutionError(ToolError):
    _code = ErrorCode.TOOL_EXECUTION_FAILED


class ParserError(ToolError):
    _code = ErrorCode.PARSE_FAILED


class ProviderError(ReconAgentError):
    _code = ErrorCode.PROVIDER_FAILED


class PlannerValidationError(ReconAgentError):
    _code = ErrorCode.PLANNER_VALIDATION_FAILED


class CancelledError(ReconAgentError):
    """Operator/control cancellation contract, aligned with existing domain status."""

    _code = ErrorCode.CANCELLED


class StateTransitionError(ReconAgentError):
    """Invalid state input, lineage or lifecycle; grants no retry/authorization."""

    _code = ErrorCode.STATE_TRANSITION_INVALID


__all__ = [
    "BudgetExhaustedError",
    "CancelledError",
    "ConfigurationError",
    "ErrorCategory",
    "ErrorCode",
    "ErrorContext",
    "ErrorInfo",
    "ParserError",
    "PlannerValidationError",
    "PolicyError",
    "ProviderError",
    "ReconAgentError",
    "ScopeRejectedError",
    "ScopeRejectionReason",
    "StateTransitionError",
    "ToolError",
    "ToolExecutionError",
    "ToolTimeoutError",
    "ToolUnavailableError",
]

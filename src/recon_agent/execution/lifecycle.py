"""Optional trusted start notification, after reservation and before contact."""

from collections.abc import Callable

from pydantic import TypeAdapter, ValidationError

from recon_agent.core.errors import StateTransitionError
from recon_agent.core.results import Failure, OperationResult, Success

ExecutionStart = Callable[[], OperationResult[None]]


def notify_execution_start(callback: ExecutionStart | None) -> OperationResult[None]:
    """Fail closed on malformed notification; caller releases its owned permit."""
    if callback is None:
        return Success[None](value=None)
    try:
        return TypeAdapter(OperationResult[None]).validate_python(callback())
    except (ValueError, TypeError, ValidationError):
        return Failure(
            error=StateTransitionError(
                "Invalid execution start notification"
            ).to_error_info()
        )

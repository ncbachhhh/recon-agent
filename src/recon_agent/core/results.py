"""Explicit typed operation outcomes, separate from reconnaissance ActionResult."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from recon_agent.core.errors import ErrorInfo


class _Outcome(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        frozen=True,
        validate_default=True,
        revalidate_instances="always",
        hide_input_in_errors=True,
        allow_inf_nan=False,
    )


class Success[T](_Outcome):
    """A completed operation with a typed value and no error field."""

    status: Literal["success"] = "success"
    value: T


class Failure(_Outcome):
    """A failed operation with portable failure data and no success value."""

    status: Literal["failure"] = "failure"
    error: ErrorInfo


type OperationResult[T] = Annotated[Success[T] | Failure, Field(discriminator="status")]

__all__ = ["Failure", "OperationResult", "Success"]

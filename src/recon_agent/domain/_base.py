"""Internal structural types; no configuration or operational dependencies."""

from datetime import UTC, datetime
from typing import Annotated

from pydantic import (
    AfterValidator,
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
)

# Opaque caller-supplied identities and remote text are preserved, never stripped.
NonEmptyText = Annotated[str, StringConstraints(min_length=1, pattern=r"\S")]
CapabilityName = Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9_]*$")]
Port = Annotated[int, Field(ge=1, le=65535)]


def _utc(value: datetime) -> datetime:
    return value.astimezone(UTC)


Timestamp = Annotated[AwareDatetime, AfterValidator(_utc)]


class DomainModel(BaseModel):
    """Strict data schemas; validation is structural, never authorization."""

    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        validate_default=True,
        validate_assignment=True,
        revalidate_instances="always",
        hide_input_in_errors=True,
        allow_inf_nan=False,
    )


class Record(DomainModel):
    """Record attributes are frozen; nested JSON payloads remain ordinary data."""

    model_config = ConfigDict(frozen=True)

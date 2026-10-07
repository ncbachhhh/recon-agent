"""Low-level process data, deliberately separate from planner/domain contracts."""

from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

from pydantic import (
    AfterValidator,
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

from recon_agent.core.config.models import PositiveSeconds


class _ProcessData(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        frozen=True,
        validate_default=True,
        revalidate_instances="always",
        hide_input_in_errors=True,
        allow_inf_nan=False,
        ser_json_bytes="base64",
        val_json_bytes="base64",
    )


class ProcessSpec(_ProcessData):
    """Trusted adapter-owned executable plus literal arguments, never a command.

    Not a planner input or authorization token. Never log/serialize this record
    into diagnostics; arguments can contain sensitive data.
    """

    executable: str = Field(repr=False)
    args: tuple[str, ...] = Field(default=(), repr=False)
    timeout_seconds: PositiveSeconds | None = None
    # Trusted complete child environment; None preserves inherited-environment
    # behavior. Tuple pairs keep this internal snapshot immutable.
    environment: tuple[tuple[str, str], ...] | None = Field(default=None, repr=False)

    # Trusted adapter-owned child cwd; never planner input or a global chdir.
    working_directory: str | None = Field(default=None, repr=False)

    @field_validator("working_directory")
    @classmethod
    def absolute_working_directory(cls, value: str | None) -> str | None:
        if value is not None and (
            not value
            or "\x00" in value
            or len(value) > 8192
            or not Path(value).is_absolute()
        ):
            raise ValueError("working directory must be a bounded absolute path")
        return value

    @field_validator("environment")
    @classmethod
    def environment_structure(
        cls, value: tuple[tuple[str, str], ...] | None
    ) -> tuple[tuple[str, str], ...] | None:
        if value is not None and (
            len(value) > 64
            or len({key for key, _ in value}) != len(value)
            or any(
                not key
                or "=" in key
                or "\x00" in key
                or "\x00" in item
                or len(key) > 256
                or len(item) > 8192
                for key, item in value
            )
        ):
            raise ValueError("invalid bounded child environment")
        return value

    @field_validator("executable")
    @classmethod
    def executable_structure(cls, value: str) -> str:
        if not value.strip() or "\x00" in value:
            raise ValueError("executable must be non-blank and contain no NUL")
        return value

    @field_validator("args")
    @classmethod
    def literal_arguments(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if any("\x00" in argument for argument in value):
            raise ValueError("arguments must contain no NUL")
        return value


def _utc(value: datetime) -> datetime:
    return value.astimezone(UTC)


_Timestamp = Annotated[AwareDatetime, AfterValidator(_utc)]


class ProcessExecution(_ProcessData):
    """Observed exit and bounded raw bytes; non-zero exit is still an outcome.

    Output is untrusted evidence, excluded from repr, never automatically logged.
    JSON explicitly encodes bytes as URL-safe base64, including malformed UTF-8.
    No executable path or argv is copied into execution metadata.
    """

    argument_count: Annotated[int, Field(ge=0)]
    return_code: int
    stdout: bytes = Field(repr=False)
    stderr: bytes = Field(repr=False)
    stdout_truncated: bool
    stderr_truncated: bool
    started_at: _Timestamp
    finished_at: _Timestamp
    duration_seconds: Annotated[float, Field(ge=0)]

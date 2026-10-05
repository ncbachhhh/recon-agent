"""Validated configuration contracts; these models do not operate subsystems."""

from pathlib import Path
from typing import Annotated, Literal, Self

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    SecretStr,
    ValidationInfo,
    field_validator,
    model_validator,
)

PositiveInt = Annotated[int, Field(gt=0)]
PositiveSeconds = Annotated[float, Field(gt=0, allow_inf_nan=False)]


def _path(value: object, info: ValidationInfo) -> str | Path:
    if isinstance(value, Path) and "\x00" not in str(value):
        return value
    if isinstance(value, str) and value.strip() and "\x00" not in value:
        return value if info.mode == "json" else Path(value)
    raise ValueError("path must be a non-empty path string or Path")


ConfigPath = Annotated[Path, BeforeValidator(_path)]


class ConfigurationModel(BaseModel):
    """Reject typos/coercion and keep input values out of displayed errors."""

    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        validate_default=True,
        hide_input_in_errors=True,
        validate_assignment=True,
    )


class ScopeConfig(ConfigurationModel):
    """Future policy preferences; no targets or authorization grants."""

    allow_subdomains: bool = False
    allow_private_ips: bool = False


class ExecutionConfig(ConfigurationModel):
    default_timeout_seconds: PositiveSeconds = 30.0
    max_concurrency: PositiveInt = 1
    max_output_bytes: PositiveInt = 1_048_576
    max_actions: PositiveInt = 100
    max_actions_per_host: PositiveInt = 10
    capability_rate_actions: PositiveInt = 1
    capability_rate_window_seconds: PositiveSeconds = 1.0
    max_session_output_bytes: PositiveInt = 16_777_216
    max_duration_seconds: PositiveSeconds = 600.0

    @model_validator(mode="after")
    def timeout_fits_budget(self) -> Self:
        if self.default_timeout_seconds > self.max_duration_seconds:
            raise ValueError("default timeout must fit within the session time budget")
        return self


class PlannerConfig(ConfigurationModel):
    enabled: bool = False
    provider: Literal["groq"] = "groq"
    model: str = ""
    max_iterations: PositiveInt = 10

    @field_validator("model")
    @classmethod
    def model_identifier(cls, value: str) -> str:
        if value and not value.strip():
            raise ValueError("model must be empty or a non-blank identifier")
        return value

    @model_validator(mode="after")
    def enabled_requires_model(self) -> Self:
        if self.enabled and not self.model:
            raise ValueError("enabled planner requires a model identifier")
        return self


class ToolsConfig(ConfigurationModel):
    """Adapter enablement preference; executable/argv selection is deferred."""

    enabled: bool = False


class PersistenceConfig(ConfigurationModel):
    enabled: bool = False
    database_path: ConfigPath = Path("recon-agent.sqlite3")


class LoggingConfig(ConfigurationModel):
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    structured: bool = True


class ReportingConfig(ConfigurationModel):
    output_directory: ConfigPath = Path("reports")
    default_formats: list[Literal["json", "terminal", "html"]] = Field(
        default=["json"], min_length=1
    )

    @field_validator("default_formats")
    @classmethod
    def unique_formats(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            raise ValueError("report formats must be unique")
        return value


class AppConfig(ConfigurationModel):
    """Non-secret effective settings, safe for repr and diagnostic JSON dumps."""

    scope: ScopeConfig = Field(default_factory=ScopeConfig)
    execution: ExecutionConfig = Field(default_factory=ExecutionConfig)
    planner: PlannerConfig = Field(default_factory=PlannerConfig)
    tools: ToolsConfig = Field(default_factory=ToolsConfig)
    persistence: PersistenceConfig = Field(default_factory=PersistenceConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    reporting: ReportingConfig = Field(default_factory=ReportingConfig)


class ProviderSecrets(ConfigurationModel):
    """Separate credentials, excluded from repr and all standard model dumps."""

    groq_api_key: SecretStr | None = Field(default=None, repr=False, exclude=True)

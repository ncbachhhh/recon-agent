"""Explicit local loading with defaults < TOML < environment < overrides."""

import json
import os
import tomllib
from collections.abc import Mapping
from pathlib import Path
from typing import Literal, get_origin

from pydantic import BaseModel, SecretStr

from recon_agent.core.config.models import AppConfig, ProviderSecrets

ENV_PREFIX = "RECON_AGENT_"


class ConfigLoadError(ValueError):
    """A file or environment source could not be read/parsed safely."""


def _merge(base: dict[str, object], update: Mapping[str, object]) -> dict[str, object]:
    result = base.copy()
    for key, value in update.items():
        previous = result.get(key)
        if isinstance(previous, dict) and isinstance(value, Mapping):
            result[key] = _merge(previous, value)
        else:
            result[key] = value
    return result


def _environment(environ: Mapping[str, str]) -> dict[str, object]:
    result: dict[str, object] = {}
    for name in sorted(environ):
        if not name.startswith(ENV_PREFIX):
            continue
        parts = name.removeprefix(ENV_PREFIX).lower().split("__")
        if len(parts) != 2:
            raise ConfigLoadError("environment settings require SECTION__FIELD")
        section, field = parts
        section_info = AppConfig.model_fields.get(section)
        section_type = section_info.annotation if section_info else None
        if not isinstance(section_type, type) or not issubclass(
            section_type, BaseModel
        ):
            raise ConfigLoadError("unknown configuration environment section")
        field_info = section_type.model_fields.get(field)
        if field_info is None:
            raise ConfigLoadError("unknown configuration environment field")
        annotation = field_info.annotation
        raw = environ[name]
        if annotation in (str, Path) or get_origin(annotation) is Literal:
            value: object = raw
        else:
            try:
                value = json.loads(raw)
            except ValueError:
                raise ConfigLoadError(
                    "invalid JSON configuration environment value"
                ) from None
        section_values = result.setdefault(section, {})
        assert isinstance(section_values, dict)
        if field in section_values:
            raise ConfigLoadError("duplicate configuration environment field")
        section_values[field] = value
    return result


def load_config(
    config_file: str | Path | None = None,
    *,
    environ: Mapping[str, str] | None = None,
    overrides: Mapping[str, object] | None = None,
) -> AppConfig:
    """Load one supplied file and an environment snapshot; never discover files.

    Pass environ={} for defaults/file/overrides independent of process environment.
    Missing/unreadable files raise OSError. Syntax/environment parsing failures raise
    ConfigLoadError. Invalid effective settings raise Pydantic ValidationError.
    """
    values: dict[str, object] = {}
    if config_file is not None:
        with Path(config_file).open("rb") as stream:
            try:
                values = tomllib.load(stream)
            except (tomllib.TOMLDecodeError, UnicodeDecodeError):
                raise ConfigLoadError("invalid TOML configuration file") from None
    environment = dict(os.environ if environ is None else environ)
    values = _merge(values, _environment(environment))
    if overrides is not None:
        values = _merge(values, overrides)
    return AppConfig.model_validate(values)


def load_provider_secrets(
    *,
    environ: Mapping[str, str] | None = None,
) -> ProviderSecrets:
    """Read GROQ_API_KEY separately; absent/empty means no credential supplied."""
    environment = dict(os.environ if environ is None else environ)
    raw = environment.get("GROQ_API_KEY")
    return ProviderSecrets(groq_api_key=SecretStr(raw) if raw else None)

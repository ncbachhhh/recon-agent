"""Bounded local diagnostics only; never mutate or reinterpret evidence objects."""

import json
import math
import re
from collections.abc import Mapping, Sequence

from pydantic import JsonValue, SecretBytes, SecretStr

REDACTED = "[REDACTED]"
MAX_TEXT_CHARACTERS = 1024
MAX_CONTEXT_BYTES = 8192
MAX_CONTEXT_DEPTH = 8
MAX_CONTAINER_ITEMS = 64

# Diagnostic context is not a command, raw artifact, environment or reasoning dump.
_FORBIDDEN_KEYS = frozenset(
    {
        "command",
        "shell_command",
        "raw_command",
        "script",
        "argv",
        "raw_args",
        "environment",
        "raw_environment",
        "stdout",
        "stderr",
        "traceback",
        "raw_exception",
        "chain_of_thought",
        "internal_reasoning",
        "scratchpad",
        "model_thoughts",
        "conversation_id",
        "chat_history",
        "assistant_message",
        "user_message",
    }
)

_FORBIDDEN_COMPACT = frozenset(key.replace("_", "") for key in _FORBIDDEN_KEYS)


def redact_text(text: str, *, secrets: Sequence[SecretStr] = ()) -> str:
    """Remove explicitly supplied secret values; do not guess from ordinary words."""
    # Longest first prevents a short secret exposing the tail of an overlapping one.
    values = sorted(
        {s.get_secret_value() for s in secrets if s.get_secret_value()},
        key=lambda value: (-len(value), value),
    )
    for value in values:
        text = text.replace(value, REDACTED)
    return text


def _key(key: str) -> str:
    separated = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", key)
    return re.sub(r"[^a-z0-9]+", "_", separated.casefold()).strip("_")


def _sensitive(key: str) -> bool:
    compact = key.replace("_", "")
    return compact.endswith(
        (
            "apikey",
            "token",
            "password",
            "passwd",
            "secret",
            "secretkey",
            "secrets",
            "passwords",
            "tokens",
            "cookie",
            "setcookie",
            "credential",
            "credentials",
            "authorization",
        )
    )


def _value(value: object, secrets: Sequence[SecretStr], depth: int) -> JsonValue:
    if depth > MAX_CONTEXT_DEPTH:
        raise ValueError("diagnostic context exceeds nesting limit")
    if isinstance(value, (SecretStr, SecretBytes)):
        return REDACTED
    if value is None or isinstance(value, (bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("diagnostic numbers must be finite")
        return value
    if isinstance(value, str):
        text = redact_text(value, secrets=secrets)
        if len(text) > MAX_TEXT_CHARACTERS:
            raise ValueError("diagnostic text exceeds length limit")
        return text
    if isinstance(value, Mapping):
        if len(value) > MAX_CONTAINER_ITEMS:
            raise ValueError("diagnostic object exceeds item limit")
        result: dict[str, JsonValue] = {}
        for key, nested in value.items():
            if not isinstance(key, str) or not key.strip() or len(key) > 256:
                raise ValueError("diagnostic keys must be bounded non-blank strings")
            normalized = _key(key)
            if normalized.replace("_", "") in _FORBIDDEN_COMPACT:
                raise ValueError(
                    "raw execution, environment or private state is forbidden"
                )
            safe_key = redact_text(key, secrets=secrets)
            if safe_key in result:
                raise ValueError("redaction produces ambiguous diagnostic keys")
            result[safe_key] = (
                REDACTED
                if _sensitive(normalized)
                else _value(nested, secrets, depth + 1)
            )
        return result
    if isinstance(value, list):
        if len(value) > MAX_CONTAINER_ITEMS:
            raise ValueError("diagnostic array exceeds item limit")
        return [_value(nested, secrets, depth + 1) for nested in value]
    raise ValueError("diagnostic context requires JSON-compatible values")


def redact_context(
    context: Mapping[str, object],
    *,
    secrets: Sequence[SecretStr] = (),
) -> dict[str, JsonValue]:
    """Return a sanitized copy, rejecting unsupported or oversized diagnostics.

    Sensitive keys and secret wrappers are masked. Explicit secrets are removed
    from text/keys. Arbitrary models, exceptions and environment dumps are not an
    input contract. Existing safe model dumps may be selected deliberately.
    """
    if not isinstance(context, Mapping):
        raise ValueError("diagnostic context must be an object")
    result = _value(context, secrets, 0)
    assert isinstance(result, dict)
    if (
        len(json.dumps(result, ensure_ascii=True, allow_nan=False).encode())
        > MAX_CONTEXT_BYTES
    ):
        raise ValueError("diagnostic context exceeds byte limit")
    return result


__all__ = ["redact_context", "redact_text"]

"""Explicit project-only console logging and audit emission; no remote sink."""

import json
import logging
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import TYPE_CHECKING, TextIO

from pydantic import JsonValue, SecretStr

from recon_agent.core.audit import AuditEvent
from recon_agent.core.config.models import LoggingConfig
from recon_agent.core.errors import ConfigurationError, ErrorInfo
from recon_agent.core.redaction import MAX_TEXT_CHARACTERS, redact_context, redact_text


def _text(value: str, secrets: Sequence[SecretStr]) -> str:
    safe = redact_text(value, secrets=secrets)
    if len(safe) > MAX_TEXT_CHARACTERS:
        return safe[:MAX_TEXT_CHARACTERS] + "[truncated]"
    return safe


def _message(record: logging.LogRecord, secrets: Sequence[SecretStr]) -> str:
    if not isinstance(record.msg, str):
        raise ValueError("diagnostic messages must be text")
    message = redact_text(record.msg, secrets=secrets)
    if record.args:
        if isinstance(record.args, tuple):
            args = redact_context({"args": list(record.args)}, secrets=secrets)["args"]
            assert isinstance(args, list)
            message = message % tuple(args)
        elif isinstance(record.args, Mapping):
            message = message % redact_context(record.args, secrets=secrets)
        else:
            raise ValueError("unsupported diagnostic arguments")
    return _text(message, secrets)


class ProjectFormatter(logging.Formatter):
    """Whitelist output fields and omit native causes, exc_info and stack_info.

    A malformed record becomes a fixed omission record, so logging's fallback
    cannot print the original message/arguments or exception secrets.
    """

    def __init__(self, *, structured: bool, secrets: Sequence[SecretStr] = ()) -> None:
        super().__init__()
        self.structured = structured
        self._secrets = tuple(secrets)

    def _payload(self, record: logging.LogRecord) -> dict[str, JsonValue]:
        event = getattr(record, "audit_event", None)
        if event is not None:
            if not isinstance(event, AuditEvent):
                raise ValueError("audit_event must be a validated event")
            event = AuditEvent.model_validate(event.model_dump())
            payload = event.model_dump(mode="json")
            payload["level"] = payload.pop("severity")
            payload["context"] = redact_context(event.context, secrets=self._secrets)
            if event.error is not None:
                payload["error_category"] = event.error.category.value
        else:
            context = getattr(record, "context", {})
            if not isinstance(context, Mapping):
                raise ValueError("diagnostic context must be an object")
            payload = {
                "timestamp": datetime.fromtimestamp(record.created, UTC)
                .isoformat()
                .replace("+00:00", "Z"),
                "level": record.levelname,
                "message": _message(record, self._secrets),
                "context": redact_context(context, secrets=self._secrets),
            }
            error = getattr(record, "error", None)
            if error is not None:
                if not isinstance(error, ErrorInfo):
                    raise ValueError("diagnostic error must be ErrorInfo")
                error = ErrorInfo.model_validate(error.model_dump())
                payload["error"] = error.model_dump(mode="json")
                payload["error_category"] = error.category.value
        payload["logger"] = _text(record.name, self._secrets)
        # Redact every output string, including summaries, identifiers and ErrorInfo.
        # The entire payload has more fixed fields than context; bound only context
        # via redact_context, and sanitize the fixed JSON recursively here.
        return self._strings(payload)

    def _strings(self, payload: dict[str, JsonValue]) -> dict[str, JsonValue]:
        def clean(value: JsonValue) -> JsonValue:
            if isinstance(value, str):
                return _text(value, self._secrets)
            if isinstance(value, list):
                return [clean(nested) for nested in value]
            if isinstance(value, dict):
                return {key: clean(nested) for key, nested in value.items()}
            return value

        result = clean(payload)
        assert isinstance(result, dict)
        return result

    def format(self, record: logging.LogRecord) -> str:
        try:
            payload = self._payload(record)
        except Exception:
            # Never stringify the formatting error or fall back to the raw record.
            payload = {
                "level": "ERROR",
                "logger": "recon_agent",
                "message": "Invalid diagnostic record omitted.",
            }
        encoded = json.dumps(
            payload,
            sort_keys=True,
            ensure_ascii=True,
            allow_nan=False,
            separators=(",", ":"),
        )
        if self.structured:
            return encoded
        # JSON escaping makes controls/ANSI/newlines visible rather than executable.
        level = json.dumps(payload["level"], ensure_ascii=True)[1:-1]
        name = json.dumps(payload["logger"], ensure_ascii=True)[1:-1]
        return f"{level} {name} {encoded}"


# StreamHandler is generic in typeshed, but not subscriptable at runtime.
if TYPE_CHECKING:
    _StreamHandler = logging.StreamHandler[TextIO]
else:
    _StreamHandler = logging.StreamHandler


class _ConsoleHandler(_StreamHandler):
    def handleError(self, record: logging.LogRecord) -> None:
        # Stdlib's debug fallback prints the original record/arguments. A sink
        # failure instead propagates a fixed project error without that leak.
        raise ConfigurationError("project diagnostic sink failed") from None


def configure_logging(
    config: LoggingConfig,
    *,
    stream: TextIO | None = None,
    secrets: Sequence[SecretStr] = (),
) -> logging.Logger:
    """Replace only our sink on recon_agent, leaving root/third-party handlers alone.

    No file/threads/environment inspection. Default sink is stderr. Callers own
    injected streams. Register secret wrappers explicitly; imports do not configure.
    """
    settings = LoggingConfig.model_validate(config.model_dump())
    logger = logging.getLogger("recon_agent")
    handler = _ConsoleHandler(stream)
    handler.setFormatter(
        ProjectFormatter(structured=settings.structured, secrets=secrets)
    )
    for previous in logger.handlers[:]:
        if previous.name == "recon_agent.console":
            logger.removeHandler(previous)
            previous.close()
    handler.name = "recon_agent.console"
    logger.addHandler(handler)
    logger.setLevel(logging.getLevelNamesMapping()[settings.level])
    logger.propagate = False
    return logger


def emit_audit_event(event: AuditEvent) -> None:
    """Emit a revalidated snapshot; its recorded decision confers no authority."""
    project = logging.getLogger("recon_agent")
    if not any(handler.name == "recon_agent.console" for handler in project.handlers):
        raise ConfigurationError("configure project logging before audit emission")
    snapshot = AuditEvent.model_validate(event.model_dump())
    logging.getLogger("recon_agent.audit").log(
        logging.getLevelNamesMapping()[snapshot.severity],
        snapshot.message,
        extra={"audit_event": snapshot},
    )


__all__ = ["ProjectFormatter", "configure_logging", "emit_audit_event"]

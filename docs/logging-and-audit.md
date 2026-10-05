# Local logging and audit foundation

M0-T06 implements `core/audit.py` (pure event data), `core/redaction.py` (bounded
copying/redaction) and `core/diagnostics.py` (explicit standard-library logging).
There are no producers, autonomous recon loop or persistent/remote sinks yet.
Domain/configuration/error models do not emit logs on construction.

## Operational diagnostics and audit records

Logging describes operator/developer diagnostics with standard severity. Audit
records describe significant reconnaissance lifecycle/decision/outcome events.
A debug line is not automatically an audit event.

The future product takes operator targets, authorized scope and configuration,
then performs discovery, internal planner decisions, deterministic policy checks
and approved capabilities until stopping. Its trail links sessions, planner
decisions, actions, executions, subjects and evidence references. It is not an
interactive AI conversation. Record concise decision summaries/action reasons,
never private chain-of-thought, scratchpads or transcripts.

`AuditEvent` records supplied data and grants no authority. Deserialization or
emission of `policy.action_approved` cannot authorize execution or replay anything.
Event producers and later policy/orchestration own truthful, consistent recording,
reference integrity and actual authorization; the model validates structure only.

## Audit contract

The strict frozen Pydantic model requires caller-supplied `event_id`, `event_type`,
aware `timestamp`, `session_id` and non-blank `message`. IDs are opaque strings up
to 256 characters; message is at most 1024 characters. No clocks/randomness run
on construction. Timestamps normalize to UTC and JSON emits ISO 8601 with `Z`.
Python inputs require datetime and AuditEventType; JSON uses their encodings.
Both Python/JSON dumps round-trip. Optional action/execution/planner-decision/asset
IDs link existing or future contracts without creating a new domain entity.

Severity defaults INFO and supports DEBUG, INFO, WARNING, ERROR and CRITICAL.
`context` is a bounded JSON object for small summaries and references;
`error` optionally uses existing ErrorInfo, with no native exception/traceback.
Context is omitted from repr, redacted on construction and serialization, and
revalidated before emission. Frozen attributes do not deeply freeze nested JSON;
mutations are unapproved data edits and must satisfy the same validation boundary.
A rejected/invalid mutation cannot bypass safe emission.

Stable types describe future operations:

| Group | Codes |
| --- | --- |
| Session | `session.started`, `session.stopped`, `session.completed`, `session.failed`, `session.cancelled` |
| Subjects/facts | `asset.discovered`, `observation.recorded`, `finding.recorded` |
| Planner | `planner.decision`, `planner.action_requested` |
| Policy | `policy.action_approved`, `policy.action_rejected` |
| Tools | `tool.execution_started`, `tool.execution_completed`, `tool.execution_failed` |
| Budget | `budget.exhausted` |

These are contracts, not implemented producers. Finding/ToolExecution domain
records remain staged with their owning tasks. Context can identify a target,
observation, finding or artifact by reference, plus capability/tool, short decision
summary/reason, priority/finished flag, duration or exit metadata. It is not a full
request/response, command, evidence body or provider output schema.

## Explicit setup and emission

```python
import logging
from datetime import UTC, datetime
from recon_agent.core.audit import AuditEvent, AuditEventType
from recon_agent.core.config import load_config, load_provider_secrets
from recon_agent.core.diagnostics import configure_logging, emit_audit_event

config = load_config(environ={})
credentials = load_provider_secrets(environ={})
keys = (credentials.groq_api_key,) if credentials.groq_api_key is not None else ()
configure_logging(config.logging, secrets=keys)
logging.getLogger("recon_agent.startup").info("Configuration loaded")

event = AuditEvent(
    event_id="event-1",
    event_type=AuditEventType.PLANNER_ACTION_REQUESTED,
    timestamp=datetime(2026, 10, 5, tzinfo=UTC),
    session_id="session-1",
    action_id="action-1",
    planner_decision_id="decision-1",
    message="HTTP metadata requested",
    context={"capability": "probe_http", "reason": "Add service evidence"},
)
emit_audit_event(event)
```

This example emits supplied records; it starts no recon/planning activity.
`configure_logging` uses existing LoggingConfig `level`/`structured` only, without
loading config/secrets or inspecting environment itself. Its default sink is
stderr; tests/operators may inject a TextIO stream. Only explicit setup configures
the `recon_agent` logger. `recon_agent.audit` is the dedicated audit namespace.
Audit emission requires the configured project sink; otherwise ConfigurationError
is raised without unformatted fallback output.

Repeated setup replaces/closes only the handler named `recon_agent.console`,
without closing caller-owned streams. Project propagation is disabled to prevent
root duplication. Root and third-party loggers/handlers remain untouched; other
project handlers are retained and must implement their own safety. Child loggers
inherit level/sink by default; callers that customize children own that behavior.
Setup is a startup operation, not a concurrent reconfiguration protocol.

## Formatting and errors

Structured output is a deterministic sorted compact JSON line with timestamp,
level, logger, message and context. Audit output additionally includes event type,
ID/correlation fields and optional ErrorInfo; its level comes from event severity
and its time is the supplied event time. Ordinary diagnostics use LogRecord time
converted to aware UTC. Native exc_info, stack_info and arbitrary record extras
are never serialized. ErrorInfo can be supplied through `extra={"error": info}`;
code/message/retryable/context and derived error_category are included safely.

Human mode prefixes level/logger to the same readable JSON record. ASCII/JSON
escaping makes newline/ANSI/control characters visible, preventing fabricated
physical log lines or terminal controls. It is a diagnostic format, not a report.
Developer-controlled printf templates support sanitized JSON arguments; remote
text should be an argument/data, never a format template. Messages/logger names
are capped at 1024 characters with an explicit `[truncated]` marker.

Invalid/oversized diagnostic records become a fixed ERROR omission record with
no raw values. Formatter failures never invoke stdlib's raw-record debug fallback.
A stream write/flush failure instead raises a fixed ConfigurationError with source
context suppressed, avoiding that fallback's message/argument dump. These failures
are visible to callers; there is no persistence, guaranteed delivery or silent
claim of a complete trail. Later application code must decide failure handling.

## Redaction and evidence boundary

`redact_context` returns a copy of JSON-compatible dictionaries/lists/scalars,
masking SecretStr/SecretBytes wrappers and values under case/format-normalized keys
ending in api_key/apikey, token(s), password(s)/passwd, secret(s)/secret_key,
credential(s), authorization or cookie/set_cookie. This covers common provider,
authentication and environment-secret labels. Ordinary words in text and metadata
names such as password_policy/token_count are preserved. Sensitive-key matching
is conservative diagnostic filtering, not forensic evidence filtering.

Register actual known local values explicitly as SecretStr wrappers with setup;
those values are then removed from all emitted text/context, including ErrorInfo,
IDs and printf arguments. Empty values are ignored and overlapping values are
handled longest first. No environment discovery, key-value log dump or raw secret
model serialization occurs. Deliberately selected safe model dumps retain M0-T03
secret exclusions; passing arbitrary model/exception objects as context is rejected.

Context limits are 1024 characters per string, 256 per key, 64 items per container,
eight nested levels and 8192 encoded JSON bytes. Raw environment/stdout/stderr,
commands/arguments/scripts, native causes/tracebacks, transcript fields and private
reasoning keys are rejected at nested levels, not interpreted as instructions.
Reference large/raw evidence through future bounded artifacts rather than logging
HTTP bodies, scanner output, provider responses or configuration dumps.

Neither key heuristics nor these limits can identify every unregistered secret
embedded in ordinary text. Producers must select non-secret diagnostics and register
known values. Direct AuditEvent message/error strings have no knowledge of setup's
secret set; safe configured sinks apply it at output. Context redaction never
mutates an Observation/Evidence or expands scope. Remote instruction-like text
remains untrusted data and cannot alter logging, policy or authority.

## Validation and deferred integration

Focused checks: `.venv/bin/python -m pytest tests/unit/test_logging_audit.py`.
See [testing strategy](testing-strategy.md) for full validation. Captured streams,
fixed timestamps, dummy secrets and blocked runtime/network paths exercise both
formats, event types, filters, repeated setup, error integration and safety.

Future application/orchestration services explicitly emit events; pure domain
records do not depend on logging. No scanner/provider/planner producer, scope
validator, runner, registry, budget engine, autonomous loop, file/rotating sink,
database, log shipping, analytics, operational report or real CLI is implemented.
The existing CLI remains inert and does not initialize logging.

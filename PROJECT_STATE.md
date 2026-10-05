# Project state

Project phase: Foundation / configuration, domain, errors/results and local logging/audit

Completed:

- M0-T01 — Repository governance and planning scaffold (DONE)
- M0-T02 — Python project and developer tooling baseline (DONE)
- M0-T03 — Configuration foundation (DONE)
- M0-T04 — Core domain model foundation (DONE)
- M0-T05 — Error taxonomy and result model (DONE)
- M0-T06 — Logging and audit-event foundation (DONE)

Active task: None.

Next READY:

- M1-T01 — Scope model and validator (not started)

## Implementation reality

The 92-task roadmap, governance, maintenance skill and design documentation exist. `recon-agent` 0.1.0 installs through setuptools with Python >=3.12 metadata. Pydantic remains the sole direct runtime dependency; developer tooling and inert CLI are unchanged.

`core/config/` implements strict seven-section settings, defaults < explicit TOML < namespaced environment < programmatic precedence, and separate excluded/redacted credentials. Configuration source/effective validation failures use ConfigurationError with fixed diagnostics and native cause chaining. Direct model construction raises Pydantic ValidationError. Loading preferences grants no authorization or runtime startup.

`domain/` exports 13 pure typed data contracts with explicit opaque IDs, aware UTC timestamps, structural validation, evidence provenance and portable serialization. Targets/scopes are declarations; planner decisions/action requests are unapproved data. ActionResult uses shared ErrorInfo and validates consistent completed/partial/rejected/failed/cancelled/timeout outcomes. Frozen records and mutable state/session containers have no operational transition APIs. Domain depends on pure shared errors, never logging/configuration/operational layers.

`core/errors.py` supplies stable codes, category catch boundaries and concrete configuration/policy/tool/parser/provider/planner/budget/cancellation exceptions, with bounded allowlisted scalar context and explicit conservative retryability. ErrorInfo omits native causes/tracebacks/credentials. `core/results.py` provides typed Success[T]/Failure and the status-discriminated OperationResult[T] union; ActionResult retains its action/evidence role. Caller-authored diagnostics require safe selection; chained causes remain explicit debugging data, not routine dumps.

M0-T06 adds pure `core/audit.py` with 16 stable event types, explicit UTC time/session IDs and optional action/execution/decision/asset correlation. `core/redaction.py` copies and bounds diagnostic JSON, masks known sensitive keys/wrappers and accepts explicitly registered secret values. `core/diagnostics.py` explicitly configures only the project logger, replaces its owned console handler, supports escaped human/JSON output and emits revalidated records through recon_agent.audit. Existing LoggingConfig and ErrorInfo are reused. Native causes/stacks are omitted; malformed records produce fixed omission output and sink failures raise fixed ConfigurationError without raw-record fallback. Imports and data constructors do not configure logging. See docs/logging-and-audit.md for precise redaction and delivery limits.

Audit events describe autonomous recon operations and confer no authorization. Event producers, Action/ToolExecution/Finding entities, scope enforcement, registry/policy, runner, scanners, Groq/provider/planner runtime, state transitions/deduplication/budget/retry enforcement, autonomous loop, persistence and operational reports remain unimplemented. No chat transcript or private reasoning contract exists. Only M1-T01 is READY; remaining 85 tasks are NOT STARTED.

## Major architecture decisions

- Capability intent never becomes LLM-generated shell/argv; future registry/policy/adapters own authorization and execution.
- Centralized deterministic fail-closed scope/action validation must precede contact, including derived destinations.
- Remote evidence and model recommendations remain non-authoritative data with provenance. Audit records do not authorize replay.
- Pure domain/error models never emit logs. Future application/orchestration services emit concise decision summaries, policy outcomes and execution records, without private reasoning or transcript state.
- Explicit local standard-library logging leaves root/third-party handlers alone, performs no remote upload/file persistence and needs no new runtime dependency or ADR.
- Bounded diagnostics exclude raw environment/output/native causes/commands. Registered secrets and key-labelled secret values are masked; arbitrary unregistered free-text secrets require producer discipline. Source evidence is never mutated.
- Exceptions handle application boundaries; ErrorInfo is portable failure data; generic results support intentionally inspected outcomes. Retryability grants no authority.
- ADR 0001's explicit TOML and separate-secret choice is unchanged. IDs/times, canonical identity and operational mutation remain separate concerns. Groq/SQLite remain planned; default tests are deterministic offline checks.

## Validation

Python 3.14.6 / Pydantic 2.13.5: editable install/pip check; 116 focused logging/audit tests; Ruff lint/format; strict Mypy (26 production modules, plus the existing result typing test); full 446-test suite; coverage (100%, 621 statements / 150 branches); sdist/wheel build and unchanged CLI passed. All 446 tests also passed with connection/DNS functions blocked and Groq key absent. Fresh external wheel installation passed guarded cold imports, pure event JSON serialization, explicit local setup/emission, handler safety, redaction/error metadata, UTC/correlation, CLI and pip check. Runtime guards blocked network/process/database/directory/file/global-logging/thread startup, allowing only ordinary dependency entry-point metadata reads. Source/field security, protected-file, archive/dependency, documentation/status/history and Git inspections passed. See TASK_HISTORY for actual evidence. Python 3.12 was not separately exercised.

Known blockers: None.

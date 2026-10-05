# Project state

Project phase: M1 / deterministic scope membership foundation

Completed:

- M0-T01 — Repository governance and planning scaffold (DONE)
- M0-T02 — Python project and developer tooling baseline (DONE)
- M0-T03 — Configuration foundation (DONE)
- M0-T04 — Core domain model foundation (DONE)
- M0-T05 — Error taxonomy and result model (DONE)
- M0-T06 — Logging and audit-event foundation (DONE)
- M1-T01 — Scope model and validator (DONE)

Active task: None.

Next READY:

- M1-T02 — Scope regression suite (not started)

## Implementation reality

The 92-task roadmap, governance, maintenance skill and design documentation exist. `recon-agent` 0.1.0 installs through setuptools with Python >=3.12 metadata. Pydantic remains the sole direct runtime dependency; developer tooling and inert CLI are unchanged.

`core/config/` implements strict seven-section settings, defaults < explicit TOML < namespaced environment < programmatic precedence, and separate excluded/redacted credentials. Configuration source/effective validation failures use ConfigurationError with fixed diagnostics and native cause chaining. Direct model construction raises Pydantic ValidationError. Loading preferences grants no authorization or runtime startup.

`domain/` exports 13 pure typed data contracts with explicit opaque IDs, aware UTC timestamps, structural validation, evidence provenance and portable serialization. Targets/scopes are declarations; planner decisions/action requests are unapproved data. ActionResult uses shared ErrorInfo and validates consistent completed/partial/rejected/failed/cancelled/timeout outcomes. Frozen records and mutable state/session containers have no operational transition APIs. Domain depends on pure shared errors, never logging/configuration/operational layers.

`core/errors.py` supplies stable codes, category catch boundaries and concrete configuration/policy/tool/parser/provider/planner/budget/cancellation exceptions, with bounded allowlisted scalar context and explicit conservative retryability. ErrorInfo omits native causes/tracebacks/credentials. `core/results.py` provides typed Success[T]/Failure and the status-discriminated OperationResult[T] union; ActionResult retains its action/evidence role. Caller-authored diagnostics require safe selection; chained causes remain explicit debugging data, not routine dumps.

M0-T06 adds pure `core/audit.py` with 16 stable event types, explicit UTC time/session IDs and optional action/execution/decision/asset correlation. `core/redaction.py` copies and bounds diagnostic JSON, masks known sensitive keys/wrappers and accepts explicitly registered secret values. `core/diagnostics.py` explicitly configures only the project logger, replaces its owned console handler, supports escaped human/JSON output and emits revalidated records through recon_agent.audit. Existing LoggingConfig and ErrorInfo are reused. Native causes/stacks are omitted; malformed records produce fixed omission output and sink failures raise fixed ConfigurationError without raw-record fallback. Imports and data constructors do not configure logging. See docs/logging-and-audit.md for precise redaction and delivery limits.

M1-T01 adds pure synchronous `policy/ScopeValidator` compiled from an explicit immutable Scope snapshot. Exact DNS names, optional domain descendants, IPv4/IPv6, aligned CIDRs and host-level HTTP/HTTPS URLs use deterministic comparisons; exclusions always win. Canonical Target/matched-rule data use existing Success/Failure outcomes; canonical ScopeRejectedError/ErrorInfo carries typed scope reason and safe authority context. RFC1918/IPv6 ULA gating never grants authorization. Unicode/IDN, scoped/mapped IPv6 and ambiguous representations fail closed. No declaration mutation, global config read, audit producer, DNS or contact occurs. See docs/scope-model.md and ADR 0002 for independent concrete-address authorization and future contact/rebinding obligations.

Audit events describe autonomous recon operations and confer no authorization. Event producers, Action/ToolExecution/Finding entities, broader action policy/registry, runner, scanners, Groq/provider/planner runtime, state transitions/deduplication/budget/retry enforcement, autonomous loop, persistence and operational reports remain unimplemented. No chat transcript or private reasoning contract exists. Only M1-T02 is READY; remaining 84 tasks are NOT STARTED.

## Major architecture decisions

- Capability intent never becomes LLM-generated shell/argv; future registry/policy/adapters own authorization and execution.
- Pure centralized scope membership is implemented; broader action validation and contact enforcement remain future work. Discovery/planner recommendations grant no authority.
- ADR 0002 requires independently declared address membership, constrained/pinned approved contacts and revalidation on address/destination changes; no DNS runtime or implicit name-to-IP expansion exists.
- Remote evidence and model recommendations remain non-authoritative data with provenance. Audit records do not authorize replay.
- Pure domain/error models never emit logs. Future application/orchestration services emit concise decision summaries, policy outcomes and execution records, without private reasoning or transcript state.
- Explicit local standard-library logging leaves root/third-party handlers alone, performs no remote upload/file persistence and needs no new runtime dependency or ADR.
- Bounded diagnostics exclude raw environment/output/native causes/commands. Registered secrets and key-labelled secret values are masked; arbitrary unregistered free-text secrets require producer discipline. Source evidence is never mutated.
- Exceptions handle application boundaries; ErrorInfo is portable failure data; generic results support intentionally inspected outcomes. Retryability grants no authority.
- ADR 0001's explicit TOML and separate-secret choice is unchanged. IDs/times, canonical identity and operational mutation remain separate concerns. Groq/SQLite remain planned; default tests are deterministic offline checks.

## Validation

Python 3.14.6 / Pydantic 2.13.5: editable install and pip check passed; 122 focused scope-selected tests (108 new implementation cases); Ruff lint/format; strict Mypy (27 production modules, 28 including the existing result typing test); all 554 tests and coverage passed (99%, 781 statements / 216 branches; two policy defensive lines unexecuted). All 554 tests also passed with network/DNS blocked and Groq key absent. Final sdist/wheel build, guarded external fresh-wheel imports, scope/error/result JSON round trips, manual domain/redirect/private-IP checks, installed CLI and pip check passed. Guards blocked network/process/database/directory/thread/global logging startup and application file use; normal dependency metadata/import reads remained allowed. Source AST, boundary suffix/fallback review, protected-file and archive/dependency parity checks passed. CLI remains the unchanged inert placeholder. Documentation/status/history, secret/artifact and final Git inspections accompany the focused closeout; see TASK_HISTORY for actual evidence and corrected development failures. Python 3.12 was not separately exercised.

Known blockers: None.

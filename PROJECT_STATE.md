# Project state

Project phase: Foundation / configuration, domain and error/result contracts

Completed:

- M0-T01 — Repository governance and planning scaffold (DONE)
- M0-T02 — Python project and developer tooling baseline (DONE)
- M0-T03 — Configuration foundation (DONE)
- M0-T04 — Core domain model foundation (DONE)
- M0-T05 — Error taxonomy and result model (DONE)

Active task: None

Next READY:

- M0-T06 — Logging and audit-event foundation (not started)

## Implementation reality

The 92-task roadmap, governance, maintenance skill and design documentation exist. `recon-agent` 0.1.0 installs through setuptools with Python >=3.12 metadata. Pydantic remains the sole direct runtime dependency; developer tooling and inert CLI are unchanged.

`core/config/` implements strict seven-section settings, defaults < explicit TOML < namespaced environment < programmatic precedence, and separate excluded/redacted credentials. M0-T05 reconciles source/effective validation failures into ConfigurationError with fixed diagnostics and native cause chaining. Direct model construction still raises Pydantic ValidationError. Preferences grant no authorization or operational startup.

`domain/` exports 13 pure typed data contracts with caller-supplied opaque IDs, explicit aware timestamps normalized to UTC, strict structural validation, evidence provenance and portable serialization. Targets/scopes remain declarations; planner decisions/action requests remain unapproved data. ActionResult now uses shared ErrorInfo, distinguishes completed/partial/rejected/failed/cancelled/timeout, and rejects inconsistent error/outcome claims. Record attributes are frozen; mutable state/session containers have no transition APIs. Domain depends only on pure shared error primitives beyond domain/Pydantic types, never configuration or operational layers.

`core/errors.py` supplies stable codes, category catch boundaries and concrete configuration/policy/tool/parser/provider/planner/budget/cancellation exceptions, with bounded allowlisted scalar context and conservative explicit retryability. ErrorInfo serializes data without raw causes/tracebacks/credentials. `core/results.py` supplies typed Success[T]/Failure and the status-discriminated OperationResult[T] union; ActionResult keeps its action/evidence-specific role. Caller-provided diagnostic text/payloads require safe handling; native chained causes are for explicit debugging, not routine diagnostic dumps. See docs/error-model.md and docs/data-model.md.

Action, ToolExecution and Finding remain staged. There is no audit logging, scope enforcement, capability registry/policy, runner, scanner adapter, Groq client, planner runtime, state machine, deduplication/budget enforcement, automatic retry, autonomous loop, SQLite persistence or operational reporting. M0-T06 is READY and unstarted; remaining 86 tasks are NOT STARTED.

## Major architecture decisions

- Capability intent never becomes LLM-generated shell/argv; later registry/policy/adapters own authorization and execution.
- Centralized deterministic fail-closed scope/action validation must precede contact, including derived destinations.
- Remote evidence and model recommendations remain non-authoritative data with provenance.
- Pydantic validates pure data contracts; shared errors/results introduce no I/O or subsystem dependencies.
- Exceptions handle application failure boundaries; ErrorInfo is portable failure data; explicit generic results represent intentionally inspected outcomes. Category derives from stable code; retryability grants no authority.
- Strict bounded context excludes credentials and raw output/environment/traceback dumps. Routine diagnostics exclude native causes; explicit debugging must handle source sensitivity.
- ADR 0001's explicit TOML and separate-secret decision remains unchanged. No new runtime dependency or redundant ADR is needed for M0-T05.
- IDs/times, canonical identity and operational state mutation remain separate concerns. Groq/SQLite stay planned; default tests are deterministic offline checks.

## Validation

Python 3.14.6 / Pydantic 2.13.5: editable install/pip check, 113 focused error/result cases, 329 focused integration/regression cases, Ruff lint/format, strict Mypy (23 production files plus a result typing test), full 330-test suite, coverage (100%, 400 statements / 76 branches), sdist/wheel build and unchanged CLI smoke passed. All 330 tests also passed with connection/DNS functions blocked and Groq key absent. A fresh external wheel environment passed isolated imports, typed result/domain serialization, configuration cause chaining, safe diagnostics, CLI and pip check. Runtime audit/file/logging guards passed, permitting only ordinary installed dependency metadata reads. Source/field security, protected-file, archive/dependency, documentation/status/append-only history and Git inspections passed. See TASK_HISTORY for actual commands/evidence. Python 3.12 was not separately exercised.

Known blockers: None.

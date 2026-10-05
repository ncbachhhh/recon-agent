# Project state

Project phase: M1 / deterministic action policy validated

Completed:

- M0-T01 — Repository governance and planning scaffold (DONE)
- M0-T02 — Python project and developer tooling baseline (DONE)
- M0-T03 — Configuration foundation (DONE)
- M0-T04 — Core domain model foundation (DONE)
- M0-T05 — Error taxonomy and result model (DONE)
- M0-T06 — Logging and audit-event foundation (DONE)
- M1-T01 — Scope model and validator (DONE)
- M1-T02 — Scope regression suite (DONE)
- M1-T03 — Execution runner abstraction (DONE)
- M1-T04 — Capability and Tool Registry (DONE)
- M1-T05 — Action policy validator (DONE)

Active task: None.

Next READY:

- M1-T06 — Execution budgets and rate limiting (not started)

## Implementation reality

The 92-task roadmap, governance, maintenance skill and design documentation exist. `recon-agent` 0.1.0 installs through setuptools with Python >=3.12 metadata. Pydantic remains the sole direct runtime dependency; developer tooling and inert CLI are unchanged.

`core/config/` implements strict seven-section settings, defaults < explicit TOML < namespaced environment < programmatic precedence, and separate excluded/redacted credentials. Configuration source/effective validation failures use ConfigurationError with fixed diagnostics and native cause chaining. Direct model construction raises Pydantic ValidationError. Loading preferences grants no authorization or runtime startup.

`domain/` exports 13 pure typed data contracts with explicit opaque IDs, aware UTC timestamps, structural validation, evidence provenance and portable serialization. Targets/scopes are declarations; planner decisions/action requests are unapproved data. ActionResult uses shared ErrorInfo and validates consistent completed/partial/rejected/failed/cancelled/timeout outcomes. Frozen records and mutable state/session containers have no operational transition APIs. Domain depends on pure shared errors, never logging/configuration/operational layers.

`core/errors.py` supplies stable codes, category catch boundaries and concrete configuration/policy/tool/parser/provider/planner/budget/cancellation exceptions, with bounded allowlisted scalar context and explicit conservative retryability. ErrorInfo omits native causes/tracebacks/credentials. `core/results.py` provides typed Success[T]/Failure and the status-discriminated OperationResult[T] union; ActionResult retains its action/evidence role. Caller-authored diagnostics require safe selection; chained causes remain explicit debugging data, not routine dumps.

M0-T06 adds pure `core/audit.py` with 16 stable event types, explicit UTC time/session IDs and optional action/execution/decision/asset correlation. `core/redaction.py` copies and bounds diagnostic JSON, masks known sensitive keys/wrappers and accepts explicitly registered secret values. `core/diagnostics.py` explicitly configures only the project logger, replaces its owned console handler, supports escaped human/JSON output and emits revalidated records through recon_agent.audit. Existing LoggingConfig and ErrorInfo are reused. Native causes/stacks are omitted; malformed records produce fixed omission output and sink failures raise fixed ConfigurationError without raw-record fallback. Imports and data constructors do not configure logging. See docs/logging-and-audit.md for precise redaction and delivery limits.

M1-T01 adds pure synchronous `policy/ScopeValidator` compiled from an explicit immutable Scope snapshot. Exact DNS names, optional domain descendants, IPv4/IPv6, aligned CIDRs and host-level HTTP/HTTPS URLs use deterministic comparisons; exclusions always win. Canonical Target/matched-rule data use existing Success/Failure outcomes; canonical ScopeRejectedError/ErrorInfo carries typed scope reason and safe authority context. RFC1918/IPv6 ULA gating never grants authorization. Unicode/IDN, scoped/mapped IPv6 and ambiguous representations fail closed. No declaration mutation, global config read, audit producer, DNS or contact occurs. See docs/scope-model.md and ADR 0002 for independent concrete-address authorization and future contact/rebinding obligations.

M1-T02 adds 343 independent regression cases under tests/unit/policy, with socket/DNS guards, deterministic generated suffix/CIDR membership checks, rule permutations and test-only mock contact checks for redirects/discovery. No validator defect was demonstrated; production code and dependencies are unchanged. The corpus verifies the documented boundary, not future production contact enforcement.

M1-T03 adds execution/ProcessSpec, ProcessExecution, ProcessRunner protocol and
AsyncProcessRunner. The internal async primitive launches trusted adapter-owned
executable/argument tuples through create_subprocess_exec, with DEVNULL stdin,
separate raw byte streams, per-stream max_output_bytes retention while concurrently
draining/discarding excess, explicit truncation, return code, UTC wall timestamps
and monotonic duration. Non-zero exits remain Success process facts; canonical
ToolUnavailableError/ToolExecutionError/ToolTimeoutError supply existing Failures.
Spec timeout overrides the snapshotted configured default. Timeout/cancellation
terminate/reap the direct child and escalate to kill after 0.5 seconds; shielded
ownership handles spawn/repeated cancellation races. Python cancellation propagates.
Failure has no partial-output payload; bytes are discarded on failure/cancellation.
JSON raw bytes use URL-safe base64. No argv/executable/environment is returned as
metadata, and the runner emits no logs/audit events or authorization. See
[execution model](docs/execution-model.md) for descendant/OS cleanup limitations.
M1-T03 added no process-tree containment, action policy, rate/concurrency/session
budget runtime, scanner, provider/planner or command CLI. The upstream registry
foundation is now implemented separately in M1-T04.

M1-T04 adds finite CapabilityId/RiskClass enums and strict frozen CapabilityDescriptor
in domain/capabilities.py. The 10 conceptual identities do not imply operational tools.
ActionRequest retains unapproved lowercase-name wire semantics; it adds nested
import_path/python_module rejection without exposing implementation selection.

tools/ implements minimal ToolAdapter abstract identity/definition, AdapterDefinition
with strict extra-forbid Pydantic input/output schema classes, explicit
AdapterRegistration availability snapshots and immutable ToolRegistry. Construction
revalidates/snapshots metadata and rejects duplicate IDs/conflicting capabilities with
canonical ConfigurationError. One explicitly selected trusted adapter per capability;
no globals, dynamic imports, discovery, runtime registration or probing. Default
ToolRegistry is empty. Synchronous lookups return existing Success/Failure: unknown
capability is planner_validation_failed; known unregistered capability/unknown adapter
or unavailable/not_checked registration is tool_unavailable. Only explicit available
registrations resolve; registration/availability grant no authorization. Lexically
sorted tuple catalogs expose only capability, description, risk_class and availability;
internal schema classes/adapter objects are excluded from planner projection. No
runner invocation, scope/budget enforcement, execution/policy audit or config consumption.
See tool-contracts.md and ADR 0003 for trust/lifecycle and future adapter boundaries.

M1-T05 adds pure synchronous ActionPolicyValidator.validate(ActionRequest). It
revalidates action structure, consumes available registry metadata via
capability_definition (no adapter access), applies explicit frozen empty-default
ActionPolicyConfig capability/risk allowlists, checks primary and declared secondary
targets through ScopeValidator and validates the registered strict input schema.
AdapterDefinition.parameter_target_fields is trusted internal metadata: absent None
fails closed; explicit () declares no secondary targets; unique named input fields
support strings/lists/tuples only. Defaults are independently checked. ScopeValidator's
validate_value classifies text then reuses its existing parsing/membership rules.

Existing Success[ApprovedAction]/Failure/ErrorInfo encode outcomes. Approval has
request ID/capability, scope matches and an internal typed parameter model excluded
from dumps/repr, never a reusable permission token. Unknown, unavailable, malformed,
unsupported, disallowed and schema-invalid requests reject with existing canonical
codes. Planner reason/priority/analysis and discovery confer no authority. Explicit
budget/completed-action eligibility interfaces default deny; permitting services exist
only in tests. No actual budgets/rate/reservation/dedup logic, execution, network/DNS,
Groq, dynamic loading or audit producer. Future dispatch must revalidate current facts,
reserve resources atomically and constrain/recheck actual contact. See tool-contracts
and ADR 0004. Existing configuration loader, domain wire fields, errors/results,
runner, CLI, dependencies and future runtime subsystems are unchanged.

Audit events describe autonomous recon operations and confer no authorization. Event producers, Action/ToolExecution/Finding entities, scanners, Groq/provider/planner runtime, state transitions/deduplication/budget/retry enforcement, autonomous loop, persistence and operational reports remain unimplemented. No chat transcript or private reasoning contract exists. Only M1-T06 is READY; remaining 80 tasks are NOT STARTED.

## Major architecture decisions

- Capability intent never becomes LLM-generated shell/argv. Immutable trusted registry supplies facts; local action policy checks eligibility and future adapters own executable construction.
- ADR 0003 selects explicit immutable composition, one selected adapter per capability and semantic-only planner catalog; declared availability defaults fail closed.
- Pure centralized scope and action eligibility are implemented; operational dispatch/contact enforcement remain future work. Discovery/planner recommendations grant no authority.
- ADR 0002 requires independently declared address membership, constrained/pinned approved contacts and revalidation on address/destination changes; no DNS runtime or implicit name-to-IP expansion exists.
- Remote evidence and model recommendations remain non-authoritative data with provenance. Audit records do not authorize replay.
- Pure domain/error models never emit logs. Future application/orchestration services emit concise decision summaries, policy outcomes and execution records, without private reasoning or transcript state.
- Explicit local standard-library logging leaves root/third-party handlers alone, performs no remote upload/file persistence and needs no new runtime dependency or ADR.
- Bounded diagnostics exclude raw environment/output/native causes/commands. Registered secrets and key-labelled secret values are masked; arbitrary unregistered free-text secrets require producer discipline. Source evidence is never mutated.
- Exceptions handle application boundaries; ErrorInfo is portable failure data; generic results support intentionally inspected outcomes. Retryability grants no authority.
- ADR 0001's explicit TOML and separate-secret choice is unchanged. IDs/times, canonical identity and operational mutation remain separate concerns. Groq/SQLite remain planned; default tests are deterministic offline checks.

## Validation

M1-T05: Python 3.14.6 / Pydantic 2.13.5 only; Python 3.12 was not tested.
Editable install/pip check passed. Focused final policy: 103 cases (included in the
309-case policy/registry/scope pass). Full, coverage and network/DNS-blocked suites:
each 1,167 passed. Ruff lint/format (73 files), strict Mypy (33 production modules),
sdist/wheel build, editable/fresh-wheel inert CLI, fresh-wheel guarded cold imports/
policy checks/pip check, static security/secret/artifact/source/README/dependency
checks and Git whitespace checks passed. Coverage 99% overall (1,132 statements /
288 branches); new action-policy and registry/base changes 100%. Only the existing
defensive scope unsupported-kind line/branch remains uncovered. Unit/wheel guards
prohibit policy execution/network/DNS/runner/dynamic imports/log startup; no scanner
or provider call exists. Offline full-suite allows AF_UNIX event-loop self-pipes for
existing local runner tests; parent guards do not sandbox children, whose harmless
local interpreter scripts were reviewed for no networking. Package-index access is
limited to installation/build provisioning. See TASK_HISTORY for acceptance/evidence.

Known blockers: None.

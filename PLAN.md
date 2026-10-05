# Implementation plan

## Roadmap operating model

This is the repository task specification, not a list of implemented features. M0-T01 bootstraps governance and inert package boundaries. Future work follows [AGENTS.md](AGENTS.md) and the [maintenance skill](.codex/skills/recon-project-maintainer/SKILL.md); one implementation task may be IN PROGRESS at a time. Current reality is in [PROJECT_STATE.md](PROJECT_STATE.md).

Statuses: **NOT STARTED**, **READY**, **IN PROGRESS**, **BLOCKED**, **DONE**. A task is eligible for READY only after all dependencies are DONE and its prerequisite/working-tree gate is reviewed. DONE requires every criterion, focused and complete phase-appropriate validation, current docs/state/history, and a focused commit when authorized and safe. Never silently broaden scope or weaken acceptance.

Priorities: **P0** safety/foundation/release gate; **P1** core product work; **P2** output/experience improvements. Dependencies take precedence over priority or milestone numbering. Cross-milestone dependencies are deliberate: M8 persistence can follow M1, then enables M7 history/resume; M10 reports precede M9 report wiring; M9 framework can follow M0. The project remains sequential in execution even where the dependency graph offers choices.

Every task inherits the repository security invariants: authorized reconnaissance only; no unrestricted shell or shell=True; predefined capabilities and argv-only adapters; centralized fail-closed target/redirect/derived-host validation; deterministic AI policy gate; enforceable time/rate/resource limits; secret separation; untrusted remote/model data; deterministic offline default tests. Local SQLite session persistence is distinct from prohibited remote persistence. No task implicitly authorizes external scans, API calls in tests, publishing, pushing, or unrelated changes.

## Validation and completion evidence

Each specification lists focused validation. Also run complete repository validation defined in [testing strategy](docs/testing-strategy.md). M0-T01 uses direct scaffold/document checks; M0-T02 establishes exact lint/type/test/build/smoke commands for all subsequent tasks. Mark external binary/network integration explicitly and exclude it from normal tests/CI. Report only actually executed checks. Update PLAN/state/CURRENT_TASK/history for every lifecycle transition; update CHANGELOG for visible changes. Expected evidence belongs in append-only history and the task-owned focused diff/commit, not conversation memory.

Library/client/CLI/migration choices remain open where not mandated. Decide consequential alternatives with an ADR using [the template](docs/decisions/0000-template.md) when evidence is available. A task's repository areas identify boundaries; only files needed for that task may change. Documentation impact lists documents to reconcile when affected, plus mandatory PLAN/PROJECT_STATE/CURRENT_TASK/TASK_HISTORY updates for every task.

## Milestone M0 — Repository foundation

### M0-T01 — Repository governance and planning scaffold

- **ID:** `M0-T01`
- **Title:** Repository governance and planning scaffold
- **Status:** DONE
- **Priority:** P0
- **Dependencies:** None (bootstrap entry task)

**Objective:** Establish repository truth, disciplined task lifecycle, and the full safety-oriented implementation roadmap before production work.

**Repository areas:** Root governance/state files; docs/; .codex/skills/; src/recon_agent/; tests/

**In scope:** Required root governance files; maintenance skill and references; architecture/security/contracts/testing/configuration documentation; ADR template; inert package/test layout; Git initialization and one focused commit if safe.

**Out of scope:** Python developer tooling (M0-T02); production models, CLI, adapters, process runner, network traffic, Groq client, and database implementation. All unrelated/future task work is excluded.

**Implementation steps:**

1. Inspect repository and Git preserving existing work
2. Record M0-T01 active
3. Create scaffold, skill and full roadmap
4. Inspect documents/source and validate required paths/statuses/dependencies
5. Reconcile idle state/history and commit only task changes.

**Acceptance criteria:**

1. Every requested path exists including tracked test directories
2. AGENTS contains all mandatory operating/security rules and startup order
3. Skill has valid YAML and two linked references
4. Docs cover all specified layers/contracts/trust boundaries
5. All 92 roadmap tasks have full specifications
6. Only M0-T01 becomes DONE, M0-T02 READY, remaining tasks NOT STARTED
7. Source remains package markers only
8. No credentials or unrelated changes
9. No active task at closure
10. Exactly one focused commit if safe, with no push.

**Tests/validation:** Direct required-file inspection; Markdown heading/fence/local-link checks; unique task IDs and valid acyclic dependencies; task-field/status checks; skill validator; inert-source and secret inspection; final Git diff/whitespace/staged-path review and post-commit tree check. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** README.md; architecture, configuration, data-model, security, and testing docs as applicable; governance/state/history. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Document every invariant without creating an execution path; no scanners, API calls, unrestricted shell facility, or remote traffic. Repository invariants remain mandatory.

**Expected evidence of completion:** Required-file inventory, skill validation output, roadmap/status/dependency checks, inert-source/secret inspection, Markdown/link inspection, focused staged diff and bootstrap commit/tree result, recorded in TASK_HISTORY.

### M0-T02 — Python project and developer tooling baseline

- **ID:** `M0-T02`
- **Title:** Python project and developer tooling baseline
- **Status:** DONE
- **Priority:** P0
- **Dependencies:** `M0-T01`

**Objective:** Make the inert package installable and establish reproducible developer validation before adding runtime behavior.

**Repository areas:** pyproject.toml; .gitignore; development dependency/build configuration; src/recon_agent/cli/ placeholder; tests/; README and testing docs

**In scope:** pyproject.toml metadata and Python >=3.12; src packaging/build configuration; Ruff, Mypy, Pytest and coverage settings; development dependency strategy; .gitignore; console entry-point placeholder.

**Out of scope:** Reconnaissance, network/Groq clients, real configuration loader, policy or tool execution. All unrelated/future task work is excluded.

**Implementation steps:**

1. Select/document build and dependency approach, using ADR if alternatives matter
2. Configure strict practical lint/type/offline test baseline and integration markers
3. Create non-scanning CLI placeholder and meaningful packaging/smoke checks
4. Document exact validation commands.

**Acceptance criteria:**

1. Package builds and installs from clean environment with Python >=3.12 metadata
2. Console entry point runs a non-network placeholder/help
3. Lint/format, types, offline tests and build all pass using documented commands
4. Coverage and opt-in integration selection are configured
5. Dependency setup is reproducible
6. .gitignore protects generated files/local secrets without concealing required files.

**Tests/validation:** Run Ruff checks, Mypy, default offline Pytest and package build; install built artifact in isolated environment and run placeholder/help smoke; verify no credentials or binaries are required. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** README.md; architecture, configuration, data-model, security, and testing docs as applicable; governance/state/history. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** No scanner installation or traffic; default test selection excludes external targets/binaries; do not place keys in metadata or lock/dependency files. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for Python project and developer tooling baseline; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M0-T03 — Configuration foundation

- **ID:** `M0-T03`
- **Title:** Configuration foundation
- **Status:** DONE
- **Priority:** P0
- **Dependencies:** `M0-T02`

**Objective:** Provide typed validated configuration and an explicit override strategy without turning secrets into ordinary state.

**Repository areas:** src/recon_agent/core/ configuration module; tests/unit/; docs/configuration.md and security model

**In scope:** Pydantic scope, execution, planner, tools, persistence, logging and reporting sections; budget settings; defaults plus file/environment precedence; separate secret mechanism.

**Out of scope:** Running tools/provider requests; CLI session start; database setup; choosing active target scope implicitly. All unrelated/future task work is excluded.

**Implementation steps:**

1. Define schema and restrictive defaults
2. Decide file format/discovery and allowed environment overrides
3. Implement loading and redacted effective configuration
4. Document errors and precedence.

**Acceptance criteria:**

1. Defaults/file/environment overrides follow documented deterministic precedence
2. Malformed/unknown settings fail validation
3. Absent scope cannot authorize actions
4. GROQ_API_KEY can be supplied separately without appearing in serialized config/repr/errors
5. Loading alone causes no network/tool activity.

**Tests/validation:** Offline tests for defaults, override conflicts, malformed/unknown fields, missing scope, secret absence/redaction and file errors; full tooling baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** README.md; architecture, configuration, data-model, security, and testing docs as applicable; governance/state/history. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Trusted settings must still satisfy repository invariants; remote/model input cannot set config; fail closed on ambiguous scope and secret exposure. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for Configuration foundation; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M0-T04 — Core domain model foundation

- **ID:** `M0-T04`
- **Title:** Core domain model foundation
- **Status:** DONE
- **Priority:** P0
- **Dependencies:** `M0-T03`

**Objective:** Establish pure typed identities and contracts for evidence-driven state before adapters or planner logic.

**Repository areas:** src/recon_agent/domain/; tests/unit/; docs/data-model.md and architecture

**In scope:** Target, Scope, Asset, Host, Service, Endpoint, Observation, Evidence, ActionRequest, ActionResult, PlannerDecision, ReconState and ReconSession; conceptually associated Action/ToolExecution/Finding records or explicit documented staging.

**Out of scope:** Scanners, process/network code, provider clients, SQLite bindings and orchestration decisions. All unrelated/future task work is excluded.

**Implementation steps:**

1. Define typed fields/relationships and serialization
2. Distinguish facts/evidence/interpretation/recommendations
3. Define identity/provenance and validation rules
4. Map documentation entities to implemented or deferred models.

**Acceptance criteria:**

1. All required initial models construct/serialize/round-trip valid data and reject malformed fields
2. Observations/evidence/decisions remain distinct
3. Domain imports have no provider, process or storage side effects
4. Staged entities are explicitly documented without claiming implementation.

**Tests/validation:** Unit tests for valid/invalid models, relationships, provenance, round-trips and identity cases; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** README.md; architecture, configuration, data-model, security, and testing docs as applicable; governance/state/history. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Target presence does not confer authorization; untrusted text remains labeled; no secret fields in public state snapshots. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for Core domain model foundation; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M0-T05 — Error taxonomy and result model

- **ID:** `M0-T05`
- **Title:** Error taxonomy and result model
- **Status:** DONE
- **Priority:** P0
- **Dependencies:** `M0-T04`

**Objective:** Expose structured failure semantics so policy, tools and planner never use arbitrary strings as control flow.

**Repository areas:** src/recon_agent/core/ error/result modules; relevant domain result contracts; tests/unit/; architecture/data-model docs

**In scope:** Configuration error, scope rejection, tool unavailable/timeout/execution failure, parser failure, provider failure, planner validation failure and budget exhaustion; typed outcome context.

**Out of scope:** Real process execution, network adapters or retry/orchestration implementation. All unrelated/future task work is excluded.

**Implementation steps:**

1. Define exception/result hierarchy and stable error identifiers
2. Distinguish rejection/failure/partial result
3. Provide safe structured context and serialization
4. Align ActionResult contract.

**Acceptance criteria:**

1. Every listed category has typed representation
2. Callers can branch on types/codes rather than message text
3. Timeout/rejection/parser error cannot imply success
4. Error context is serializable and secret-safe.

**Tests/validation:** Unit tests of category mapping, result serialization, partial/error outcomes and redaction; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** README.md; architecture, configuration, data-model, security, and testing docs as applicable; governance/state/history. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Errors must not leak keys or unbounded remote text; failure never authorizes broader fallback. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for Error taxonomy and result model; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M0-T06 — Logging and audit-event foundation

- **ID:** `M0-T06`
- **Title:** Logging and audit-event foundation
- **Status:** DONE
- **Priority:** P0
- **Dependencies:** `M0-T05`

**Objective:** Create local structured audit primitives for traceable decisions and execution without leaking sensitive inputs.

**Repository areas:** src/recon_agent/core/ logging/audit modules; configuration schema as needed; tests/unit/; configuration/security/data-model docs

**In scope:** Session lifecycle, planner decision, policy rejection, budget and execution metadata events; local logging configuration and redaction.

**Out of scope:** Remote log upload, actual tool/provider execution and persistence implementation. All unrelated/future task work is excluded.

**Implementation steps:**

1. Define event schemas and safe context
2. Implement configurable local sinks/redaction
3. Support correlation/session/action IDs
4. Document retention and log-level behavior.

**Acceptance criteria:**

1. Listed event types serialize with correlation and timestamps
2. Redaction covers secret settings and error contexts
3. Untrusted text is bounded/escaped
4. Local logging needs no credentials/network and does not alter policy.

**Tests/validation:** Captured-sink unit tests for event shape, correlation, secret redaction and remote control text; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** README.md; architecture, configuration, data-model, security, and testing docs as applicable; governance/state/history. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Keys are never logged; evidence remains untrusted; local audit storage is distinct from remote persistence. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for Logging and audit-event foundation; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

## Milestone M1 — Safety and deterministic execution core

### M1-T01 — Scope model and validator

- **ID:** `M1-T01`
- **Title:** Scope model and validator
- **Status:** READY
- **Priority:** P0
- **Dependencies:** `M0-T06`

**Objective:** Centralize fail-closed authorization for every target and derived destination.

**Repository areas:** src/recon_agent/domain/, policy/, execution/, orchestration/, tools/; tests/unit/ and fixtures/

**In scope:** Domains, explicit subdomain rules, IP/CIDR, IPv4/IPv6, URLs and redirect-derived targets; normalization, exclusions and resolution/address-change semantics.

**Out of scope:** Live scanners, permissive discovery-driven scope expansion and remote authorization inference. All unrelated/future task work is excluded.

**Implementation steps:**

1. Define exact-domain/subdomain/IP authorization semantics and ambiguous URL handling
2. Resolve DNS/IP and rebinding policy in an ADR if needed
3. Implement a single validator and structured rejection reasons
4. Define revalidation hooks before any derived contact.

**Acceptance criteria:**

1. Allowed/denied results are deterministic with canonical targets and explicit reasons
2. Lookalikes, malformed targets and ambiguous scope fail closed
3. Redirects/new hostnames require new validation
4. DNS/address semantics are documented and cannot silently authorize arbitrary IP scanning.

**Tests/validation:** Offline table tests for each target category, exact/subdomain boundary, exclusions, malformed inputs and redirect changes; full baseline; deeper corpus follows M1-T02. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** docs/security-model.md; docs/architecture.md; docs/data-model.md; docs/tool-contracts.md; docs/testing-strategy.md. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** No network needed for validation tests; never accept a suffix match without label boundary; post-contact filtering is insufficient. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for Scope model and validator; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M1-T02 — Scope regression suite

- **ID:** `M1-T02`
- **Title:** Scope regression suite
- **Status:** NOT STARTED
- **Priority:** P0
- **Dependencies:** `M1-T01`

**Objective:** Prove scope safety against confusing host/URL/IP representations before network adapters depend on it.

**Repository areas:** src/recon_agent/domain/, policy/, execution/, orchestration/, tools/; tests/unit/ and fixtures/

**In scope:** Exact domain, allowed subdomains, lookalikes/suffix confusion, IPv4/IPv6, CIDR boundaries, URL parsing, redirect scope changes, malformed inputs and canonicalization cases.

**Out of scope:** Live Internet probes and unrelated policy redesign. All unrelated/future task work is excluded.

**Implementation steps:**

1. Build an independently reasoned allowed/denied corpus
2. Cover parsing/encoding/case/address edge cases and exclusions
3. Verify derived-target rejection before dispatch
4. Repair only demonstrated validator defects within scope.

**Acceptance criteria:**

1. All required edge-case groups have explicit expected outcomes
2. Out-of-scope/lookalike/ambiguous targets are denied
3. Authorized canonical forms behave consistently
4. Fake dispatch shows no contact on rejection
5. Regression suite runs offline.

**Tests/validation:** Run scope regression suite and full baseline; record bug examples and resulting behavior, with no external resolution. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** docs/security-model.md; docs/architecture.md; docs/data-model.md; docs/tool-contracts.md; docs/testing-strategy.md. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Use reserved fixture names and addresses only as data; tests must not grant authority based on discovery. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for Scope regression suite; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M1-T03 — Execution runner abstraction

- **ID:** `M1-T03`
- **Title:** Execution runner abstraction
- **Status:** NOT STARTED
- **Priority:** P0
- **Dependencies:** `M1-T02`

**Objective:** Provide controlled async-capable process execution with bounded failure and cancellation behavior.

**Repository areas:** src/recon_agent/domain/, policy/, execution/, orchestration/, tools/; tests/unit/ and fixtures/

**In scope:** Argv-only runner interface; timeouts; stdout/stderr capture; return code; cancellation/child cleanup; bounded output and structured metadata; injected fake runner.

**Out of scope:** LLM access to runner, unrestricted command endpoint, real reconnaissance adapters and shell strings. All unrelated/future task work is excluded.

**Implementation steps:**

1. Define runner input/result contracts restricted to adapter dispatch
2. Implement no-shell async process handling
3. Enforce time/output/cancellation limits
4. Expose injected fakes and structured errors.

**Acceptance criteria:**

1. Runner accepts approved argv arrays only and never uses shell=True
2. Captures status and bounded stdout/stderr
3. Timeout/cancel terminate child work and report metadata
4. Missing executable/non-zero exit/overflow are distinguishable
5. No planner-facing execution API.

**Tests/validation:** Fake-process tests for success, failure, timeout, cancellation, output bounds and argument fidelity; any real harmless-process tests explicitly marked; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** docs/security-model.md; docs/architecture.md; docs/data-model.md; docs/tool-contracts.md; docs/testing-strategy.md. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** No shell or arbitrary planner argv; audit context redacts secrets; bounded resources must survive error paths. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for Execution runner abstraction; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M1-T04 — Capability and Tool Registry

- **ID:** `M1-T04`
- **Title:** Capability and Tool Registry
- **Status:** NOT STARTED
- **Priority:** P0
- **Dependencies:** `M1-T03`

**Objective:** Separate semantic capabilities from deterministic adapter selection and availability.

**Repository areas:** src/recon_agent/domain/, policy/, execution/, orchestration/, tools/; tests/unit/ and fixtures/

**In scope:** Typed capability schemas, risk classes, adapter registration, deterministic resolution and availability catalog; fixture/fake adapters.

**Out of scope:** Real scanners, runtime model-generated capabilities and arbitrary binary/flag registration from planner output. All unrelated/future task work is excluded.

**Implementation steps:**

1. Define catalog identities and input/output schemas
2. Add deterministic selection/availability handling
3. Reject unknown/duplicate registry entries
4. Expose sanitized catalog for future planner/CLI.

**Acceptance criteria:**

1. Known capability resolves only to configured registered adapter
2. Unknown/invented capability is rejected
3. Duplicate/conflicting entries fail clearly
4. Unavailable tools are structured outcomes
5. Catalog has no executable secret paths exposed unnecessarily.

**Tests/validation:** Unit tests for registration/conflicts, selection, unavailable tools, serialization and unknown capability; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** docs/security-model.md; docs/architecture.md; docs/data-model.md; docs/tool-contracts.md; docs/testing-strategy.md. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Installation/availability is not authorization; model cannot mutate registry or choose arbitrary executable. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for Capability and Tool Registry; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M1-T05 — Action policy validator

- **ID:** `M1-T05`
- **Title:** Action policy validator
- **Status:** NOT STARTED
- **Priority:** P0
- **Dependencies:** `M1-T04`, `M1-T02`

**Objective:** Authorize each requested action deterministically before any execution.

**Repository areas:** src/recon_agent/domain/, policy/, execution/, orchestration/, tools/; tests/unit/ and fixtures/

**In scope:** Capability existence, target scope, parameter schema, risk allowlist, budget availability and unnecessary completed-action rejection; dispatch revalidation contract.

**Out of scope:** Actual scanner execution or trusting a planner summary as authorization. All unrelated/future task work is excluded.

**Implementation steps:**

1. Compose registry/scope/parameter/risk checks
2. Define budget/dedup interfaces for later implementations
3. Return typed approval/rejection with audit reason
4. Ensure approval cannot skip dispatch checks.

**Acceptance criteria:**

1. Unknown capability, outside target, invalid/extra parameters, forbidden risk, insufficient budget and needless repeated action are denied
2. Allowed action produces typed validated request
3. Fake execution never receives denied requests
4. Pending budget/dedup interfaces are restrictive fakes until implemented.

**Tests/validation:** Policy matrix with allowed/denied requests, injection-shaped parameters and stale approval; fake dispatch assertions; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** docs/security-model.md; docs/architecture.md; docs/data-model.md; docs/tool-contracts.md; docs/testing-strategy.md. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** All targets including redirects require centralized checks; reasons cannot inject arguments; fail closed on unavailable policy data. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for Action policy validator; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M1-T06 — Execution budgets and rate limiting

- **ID:** `M1-T06`
- **Title:** Execution budgets and rate limiting
- **Status:** NOT STARTED
- **Priority:** P0
- **Dependencies:** `M1-T05`

**Objective:** Bound work and traffic independently of model recommendations, including concurrent dispatch.

**Repository areas:** src/recon_agent/domain/, policy/, execution/, orchestration/, tools/; tests/unit/ and fixtures/

**In scope:** Max actions/session, max concurrency, per-tool rate, per-host budget, session timeout and output-size limits; atomic reservation/release and retry accounting.

**Out of scope:** Live load tests, unlimited defaults and planner-controlled budget changes. All unrelated/future task work is excluded.

**Implementation steps:**

1. Define counting/time semantics and restrictive defaults
2. Implement shared budget/rate controller with injected clock
3. Integrate validator/dispatch reservations
4. Record exhaustion/cancellation accounting.

**Acceptance criteria:**

1. Every specified limit is enforceable with documented counting semantics
2. Concurrent requests cannot oversubscribe reservations
3. Exhaustion prevents dispatch
4. Timeout and cancellation release/account correctly
5. Planner cannot extend budgets.

**Tests/validation:** Deterministic fake-clock tests for boundaries, concurrent reservation, rate windows, retry/cancel accounting and output caps; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** docs/security-model.md; docs/architecture.md; docs/data-model.md; docs/tool-contracts.md; docs/testing-strategy.md. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Check/reserve atomically before traffic; no failure path silently resets budgets. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for Execution budgets and rate limiting; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M1-T07 — ReconState state machine

- **ID:** `M1-T07`
- **Title:** ReconState state machine
- **Status:** NOT STARTED
- **Priority:** P0
- **Dependencies:** `M1-T06`, `M0-T04`

**Objective:** Maintain consistent evidence and action lifecycle through success, failure and rejection.

**Repository areas:** src/recon_agent/domain/, policy/, execution/, orchestration/, tools/; tests/unit/ and fixtures/

**In scope:** Known assets, observations, completed/failed/rejected actions, evidence, planner decisions and budgets; typed transitions.

**Out of scope:** Scanners, provider calls and database binding. All unrelated/future task work is excluded.

**Implementation steps:**

1. Define lifecycle transition rules and invariants
2. Implement controlled state updates and evidence relationships
3. Integrate budget outcomes
4. Preserve rejection/failure histories.

**Acceptance criteria:**

1. Invalid transitions are rejected
2. Successful observations retain provenance
3. Failed/rejected actions never become successful facts
4. Assets/history/budgets update coherently
5. Serialized state preserves decision/evidence distinctions.

**Tests/validation:** Transition table, rollback/error cases, evidence-link integrity, budget update and serialization tests; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** docs/security-model.md; docs/architecture.md; docs/data-model.md; docs/tool-contracts.md; docs/testing-strategy.md. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Untrusted content cannot mutate policy; discovering an asset does not make it authorized. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for ReconState state machine; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M1-T08 — Action deduplication

- **ID:** `M1-T08`
- **Title:** Action deduplication
- **Status:** NOT STARTED
- **Priority:** P0
- **Dependencies:** `M1-T07`

**Objective:** Prevent repeated equivalent work and bounded-retry loops using canonical action identity.

**Repository areas:** src/recon_agent/domain/, policy/, execution/, orchestration/, tools/; tests/unit/ and fixtures/

**In scope:** Capability/target/parameter canonical identity; completed and in-flight equivalence; explicit retry eligibility; validator/state integration.

**Out of scope:** Asset/finding dedup beyond what action identity needs and AI prioritization logic. All unrelated/future task work is excluded.

**Implementation steps:**

1. Define canonical parameter/target identity
2. Implement completed/in-flight lookup
3. Connect policy denial and bounded failed-action retries
4. Document equivalence and deliberate rerun semantics.

**Acceptance criteria:**

1. Equivalent authorized requests collapse consistently despite representation/order differences
2. Distinct meaningful parameters remain distinct
3. Completed/in-flight duplicates deny dispatch
4. Failed actions retry only within configured limits
5. No policy bypass via alternate target spelling.

**Tests/validation:** Table tests for canonical equivalents, distinct requests, concurrent duplicates and bounded retry; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** docs/security-model.md; docs/architecture.md; docs/data-model.md; docs/tool-contracts.md; docs/testing-strategy.md. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Dedup never broadens scope or treats failed work as successful evidence. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for Action deduplication; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

## Milestone M2 — Basic asset discovery adapters

### M2-T01 — DNS resolver capability

- **ID:** `M2-T01`
- **Title:** DNS resolver capability
- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** `M1-T08`

**Objective:** Collect deterministic DNS records through a bounded scoped resolver capability.

**Repository areas:** src/recon_agent/tools/, execution/, policy/, orchestration/; tests/unit/, fixtures/, integration/

**In scope:** Native resolver or adapter abstraction for resolve_dns; typed records, resolver context, availability/errors, fixtures and normalized evidence.

**Out of scope:** Unscoped recursive discovery, provider planning and port/service scans. All unrelated/future task work is excluded.

**Implementation steps:**

1. Choose resolver approach based on scope/testability constraints
2. Define record and target schema
3. Enforce scoped requests/timeouts/budgets
4. Normalize records with evidence and validate discovered names/addresses before follow-up.

**Acceptance criteria:**

1. Authorized names produce typed records/provenance through fake resolver
2. Missing/malformed/timeout answers are structured
3. Derived destinations do not automatically become actionable
4. Resolver network behavior is bounded and documented.

**Tests/validation:** Fixture/fake resolver tests for common record types, no-answer, malformed/timeout responses and outside derived addresses; opt-in local integration only; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** docs/tool-contracts.md; docs/architecture.md; docs/data-model.md; docs/security-model.md; docs/testing-strategy.md. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** DNS data is untrusted; an answer grants no new target authority; enforce documented resolution/IP semantics. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for DNS resolver capability; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M2-T02 — Subfinder adapter

- **ID:** `M2-T02`
- **Title:** Subfinder adapter
- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** `M2-T01`

**Objective:** Add passive subdomain enumeration behind enumerate_subdomains without exposing tool flags to the planner.

**Repository areas:** src/recon_agent/tools/, execution/, policy/, orchestration/; tests/unit/, fixtures/, integration/

**In scope:** Availability/version detection, validated argv, controlled runner invocation, parser fixtures and normalized observations.

**Out of scope:** Automatic scans of discovered names, unrestricted sources/flags and credentials in outputs. All unrelated/future task work is excluded.

**Implementation steps:**

1. Define bounded schema and passive/source policy
2. Detect availability without scanning
3. Build fixed argv and parse machine-readable records
4. Validate subdomain candidates and attach provenance.

**Acceptance criteria:**

1. Known fixture output normalizes candidates with source/evidence
2. Malformed output/missing binary/timeout are structured
3. Argv honors limits and denies extra parameters
4. Outside names remain rejected/unactionable
5. Passive third-party data handling is documented.

**Tests/validation:** Fixture parsers and fake-runner argv/failure/scope tests; opt-in binary integration excluded by default; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** docs/tool-contracts.md; docs/architecture.md; docs/data-model.md; docs/security-model.md; docs/testing-strategy.md. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Enumeration does not authorize follow-up traffic; configured external sources are explicit; secrets are redacted. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for Subfinder adapter; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M2-T03 — DNSX adapter

- **ID:** `M2-T03`
- **Title:** DNSX adapter
- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** `M2-T02`

**Objective:** Verify discovered names in bounded batches and normalize DNS evidence.

**Repository areas:** src/recon_agent/tools/, execution/, policy/, orchestration/; tests/unit/, fixtures/, integration/

**In scope:** Bulk scoped DNS verification, DNSX availability/argv/parser, normalized records, rate and batch limits.

**Out of scope:** Permissive wildcard promotion, outside-name resolution and arbitrary DNSX arguments. All unrelated/future task work is excluded.

**Implementation steps:**

1. Define scoped batch inputs and allowed record modes
2. Build bounded invocation
3. Parse verified records/resolution metadata
4. Handle wildcard/partial/error results without inventing assets.

**Acceptance criteria:**

1. Only validated batch entries dispatch
2. Records retain name/address provenance
3. Batch/rate/output limits apply
4. Wildcard/ambiguous answers are flagged under documented policy
5. Derived IPs/hostnames require validation before action.

**Tests/validation:** Sanitized record/wildcard/partial fixtures; fake-runner batch, argv, limits and outside-target tests; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** docs/tool-contracts.md; docs/architecture.md; docs/data-model.md; docs/security-model.md; docs/testing-strategy.md. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Validate each batch target before contact; DNSX defaults cannot broaden recursion/scope. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for DNSX adapter; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M2-T04 — HTTPX adapter

- **ID:** `M2-T04`
- **Title:** HTTPX adapter
- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** `M2-T03`

**Objective:** Collect HTTP service metadata as normalized scoped observations.

**Repository areas:** src/recon_agent/tools/, execution/, policy/, orchestration/; tests/unit/, fixtures/, integration/

**In scope:** probe_http availability/argv/parser; URL, status, title, server, content type, redirect and technology hints with provenance.

**Out of scope:** Uncontrolled redirect following, crawling, authentication or exploit requests. All unrelated/future task work is excluded.

**Implementation steps:**

1. Define allowed probe methods/options and redirect strategy
2. Disable implicit outside contact
3. Implement bounded runner/parser
4. Normalize metadata and validate every redirect before later contact/use.

**Acceptance criteria:**

1. Fixture metadata fields normalize consistently
2. Target and redirects enforce scope before request
3. Unknown/unsafe redirect behavior rejects mode
4. Output/time/rate limits apply
5. Failures and absent fields do not invent service facts.

**Tests/validation:** Fixture HTTP metadata and fake-runner tests for redirects inside/outside scope, malformed URL/output, argv and timeouts; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** docs/tool-contracts.md; docs/architecture.md; docs/data-model.md; docs/security-model.md; docs/testing-strategy.md. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** HTTP headers/titles/technology hints are untrusted; post-response redirect filtering cannot protect prior outside requests. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for HTTPX adapter; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M2-T05 — Naabu port discovery adapter

- **ID:** `M2-T05`
- **Title:** Naabu port discovery adapter
- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** `M2-T04`

**Objective:** Expose bounded port discovery with deliberate approved port sets.

**Repository areas:** src/recon_agent/tools/, execution/, policy/, orchestration/; tests/unit/, fixtures/, integration/

**In scope:** discover_ports adapter availability/argv/parser, configured finite port ranges, target/rate/concurrency limits and service observations.

**Out of scope:** Uncontrolled full-range defaults, stealth/evasion modes, arbitrary scan flags and deeper fingerprinting. All unrelated/future task work is excluded.

**Implementation steps:**

1. Define approved port set and transport/risk settings
2. Reject excessive/malformed ranges
3. Build bounded invocation and normalize open-port evidence
4. Connect scope/budget/timeout controls.

**Acceptance criteria:**

1. No implicit full-range scan
2. Only authorized targets and approved ranges dispatch
3. Parser yields host/port/transport facts with evidence
4. Missing binary/timeout/partial output are explicit
5. Rate/concurrency settings are enforced.

**Tests/validation:** Fixture ports, boundary/invalid range tests, fake argv/scope/budget/failure tests; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** docs/tool-contracts.md; docs/architecture.md; docs/data-model.md; docs/security-model.md; docs/testing-strategy.md. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** No evasion/stealth or unbounded traffic; tool-internal target expansion must remain constrained. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for Naabu port discovery adapter; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M2-T06 — Nmap service fingerprint adapter

- **ID:** `M2-T06`
- **Title:** Nmap service fingerprint adapter
- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** `M2-T05`

**Objective:** Identify services more deeply on already discovered approved ports.

**Repository areas:** src/recon_agent/tools/, execution/, policy/, orchestration/; tests/unit/, fixtures/, integration/

**In scope:** fingerprint_services adapter; bounded explicit targets/ports; machine-readable parsing where practical; protocol/product/version observations.

**Out of scope:** Default vulnerability/exploit scripts, unrestricted NSE/flags, credential tests, stealth and broad undiscovered port scans. All unrelated/future task work is excluded.

**Implementation steps:**

1. Define safe fingerprint profile and explicit port inputs
2. Construct controlled argv
3. Parse XML or suitable machine-readable format defensively
4. Retain banner/evidence and structured execution failures.

**Acceptance criteria:**

1. Only validated hosts and approved discovered ports dispatch
2. Safe profile excludes arbitrary scripts/options
3. Machine-readable fixtures normalize services/provenance
4. Malformed/partial output remains explicit
5. Timeout/output limits work.

**Tests/validation:** Sanitized XML/service fixtures including hostile text/malformed input; argv profile and fake timeout/scope tests; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** docs/tool-contracts.md; docs/architecture.md; docs/data-model.md; docs/security-model.md; docs/testing-strategy.md. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Banners are evidence not instructions; disable parser external-resource expansion; no intrusive scripts or shell fallback. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for Nmap service fingerprint adapter; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M2-T07 — Initial deterministic discovery pipeline

- **ID:** `M2-T07`
- **Title:** Initial deterministic discovery pipeline
- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** `M2-T06`

**Objective:** Prove discovery adapters populate state under explicit workflows before adding AI.

**Repository areas:** src/recon_agent/tools/, execution/, policy/, orchestration/; tests/unit/, fixtures/, integration/

**In scope:** Explicit scoped DNS/subdomain/HTTP/port/service discovery coordination with registry, validator, budgets and ReconState.

**Out of scope:** Groq planning, autonomous action selection and live public-target tests. All unrelated/future task work is excluded.

**Implementation steps:**

1. Define deterministic requested workflow
2. Route every step through policy/registry/runner
3. Normalize results and derived-target validation
4. Persist in-memory state and audit outcomes with fakes.

**Acceptance criteria:**

1. Offline workflow produces traceable assets/services/observations
2. No action skips policy
3. Outside discoveries never dispatch
4. Failures/rejections remain recorded
5. Budgets/dedup prevent repeats
6. No provider required.

**Tests/validation:** Fake adapter end-to-end workflow for success, scope rejection, failure, budget and dedup; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** docs/tool-contracts.md; docs/architecture.md; docs/data-model.md; docs/security-model.md; docs/testing-strategy.md. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Initial seed execution is gated just like follow-up actions; new targets cannot silently widen scope. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for Initial deterministic discovery pipeline; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

## Milestone M3 — Web reconnaissance capabilities

### M3-T01 — Common-file inspector

- **ID:** `M3-T01`
- **Title:** Common-file inspector
- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** `M2-T07`

**Objective:** Collect safe common web metadata without executing remote instructions.

**Repository areas:** src/recon_agent/tools/, policy/, domain/, orchestration/; tests/unit/, fixtures/, integration/

**In scope:** Controlled retrieval of robots.txt, sitemap.xml and .well-known/security.txt; typed bounded evidence and discovered URLs.

**Out of scope:** Authentication, arbitrary downloads/local file access, unlimited sitemap recursion and automatic outside requests. All unrelated/future task work is excluded.

**Implementation steps:**

1. Define allowed methods/paths and body/redirect limits
2. Implement injectable bounded retrieval
3. Normalize metadata/URLs with provenance
4. Revalidate each derived URL before any retrieval.

**Acceptance criteria:**

1. Only explicit common paths on scoped services are requested
2. Body/time/redirect budgets hold
3. Injection text stays evidence
4. Outside links remain non-actionable
5. Parsing errors/partial bodies are recorded.

**Tests/validation:** Fake HTTP fixtures for all files, nested/hostile sitemap, redirects and oversized bodies; assert zero outside contact; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** docs/tool-contracts.md; docs/security-model.md; docs/data-model.md; docs/configuration.md; docs/testing-strategy.md. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Disable XML external entities/network expansion; remote text cannot request commands, uploads or policy edits. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for Common-file inspector; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M3-T02 — TLSX adapter

- **ID:** `M3-T02`
- **Title:** TLSX adapter
- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** `M3-T01`

**Objective:** Normalize TLS certificate metadata without trusting certificate names as authorized targets.

**Repository areas:** src/recon_agent/tools/, policy/, domain/, orchestration/; tests/unit/, fixtures/, integration/

**In scope:** inspect_tls adapter availability, bounded argv, certificate metadata/SAN parsing, provenance and derived-name validation.

**Out of scope:** Automatic scanning of all SANs, TLS exploitation and arbitrary tool flags. All unrelated/future task work is excluded.

**Implementation steps:**

1. Define safe handshake profile and scope/port limits
2. Implement invocation/parser
3. Attach certificate/evidence metadata
4. Validate SAN hostnames before actionable asset creation.

**Acceptance criteria:**

1. Certificate/SAN fixtures normalize typed metadata
2. Invalid/expired/malformed data preserves limitations
3. Outside SAN names never trigger contact
4. Configured scope/time/rate/output limits apply.

**Tests/validation:** Certificate fixture and fake-runner tests for mixed in/out-of-scope SANs, malformed outputs, availability and timeouts; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** docs/tool-contracts.md; docs/security-model.md; docs/data-model.md; docs/configuration.md; docs/testing-strategy.md. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Certificate text is untrusted; handshake/derived destinations require independent authorization. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for TLSX adapter; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M3-T03 — Katana crawler adapter

- **ID:** `M3-T03`
- **Title:** Katana crawler adapter
- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** `M3-T02`

**Objective:** Discover web endpoints through scope-constrained bounded crawling.

**Repository areas:** src/recon_agent/tools/, policy/, domain/, orchestration/; tests/unit/, fixtures/, integration/

**In scope:** crawl_web adapter, controlled depth/count/rate/time, URL normalization, metadata/evidence and scope checks before follows.

**Out of scope:** Unbounded crawling, remote state-changing submissions, arbitrary JavaScript execution/options and outside links. All unrelated/future task work is excluded.

**Implementation steps:**

1. Define read-only crawl profile and tool-internal scope enforcement
2. Configure redirect/link limits before invocation
3. Parse endpoints
4. Integrate URL/host revalidation and budgets.

**Acceptance criteria:**

1. Depth/URL/rate/time limits are enforceable
2. Tool cannot contact outside links/redirects before validation
3. If mode cannot enforce scope it is rejected
4. Endpoint observations retain provenance
5. No state-changing forms are submitted.

**Tests/validation:** Crawl graph fixtures with mixed hosts/redirects/loops; fake-runner argv/limits and rejection tests; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** docs/tool-contracts.md; docs/security-model.md; docs/data-model.md; docs/configuration.md; docs/testing-strategy.md. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Post-crawl filtering is insufficient; links/JavaScript are untrusted data and not instructions. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for Katana crawler adapter; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M3-T04 — Feroxbuster content-discovery adapter

- **ID:** `M3-T04`
- **Title:** Feroxbuster content-discovery adapter
- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** `M3-T03`

**Objective:** Add controlled content discovery with deliberate small approved wordlists and strict limits.

**Repository areas:** src/recon_agent/tools/, policy/, domain/, orchestration/; tests/unit/, fixtures/, integration/

**In scope:** discover_content adapter, approved wordlist/mode configuration, request/depth/rate/concurrency budgets and result normalization.

**Out of scope:** Massive automatic brute-force settings, authentication guessing, arbitrary file paths/options and uncontrolled recursive expansion. All unrelated/future task work is excluded.

**Implementation steps:**

1. Define approved local wordlist provenance and bounded modes
2. Restrict argv and recursion/redirect behavior
3. Normalize results and explicit budget/partial outcomes
4. Integrate scope dispatch gates.

**Acceptance criteria:**

1. Only approved wordlist/modes and scoped services dispatch
2. Strict request/rate/depth/time limits apply
3. Defaults cannot cause massive scans
4. Outside redirects are prevented
5. Results retain evidence and limitations.

**Tests/validation:** Fixtures and fake argv/request-budget/scope tests including recursion and malformed outputs; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** docs/tool-contracts.md; docs/security-model.md; docs/data-model.md; docs/configuration.md; docs/testing-strategy.md. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Content path discovery is not credential brute force; planner cannot supply arbitrary wordlists/local paths. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for Feroxbuster content-discovery adapter; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M3-T05 — FFUF adapter

- **ID:** `M3-T05`
- **Title:** FFUF adapter
- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** `M3-T04`

**Objective:** Expose FFUF for specialized safe discovery modes without duplicating default Feroxbuster work.

**Repository areas:** src/recon_agent/tools/, policy/, domain/, orchestration/; tests/unit/, fixtures/, integration/

**In scope:** Named explicitly safe discovery modes; distinct capability parameters/use cases; controlled wordlists, limits, availability, argv and parser.

**Out of scope:** Unrestricted fuzzing, authentication attacks, arbitrary request templates/headers/body/files and duplicate default Ferox execution. All unrelated/future task work is excluded.

**Implementation steps:**

1. Document specialized mode boundaries
2. Define restrictive schemas and approved inputs
3. Implement bounded invocation/parser
4. Align registry selection/dedup with Ferox overlap.

**Acceptance criteria:**

1. Each supported mode has explicit safe purpose and limits
2. Unsupported parameters/modes are denied
3. Equivalent Ferox work is not automatically duplicated
4. Scope/redirect/output/rate checks hold
5. Fixture results normalize with evidence.

**Tests/validation:** Mode/argv/overlap-dedup and fixture/failure tests with fake runners; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** docs/tool-contracts.md; docs/security-model.md; docs/data-model.md; docs/configuration.md; docs/testing-strategy.md. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** No credential fuzzing or state-changing request modes; named profiles prevent raw FFUF argument access. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for FFUF adapter; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M3-T06 — Web asset deduplication and URL canonicalization

- **ID:** `M3-T06`
- **Title:** Web asset deduplication and URL canonicalization
- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** `M3-T05`, `M1-T08`

**Objective:** Prevent repeat crawling/content discovery while preserving meaningful URL distinctions and scope.

**Repository areas:** src/recon_agent/tools/, policy/, domain/, orchestration/; tests/unit/, fixtures/, integration/

**In scope:** Canonical URL/endpoint identity, host/port/path/query handling and web action equivalence across adapters.

**Out of scope:** Lossy merging of semantically distinct resources and full finding deduplication. All unrelated/future task work is excluded.

**Implementation steps:**

1. Define canonicalization semantics with explicit ambiguous/encoded URL handling
2. Implement asset/action identity integration
3. Apply to crawl/content results and follow-up scheduling.

**Acceptance criteria:**

1. Equivalent URLs collapse deterministically
2. Meaningful path/query/method distinctions survive
3. Malformed or ambiguous authority fails closed
4. Canonicalization cannot turn outside host into allowed one
5. Repeated equivalent crawl/fuzz actions do not dispatch.

**Tests/validation:** URL table tests for schemes, default ports, fragments, encoding, queries, IPv6 and host confusion; cross-adapter dedup tests; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** docs/tool-contracts.md; docs/security-model.md; docs/data-model.md; docs/configuration.md; docs/testing-strategy.md. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Normalize then validate consistently; never decode/merge in a way that broadens authorization. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for Web asset deduplication and URL canonicalization; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

## Milestone M4 — Protocol-aware reconnaissance

### M4-T01 — Protocol capability framework

- **ID:** `M4-T01`
- **Title:** Protocol capability framework
- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** `M3-T06`

**Objective:** Route normalized service observations to explicitly registered low-impact protocol metadata modules.

**Repository areas:** src/recon_agent/tools/, policy/, domain/; tests/unit/, fixtures/, integration/

**In scope:** Protocol module interface/catalog, service relevance rules, safe request/result schemas, scoped dispatch and capability registration.

**Out of scope:** Actual SSH/SMB/FTP/SMTP/database collection, authentication or generic arbitrary protocol scripting. All unrelated/future task work is excluded.

**Implementation steps:**

1. Define protocol metadata contract and relevance mapping
2. Integrate registry/risk/parameter checks
3. Provide fake modules and evidence normalization
4. Document unsupported/ambiguous service handling.

**Acceptance criteria:**

1. Only predefined relevant capabilities can be selected from service evidence
2. Unknown protocols do not create executable modules
3. Every request still passes scope/budgets
4. Metadata results retain source/evidence
5. Fake framework runs offline.

**Tests/validation:** Unit tests for service mapping, unknown/ambiguous services, fake modules and rejected dispatch; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** docs/tool-contracts.md; docs/security-model.md; docs/data-model.md; docs/testing-strategy.md. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Port numbers alone are hints not permission; framework prohibits credential/exploit/state-changing modules. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for Protocol capability framework; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M4-T02 — SSH metadata capability

- **ID:** `M4-T02`
- **Title:** SSH metadata capability
- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** `M4-T01`

**Objective:** Collect SSH non-authentication metadata from discovered scoped services.

**Repository areas:** src/recon_agent/tools/, policy/, domain/; tests/unit/, fixtures/, integration/

**In scope:** Bounded banner/handshake/protocol metadata, relevant service mapping, structured results/evidence and availability/failure handling.

**Out of scope:** Login attempts, key/password guessing, credential collection, exploitation and host modification. All unrelated/future task work is excluded.

**Implementation steps:**

1. Define exact permitted pre-authentication exchanges
2. Implement injected collector/runner and bounded parsing
3. Register relevance/risk schema
4. Preserve hostile banner text as evidence.

**Acceptance criteria:**

1. Only approved metadata exchanges occur on scoped SSH services
2. No authentication request/credential input exists
3. Results preserve banner/protocol provenance
4. Timeout/malformed/closed connection outcomes are explicit.

**Tests/validation:** Fake transport/fixture handshake tests including hostile banner and no-auth assertions; opt-in lab only for live exchange; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** docs/tool-contracts.md; docs/security-model.md; docs/data-model.md; docs/testing-strategy.md. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** No password guessing or authentication side effects; banners cannot direct subsequent execution. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for SSH metadata capability; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M4-T03 — SMB metadata capability

- **ID:** `M4-T03`
- **Title:** SMB metadata capability
- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** `M4-T02`

**Objective:** Collect safe SMB protocol/share/configuration metadata within explicitly authorized limits.

**Repository areas:** src/recon_agent/tools/, policy/, domain/; tests/unit/, fixtures/, integration/

**In scope:** Reviewed non-destructive metadata profile, allowable share/configuration visibility, scoped service inputs, bounded results/evidence.

**Out of scope:** Credential attacks, login guessing, share writes, file retrieval/execution, exploitation and privilege escalation. All unrelated/future task work is excluded.

**Implementation steps:**

1. Define permitted negotiation/share metadata and whether unauthenticated visibility is safe through documented policy/ADR
2. Implement only approved exchanges and limits
3. Normalize results
4. Reject unsupported/auth-dependent requests.

**Acceptance criteria:**

1. Only named approved metadata operations dispatch
2. No credential guessing or remote modification occurs
3. Inaccessible/auth-required data yields limitations not attack fallback
4. Scope/time/request limits hold
5. Evidence links remain traceable.

**Tests/validation:** Sanitized SMB negotiation/share fixtures and fake transport tests for denial, auth-required response and no write/auth-attack dispatch; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** docs/tool-contracts.md; docs/security-model.md; docs/data-model.md; docs/testing-strategy.md. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** If safe metadata semantics cannot be established, fail closed; do not auto-escalate to credentials or remote file access. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for SMB metadata capability; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M4-T04 — FTP metadata capability

- **ID:** `M4-T04`
- **Title:** FTP metadata capability
- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** `M4-T03`

**Objective:** Collect FTP banner and safe pre-authentication capabilities without credential brute force.

**Repository areas:** src/recon_agent/tools/, policy/, domain/; tests/unit/, fixtures/, integration/

**In scope:** Bounded banner/protocol capability profile, evidence normalization and service relevance.

**Out of scope:** USER/PASS guessing, anonymous-login automation unless separately scoped future task, file listing/download/upload and exploit commands. All unrelated/future task work is excluded.

**Implementation steps:**

1. Define read-only pre-authentication commands
2. Implement fake-testable collector with deadlines and bounds
3. Normalize capabilities/banners
4. Reject auth or mutation parameters.

**Acceptance criteria:**

1. Only documented pre-auth metadata exchanges occur
2. No credentials/login brute force or file modification
3. Malformed/timeout responses produce structured results
4. Collected facts retain provenance and limits.

**Tests/validation:** FTP banner/capability fixtures and fake exchange/timeout/rejection tests; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** docs/tool-contracts.md; docs/security-model.md; docs/data-model.md; docs/testing-strategy.md. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Protocol commands are fixed validated operations, never model-provided strings; no auth fallback. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for FTP metadata capability; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M4-T05 — SMTP metadata capability

- **ID:** `M4-T05`
- **Title:** SMTP metadata capability
- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** `M4-T04`

**Objective:** Collect SMTP service metadata/capabilities without generating mail or abusing relay behavior.

**Repository areas:** src/recon_agent/tools/, policy/, domain/; tests/unit/, fixtures/, integration/

**In scope:** Bounded banner and safe capability negotiation profile, normalization and scoped dispatch.

**Out of scope:** Mail submission, recipient enumeration, relay abuse, bulk mail, authentication attacks and arbitrary SMTP commands. All unrelated/future task work is excluded.

**Implementation steps:**

1. Define permitted capability negotiation and connection cleanup
2. Implement controlled fake-testable exchanges
3. Normalize metadata and failures
4. Register schema/risk/limits.

**Acceptance criteria:**

1. No message or recipient operation is available
2. Safe banner/capability results retain evidence
3. Scope/request/time limits are enforced
4. Auth-required responses do not trigger attacks or mail tests.

**Tests/validation:** Fixture capabilities and fake exchange assertions excluding mail/auth/recipient commands; malformed/timeout tests; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** docs/tool-contracts.md; docs/security-model.md; docs/data-model.md; docs/testing-strategy.md. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** No abuse or bulk-mail behavior; remote server text cannot extend protocol actions. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for SMTP metadata capability; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M4-T06 — Database service metadata capability

- **ID:** `M4-T06`
- **Title:** Database service metadata capability
- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** `M4-T05`

**Objective:** Identify detected database protocols/versions through reviewed safe non-authentication metadata.

**Repository areas:** src/recon_agent/tools/, policy/, domain/; tests/unit/, fixtures/, integration/

**In scope:** Named supported database handshake profiles, scoped service inputs, bounded version/protocol evidence and unsupported outcomes.

**Out of scope:** Login guessing, query execution, data extraction, writes, exploit probes and arbitrary database driver access. All unrelated/future task work is excluded.

**Implementation steps:**

1. Select initial safe protocol set based on observable non-auth semantics
2. Document exchanges/limitations
3. Implement fixed parsers/collectors with fakes
4. Reject any auth/query-required path.

**Acceptance criteria:**

1. Each supported database profile has explicit permitted exchanges
2. Unsupported/auth-required metadata fails safely
3. No query or credential attack path exists
4. Version/protocol output is attributed to evidence with limits.

**Tests/validation:** Sanitized handshake fixtures, fake collector no-auth/no-query assertions, malformed/timeout/scope tests; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** docs/tool-contracts.md; docs/security-model.md; docs/data-model.md; docs/testing-strategy.md. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** If a protocol needs authentication for metadata, record unavailable rather than expanding capability. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for Database service metadata capability; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M4-T07 — Protocol selection tests

- **ID:** `M4-T07`
- **Title:** Protocol selection tests
- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** `M4-T06`

**Objective:** Prove service observations yield only relevant authorized protocol metadata capabilities.

**Repository areas:** src/recon_agent/tools/, policy/, domain/; tests/unit/, fixtures/, integration/

**In scope:** SSH/SMB/FTP/SMTP/database mapping regression matrix, ambiguous/misidentified service data and denied-action absence.

**Out of scope:** Live protocol scanning and adding new protocol implementations. All unrelated/future task work is excluded.

**Implementation steps:**

1. Build known/unknown/ambiguous service cases including 22, 80 and 445
2. Test relevance independent of pure port assumptions
3. Combine policy/risk/budget rejection and fake dispatch assertions.

**Acceptance criteria:**

1. Known service observations select only permitted relevant modules
2. Ambiguous/unsupported evidence is handled explicitly
3. Scope/parameter/risk denial prevents all dispatch
4. No mapping enables auth/exploit capability.

**Tests/validation:** Offline protocol selection regression suite with fake modules plus full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** docs/tool-contracts.md; docs/security-model.md; docs/data-model.md; docs/testing-strategy.md. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Test hostile service labels and model-shaped module names cannot create a capability. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for Protocol selection tests; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

## Milestone M5 — Nuclei and template-based checks

### M5-T01 — Nuclei adapter foundation

- **ID:** `M5-T01`
- **Title:** Nuclei adapter foundation
- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** `M4-T07`

**Objective:** Implement a controlled Nuclei adapter/parser without enabling unreviewed template execution.

**Repository areas:** src/recon_agent/tools/, policy/, domain/; tests/unit/, fixtures/, integration/

**In scope:** Availability, safe argv contract, machine-readable result parsing, normalized candidate metadata and fake runner; default deny for real profiles until policy tasks complete.

**Out of scope:** Unrestricted template scanning, arbitrary paths/flags and default automatic template selection. All unrelated/future task work is excluded.

**Implementation steps:**

1. Define candidate result schema and controlled profile interface
2. Implement availability/parser/runner wiring with restrictive profile stub
3. Handle timeout/partial/non-zero results
4. Preserve evidence.

**Acceptance criteria:**

1. Fixtures parse template/result metadata with source references
2. Argv cannot accept raw paths/arguments
3. Real invocation fails closed without an approved enforced profile
4. Missing binary/timeout/parser failure remain structured.

**Tests/validation:** Sanitized Nuclei JSON fixtures, hostile metadata, malformed/partial outputs, fake-runner profile-denial tests; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** docs/tool-contracts.md; docs/security-model.md; docs/data-model.md; docs/configuration.md; docs/testing-strategy.md. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Parser/adapter availability is not authorization to execute templates; no intrusive defaults. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for Nuclei adapter foundation; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M5-T02 — Safe Nuclei profile policy

- **ID:** `M5-T02`
- **Title:** Safe Nuclei profile policy
- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** `M5-T01`

**Objective:** Define reviewed explicit allowed template classes and safe/default policy profiles.

**Repository areas:** src/recon_agent/tools/, policy/, domain/; tests/unit/, fixtures/, integration/

**In scope:** Risk classification, named profile catalog, permitted template behavior, reviewed provenance/version rules, deny behavior and update policy.

**Out of scope:** Enabling intrusive templates, exploitation, arbitrary operator/model template paths and implementation-wide scanning. All unrelated/future task work is excluded.

**Implementation steps:**

1. Review candidate classes and documented request behavior
2. Define safe named default and excluded classes
3. Record classification/provenance decision via ADR where needed
4. Specify fail-closed unknown/update handling.

**Acceptance criteria:**

1. Allowed classes/profiles are explicit and reviewable
2. Anything potentially intrusive or unknown is excluded from default
3. Profile selection cannot override exclusions
4. Template updates cannot silently broaden allowed behavior.

**Tests/validation:** Policy table tests for safe/forbidden/unknown classes and changed provenance/version; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** docs/tool-contracts.md; docs/security-model.md; docs/data-model.md; docs/configuration.md; docs/testing-strategy.md. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Template labels alone may be insufficient; actual effective behavior must remain within authorized reconnaissance. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for Safe Nuclei profile policy; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M5-T03 — Template policy enforcement

- **ID:** `M5-T03`
- **Title:** Template policy enforcement
- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** `M5-T02`

**Objective:** Enforce named Nuclei profiles at request validation and execution dispatch.

**Repository areas:** src/recon_agent/tools/, policy/, domain/; tests/unit/, fixtures/, integration/

**In scope:** Planner-selected named profile schema; resolved reviewed templates; restricted argv; scope/risk/budget checks and update validation.

**Out of scope:** Arbitrary template paths, unrestricted Nuclei arguments, dynamic template download from planner and intrusive profiles. All unrelated/future task work is excluded.

**Implementation steps:**

1. Integrate profile resolver with registry/validator
2. Construct argv only from trusted reviewed configuration
3. Enforce template/redirect/network behavior and budgets
4. Reject unknown/changed profiles before runner call.

**Acceptance criteria:**

1. Only named approved profiles execute
2. Invalid/unknown/updated-unreviewed template or raw arguments deny dispatch
3. Per-template destinations obey scope before contact
4. Budgets/output/time limits hold
5. Denials are audited.

**Tests/validation:** Fake-runner tests for profile allow/deny, path/flag injection, template drift, outside secondary targets and budget limits; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** docs/tool-contracts.md; docs/security-model.md; docs/data-model.md; docs/configuration.md; docs/testing-strategy.md. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Profile names do not authorize hidden out-of-scope requests; unsafe/unconstrainable templates fail closed. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for Template policy enforcement; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M5-T04 — Nuclei finding normalization

- **ID:** `M5-T04`
- **Title:** Nuclei finding normalization
- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** `M5-T03`

**Objective:** Convert approved scanner results into interpreted Finding records with traceable Evidence.

**Repository areas:** src/recon_agent/tools/, policy/, domain/; tests/unit/, fixtures/, integration/

**In scope:** Template ID/source/version, matched asset/URL, severity/confidence/limitations and observation/evidence links; structured malformed/partial handling.

**Out of scope:** Claims of confirmed exploitation, AI-created evidence and additional template execution modes. All unrelated/future task work is excluded.

**Implementation steps:**

1. Map scanner result fields to finding/evidence models
2. Preserve reported versus inferred semantics
3. Attach execution references and truncation limits
4. Sanitize remote metadata for downstream reports.

**Acceptance criteria:**

1. Every normalized finding links scanner execution and supporting evidence
2. Severity/source are explicit and missing facts are not invented
3. Hostile result text stays data
4. Malformed/unmatched records are errors/limitations rather than confirmed findings.

**Tests/validation:** Finding fixtures for complete/partial/malformed/duplicate candidate records and provenance integrity; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** docs/tool-contracts.md; docs/security-model.md; docs/data-model.md; docs/configuration.md; docs/testing-strategy.md. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Scanner output is untrusted; finding normalization never triggers remote modification or implied exploit verification. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for Nuclei finding normalization; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M5-T05 — Finding deduplication

- **ID:** `M5-T05`
- **Title:** Finding deduplication
- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** `M5-T04`

**Objective:** Collapse equivalent security conclusions across tools/URLs/templates without discarding distinct evidence.

**Repository areas:** src/recon_agent/tools/, policy/, domain/; tests/unit/, fixtures/, integration/

**In scope:** Canonical finding identity, merge/provenance rules, confidence/source preservation and duplicate tracking.

**Out of scope:** Lossy asset merging, exploitation validation and overwriting scanner facts with model assumptions. All unrelated/future task work is excluded.

**Implementation steps:**

1. Define equivalence based on affected asset/location and interpreted issue
2. Implement merge of evidence/source references
3. Preserve conflicting/uncertain conclusions
4. Integrate normalized findings.

**Acceptance criteria:**

1. Equivalent findings merge deterministically with all evidence references
2. Distinct locations/issues remain separate
3. Conflicting severity/confidence is resolved or disclosed by documented rules
4. No evidence lineage is lost.

**Tests/validation:** Cross-tool/template/URL fixture cases for duplicates, distinct issues, conflicts and stable serialization; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** docs/tool-contracts.md; docs/security-model.md; docs/data-model.md; docs/configuration.md; docs/testing-strategy.md. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Merged findings remain interpretations with attribution; dedup cannot fabricate certainty or authorization. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for Finding deduplication; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

## Milestone M6 — Groq provider and AI planner

### M6-T01 — LLM provider abstraction

- **ID:** `M6-T01`
- **Title:** LLM provider abstraction
- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** `M5-T05`

**Objective:** Decouple planning from provider-specific clients and errors before integrating Groq.

**Repository areas:** src/recon_agent/providers/, orchestration/, policy/, domain/; tests/unit/, fixtures/

**In scope:** Async-capable provider interface, typed bounded request/response and failure/timeout contracts; injectable fake implementation shape.

**Out of scope:** Groq API calls, secret loading changes and autonomous orchestration. All unrelated/future task work is excluded.

**Implementation steps:**

1. Define provider methods and context/result contracts
2. Isolate provider metadata/errors from domain
3. Support injection/cancellation/timeout expectations
4. Document interface and fake seam.

**Acceptance criteria:**

1. Orchestration can depend on the interface without Groq imports
2. Typed requests/responses/errors are provider-independent
3. Interface exposes no process/shell tools or secret fields
4. Fake calls work offline.

**Tests/validation:** Contract tests with minimal fake provider for success/failure/cancel and type checking; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** docs/planner-contract.md; docs/security-model.md; docs/configuration.md; docs/data-model.md; docs/testing-strategy.md. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Provider access does not grant execution authority; request contracts retain untrusted labels and bounds. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for LLM provider abstraction; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M6-T02 — Groq provider implementation

- **ID:** `M6-T02`
- **Title:** Groq provider implementation
- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** `M6-T01`, `M0-T03`

**Objective:** Integrate Groq behind the provider interface with secure key handling and bounded calls.

**Repository areas:** src/recon_agent/providers/, orchestration/, policy/, domain/; tests/unit/, fixtures/

**In scope:** Groq API client adaptation, separate GROQ_API_KEY loading, model/config settings, timeout/cancellation and bounded retry/error mapping.

**Out of scope:** Direct shell/tool execution, domain provider dependencies, public-target scanning and live API tests by default. All unrelated/future task work is excluded.

**Implementation steps:**

1. Select current supported client/structured-response approach using primary documentation at implementation time
2. Implement interface adapter
3. Redact credentials/errors
4. Expose fake transport tests and optional explicit provider integration.

**Acceptance criteria:**

1. Configured requests map through abstraction with bounded time/retries
2. Absent key is clear secret-safe error
3. Key never appears in logs/repr/state/prompts
4. Domain has no Groq dependency
5. Default tests use fake transport without connectivity.

**Tests/validation:** Mocked/fake transport success, timeout, rate/error, cancellation, missing key and redaction tests; full baseline; live calls only explicitly opted in. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** docs/planner-contract.md; docs/security-model.md; docs/configuration.md; docs/data-model.md; docs/testing-strategy.md. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** API keys stay in secret mechanism; hosted input must be minimized; provider cannot access runner. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for Groq provider implementation; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M6-T03 — Planner input schema

- **ID:** `M6-T03`
- **Title:** Planner input schema
- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** `M6-T02`, `M1-T08`

**Objective:** Build relevant bounded normalized planner context without uncontrolled raw-output forwarding.

**Repository areas:** src/recon_agent/providers/, orchestration/, policy/, domain/; tests/unit/, fixtures/

**In scope:** Authorized scope, known assets/observations, completed/failed/rejected actions, capability catalog, budget and evidence provenance/trust labels.

**Out of scope:** Unlimited raw bodies/stdout, credentials, changing policy and output action schema. All unrelated/future task work is excluded.

**Implementation steps:**

1. Define typed input envelope and deterministic selection/truncation policy
2. Build from state/catalog/budgets
3. Redact secrets and label untrusted evidence
4. Record omissions/limits.

**Acceptance criteria:**

1. All required context categories are represented
2. Input size is bounded deterministically
3. Secrets/raw excess are excluded
4. Omitted evidence is disclosed
5. Remote text cannot occupy policy/system instruction fields.

**Tests/validation:** Input-building tests for large state, bounded truncation, history/catalog/budget presence, hostile evidence and redaction; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** docs/planner-contract.md; docs/security-model.md; docs/configuration.md; docs/data-model.md; docs/testing-strategy.md. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Normalization does not promote trust; scope snapshot cannot be rewritten by evidence. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for Planner input schema; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M6-T04 — Planner output schema

- **ID:** `M6-T04`
- **Title:** Planner output schema
- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** `M6-T03`

**Objective:** Require strictly typed recommendations that cannot contain executable commands.

**Repository areas:** src/recon_agent/providers/, orchestration/, policy/, domain/; tests/unit/, fixtures/

**In scope:** Analysis summary, actions with capability/target/priority/reason and allowed typed parameters, finished flag; strict unknown-field behavior.

**Out of scope:** Shell-command field, execution, inferred facts inserted as observations and permissive arbitrary parameters. All unrelated/future task work is excluded.

**Implementation steps:**

1. Define strict schema and priority bounds
2. Align action parameters with capability catalog
3. Parse responses into typed decisions
4. Distinguish parse/schema failures from provider errors.

**Acceptance criteria:**

1. Valid decisions parse with bounded priorities and strict types
2. Unknown/extra fields, executable command fields and malformed actions reject
3. Summaries/reasons remain data
4. Empty/finished decisions have explicit semantics.

**Tests/validation:** Valid/invalid response fixtures including command fields, extra parameters, malformed JSON, priority boundaries and finished/empty outputs; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** docs/planner-contract.md; docs/security-model.md; docs/configuration.md; docs/data-model.md; docs/testing-strategy.md. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Valid JSON is not authorization; parser must not execute strings or relax schema on model failure. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for Planner output schema; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M6-T05 — Planner system policy

- **ID:** `M6-T05`
- **Title:** Planner system policy
- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** `M6-T04`

**Objective:** Provide fixed planner guidance matching authorization and evidence boundaries.

**Repository areas:** src/recon_agent/providers/, orchestration/, policy/, domain/; tests/unit/, fixtures/

**In scope:** Authorized reconnaissance only; untrusted remote evidence; provided capabilities only; no invented observations/outside targets; avoid duplicate work; prefer high-information low-impact actions.

**Out of scope:** Remote-derived instruction edits, new capabilities, deterministic validator replacement and heuristic exploitation advice. All unrelated/future task work is excluded.

**Implementation steps:**

1. Create versioned fixed policy separate from evidence
2. Describe capability/target/action output limits and stop behavior
3. Attach safely to provider input
4. Document policy provenance and tests.

**Acceptance criteria:**

1. All stated rules appear in fixed policy
2. Evidence is structurally separate and cannot replace it
3. Planner prompts do not contain credentials
4. Version/reference is auditable
5. Policy describes recommendations rather than terminal access.

**Tests/validation:** Prompt assembly tests for fixed policy separation, hostile evidence, catalog-only actions and no secrets; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** docs/planner-contract.md; docs/security-model.md; docs/configuration.md; docs/data-model.md; docs/testing-strategy.md. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Instructions alone are not security enforcement; deterministic validator remains mandatory. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for Planner system policy; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M6-T06 — Planner response validator

- **ID:** `M6-T06`
- **Title:** Planner response validator
- **Status:** NOT STARTED
- **Priority:** P0
- **Dependencies:** `M6-T05`, `M1-T08`

**Objective:** Apply deterministic safety checks to every model recommendation before dispatch.

**Repository areas:** src/recon_agent/providers/, orchestration/, policy/, domain/; tests/unit/, fixtures/

**In scope:** Strict schema, unknown capability, out-of-scope target, invalid parameters, unsupported action/risk, budgets/dedup and typed rejection outcomes.

**Out of scope:** Execution of model commands, automatic schema relaxation and broad retry/recovery logic. All unrelated/future task work is excluded.

**Implementation steps:**

1. Compose output parsing and action policy validation
2. Validate each recommendation under current scope/catalog/budgets
3. Record approved/rejected decisions
4. Ensure stale approvals revalidate at dispatch.

**Acceptance criteria:**

1. All listed invalid request groups reject deterministically
2. Unknown command fields never reach runner
3. Allowed decisions yield typed approved actions
4. Mixed valid/invalid actions have explicit audited behavior
5. Rejection cannot broaden scope.

**Tests/validation:** Adversarial response matrix with fake dispatch absence assertions and stale budget/scope cases; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** docs/planner-contract.md; docs/security-model.md; docs/configuration.md; docs/data-model.md; docs/testing-strategy.md. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Model output is untrusted even when apparently reasonable; no unsafe fallback after rejection. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for Planner response validator; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M6-T07 — Prompt-injection resistance tests

- **ID:** `M6-T07`
- **Title:** Prompt-injection resistance tests
- **Status:** NOT STARTED
- **Priority:** P0
- **Dependencies:** `M6-T06`

**Objective:** Prove malicious evidence and adversarial model responses cannot bypass execution policy.

**Repository areas:** src/recon_agent/providers/, orchestration/, policy/, domain/; tests/unit/, fixtures/

**In scope:** Hostile webpage/banner/DNS/certificate/tool metadata fixtures asking to ignore policy, scan another host, run commands or expose secrets; validator/dispatch assertions.

**Out of scope:** Claiming perfect model obedience, live Groq dependency and changes to scope to accommodate injected requests. All unrelated/future task work is excluded.

**Implementation steps:**

1. Build labeled malicious evidence in state
2. Fake adversarial provider decisions including outside targets/commands/secret requests
3. Verify schema/policy/runner barriers and audit outcomes
4. Repair demonstrated boundary defects.

**Acceptance criteria:**

1. Injected evidence remains data and cannot mutate system policy/config/catalog
2. Prohibited recommendations produce no tool dispatch or secret reads/uploads
3. Valid allowed actions still work
4. All tests run offline with fake provider/runner.

**Tests/validation:** Injection regression suite across evidence origins and response shapes; full baseline; report enforcement evidence rather than model-behavior guarantees. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** docs/planner-contract.md; docs/security-model.md; docs/configuration.md; docs/data-model.md; docs/testing-strategy.md. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Deterministic controls must hold even if model obeys injection completely. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for Prompt-injection resistance tests; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M6-T08 — Planner prioritization model

- **ID:** `M6-T08`
- **Title:** Planner prioritization model
- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** `M6-T07`

**Objective:** Provide sufficient state and decision semantics for useful adaptive prioritization without a fixed full decision tree.

**Repository areas:** src/recon_agent/providers/, orchestration/, policy/, domain/; tests/unit/, fixtures/

**In scope:** Information gaps, service/capability relevance, completed/failed history, risk/cost/budget context and stable priority tie handling.

**Out of scope:** Hard-coded full recon tree, model-created capabilities, exploitation prioritization and guaranteed live-model choices. All unrelated/future task work is excluded.

**Implementation steps:**

1. Define state/context cues and priority semantics
2. Enrich bounded input without duplicating facts
3. Map ties deterministically and document low-impact preference
4. Test useful recommendation selection with fakes.

**Acceptance criteria:**

1. Input exposes useful service gaps/history/remaining cost context
2. Priorities select only validated actions with deterministic tie handling
3. No full fixed tree is required
4. Duplicate/high-risk/outside actions still deny regardless of priority.

**Tests/validation:** Fake decision scenarios for SSH/HTTP/SMB evidence, ties, limited budgets and completed work; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** docs/planner-contract.md; docs/security-model.md; docs/configuration.md; docs/data-model.md; docs/testing-strategy.md. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Priority never overrides authorization, risk limits or stop conditions. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for Planner prioritization model; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M6-T09 — Planner fake provider

- **ID:** `M6-T09`
- **Title:** Planner fake provider
- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** `M6-T08`

**Objective:** Support reproducible offline planner and autonomous-loop tests independent of Groq behavior.

**Repository areas:** src/recon_agent/providers/, orchestration/, policy/, domain/; tests/unit/, fixtures/

**In scope:** Deterministic scripted/state-aware fake responses, malformed/failure/cancel scenarios, call capture with redaction and provider interface compliance.

**Out of scope:** Live API calls, replacing production policy with fake shortcuts and realistic-model guarantees. All unrelated/future task work is excluded.

**Implementation steps:**

1. Implement injected fake provider and response fixtures
2. Define deterministic sequence/state expectations
3. Support errors/exhaustion/invalid outputs
4. Document test usage and no-secret behavior.

**Acceptance criteria:**

1. Fake follows same provider/output/validation contracts as real provider
2. Responses repeat deterministically
3. Simulated failures/injection are available
4. No key/network needed
5. Exhaustion is explicit and does not spin forever.

**Tests/validation:** Fake provider contract tests, repeatability and failure/cancel/call-capture tests; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** docs/planner-contract.md; docs/security-model.md; docs/configuration.md; docs/data-model.md; docs/testing-strategy.md. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Test fakes must exercise real policy validators; fake approval cannot bypass execution controls. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for Planner fake provider; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

## Milestone M7 — Autonomous orchestration loop

### M7-T01 — Single-step planning cycle

- **ID:** `M7-T01`
- **Title:** Single-step planning cycle
- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** `M6-T09`

**Objective:** Connect state, planner and validator for exactly one selected recommendation before adding execution loops.

**Repository areas:** src/recon_agent/orchestration/, policy/, domain/, providers/, persistence/; tests/unit/, integration/, fixtures/

**In scope:** State → planner → deterministic validation → selected approved action or explicit no-action outcome; audit decision/rejections.

**Out of scope:** Tool execution, repeated autonomous cycles and persistence wiring. All unrelated/future task work is excluded.

**Implementation steps:**

1. Compose typed bounded input/provider/output validation
2. Choose allowed action by priority under budgets/dedup
3. Record decision/rejections
4. Return selection without executing.

**Acceptance criteria:**

1. One invocation makes one planning cycle only
2. Selected action is validated and traceable to decision
3. Invalid/all-rejected/finished/failure outcomes are explicit
4. No runner call occurs.

**Tests/validation:** Fake provider scenarios for allowed/mixed/rejected/finished/malformed responses and zero execution assertions; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** docs/architecture.md; docs/planner-contract.md; docs/data-model.md; docs/security-model.md; docs/testing-strategy.md. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Planner choice never skips policy; selected request is not permanent execution approval. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for Single-step planning cycle; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M7-T02 — Execute-and-observe cycle

- **ID:** `M7-T02`
- **Title:** Execute-and-observe cycle
- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** `M7-T01`, `M2-T07`

**Objective:** Execute one approved capability and return normalized outcomes to state.

**Repository areas:** src/recon_agent/orchestration/, policy/, domain/, providers/, persistence/; tests/unit/, integration/, fixtures/

**In scope:** Dispatch revalidation/reservation, registry adapter/runner, result normalization, evidence/state updates and audit outcomes.

**Out of scope:** Unbounded multi-step loop and persistence/resume implementation. All unrelated/future task work is excluded.

**Implementation steps:**

1. Wire selected action to policy recheck and budget reservation
2. Dispatch controlled adapter
3. Normalize success/partial/failure
4. Apply state transitions and record evidence/execution links.

**Acceptance criteria:**

1. Exactly one approved action dispatches
2. Stale/outside/exhausted requests deny
3. Observations/evidence update coherently
4. Failure does not corrupt state or imply success
5. Cancellation cleans up and records outcome.

**Tests/validation:** Fake adapter/runner execution cycle for success, partial, timeout, rejection, budget race and cancellation; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** docs/architecture.md; docs/planner-contract.md; docs/data-model.md; docs/security-model.md; docs/testing-strategy.md. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Revalidate immediately before contact; adapter-derived destinations retain scope controls. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for Execute-and-observe cycle; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M7-T03 — Multi-step agent loop

- **ID:** `M7-T03`
- **Title:** Multi-step agent loop
- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** `M7-T02`

**Objective:** Run adaptive planning and execution repeatedly with provisional hard bounds.

**Repository areas:** src/recon_agent/orchestration/, policy/, domain/, providers/, persistence/; tests/unit/, integration/, fixtures/

**In scope:** Observe/reason/plan/validate/act/observe loop, injected provider/adapters, state updates and bounded cycle guard.

**Out of scope:** Persistent resume, unlimited autonomy and bypassing dedicated stop-condition work. All unrelated/future task work is excluded.

**Implementation steps:**

1. Compose single cycles
2. Carry updated evidence/history into next plan
3. Add restrictive hard action/time/repetition bounds from existing policy
4. Record each cycle and terminal outcome.

**Acceptance criteria:**

1. Later cycles receive previous observations/actions
2. Only approved actions execute
3. Budgets remain enforced and loop always has bounded termination
4. Fake service scenario adapts actions
5. No uncontrolled recursion/retries.

**Tests/validation:** Offline multi-cycle fake scenarios for adaptive action changes, budget limits, repeated recommendations and errors; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** docs/architecture.md; docs/planner-contract.md; docs/data-model.md; docs/security-model.md; docs/testing-strategy.md. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Autonomy does not grant broader scope or capabilities; retain provisional guards until M7-T04 formalizes stops. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for Multi-step agent loop; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M7-T04 — Stop conditions

- **ID:** `M7-T04`
- **Title:** Stop conditions
- **Status:** NOT STARTED
- **Priority:** P0
- **Dependencies:** `M7-T03`

**Objective:** Make loop termination deterministic and auditable across completion, limits and unsafe states.

**Repository areas:** src/recon_agent/orchestration/, policy/, domain/, providers/, persistence/; tests/unit/, integration/, fixtures/

**In scope:** Finished, no valid actions, action/time exhaustion, operator cancel, repetition protection, fatal provider/execution/environment failure and fatal policy state.

**Out of scope:** Model-granted budget extensions, silent indefinite waits and persistence implementation. All unrelated/future task work is excluded.

**Implementation steps:**

1. Define typed stop reasons/precedence
2. Integrate checks before/after planning and dispatch
3. Ensure cancellation cleanup/final state
4. Disclose unfinished coverage.

**Acceptance criteria:**

1. Each specified condition reliably stops without extra dispatch
2. Simultaneous stop events follow documented precedence
3. Stop reason and state are recorded
4. No-valid/policy-blocked responses cannot spin
5. Operator cancel wins before further traffic.

**Tests/validation:** Fake-clock/provider/runner matrix for all stop reasons and competing events; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** docs/architecture.md; docs/planner-contract.md; docs/data-model.md; docs/security-model.md; docs/testing-strategy.md. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Fail closed on fatal policy ambiguity; stop cannot be suppressed by model output. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for Stop conditions; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M7-T05 — Planner/action history

- **ID:** `M7-T05`
- **Title:** Planner/action history
- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** `M7-T04`, `M8-T03`, `M8-T05`

**Objective:** Persist actionable decision/action history so each cycle knows prior attempts and policy outcomes.

**Repository areas:** src/recon_agent/orchestration/, policy/, domain/, providers/, persistence/; tests/unit/, integration/, fixtures/

**In scope:** Persist completed/failed/rejected actions and planner recommendations/validation results; bounded history selection in planner input.

**Out of scope:** Full session resume logic and unlimited raw evidence forwarding. All unrelated/future task work is excluded.

**Implementation steps:**

1. Wire storage repositories to cycle lifecycle
2. Record decision/action IDs and state transitions
3. Reconstruct bounded history for planner
4. Define write-failure stop/recovery semantics.

**Acceptance criteria:**

1. Each attempted/rejected action and originating decision is stored with outcome/links
2. Restored history prevents unnecessary repeats
3. Planner sees bounded relevant history
4. Storage failure cannot produce untracked continued execution.

**Tests/validation:** Temporary SQLite plus fake planner/adapter tests for history round-trip, linkage, bounded input and failed writes; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** docs/architecture.md; docs/planner-contract.md; docs/data-model.md; docs/security-model.md; docs/testing-strategy.md. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** History is audit data, not authority; secret-free persisted recommendations retain untrusted attribution. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for Planner/action history; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M7-T06 — Failure recovery

- **ID:** `M7-T06`
- **Title:** Failure recovery
- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** `M7-T05`

**Objective:** Handle tool failures predictably without corrupting state or permitting endless retry.

**Repository areas:** src/recon_agent/orchestration/, policy/, domain/, providers/, persistence/; tests/unit/, integration/, fixtures/

**In scope:** Tool unavailable/timeout/non-zero/parser/partial results, recoverable versus fatal classification, bounded retry and planner failure observations.

**Out of scope:** More intrusive fallback scans, policy relaxation and retry-until-success behavior. All unrelated/future task work is excluded.

**Implementation steps:**

1. Define recovery classes and retry accounting
2. Record safe failure summaries for planner
3. Preserve evidence/partial limitations
4. Enforce dedup/budgets and fatal stops during retries.

**Acceptance criteria:**

1. Failures leave consistent persisted state
2. Retries are explicit and finite
3. Model may choose another allowed useful action but cannot bypass policy
4. Partial output is labeled
5. Fatal/limit failures stop with reasons.

**Tests/validation:** Failure matrix using fake runner/provider and temporary storage for retries, alternative allowed actions, partial output and write faults; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** docs/architecture.md; docs/planner-contract.md; docs/data-model.md; docs/security-model.md; docs/testing-strategy.md. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** A tool failure never authorizes credential/exploit behavior or expanded targets. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for Failure recovery; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M7-T07 — Session resume

- **ID:** `M7-T07`
- **Title:** Session resume
- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** `M7-T06`, `M8-T04`, `M8-T06`

**Objective:** Resume persisted sessions without unnecessary repeated work or stale authorization.

**Repository areas:** src/recon_agent/orchestration/, policy/, domain/, providers/, persistence/; tests/unit/, integration/, fixtures/

**In scope:** Restored state/history/budgets/evidence, current configuration/policy compatibility, interrupted-action reconciliation and resume lifecycle.

**Out of scope:** Silently expanding scope, erasing audit history and automatic live resume from untrusted files. All unrelated/future task work is excluded.

**Implementation steps:**

1. Define compatibility and interrupted-action policy
2. Load/validate stored session and schema
3. Reconcile current scope/budgets/completed identities
4. Resume controlled loop or stop with actionable incompatibility.

**Acceptance criteria:**

1. Completed equivalent work remains deduplicated
2. Remaining budgets persist
3. Changed/invalid scope or schema fails safely
4. Interrupted work is explicitly reconciled
5. Evidence/history remain traceable
6. Resumed actions revalidate at dispatch.

**Tests/validation:** Temporary SQLite resume tests with fake tools/provider, changed policy, partial interruption, migration compatibility and exhausted limits; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** docs/architecture.md; docs/planner-contract.md; docs/data-model.md; docs/security-model.md; docs/testing-strategy.md. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Stored approvals are not permanent authorization; secrets are reloaded separately, never persisted. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for Session resume; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M7-T08 — End-to-end simulated autonomous recon test

- **ID:** `M7-T08`
- **Title:** End-to-end simulated autonomous recon test
- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** `M7-T07`, `M4-T07`

**Objective:** Prove the complete adaptive recon loop with safe service-specific choices and no network.

**Repository areas:** src/recon_agent/orchestration/, policy/, domain/, providers/, persistence/; tests/unit/, integration/, fixtures/

**In scope:** Fake tools and fake Groq/provider scenario beginning with 22/tcp SSH, 80/tcp HTTP and 445/tcp SMB; state/history/evidence/stop assertions.

**Out of scope:** Real targets, binaries, API keys and deterministic claims about live model behavior. All unrelated/future task work is excluded.

**Implementation steps:**

1. Build staged service/evidence fixtures and scripted useful recommendations
2. Run real orchestration/policy/storage with fakes
3. Include outside/injection/duplicate/failure branches
4. Assert termination and traceability.

**Acceptance criteria:**

1. Simulation chooses relevant allowed SSH/HTTP/SMB metadata capabilities, updates state each cycle and stops
2. Denied actions never dispatch
3. Evidence/decision/action history persists
4. Test requires no Internet, Groq or binaries.

**Tests/validation:** Run simulated end-to-end suite and full offline baseline; capture final state/stop evidence. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** docs/architecture.md; docs/planner-contract.md; docs/data-model.md; docs/security-model.md; docs/testing-strategy.md. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Fakes do not bypass policy; outside targets, command requests and retries remain denied. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for End-to-end simulated autonomous recon test; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

## Milestone M8 — Persistence

### M8-T01 — SQLite schema design

- **ID:** `M8-T01`
- **Title:** SQLite schema design
- **Status:** NOT STARTED
- **Priority:** P0
- **Dependencies:** `M1-T08`, `M0-T06`

**Objective:** Design local storage for traceable session state before orchestration needs durable history.

**Repository areas:** src/recon_agent/persistence/, domain/; tests/unit/, integration/

**In scope:** Sessions/scopes/targets/assets/services/endpoints/observations/actions/executions/findings/decisions/evidence references; keys, constraints, indexing and transaction requirements.

**Out of scope:** Production repository CRUD, orchestration coupling and storing credentials. All unrelated/future task work is excluded.

**Implementation steps:**

1. Map domain entities to tables/relationships
2. Specify lifecycle/provenance constraints and atomic writes
3. Record schema/version/migration requirements with ADR where alternatives matter
4. Validate draft schema in temporary SQLite if DDL is included.

**Acceptance criteria:**

1. Schema covers listed core records and lineage
2. Referential integrity and transaction boundaries are explicit
3. Safe config snapshots exclude secrets
4. Schema version/resume requirements are documented
5. Design is compatible with pure domain interfaces.

**Tests/validation:** Schema review against domain entities; temporary offline SQLite integrity checks for any supplied DDL; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** docs/data-model.md; docs/architecture.md; docs/configuration.md; docs/security-model.md; docs/testing-strategy.md. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Storage content remains untrusted; use parameterized writes later and never store Groq keys. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for SQLite schema design; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M8-T02 — Repository interfaces

- **ID:** `M8-T02`
- **Title:** Repository interfaces
- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** `M8-T01`

**Objective:** Isolate persistence operations from domain and orchestration so SQLite details remain contained.

**Repository areas:** src/recon_agent/persistence/, domain/; tests/unit/, integration/

**In scope:** Typed repository/unit-of-work contracts for sessions, state, actions, observations/evidence, findings and decisions; in-memory fake repositories.

**Out of scope:** Provider/tool execution and full SQLite CRUD implementation. All unrelated/future task work is excluded.

**Implementation steps:**

1. Define interfaces and transaction/error semantics from schema
2. Add fake implementations
3. Specify query/update behavior and data ownership
4. Avoid leaking SQL into orchestration.

**Acceptance criteria:**

1. Clients can persist/query contracts through injected fakes without SQLite imports
2. Transaction/failure behavior is typed
3. Interface supports history/evidence/resume needs
4. Models stay provider/storage independent.

**Tests/validation:** Contract tests using in-memory repositories for ordering, identity, missing records and transaction failure; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** docs/data-model.md; docs/architecture.md; docs/configuration.md; docs/security-model.md; docs/testing-strategy.md. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Repositories cannot treat stored recommendations as facts or saved scope as unchecked authority. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for Repository interfaces; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M8-T03 — Session persistence

- **ID:** `M8-T03`
- **Title:** Session persistence
- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** `M8-T02`

**Objective:** Persist and reconstruct ReconSession metadata/state safely behind repository contracts.

**Repository areas:** src/recon_agent/persistence/, domain/; tests/unit/, integration/

**In scope:** SQLite session/scopes/targets/assets/actions/budgets lifecycle storage, safe config snapshot, transactional state round-trip.

**Out of scope:** Autonomous resume execution, full evidence blobs/decision persistence and migrations beyond initial schema setup. All unrelated/future task work is excluded.

**Implementation steps:**

1. Implement session repository with parameterized SQL and transactions
2. Serialize/restore typed state and remaining budgets
3. Handle interruption/write failure
4. Document storage path/access behavior.

**Acceptance criteria:**

1. Session state and action/budget outcomes round-trip without secret values
2. Interrupted writes do not leave contradictory success
3. Storage errors are typed
4. Local temporary DB works offline
5. No execution occurs on load.

**Tests/validation:** Temporary SQLite create/update/load, transaction rollback, budget/action integrity and secret exclusion tests; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** docs/data-model.md; docs/architecture.md; docs/configuration.md; docs/security-model.md; docs/testing-strategy.md. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Parameterized operations; no implicit execution on deserialization; persisted scope requires resume revalidation. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for Session persistence; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M8-T04 — Observation/evidence persistence

- **ID:** `M8-T04`
- **Title:** Observation/evidence persistence
- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** `M8-T03`

**Objective:** Maintain durable provenance from observations/findings to original collection/execution sources.

**Repository areas:** src/recon_agent/persistence/, domain/; tests/unit/, integration/

**In scope:** Observation/evidence/execution repositories, references/integrity, partial/truncation/redaction metadata and retention semantics.

**Out of scope:** Unlimited sensitive raw storage, remote uploads and autonomous action scheduling. All unrelated/future task work is excluded.

**Implementation steps:**

1. Implement typed parameterized storage and lineage constraints
2. Preserve bounded source references and integrity metadata
3. Restore relationships
4. Define safe deletion/retention without dangling findings.

**Acceptance criteria:**

1. Every stored observation/finding reference resolves to source evidence/execution or explicit collection origin
2. Partial/redacted evidence remains labeled
3. Round-trip preserves trust/source
4. Transaction failures cannot create orphaned success records.

**Tests/validation:** Temporary SQLite lineage/round-trip/rollback/retention and hostile text tests; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** docs/data-model.md; docs/architecture.md; docs/configuration.md; docs/security-model.md; docs/testing-strategy.md. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Remote evidence is data; bounded local retention and secret redaction apply even before reporting. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for Observation/evidence persistence; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M8-T05 — Planner decision persistence

- **ID:** `M8-T05`
- **Title:** Planner decision persistence
- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** `M8-T04`, `M6-T04`

**Objective:** Store AI recommendations and policy outcomes separately from collected facts.

**Repository areas:** src/recon_agent/persistence/, domain/; tests/unit/, integration/

**In scope:** Decision input references, provider/model/policy metadata, structured requested actions, approval/rejection outcomes and linked executions.

**Out of scope:** Storing keys, unlimited prompts/raw content and changing decision meaning after the fact. All unrelated/future task work is excluded.

**Implementation steps:**

1. Implement decision/action linkage behind repositories
2. Preserve version/input references and validated outcomes
3. Expose bounded history queries
4. Document retention/redaction.

**Acceptance criteria:**

1. Decisions round-trip with recommendation attribution and policy outcome
2. Action/execution relationships remain resolvable
3. Rejected requests do not become observations
4. Credentials/excess raw prompts are excluded.

**Tests/validation:** Temporary SQLite decision/validation/linkage/history/redaction tests with fake planner records; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** docs/data-model.md; docs/architecture.md; docs/configuration.md; docs/security-model.md; docs/testing-strategy.md. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Saved model output remains untrusted recommendation, never authority to dispatch. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for Planner decision persistence; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M8-T06 — Migration strategy

- **ID:** `M8-T06`
- **Title:** Migration strategy
- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** `M8-T05`

**Objective:** Provide explicit versioned local schema evolution compatible with safe session resume.

**Repository areas:** src/recon_agent/persistence/, domain/; tests/unit/, integration/

**In scope:** Migration/version management, supported upgrade paths, transaction/backup/recovery behavior and incompatibility errors.

**Out of scope:** Silent destructive upgrades, automatic network operations and broad data-model redesign. All unrelated/future task work is excluded.

**Implementation steps:**

1. Choose/document migration approach via ADR if needed
2. Implement schema version checks and ordered migrations
3. Protect existing evidence/decisions
4. Define unsupported downgrade/failure behavior.

**Acceptance criteria:**

1. Fresh database and supported upgrade preserve state/evidence/history
2. Failure rolls back or leaves documented recoverable backup
3. Incompatible versions fail before resume
4. Migration requires no keys/network
5. Secret exclusion persists.

**Tests/validation:** Temporary SQLite fresh/upgrade/repeated/failure/unsupported-version fixtures and lineage preservation tests; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** docs/data-model.md; docs/architecture.md; docs/configuration.md; docs/security-model.md; docs/testing-strategy.md. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Never execute instructions from database content; no silent destructive conversion or authorization expansion. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for Migration strategy; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

## Milestone M9 — CLI

### M9-T01 — CLI framework

- **ID:** `M9-T01`
- **Title:** CLI framework
- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** `M0-T02`, `M0-T06`

**Objective:** Establish operator command structure and consistent non-scanning help/errors before wiring operations.

**Repository areas:** src/recon_agent/cli/; relevant configuration/orchestration/storage interfaces; tests/unit/, integration/

**In scope:** CLI framework selection, command groups/help, configuration plumbing, exit codes, injectable application services and placeholder migration.

**Out of scope:** Implicit scans on import/help and real doctor/tools/recon/status/report behavior. All unrelated/future task work is excluded.

**Implementation steps:**

1. Choose practical framework without locking unrelated libraries
2. Build command tree and typed service seams
3. Integrate non-secret error/exit formatting
4. Update console entry-point baseline.

**Acceptance criteria:**

1. Help/version and invalid-command paths work without key/network/binaries
2. Advertised unimplemented commands are clearly marked or omitted
3. Exit codes are documented
4. Imports/help cannot start session work.

**Tests/validation:** CLI invocation tests for help/version/errors/config injection and no dispatch; built-entry-point smoke; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** README.md; docs/configuration.md; docs/architecture.md; docs/security-model.md; docs/testing-strategy.md; CLI usage/reference. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** CLI flags cannot bypass policy; secret values must not appear in errors or help. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for CLI framework; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M9-T02 — recon-agent doctor

- **ID:** `M9-T02`
- **Title:** recon-agent doctor
- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** `M9-T01`, `M6-T02`, `M5-T03`

**Objective:** Diagnose environment readiness without scanning targets or exposing credentials.

**Repository areas:** src/recon_agent/cli/; relevant configuration/orchestration/storage interfaces; tests/unit/, integration/

**In scope:** Configuration validation, Groq key presence only, tool availability/version and environment diagnostics; human-readable status/exit results.

**Out of scope:** Printing secrets, automatic binary installation, live Groq validation by default and target probes. All unrelated/future task work is excluded.

**Implementation steps:**

1. Compose non-scanning checks behind interfaces
2. Show actionable missing/invalid settings and tool versions
3. Redact secret-related context
4. Define diagnostics exit behavior.

**Acceptance criteria:**

1. Doctor displays configuration/key presence/tool/environment readiness with safe errors
2. Never reveals key value or scans targets
3. Optional unavailable tools are distinguished from required blockers
4. No silent installs/API calls.

**Tests/validation:** Fake availability/config/environment CLI tests for missing key, missing/versioned tools, malformed config and redaction; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** README.md; docs/configuration.md; docs/architecture.md; docs/security-model.md; docs/testing-strategy.md; CLI usage/reference. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Diagnostics must not become an unrestricted executable/version-command endpoint. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for recon-agent doctor; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M9-T03 — recon-agent tools

- **ID:** `M9-T03`
- **Title:** recon-agent tools
- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** `M9-T02`, `M1-T04`

**Objective:** Expose registered capabilities and deterministic adapter availability to operators.

**Repository areas:** src/recon_agent/cli/; relevant configuration/orchestration/storage interfaces; tests/unit/, integration/

**In scope:** Capability/adapter listing, input/risk/limit summaries, unavailable reasons and optional machine-readable listing.

**Out of scope:** Scans, installing tools, planner-defined registrations and arbitrary availability commands. All unrelated/future task work is excluded.

**Implementation steps:**

1. Query registry and controlled availability checks
2. Format capability/implementation distinctions
3. Show risk/limits/optional requirements
4. Document listing behavior.

**Acceptance criteria:**

1. Listing reflects registry truth including unavailable adapters
2. Capabilities and implementations remain distinct
3. No target scan or secret values
4. Unknown capability filters fail clearly.

**Tests/validation:** Fake registry/availability CLI tests for active/missing/filtered tools and stable listing output; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** README.md; docs/configuration.md; docs/architecture.md; docs/security-model.md; docs/testing-strategy.md; CLI usage/reference. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Tool availability is not permission; no raw argument or executable customization via listing. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for recon-agent tools; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M9-T04 — recon-agent recon

- **ID:** `M9-T04`
- **Title:** recon-agent recon
- **Status:** NOT STARTED
- **Priority:** P0
- **Dependencies:** `M9-T03`, `M7-T08`, `M8-T06`

**Objective:** Start an authorized bounded session through the complete policy-controlled orchestration path.

**Repository areas:** src/recon_agent/cli/; relevant configuration/orchestration/storage interfaces; tests/unit/, integration/

**In scope:** Explicit target/scope/config requirement, validated operator inputs, session creation/start and safe progress/exit summaries.

**Out of scope:** Implicit broad scope, disabled policy mode, exploitation and unrestricted tool/provider flags. All unrelated/future task work is excluded.

**Implementation steps:**

1. Define required explicit authorization/scope interface
2. Validate config/targets before any traffic
3. Compose loop/storage/provider through injections
4. Document budgets/output/stop reasons.

**Acceptance criteria:**

1. No session traffic begins without explicit valid scope and target
2. Every action uses policy/registry/runner
3. Fake CLI workflow creates persisted state and reports stop reasons
4. Invalid scope/missing key/tool fails safely
5. No bypass flag exists.

**Tests/validation:** Offline CLI-to-loop/storage test with fake provider/tools including missing scope, outside target, budgets and failures; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** README.md; docs/configuration.md; docs/architecture.md; docs/security-model.md; docs/testing-strategy.md; CLI usage/reference. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Operator authorization is required but cannot enable forbidden capabilities; external activity only explicit approved run. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for recon-agent recon; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M9-T05 — recon-agent status

- **ID:** `M9-T05`
- **Title:** recon-agent status
- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** `M9-T04`

**Objective:** Show persisted session progress without triggering reconnaissance.

**Repository areas:** src/recon_agent/cli/; relevant configuration/orchestration/storage interfaces; tests/unit/, integration/

**In scope:** Session state/assets/action outcomes/budget/stop status, missing-session errors and concise or structured display.

**Out of scope:** Resuming/scanning automatically, changing scope and fabricating completion/coverage. All unrelated/future task work is excluded.

**Implementation steps:**

1. Read state through repositories
2. Format observed progress versus remaining work
3. Expose safe errors and redaction
4. Define active/stopped/completed semantics.

**Acceptance criteria:**

1. Status reads only and shows actual action/observation/budget/stop state
2. Nonexistent/corrupt session errors are actionable
3. No network/provider/runner dispatch
4. Model recommendation is not labeled completed observation.

**Tests/validation:** Temporary storage/fake service CLI tests for active/completed/failed/missing sessions and zero dispatch; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** README.md; docs/configuration.md; docs/architecture.md; docs/security-model.md; docs/testing-strategy.md; CLI usage/reference. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Remote text is escaped; stored state is untrusted and never executed on display. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for recon-agent status; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M9-T06 — recon-agent report

- **ID:** `M9-T06`
- **Title:** recon-agent report
- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** `M9-T05`, `M10-T01`, `M10-T02`

**Objective:** Generate selected reports from stored sessions without new collection activity.

**Repository areas:** src/recon_agent/cli/; relevant configuration/orchestration/storage interfaces; tests/unit/, integration/

**In scope:** Report format/destination selection, repository-to-report service wiring, safe output handling and clear unsupported format errors.

**Out of scope:** Implicit scans/provider calls, arbitrary remote uploads and unimplemented HTML format claims. All unrelated/future task work is excluded.

**Implementation steps:**

1. Load validated stored snapshot
2. Invoke registered JSON/terminal renderers
3. Handle file output and overwrite behavior explicitly
4. Document format availability and evidence/AI labels.

**Acceptance criteria:**

1. Implemented report formats export stored facts/findings/evidence with attribution
2. Unsupported formats fail clearly
3. No scan/API activity
4. File output is deliberate and errors preserve existing data
5. Secrets excluded.

**Tests/validation:** CLI report tests with stored fixtures, invalid format/path and existing destination handling; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** README.md; docs/configuration.md; docs/architecture.md; docs/security-model.md; docs/testing-strategy.md; CLI usage/reference. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Paths are operator input, never remote/model instructions; avoid secret leaks and unsafe overwrite. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for recon-agent report; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M9-T07 — Operator cancellation and graceful shutdown

- **ID:** `M9-T07`
- **Title:** Operator cancellation and graceful shutdown
- **Status:** NOT STARTED
- **Priority:** P0
- **Dependencies:** `M9-T06`, `M7-T04`

**Objective:** Make interruption terminate child work and leave recoverable auditable session state.

**Repository areas:** src/recon_agent/cli/; relevant configuration/orchestration/storage interfaces; tests/unit/, integration/

**In scope:** CLI interrupt/signal handling, orchestrator cancellation propagation, runner cleanup, final storage/audit and documented exit codes.

**Out of scope:** Ignoring operator cancellation, forced unrelated-process termination and indefinite shutdown. All unrelated/future task work is excluded.

**Implementation steps:**

1. Connect cancellation token/signal paths to loop and runner
2. Stop new dispatch
3. Bound cleanup and persist interrupted outcomes
4. Verify resumable state and output/exit semantics.

**Acceptance criteria:**

1. Interrupt prevents additional actions and terminates owned work within bounded time
2. Action/session cancellation records persist
3. Evidence/history remain consistent for resume
4. No unrelated process is targeted.

**Tests/validation:** Fake signal/token/runner/storage tests for cancellation during plan/execute/write and bounded cleanup; opt-in harmless process test if required; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** README.md; docs/configuration.md; docs/architecture.md; docs/security-model.md; docs/testing-strategy.md; CLI usage/reference. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Cancellation cannot be overridden by provider; no unrecorded successful action after interruption. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for Operator cancellation and graceful shutdown; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

## Milestone M10 — Reporting

### M10-T01 — JSON report

- **ID:** `M10-T01`
- **Title:** JSON report
- **Status:** NOT STARTED
- **Priority:** P2
- **Dependencies:** `M8-T06`, `M5-T05`

**Objective:** Export normalized session state as a machine-readable traceable report.

**Repository areas:** src/recon_agent/reporting/; domain/storage interfaces; tests/unit/, fixtures/

**In scope:** Versioned report schema with assets/services/endpoints/observations/findings/evidence/actions/decisions/budgets/stop limitations.

**Out of scope:** Live collection, credential export and converting AI recommendations into facts. All unrelated/future task work is excluded.

**Implementation steps:**

1. Define report schema and field attribution
2. Serialize stored snapshots deterministically
3. Validate evidence references and redaction
4. Document compatibility and incomplete coverage.

**Acceptance criteria:**

1. JSON is schema-valid/stable for fixtures and includes source/limitations/evidence links
2. Facts/findings/decisions stay distinct
3. Secrets excluded
4. Partial/failed sessions are representable without invented coverage.

**Tests/validation:** Report fixtures/schema round-trip, ordering, partial state, lineage and redaction tests; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** README.md; docs/data-model.md; docs/security-model.md; docs/configuration.md; reporting format/reference docs. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Untrusted strings remain JSON data; no executable fields or automatic external evidence fetching. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for JSON report; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M10-T02 — Terminal summary

- **ID:** `M10-T02`
- **Title:** Terminal summary
- **Status:** NOT STARTED
- **Priority:** P2
- **Dependencies:** `M10-T01`

**Objective:** Present concise operator-readable session outcomes with accurate provenance and limitations.

**Repository areas:** src/recon_agent/reporting/; domain/storage interfaces; tests/unit/, fixtures/

**In scope:** Assets/services/findings, action/stop/budget summary and AI attribution; safe terminal escaping and optional non-interactive output.

**Out of scope:** Live progress collection changes and replacing detailed evidence with unsupported claims. All unrelated/future task work is excluded.

**Implementation steps:**

1. Design compact summary from report/domain snapshots
2. Distinguish observed facts and interpreted conclusions
3. Escape control text and redact
4. Handle empty/partial sessions.

**Acceptance criteria:**

1. Summary matches stored state and discloses failure/coverage/stop reason
2. Evidence references are discoverable
3. AI interpretation is labeled
4. Malicious terminal control sequences do not render as control commands
5. Secrets omitted.

**Tests/validation:** Captured output tests for complete/empty/partial/hostile fixtures and semantic attribution; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** README.md; docs/data-model.md; docs/security-model.md; docs/configuration.md; reporting format/reference docs. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Remote banners/titles cannot control terminal or impersonate trusted operator messages. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for Terminal summary; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M10-T03 — HTML report

- **ID:** `M10-T03`
- **Title:** HTML report
- **Status:** NOT STARTED
- **Priority:** P2
- **Dependencies:** `M10-T02`

**Objective:** Render navigable local evidence-aware reports with explicit AI interpretation labels.

**Repository areas:** src/recon_agent/reporting/; domain/storage interfaces; tests/unit/, fixtures/

**In scope:** Assets/services/observations/findings/evidence/planner activity views, static escaped rendering and safe local output.

**Out of scope:** Remote script execution, credential exposure, remote asset loading by default and live scan controls. All unrelated/future task work is excluded.

**Implementation steps:**

1. Choose static rendering approach
2. Build views from validated report model
3. Escape all remote/model content and restrict links/assets
4. Provide evidence navigation and incomplete coverage notices.

**Acceptance criteria:**

1. HTML exposes requested entities/relationships and provenance
2. Observed evidence differs visually/semantically from AI interpretation
3. Hostile markup/script is escaped
4. Report loads locally without external assets or network
5. No secrets.

**Tests/validation:** HTML render fixtures with injection/link/control text, empty/partial sessions and evidence navigation checks; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** README.md; docs/data-model.md; docs/security-model.md; docs/configuration.md; reporting format/reference docs. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Remote HTML/JavaScript is evidence, never report executable content; unsafe link schemes disallowed. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for HTML report; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M10-T04 — Evidence traceability

- **ID:** `M10-T04`
- **Title:** Evidence traceability
- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** `M10-T03`

**Objective:** Ensure meaningful findings remain explainable back to collected evidence and executions across reports.

**Repository areas:** src/recon_agent/reporting/; domain/storage interfaces; tests/unit/, fixtures/

**In scope:** Cross-format evidence/source links, integrity checks, missing/retained/truncated source handling and lineage validation.

**Out of scope:** Fabricated evidence, exploitation verification and silently deleting source limitations. All unrelated/future task work is excluded.

**Implementation steps:**

1. Audit finding-to-observation/evidence/execution paths
2. Implement validation and consistent reference rendering
3. Expose missing/expired/truncated source limitations
4. Prevent unsupported confidence claims.

**Acceptance criteria:**

1. Every meaningful finding has resolvable supporting evidence/execution or explicit unavailable-source limitation that prevents unsupported confirmation
2. All formats expose same lineage
3. Redaction/retention does not silently break references.

**Tests/validation:** Cross-format lineage fixtures with complete/orphaned/redacted/expired/truncated evidence; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** README.md; docs/data-model.md; docs/security-model.md; docs/configuration.md; reporting format/reference docs. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** AI text cannot serve as collected proof of a vulnerability; preserve untrusted source labels. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for Evidence traceability; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M10-T05 — Planner disclosure

- **ID:** `M10-T05`
- **Title:** Planner disclosure
- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** `M10-T04`

**Objective:** Label AI-derived recommendations and interpretations consistently rather than presenting them as scanner facts.

**Repository areas:** src/recon_agent/reporting/; domain/storage interfaces; tests/unit/, fixtures/

**In scope:** Provider/model/policy attribution, decision versus observation labels, uncertainty/coverage disclosures across JSON/terminal/HTML.

**Out of scope:** Claiming model certainty or editing original observations to match recommendations. All unrelated/future task work is excluded.

**Implementation steps:**

1. Define disclosure vocabulary and metadata
2. Apply to all report formats and planner-derived findings
3. Document which fields are collected/inferred/recommended
4. Audit examples.

**Acceptance criteria:**

1. AI-derived interpretation has explicit attribution in every format
2. Decisions cannot be mistaken for executed actions or facts
3. Uncertainty/unfinished work is visible
4. Evidence remains the source of observations.

**Tests/validation:** Cross-format fixture tests for recommendation-only, scanner finding and AI interpretation records; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** README.md; docs/data-model.md; docs/security-model.md; docs/configuration.md; reporting format/reference docs. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Disclosure preserves trust hierarchy and avoids implying exploitation or confirmed findings from mere recommendations. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for Planner disclosure; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

## Milestone M11 — Reliability and testing hardening

### M11-T01 — Fixture corpus

- **ID:** `M11-T01`
- **Title:** Fixture corpus
- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** `M7-T08`, `M10-T05`

**Objective:** Maintain a sanitized representative evidence corpus for every supported tool/protocol/provider contract.

**Repository areas:** tests/unit/, integration/, fixtures/; changed parsers/policy/runner/orchestration for demonstrated defects only

**In scope:** Sample outputs/version metadata, complete/partial/malformed/hostile cases, provenance and contribution/sanitization rules.

**Out of scope:** Collecting unauthorized live data and committing private target details or credentials. All unrelated/future task work is excluded.

**Implementation steps:**

1. Inventory supported adapters/formats
2. Sanitize and record fixture context
3. Add missing edge/failure cases
4. Define stable naming/version update rules.

**Acceptance criteria:**

1. Every supported adapter has representative safe fixture coverage including errors/partial/injection data
2. Provenance/version and sanitization are documented
3. Fixtures need no binaries/network and contain no secrets/private identifiers.

**Tests/validation:** Fixture inventory and secret/sanitization inspection; execute fixture-driven tests and full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** docs/testing-strategy.md; docs/security-model.md; docs/tool-contracts.md; docs/planner-contract.md; fixture provenance/reference. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Fixtures are untrusted data and cannot influence test policy or execute commands. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for Fixture corpus; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M11-T02 — Parser regression suite

- **ID:** `M11-T02`
- **Title:** Parser regression suite
- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** `M11-T01`

**Objective:** Prevent tool-format drift and malformed output from corrupting normalized state.

**Repository areas:** tests/unit/, integration/, fixtures/; changed parsers/policy/runner/orchestration for demonstrated defects only

**In scope:** Corpus-wide parser tests, supported-version compatibility, partial/unknown fields and provenance/error behavior.

**Out of scope:** Unreviewed live tool upgrades and parser fallback to arbitrary presentation scraping. All unrelated/future task work is excluded.

**Implementation steps:**

1. Map corpus to parser cases
2. Assert typed facts/evidence and limitations rather than implementation internals
3. Add format drift/malformed cases
4. Fix demonstrated parser defects.

**Acceptance criteria:**

1. All supported-format fixtures parse or fail explicitly by documented compatibility
2. Partial/unknown data does not invent facts
3. Hostile text remains evidence
4. Lineage and output bounds survive regression cases.

**Tests/validation:** Run parser corpus suite, targeted defect regressions and full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** docs/testing-strategy.md; docs/security-model.md; docs/tool-contracts.md; docs/planner-contract.md; fixture provenance/reference. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Parsers must not evaluate remote text or fetch external XML/resources. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for Parser regression suite; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M11-T03 — Process failure matrix

- **ID:** `M11-T03`
- **Title:** Process failure matrix
- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** `M11-T02`, `M1-T03`

**Objective:** Prove runner/adapter behavior for all controlled process failures and resource edge cases.

**Repository areas:** tests/unit/, integration/, fixtures/; changed parsers/policy/runner/orchestration for demonstrated defects only

**In scope:** Missing binary, non-zero exit, timeout, invalid/partial/large output, cancellation and cleanup outcomes across adapters.

**Out of scope:** Real security-tool scans and unrestricted process fault injection. All unrelated/future task work is excluded.

**Implementation steps:**

1. Create fake runner/process matrix
2. Test result classification, evidence limits, child cleanup and no unsafe fallback
3. Exercise adapters under each applicable failure.

**Acceptance criteria:**

1. Every listed failure has expected typed outcome and bounded cleanup/output
2. Partial data is labeled
3. No failure creates false success or unrestricted fallback
4. Audits preserve safe execution metadata.

**Tests/validation:** Offline fake-process matrix and adapter contract suites; explicitly marked harmless process integration only if necessary; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** docs/testing-strategy.md; docs/security-model.md; docs/tool-contracts.md; docs/planner-contract.md; fixture provenance/reference. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Failure cannot reset budgets, expand scope or leak environment/keys. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for Process failure matrix; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M11-T04 — Policy fuzz/property tests

- **ID:** `M11-T04`
- **Title:** Policy fuzz/property tests
- **Status:** NOT STARTED
- **Priority:** P0
- **Dependencies:** `M11-T03`, `M1-T02`, `M6-T07`

**Objective:** Challenge scope/action boundaries with generated confusing representations and invariant-based tests.

**Repository areas:** tests/unit/, integration/, fixtures/; changed parsers/policy/runner/orchestration for demonstrated defects only

**In scope:** Property/fuzz tests for host/URL/IP/CIDR normalization, parameter/schema validation, derived targets, budget/dedup invariants.

**Out of scope:** Network fuzzing, attacks against live services and weakening expectations to satisfy generated cases. All unrelated/future task work is excluded.

**Implementation steps:**

1. Define security invariants and bounded deterministic seeds
2. Generate malformed/ambiguous equivalents
3. Minimize failures into regression fixtures
4. Fix only demonstrated boundary defects.

**Acceptance criteria:**

1. Properties show outside/ambiguous inputs never dispatch and valid canonical equivalents agree
2. Deterministic bounded test runs reproduce failures
3. Minimized discovered bugs are retained
4. No generated case causes live activity.

**Tests/validation:** Property/fuzz suite with documented seeds/bounds plus regressions and full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** docs/testing-strategy.md; docs/security-model.md; docs/tool-contracts.md; docs/planner-contract.md; fixture provenance/reference. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Assertions test authorization outcomes rather than mirroring parser code; all execution uses fakes. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for Policy fuzz/property tests; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M11-T05 — Autonomous-loop regression suite

- **ID:** `M11-T05`
- **Title:** Autonomous-loop regression suite
- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** `M11-T04`, `M7-T08`

**Objective:** Guard adaptive orchestration behavior across decision failures, histories and stop paths.

**Repository areas:** tests/unit/, integration/, fixtures/; changed parsers/policy/runner/orchestration for demonstrated defects only

**In scope:** Deterministic fake providers/tools for useful transitions, duplicate loops, rejection, retry, cancellation, resume and report lineage.

**Out of scope:** Live model comparisons and fixed text assertions pretending to prove reasoning quality. All unrelated/future task work is excluded.

**Implementation steps:**

1. Build scenario matrix from actual loop contracts
2. Assert decisions/dispatch/state/history/stop invariants
3. Cover changed policy and partial failures
4. Persist regression fixtures.

**Acceptance criteria:**

1. All key loop/stop/recovery/resume paths run offline and terminate
2. Rejected actions never dispatch
3. Useful allowed actions update state
4. Histories/budgets/evidence remain coherent
5. No endless repeats.

**Tests/validation:** Run loop regression matrix and full baseline without credentials or binaries. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** docs/testing-strategy.md; docs/security-model.md; docs/tool-contracts.md; docs/planner-contract.md; fixture provenance/reference. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Adversarial fake provider must face real policy; test no execution, not merely returned error. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for Autonomous-loop regression suite; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M11-T06 — Concurrency tests

- **ID:** `M11-T06`
- **Title:** Concurrency tests
- **Status:** NOT STARTED
- **Priority:** P0
- **Dependencies:** `M11-T05`, `M1-T06`

**Objective:** Prove simultaneous actions cannot oversubscribe limits, bypass scope or corrupt state/history.

**Repository areas:** tests/unit/, integration/, fixtures/; changed parsers/policy/runner/orchestration for demonstrated defects only

**In scope:** Concurrent budget reservation, per-host/tool rate limits, dedup claims, cancellation and state/storage consistency.

**Out of scope:** Public-target load testing and unrestricted performance optimization. All unrelated/future task work is excluded.

**Implementation steps:**

1. Use deterministic barriers/fake clocks/runners to force race windows
2. Assert atomic dispatch decisions and lifecycle writes
3. Test cancellation/rejection while work is pending
4. Fix demonstrated race defects.

**Acceptance criteria:**

1. Concurrency/action/host/rate/output limits hold across races
2. Duplicate actions do not double dispatch
3. Scope updates/stale approvals fail safely
4. Cancelled work leaves coherent audited storage and budgets.

**Tests/validation:** Deterministic race/concurrency suite with repeated bounded runs only where needed; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** docs/testing-strategy.md; docs/security-model.md; docs/tool-contracts.md; docs/planner-contract.md; fixture provenance/reference. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Authorization and reservation must be atomic or revalidated immediately before dispatch; no outside contact in tests. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for Concurrency tests; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M11-T07 — Secret-handling audit

- **ID:** `M11-T07`
- **Title:** Secret-handling audit
- **Status:** NOT STARTED
- **Priority:** P0
- **Dependencies:** `M11-T06`, `M6-T02`, `M10-T05`

**Objective:** Verify credentials cannot escape through logs, reports, exceptions, fixtures, planner input or persisted state.

**Repository areas:** tests/unit/, integration/, fixtures/; changed parsers/policy/runner/orchestration for demonstrated defects only

**In scope:** Groq secret paths, configuration redaction, diagnostic presence checks, error/provider transport context and evidence sanitization.

**Out of scope:** Real credential collection, remote secret scanning and general unrelated security rewrites. All unrelated/future task work is excluded.

**Implementation steps:**

1. Trace synthetic sentinel key through config/provider/error paths
2. Inspect logs/state/reports/prompts/fixtures
3. Add regression tests for demonstrated leaks
4. Document audit evidence and remaining boundaries.

**Acceptance criteria:**

1. Synthetic credentials never appear in any exported/logged/persisted/planner artifact
2. Doctor shows presence only
3. Exceptions are safe
4. Fixtures/committed files contain no real credentials
5. No live key is needed.

**Tests/validation:** Sentinel-key leakage tests and direct tracked-file inspection; full baseline; record audit coverage. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** docs/testing-strategy.md; docs/security-model.md; docs/tool-contracts.md; docs/planner-contract.md; fixture provenance/reference. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Use fake secrets only; do not reveal discovered real secrets in output; no secret mechanism can grant execution authority. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for Secret-handling audit; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

## Milestone M12 — Packaging and operations

### M12-T01 — Installable package

- **ID:** `M12-T01`
- **Title:** Installable package
- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** `M11-T07`, `M9-T07`

**Objective:** Confirm reproducible local installation of the implemented product and console entry point.

**Repository areas:** pyproject.toml; dependency/build configuration; docs/; CI configuration; package/CLI boundaries; tests/

**In scope:** Wheel/sdist contents, Python >=3.12 metadata, dependency strategy, package resources and clean-environment install/smoke.

**Out of scope:** Publishing artifacts, silently installing security binaries and changing capability semantics. All unrelated/future task work is excluded.

**Implementation steps:**

1. Build clean artifacts
2. Inspect inclusion/exclusion of docs/resources/secrets
3. Install in isolated environments
4. Verify entry point/help/doctor through non-scanning paths
5. Document reproducibility inputs.

**Acceptance criteria:**

1. Wheel/sdist build and install reproducibly with declared dependencies and required resources
2. Console entry point works
3. No secrets/test-private artifacts included
4. No security binaries/network scans are installed/run implicitly.

**Tests/validation:** Build/install/artifact inspection and offline post-install smoke; full baseline; dependency provisioning documented separately. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** README.md; docs/configuration.md; docs/testing-strategy.md; installation/operations/release guidance; CHANGELOG.md. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Installation must not trigger scans or key exposure; supply-chain/tool dependencies remain explicit. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for Installable package; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M12-T02 — External tool discovery strategy

- **ID:** `M12-T02`
- **Title:** External tool discovery strategy
- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** `M12-T01`, `M9-T02`

**Objective:** Document and verify controlled binary discovery/version support for required and optional adapters.

**Repository areas:** pyproject.toml; dependency/build configuration; docs/; CI configuration; package/CLI boundaries; tests/

**In scope:** Trusted configured paths/search order, supported versions, availability statuses and optional/required capability mapping.

**Out of scope:** Automatic downloads/installs and arbitrary executable paths supplied by model/remote content. All unrelated/future task work is excluded.

**Implementation steps:**

1. Inventory adapters and supported versions
2. Reconcile doctor/registry detection behavior
3. Define trusted path precedence and incompatibility handling
4. Document operator diagnostics.

**Acceptance criteria:**

1. Discovery precedence and required/optional binaries are explicit
2. Unsupported/missing versions fail clearly without scan
3. No silent fallback broadens capability
4. Configured executable paths are trusted operator inputs only.

**Tests/validation:** Fake path/version/availability tests and doctor/tools smoke; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** README.md; docs/configuration.md; docs/testing-strategy.md; installation/operations/release guidance; CHANGELOG.md. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Availability checks run controlled known commands without shell; tool updates cannot silently change effective safety. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for External tool discovery strategy; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M12-T03 — Environment bootstrap documentation

- **ID:** `M12-T03`
- **Title:** Environment bootstrap documentation
- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** `M12-T02`

**Objective:** Provide reproducible operator/developer setup guidance with explicit security-tool provisioning.

**Repository areas:** pyproject.toml; dependency/build configuration; docs/; CI configuration; package/CLI boundaries; tests/

**In scope:** Python/dependencies, optional/required binary requirements, trusted setup sources, Groq secret setup, local storage and offline/lab test guidance.

**Out of scope:** Silent system-tool installation, real credentials in examples and public-target quick scans. All unrelated/future task work is excluded.

**Implementation steps:**

1. Write clean environment/development procedures using current supported prerequisites
2. Explain manual explicit tool installation and versions
3. Include no-key offline validation and safe troubleshooting.

**Acceptance criteria:**

1. Guidance matches package/tool/config evidence and separates dependency setup from scans
2. Examples use placeholders/local authorized targets
3. No secrets or unreviewed automatic security-tool installs
4. Offline developer path is clear.

**Tests/validation:** Execute applicable clean-environment package/help/offline steps; manually reconcile binary instructions with discovery support; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** README.md; docs/configuration.md; docs/testing-strategy.md; installation/operations/release guidance; CHANGELOG.md. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Setup does not imply scan authorization; never commit environment secrets. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for Environment bootstrap documentation; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M12-T04 — CI

- **ID:** `M12-T04`
- **Title:** CI
- **Status:** NOT STARTED
- **Priority:** P0
- **Dependencies:** `M12-T03`, `M11-T07`

**Objective:** Automate complete credential-free validation without external reconnaissance traffic.

**Repository areas:** pyproject.toml; dependency/build configuration; docs/; CI configuration; package/CLI boundaries; tests/

**In scope:** CI lint/format, type checks, unit tests, offline integration tests, package build and non-network smoke; explicit external-test exclusion.

**Out of scope:** Live Groq/scanning jobs, secret-dependent default CI, publishing/releases and silent system-tool installation. All unrelated/future task work is excluded.

**Implementation steps:**

1. Define Python >=3.12 job/dependency strategy
2. Run exact documented complete checks
3. Gate external markers out
4. Expose failures/artifacts without secrets
5. Document local parity.

**Acceptance criteria:**

1. CI definition runs all required lint/type/unit/offline integration/build checks and smoke
2. Needs no Groq credentials/recon binaries
3. No live target job
4. Local equivalent commands pass
5. Actual hosted execution is reported only if observed.

**Tests/validation:** Run local CI-equivalent checks and inspect workflow/marker selection; validate syntax using available appropriate tooling; report hosted run if actually executed. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** README.md; docs/configuration.md; docs/testing-strategy.md; installation/operations/release guidance; CHANGELOG.md. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** CI must not perform Internet reconnaissance; dependency provisioning is distinct from tests; artifacts exclude secrets. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for CI; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M12-T05 — Release/versioning policy

- **ID:** `M12-T05`
- **Title:** Release/versioning policy
- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** `M12-T04`

**Objective:** Define evidence-based versioning and release gates before MVP declaration.

**Repository areas:** pyproject.toml; dependency/build configuration; docs/; CI configuration; package/CLI boundaries; tests/

**In scope:** Semantic version approach, changelog rules, artifacts/provenance, acceptance/security/docs gates and rollback/support policy.

**Out of scope:** Publishing/tagging/pushing a release without separate explicit authorization and inventing MVP completion. All unrelated/future task work is excluded.

**Implementation steps:**

1. Record versioning/release decision via ADR if alternatives matter
2. Document gate checklist tied to completed tasks/CI
3. Define artifact/review procedure and user-visible changes.

**Acceptance criteria:**

1. Release/versioning policy is explicit and consistent with metadata/changelog
2. Security/validation/docs/MVP gates precede publication
3. External publication remains separately authorized
4. No release claimed solely from roadmap status.

**Tests/validation:** Document/policy consistency inspection, release dry-run checklist without publication, full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** README.md; docs/configuration.md; docs/testing-strategy.md; installation/operations/release guidance; CHANGELOG.md. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Release gates include secret audit, scope controls and offline tests; never force push or rewrite history. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for Release/versioning policy; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

## Milestone M13 — Documentation closeout and MVP release

### M13-T01 — Architecture reconciliation

- **ID:** `M13-T01`
- **Title:** Architecture reconciliation
- **Status:** NOT STARTED
- **Priority:** P0
- **Dependencies:** `M12-T05`, `M10-T05`

**Objective:** Align architecture claims with actual implemented boundaries and repository evidence.

**Repository areas:** Root governance/state/README/CHANGELOG; docs/; relevant code/tests only for scoped reconciliation defects; authorized lab acceptance artifacts

**In scope:** Domain/policy/execution/adapter/provider/orchestration/persistence/reporting/CLI review, diagrams/interfaces and ADR reconciliation.

**Out of scope:** Unapproved redesign, new capabilities and documenting plans as delivered product. All unrelated/future task work is excluded.

**Implementation steps:**

1. Trace each architectural claim to code/tests and current ADRs
2. Classify implemented/deferred behavior
3. Correct documents or record scoped follow-up defects
4. Audit provider/runner boundary isolation.

**Acceptance criteria:**

1. Architecture doc reflects real layers/dependencies and known limitations
2. Unresolved inconsistencies are explicit blockers/follow-ups
3. No delivered claim lacks evidence
4. Important decisions have current ADR references.

**Tests/validation:** Repository/code/doc comparison with acceptance mapping; focused tests if code fixes are authorized within scope; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** README.md; PLAN.md; PROJECT_STATE.md; CURRENT_TASK.md; TASK_HISTORY.md; CHANGELOG.md; all subsystem contracts/security/configuration/testing docs. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** No documented safety control substitutes for missing implementation; missing mandatory boundary blocks release. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for Architecture reconciliation; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M13-T02 — Security model review

- **ID:** `M13-T02`
- **Title:** Security model review
- **Status:** NOT STARTED
- **Priority:** P0
- **Dependencies:** `M13-T01`, `M11-T07`

**Objective:** Revalidate every non-negotiable safety invariant against implemented code and tests before MVP.

**Repository areas:** Root governance/state/README/CHANGELOG; docs/; relevant code/tests only for scoped reconciliation defects; authorized lab acceptance artifacts

**In scope:** Scope/redirect/DNS enforcement, injection, argv/no shell, profiles, budgets/concurrency, secrets, evidence trust, cancellation/resume and non-goals.

**Out of scope:** Penetration/exploitation of live systems and accepting missing invariants as documentation-only promises. All unrelated/future task work is excluded.

**Implementation steps:**

1. Map trust boundaries/constraints to execution paths and regression evidence
2. Inspect tool-internal behavior and current profiles
3. Reconcile security doc
4. Record/block unresolved violations.

**Acceptance criteria:**

1. Every invariant has code/test evidence and documented limits
2. No LLM execution bypass exists
3. Outside derived requests are prevented before contact
4. Secrets/budgets/profile restrictions hold
5. Unresolved safety violations block MVP.

**Tests/validation:** Security checklist/code inspection plus targeted scope/injection/concurrency/secret suites and full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** README.md; PLAN.md; PROJECT_STATE.md; CURRENT_TASK.md; TASK_HISTORY.md; CHANGELOG.md; all subsystem contracts/security/configuration/testing docs. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Fail closed; security acceptance cannot be waived by model behavior or broad operator configuration. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for Security model review; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M13-T03 — Operator quickstart

- **ID:** `M13-T03`
- **Title:** Operator quickstart
- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** `M13-T02`, `M9-T07`

**Objective:** Document the actual authorized first-run workflow including scope, limits, evidence and stop behavior.

**Repository areas:** Root governance/state/README/CHANGELOG; docs/; relevant code/tests only for scoped reconciliation defects; authorized lab acceptance artifacts

**In scope:** Install/doctor/tools, explicit lab target/scope/config/key setup, recon/status/report/cancel/resume and limitations.

**Out of scope:** Public-target defaults, real keys, automatic attacks and unimplemented command examples. All unrelated/future task work is excluded.

**Implementation steps:**

1. Write steps from current CLI/config contracts
2. Use explicit local/lab placeholders and authorization context
3. Demonstrate conservative budgets and evidence/AI distinctions
4. Explain safe errors and cancellation.

**Acceptance criteria:**

1. Quickstart matches executable commands/config and requires explicit authorization/scope
2. No default public scan or secret values
3. Limits/cancellation/report interpretation are understandable
4. Deferred features labeled accurately.

**Tests/validation:** Fake/offline walkthrough commands and help/config validation; real scan only reserved for separately authorized M13-T05 lab; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** README.md; PLAN.md; PROJECT_STATE.md; CURRENT_TASK.md; TASK_HISTORY.md; CHANGELOG.md; all subsystem contracts/security/configuration/testing docs. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Examples cannot normalize broad scanning or imply discovered assets are automatically authorized. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for Operator quickstart; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M13-T04 — Tool capability reference

- **ID:** `M13-T04`
- **Title:** Tool capability reference
- **Status:** NOT STARTED
- **Priority:** P1
- **Dependencies:** `M13-T03`, `M12-T02`

**Objective:** Provide a complete operator reference for actual capabilities and controlled adapter requirements.

**Repository areas:** Root governance/state/README/CHANGELOG; docs/; relevant code/tests only for scoped reconciliation defects; authorized lab acceptance artifacts

**In scope:** Capability/adapter mapping, required/optional binaries/versions, schemas, outputs/provenance, risk profiles, scope behavior and limits.

**Out of scope:** Unrestricted argument recipes, undocumented capabilities and claimed support for unimplemented tools. All unrelated/future task work is excluded.

**Implementation steps:**

1. Inventory registry/code/fixture evidence
2. Document each implemented capability and availability
3. Show permitted named modes/profiles and failure behavior
4. Reconcile tool contracts and installation guidance.

**Acceptance criteria:**

1. Reference matches registry/adapter reality with inputs/outputs/limits and required/optional binaries
2. Scope/redirect/profile behavior is explicit
3. Unimplemented/deferred capabilities are labeled
4. No raw model command interface implied.

**Tests/validation:** Cross-check reference against registry, schemas, supported fixtures and doctor/tools; full baseline. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** README.md; PLAN.md; PROJECT_STATE.md; CURRENT_TASK.md; TASK_HISTORY.md; CHANGELOG.md; all subsystem contracts/security/configuration/testing docs. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Reference must explain effective safety envelope, not just binary invocation options. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for Tool capability reference; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M13-T05 — MVP acceptance test

- **ID:** `M13-T05`
- **Title:** MVP acceptance test
- **Status:** NOT STARTED
- **Priority:** P0
- **Dependencies:** `M13-T04`, `M7-T08`, `M12-T04`

**Objective:** Verify controlled end-to-end behavior in an explicitly authorized local/lab environment with recorded evidence.

**Repository areas:** Root governance/state/README/CHANGELOG; docs/; relevant code/tests only for scoped reconciliation defects; authorized lab acceptance artifacts

**In scope:** Lab authorization/scope manifest, conservative budgets/profiles, selected supported tools/provider configuration, reports/traceability/cancel/resume and deny checks.

**Out of scope:** Public Internet reconnaissance, exploitation/authentication attacks and implicit authorization from this roadmap. All unrelated/future task work is excluded.

**Implementation steps:**

1. Prepare concrete lab targets and authorization before real traffic
2. Run offline baseline first
3. Execute bounded controlled session and denial/cancel/resume scenarios
4. Record sanitized outputs, versions, limits and acceptance outcome.

**Acceptance criteria:**

1. Explicit lab authorization exists before traffic
2. Supported end-to-end session yields traceable observations/findings/disclosed AI activity
3. Outside targets deny without contact
4. Stops/cancel/resume/limits work
5. Report and execution evidence are sanitized
6. Missing lab/key/tool prerequisites block rather than weaken acceptance.

**Tests/validation:** Complete offline baseline plus explicitly authorized lab scenario and evidence review; no lab run is claimed unless actually executed. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** README.md; PLAN.md; PROJECT_STATE.md; CURRENT_TASK.md; TASK_HISTORY.md; CHANGELOG.md; all subsystem contracts/security/configuration/testing docs. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** This task specification alone does not authorize scanning; require operator-established lab scope and forbid intrusive modes. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for MVP acceptance test; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

### M13-T06 — MVP documentation closeout

- **ID:** `M13-T06`
- **Title:** MVP documentation closeout
- **Status:** NOT STARTED
- **Priority:** P0
- **Dependencies:** `M13-T05`

**Objective:** Declare MVP only when repository evidence and completed release gates support it.

**Repository areas:** Root governance/state/README/CHANGELOG; docs/; relevant code/tests only for scoped reconciliation defects; authorized lab acceptance artifacts

**In scope:** Reconcile README/PLAN/PROJECT_STATE/CHANGELOG, architecture/config/security/tool/planner/testing docs, history, release readiness and remaining known limitations.

**Out of scope:** Unapproved publication/push/tag, starting follow-up implementation and declaring incomplete security work complete. All unrelated/future task work is excluded.

**Implementation steps:**

1. Check every MVP dependency/evidence/gate
2. Reconcile all listed documents with acceptance results
3. Record actual delivered/deferred scope and follow-ups
4. Close active task and produce reviewable release-ready state.

**Acceptance criteria:**

1. All preceding required MVP tasks/gates are DONE with real validation/lab evidence
2. Listed docs agree with implementation and each other
3. No active task at closure
4. Known limitations disclosed
5. MVP declaration is evidence-based
6. Publication remains separately authorized.

**Tests/validation:** Full validation, documentation/link/status/dependency consistency, acceptance evidence audit and final diff/tree inspection. Also complete the phase-appropriate repository baseline and inspect final Git diff.

**Documentation impact:** README.md; PLAN.md; PROJECT_STATE.md; CURRENT_TASK.md; TASK_HISTORY.md; CHANGELOG.md; all subsystem contracts/security/configuration/testing docs. Reconcile specific changed contracts/behavior; update PLAN, PROJECT_STATE, CURRENT_TASK and append TASK_HISTORY; CHANGELOG for visible changes.

**Security considerations:** Unresolved mandatory safety/security blockers prevent MVP; no credentials in release documentation/artifacts. Repository invariants remain mandatory.

**Expected evidence of completion:** Task-owned implementation/docs for MVP documentation closeout; executed results from the specified validation (including failures/limitations), concrete mapping of each acceptance criterion to code/tests or reviewed documentation, and focused commit/tree outcome in TASK_HISTORY. No planned or unrun check counts as evidence.

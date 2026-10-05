# Project state

Project phase: Foundation / domain contracts

Completed:

- M0-T01 — Repository governance and planning scaffold (DONE)
- M0-T02 — Python project and developer tooling baseline (DONE)
- M0-T03 — Configuration foundation (DONE)
- M0-T04 — Core domain model foundation (DONE)

Active task: None

Next READY:

- M0-T05 — Error taxonomy and result model (not started)

## Implementation reality

The 92-task roadmap, governance, maintenance skill and design documentation exist. `recon-agent` 0.1.0 installs through setuptools with Python >=3.12 metadata. Pydantic is the sole direct runtime dependency; the existing developer tooling and inert CLI are unchanged.

`core/config/` implements strict scope/execution/planner/tools/persistence/logging/reporting settings, explicit defaults < TOML < namespaced environment < programmatic precedence, and separately redacted/excluded credentials. Preferences do not grant authorization or enforce budgets.

`domain/` now exports 13 pure data contracts: Target, Scope, Asset, Host, Service, Endpoint, Observation, Evidence, ActionRequest, ActionResult, PlannerDecision, ReconState and ReconSession. They reject unknown fields/invalid structural values and serialize deterministically with caller-supplied opaque IDs and aware timestamps normalized to UTC. Observations require evidence/source provenance; evidence is untrusted and uses opaque artifact references. Action requests contain unapproved capability intent and JSON parameters without executable keys; decisions are recommendations. Results distinguish completed/partial/failed outcomes with a minimal failure/limitation reason, not the M0-T05 taxonomy. Record attributes are frozen; state/session containers are mutable data with no transition APIs. See docs/data-model.md for exact contracts and limitations.

Action, ToolExecution and Finding are explicitly staged for later lifecycle/runner/finding tasks. There is no project-wide error taxonomy, audit logging, scope enforcement, capability registry/policy, runner, scanner adapter, Groq client, planner runtime, state machine, deduplication/budget enforcement, autonomous orchestration, SQLite persistence or operational reporting. M0-T05 is READY and unstarted; remaining 87 tasks are NOT STARTED.

## Major architecture decisions

- Predefined capability intent, never LLM-generated shell/argv; registry/policy/adapters will own validation and execution.
- Centralized deterministic fail-closed scope/action validation must precede contact, including derived destinations.
- Remote evidence and model recommendations remain non-authoritative data with provenance.
- Pydantic validates configuration/domain contracts; domain imports no configuration or higher layers and performs no I/O.
- Explicit TOML sources and separate credentials remain as ADR 0001 defines; no new runtime dependency or ADR was necessary for domain contracts.
- IDs/timestamps are explicit rather than automatically generated; canonical identity and operational mutation remain future work.
- Groq provider abstraction and SQLite repositories remain planned; default tests use deterministic offline fixtures/fakes and exclude external/network markers.

## Validation

Python 3.14.6 / Pydantic 2.13.5: editable install/pip check, 151 focused domain cases, Ruff lint/format, strict Mypy (21 production modules), full 217-test suite, coverage (100%, 269 statements / 52 branches), sdist/wheel build and inert CLI smoke passed. All 217 tests also passed with socket network functions blocked. A clean temporary wheel installation outside the checkout passed isolated domain imports, Service/ActionRequest validation, nested session JSON round trip, CLI and pip check with runtime network/process/database/directory/logging/config-file activity blocked during model smoke; ordinary dependency metadata reads were allowed. Source boundaries, archives/dependencies, documentation/status/append-only history and Git diff checks passed. Detailed commands/results are in TASK_HISTORY. Python 3.12 was not separately exercised.

Known blockers: None.

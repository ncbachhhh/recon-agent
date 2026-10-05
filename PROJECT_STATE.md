# Project state

Project phase: Foundation / configuration

Completed:

- M0-T01 — Repository governance and planning scaffold (DONE)
- M0-T02 — Python project and developer tooling baseline (DONE)
- M0-T03 — Configuration foundation (DONE)

Active task: None

Next READY:

- M0-T04 — Core domain model foundation (not started)

## Implementation reality

The 92-task roadmap, governance, maintenance skill and design documentation exist. `recon-agent` 0.1.0 is installable through setuptools with the existing src layout and Python >=3.12 metadata. Pydantic is the sole direct runtime dependency; the development extra supplies Ruff, Mypy, Pytest, coverage and build. The CLI remains the unchanged inert status-printing placeholder.

`core/config/` implements strict Pydantic scope, execution (including budgets), planner, tools, persistence, logging and reporting contracts. Explicit loading uses defaults < one TOML file < RECON_AGENT_SECTION__FIELD environment < programmatic overrides. Unknown keys and invalid effective values fail. ProviderSecrets loads GROQ_API_KEY separately with redacted/excluded representation. Imports/loaders start no operational subsystems. The example TOML matches safe defaults; configuration docs and ADR 0001 describe actual behavior. There are 65 offline configuration cases plus the existing CLI unit test.

No domain models/ReconState, target scope enforcement, process runner, registry, scanner adapters, Groq client, AI planner, state engine, database persistence, audit logging or operational reporting exist. Preferences do not grant authorization or enforce budgets. M0-T04 is READY and has not begun; all later tasks remain NOT STARTED.

## Major architecture decisions

- Planner will select predefined capabilities, never arbitrary shell commands.
- Deterministic policy must validate actions with centralized fail-closed scope enforcement before contact, including redirects and discovered hosts.
- Remote/tool output and model responses remain untrusted evidence/recommendations.
- Provider abstraction will isolate Groq; SQLite remains planned behind interfaces.
- CLI-first, async-capable architecture; Pydantic now validates configuration and remains planned for domain boundaries.
- Explicit standard-library TOML/JSON sources without settings/YAML/dotenv dependencies; strict types, unknown-key rejection, disabled planner/tools/persistence defaults and separate excluded credentials (ADR 0001).
- Standard pip/venv/setuptools workflow; no dependency-manager lock-in or exact/transitive lockfile. Default Pytest selects unit tests and excludes external/network markers.

Product controls above remain planned unless explicitly described as configuration validation.

## Validation

Python 3.14.6 / Pydantic 2.13.5: editable install and pip check; focused 65-case configuration suite; Ruff lint/format; strict Mypy (15 source files); full 66-test suite; coverage (100%, 142 statements / 34 branches); sdist/wheel build; unchanged CLI smoke all passed. A fresh wheel installation outside the checkout passed import/loading/CLI/pip checks with runtime network/process/database/directory/logging activity blocked during configuration smoke. Installed dependency entry-point metadata reads were allowed during imports. Full tests also passed with socket network functions blocked. Archive/source/security, documentation/status and Git diff/whitespace checks passed; detailed evidence is in TASK_HISTORY. Python 3.12 was not separately exercised.

Known blockers: None.

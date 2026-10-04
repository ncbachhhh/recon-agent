# Project state

Project phase: Foundation / developer tooling

Completed:

- M0-T01 — Repository governance and planning scaffold (DONE)
- M0-T02 — Python project and developer tooling baseline (DONE)

Active task: None

Next READY:

- M0-T03 — Configuration foundation (not started)

## Implementation reality

The 92-task roadmap, governance, maintenance skill and design documentation exist. `recon-agent` 0.1.0 is installable through setuptools with the existing `src/recon_agent` layout and Python >=3.12 metadata. Runtime dependencies are empty. The development extra supplies Ruff, Mypy, Pytest, coverage and build; configuration lives in pyproject.toml. An inert console entry point prints foundation status and exits successfully. One offline unit test checks that placeholder. All other source boundaries remain docstring-only markers.

There is no configuration loader/model, domain model, scope validator, process runner, registry, scanner adapter, Groq client, planner, state engine, database or reporting implementation. M0-T03 has not begun; all tasks after it remain NOT STARTED.

## Major architecture decisions

- Planner selects predefined capabilities, never arbitrary shell commands.
- Deterministic policy validates actions with centralized fail-closed scope enforcement before contact, including redirects and discovered hosts.
- Remote/tool output and model responses remain untrusted evidence/recommendations.
- Provider abstraction will isolate Groq; SQLite remains planned behind interfaces.
- CLI-first, async-capable architecture with Pydantic planned for later domain/configuration boundaries.
- Offline deterministic tests use fixtures/fake providers/runners; default Pytest currently selects unit tests and excludes external/network markers.
- Standard pip/venv/setuptools workflow; no runtime libraries, CLI framework, license/author invention, dependency-manager lock-in, exact/transitive lockfile or new ADR needed for M0-T02.

Product controls above are planned constraints, not implemented safety engines.

## Validation

Editable install/import, Ruff lint/format, strict production Mypy, focused/default Pytest, coverage, sdist/wheel build and console smoke passed under Python 3.14.6. A fresh wheel installed offline with no dependencies outside the checkout and passed import/CLI smoke. Source/secret/ignore/artifact and marker/state checks passed; see TASK_HISTORY for detailed executed evidence and docs/testing-strategy.md for complete validation commands. Python 3.12 was not separately exercised in this run.

Known blockers: None.

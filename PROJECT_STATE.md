# Project state

Project phase: Foundation / governance

Completed:

- M0-T01 — Repository governance and planning scaffold (DONE)

Active task: None

Next READY:

- M0-T02 — Python project and developer tooling baseline

## Implementation reality

Governance, the 92-task roadmap across M0–M13, the repository maintenance skill, design documentation, and inert package/test directories exist. Python package: `recon_agent`; target Python: 3.12+. There is no pyproject/developer toolchain, runnable CLI, typed runtime model, configuration loader, policy validator, process runner, reconnaissance adapter, Groq client, orchestration loop, or database yet. All tasks after M0-T02 remain NOT STARTED; M0-T02 has not begun.

## Major architecture decisions

- AI planner selects predefined capabilities, never arbitrary shell commands.
- Deterministic policy validates every action before execution.
- Centralized fail-closed scope enforcement includes redirects and discovered hosts before contact.
- Tool/remote output and model responses are untrusted evidence/recommendations.
- Provider abstraction isolates Groq as the first planned reasoning provider.
- Tests default to offline and deterministic, with fake providers/runners and fixtures.
- SQLite is planned behind persistence interfaces; it is not implemented.
- CLI-first and async-capable architecture; Pydantic planned for typed domain/configuration boundaries.

These are bootstrap constraints/design intent, not claims of working controls. No decision ADR was needed; `docs/decisions/0000-template.md` is the only ADR file.

Known blockers: None.

## Validation boundary

M0-T01 uses direct required-file, roadmap, Markdown/link, skill, inert-source, credential and Git checks. See TASK_HISTORY for executed evidence. Lint/type/test/build/smoke commands will be established by M0-T02; they have not been run or claimed as passing in this bootstrap.

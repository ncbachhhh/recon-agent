---
name: recon-project-maintainer
description: Implement, review, resume, validate, and close tasks in recon-agent; reconcile PLAN, PROJECT_STATE, CURRENT_TASK, and TASK_HISTORY with repository evidence and record scoped follow-up work.
---

# Recon project maintainer

## When to use

Use when starting a PLAN task, resuming or implementing work, validating/closing a task, updating state, creating follow-up tasks, or investigating a documentation/code mismatch in `recon-agent`.

`AGENTS.md` is authoritative for operating rules and security invariants. This skill supplies workflow; it does not grant permission to commit, push, scan, or expand scope.

## Start a task

Follow the ordered repository startup sequence in `AGENTS.md`: read governance/state/roadmap and relevant docs/ADRs/history, then inspect Git and relevant code/tests. Confirm prerequisite tasks are DONE, blockers absent, and task scope/exclusions clear. Identify and preserve unrelated changes. Record exactly one task IN PROGRESS in PLAN/state and CURRENT_TASK before substantial implementation. Use [task workflow](references/task-workflow.md) for lifecycle/reconciliation details.

## Implement

Stay within scope. Prefer typed interfaces and preserve domain/policy/runner/adapter/provider boundaries. Write deterministic tests with implementation; use fixtures/fake runners/providers rather than live services. Update contract documentation and record consequential choices as ADRs when alternatives require a decision. Record newly discovered work as scoped follow-up or blocker.

## Validate

Use [validation workflow](references/validation-workflow.md). Focused validation checks changed behavior. Complete validation runs the repository-wide lint/type/test/build/smoke checks defined for the current phase in `docs/testing-strategy.md`. A focused pass alone cannot make a task DONE. Bootstrap uses direct scaffold/document validation until M0-T02 establishes tooling. Record only actually executed checks/results.

## Close a task

Verify each acceptance criterion, run full validation, and reconcile PLAN, PROJECT_STATE, CURRENT_TASK, and append-only TASK_HISTORY. Update CHANGELOG for user-visible changes and inspect the final diff. Create exactly one focused commit if authorized and safe; verify the clean/expected tree. Report task/status/files/checks/result/hash/blockers and next work. See [task workflow](references/task-workflow.md) for commit/history handling.

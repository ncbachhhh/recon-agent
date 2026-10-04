# Task lifecycle and repository reconciliation

## Start and resume

Read files in the exact order specified by root AGENTS; inspect both working-tree and staged diffs and recent log before edits. Repository evidence wins over old prompts. If state claims functionality unsupported by code/tests, investigate and explicitly reconcile before building on it.

Locate the full PLAN specification and list acceptance criteria. Verify every dependency is DONE with completion evidence, no other task is IN PROGRESS, and no blocking issue exists. Map allowed files/subsystems, exclusions, and protected/unrelated modifications. READY is permission to consider starting, not permission to expand scope or run external scans.

Set the selected task IN PROGRESS in PLAN; update PROJECT_STATE and replace CURRENT_TASK with that task's objective, scope, prerequisites, planned validation, progress, and blockers. Resume the same active task using actual diff/evidence rather than creating a second active task.

## During implementation

Keep scope tied to the task specification. Preserve unrelated user edits byte-for-byte; avoid formatting or staging them. Maintain typed interfaces and architecture boundaries. Add offline tests alongside changed behavior and document changed contracts/operator behavior. Use an ADR for a consequential unresolved choice with alternatives, not routine implementation details.

If a new requirement appears, append a future task with all PLAN fields/dependencies, or record a blocker with evidence. Do not silently widen the task or relax acceptance. A genuinely missing prerequisite makes the task BLOCKED; record which prerequisite is absent and what resolves it in PLAN, PROJECT_STATE, and CURRENT_TASK. Do not fabricate DONE evidence.

## Close and reconcile

1. Map each acceptance criterion to actual evidence and run focused plus complete phase-appropriate validation.
2. Set the completed task DONE in PLAN only after acceptance passes. Review readiness of immediate dependents; do not start them automatically. For M0-T01 closure only M0-T02 becomes READY; later tasks stay NOT STARTED pending their prerequisite gates.
3. Update PROJECT_STATE with actual phase, completed task, next READY task, implementation limits, and blockers.
4. Replace CURRENT_TASK with “No active task” and short next-task context. Completed history belongs elsewhere.
5. Append TASK_HISTORY with date, ID/title, objective, changes, decisions, checks/results, outcome, and commit handling. Never revise historical entries; append corrections separately.
6. Update CHANGELOG if user-visible/infrastructure behavior changed and ensure subsystem docs are current.
7. Inspect the final diff, including all state/docs changes, and stage only task-owned changes. Verify expected staged paths.
8. If committing is authorized and safe, create exactly one focused commit. Never amend/rewrite/push unless explicitly requested. If isolation is impossible, leave changes reviewable and document why no commit was made.
9. Verify the post-commit tree and report actual hash, validation results, blockers, and next task. Stop at the authorized task boundary.

## Commit references in history

Do not invent a hash. The task entry can say “the focused commit containing this entry; resolve via `git log --format=%H -- TASK_HISTORY.md`” before committing and report the actual hash afterward. A commit cannot contain its own hash without changing that hash; do not create a second task commit or amend solely to embed it. A later authorized append may record a known prior hash if needed.

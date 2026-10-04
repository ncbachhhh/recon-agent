# Validation and evidence

## Focused validation

Select tests/checks for the behavior actually changed, including error paths and security boundaries. For policy/adapter/planner changes, assert a rejected action never dispatches, not merely that an error string appears. Use deterministic fixtures and injected fakes; no credentials, public targets, or installed reconnaissance tools in unit tests.

For documentation/scaffolding, inspect required paths, links, statuses, schemas/examples, and inert source rather than adding ceremonial implementation tests.

## Complete validation

Read `docs/testing-strategy.md` for the current baseline. After M0-T02, run the exact documented repository lint/format, type, offline test/coverage, build, and smoke commands. Respect explicit integration gates; no silent external scans. A focused pass cannot replace complete validation. If a required check cannot run, record the command/failure and blocker; do not claim it passed or weaken acceptance.

M0-T01 has no developer toolchain yet. Complete bootstrap checks verify required files/directories; skill frontmatter/references; Markdown headings/fences/local links; full unique task specifications; valid acyclic dependencies; DONE/READY/pending statuses; no active task at closure; package markers only; no secrets; expected Git changes and whitespace. Use temporary checks/direct inspection; no permanent framework is needed.

## Completion evidence

Record checks actually executed and their results, separately from planned tests. Inspect final working-tree and staged diffs, verify each acceptance criterion, and reconcile documentation/state/history. Never label a missing or unrun check successful. Confirm staged changes are task-owned and the final tree is clean or matches explicitly described unrelated work. Report limitations precisely; compilation or Markdown checks are not evidence of implemented reconnaissance behavior.

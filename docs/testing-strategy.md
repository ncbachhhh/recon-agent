# Testing strategy

## Default execution boundary

Tests default to deterministic offline execution with no Groq key, Internet, external reconnaissance binaries, or live targets. No automated test silently scans public Internet targets. Use sanitized fixtures, fakes, reserved names such as `example.test`, and loopback/local lab targets only when explicitly authorized. Reserved names are test data, not permission to make DNS/network requests.

## Testing pyramid

1. **Unit tests:** parsers, Pydantic models, configuration/error handling, centralized scope policy, state transitions, action validation, deduplication, argv construction, budgets, and planner schema handling. These constitute most tests.
2. **Fixture-based adapter tests:** stored sanitized sample outputs exercise parse/normalization, provenance, partial/malformed/truncated output, and version variations. No real binary is needed.
3. **Provider tests:** deterministic fake Groq/provider responses test schemas, retries, malformed output, policy rejection, and prompt injection without API calls or credentials.
4. **Execution tests:** injected fake subprocess/process runners model return codes, missing binary, timeout, cancellation/cleanup, large output, and concurrency. Any future real-process runner test must be isolated and explicitly marked; normal unit tests use fakes.
5. **Offline orchestration/storage integration:** fake tools/providers plus local temporary SQLite prove session cycles, stop conditions, traceability, and resume. Mark separately from network/binary integration.
6. **Opt-in external/lab integration:** explicitly marked tests requiring binaries or network targets; selected only through a deliberate command/configuration gate and explicit authorized scope. They are excluded from normal tests and CI by default.

## Markers and fixture governance

M0-T02 will define Pytest markers and default selection, distinguishing offline integration from external binary/network tests. Fixtures never include API keys, real credentials, unsanitized private target data, or content capable of changing test policy. Record format/version/source context. Fake runners must assert no prohibited dispatch occurred, not just that a rejection message exists.

## Validation layers

**Focused validation** covers directly changed behavior, including adversarial/error cases. **Complete validation** covers the repository-wide baseline for the current phase. A task cannot become DONE solely because focused checks pass.

### M0-T01 bootstrap baseline

Direct inspection/temporary checks must verify all required files and package/test directories; coherent Markdown headings/fences and local links; valid skill frontmatter and referenced procedures; unique PLAN task IDs; valid acyclic dependencies; full task fields; exactly M0-T01 DONE, M0-T02 READY, all other tasks NOT STARTED at closure; no active task; source contains only inert markers; no secrets; and only expected bootstrap Git changes. Inspect the final diff and verify acceptance criteria individually. No permanent validator infrastructure is required for this phase.

There is no pyproject, lint/type/test/build setup yet. Do not claim those checks pass or run live tools to validate documentation.

### Baseline established by M0-T02

M0-T02 must document exact reproducible commands here for Ruff lint/format checks, Mypy, default offline Pytest with coverage configuration, package build, and non-network CLI smoke check. Require clean lint/type/test/build/smoke results. Define an honest minimal inert test/smoke baseline then; do not hide an empty test suite as a pass. Package/developer dependency installation may require provisioning, but provisioned tests must run offline and without credentials.

### Later task closeout

Run focused checks, then all documented complete baseline commands, inspect diff, update task/state/history/docs, and recheck acceptance and final diff. Report commands and actual results; disclose unavailable checks as blockers where required. Broaden checks only for material new changes/failures. Integration tasks remain explicit opt-in and require fixture/fake alternatives for default tests.

## CI intent

Eventually CI runs lint, types, unit tests, offline integration, and build without Groq credentials or reconnaissance binaries. Controlled lab MVP testing is a separate explicitly authorized activity, never a default CI step.

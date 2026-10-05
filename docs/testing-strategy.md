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

Pytest defaults to `tests/unit` and excludes `external` and `network` markers. Registered markers are `integration` (offline fixtures/fakes), `external` (external binaries/lab requirements), and `network` (network/live targets/provider APIs). Integration tests require an explicit path; external/network tests additionally require an explicit marker selection and authorized environment. Marker filtering is a selection gate, not a network sandbox. Future test modules must have no external activity at import/collection time. No integration tests exist yet. Fixtures never include API keys, real credentials, unsanitized private target data, or content capable of changing test policy. Record format/version/source context. Fake runners must assert no prohibited dispatch occurred, not just that a rejection message exists.

## Validation layers

**Focused validation** covers directly changed behavior, including adversarial/error cases. **Complete validation** covers the repository-wide baseline for the current phase. A task cannot become DONE solely because focused checks pass.

### M0-T01 bootstrap baseline

Direct inspection/temporary checks must verify all required files and package/test directories; coherent Markdown headings/fences and local links; valid skill frontmatter and referenced procedures; unique PLAN task IDs; valid acyclic dependencies; full task fields; exactly M0-T01 DONE, M0-T02 READY, all other tasks NOT STARTED at closure; no active task; source contains only inert markers; no secrets; and only expected bootstrap Git changes. Inspect the final diff and verify acceptance criteria individually. No permanent validator infrastructure is required for this phase.

At M0-T01 closure there was no pyproject or lint/type/test/build setup. Its recorded evidence is scaffold/document inspection, not product validation.

### Baseline established by M0-T02

Use a Python >=3.12 interpreter from the repository root. Setup and editable import/entry-point smoke:

```bash
python --version
python -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/python -c "import recon_agent; print(recon_agent)"
.venv/bin/recon-agent
```

Focused validation for the placeholder:

```bash
.venv/bin/python -m pytest tests/unit/test_cli.py
```

Complete validation required before closing later tasks:

```bash
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check .
.venv/bin/python -m mypy src/recon_agent
.venv/bin/python -m pytest
.venv/bin/python -m coverage run -m pytest
.venv/bin/python -m coverage report
.venv/bin/python -m build
.venv/bin/recon-agent
```

Require all commands to pass. Ruff targets Python 3.12 and includes correctness, import sorting, modernization and bugbear rules; formatter settings are in pyproject. Mypy applies strict checks to `src/recon_agent` without broad suppression. Tests remain linted, while production is the default type-check scope. One unit test imports the installed package's entry-point function and checks its status/message/stderr. No `pythonpath` workaround masks a broken install. The installed console command is separately smoke-tested.

Coverage uses package source `recon_agent`, branch measurement and missing-line reporting; tests are not production coverage. Empty package markers are omitted from the displayed report, not from source measurement. No minimum percentage gate is imposed during foundation work. M0-T03 adds offline configuration tests; focused validation is `.venv/bin/python -m pytest tests/unit/test_config.py`. M0-T04 adds deterministic domain construction/validation/serialization tests; focused validation is `.venv/bin/python -m pytest tests/unit/test_domain.py`. M0-T05 adds error/result hierarchy, diagnostic safety, generic typing and boundary integration tests; focused validation is `.venv/bin/python -m pytest tests/unit/test_errors.py tests/unit/test_results.py`, plus config/domain regression suites. `.venv/bin/python -m mypy src/recon_agent tests/unit/test_results.py` additionally proves generic payload narrowing. M0-T06 focused validation is `.venv/bin/python -m pytest tests/unit/test_logging_audit.py`: fixed aware timestamps, captured streams, JSON parsing, redaction/evidence-preservation, idempotent project setup, error/failure and import guards. Logger state is isolated/restored; no remote telemetry tests or future producers are introduced. A current 100% result does not imply future reconnaissance coverage.

Build uses standard setuptools and emits both sdist and wheel. Inspect archive contents/metadata and ensure artifacts are ignored. When packaging/entry-point behavior changes, install the built wheel into a fresh environment outside the checkout and repeat import/console smoke to detect editable-install masking.

Initial validation environment: Python 3.14.6, Ruff 0.16.10, Mypy 2.4.0, Pytest 9.1.1, coverage 7.16.2, build 1.6.1, isolated setuptools 84.0.0. Python >=3.12 is the declared compatibility target; this run did not execute under Python 3.12. Compatible dependency ranges are defined in pyproject, with no exact/transitive lock or bit-for-bit reproducibility claim. Standard environment creation and installation are reproducible procedures; resolved versions may vary.

Installation/build isolation can provision dependencies from a package index; afterward default tests need neither connectivity nor credentials. M0-T02 also verified its unit test with Groq key absent and socket connection/DNS functions blocked, and verified marker filtering using temporary non-network fixtures. These checks do not implement a future production scope engine or scanner.

### Later task closeout

Run focused checks, then all documented complete baseline commands, inspect diff, update task/state/history/docs, and recheck acceptance and final diff. Report commands and actual results; disclose unavailable checks as blockers where required. Broaden checks only for material new changes/failures. Integration tasks remain explicit opt-in and require fixture/fake alternatives for default tests.

## CI intent

Eventually CI runs lint, types, unit tests, offline integration, and build without Groq credentials or reconnaissance binaries. Controlled lab MVP testing is a separate explicitly authorized activity, never a default CI step.

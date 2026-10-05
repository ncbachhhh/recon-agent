# Testing strategy

## Default execution boundary

Tests default to deterministic offline execution with no Groq key, Internet, external reconnaissance binaries, or live targets. No automated test silently scans public Internet targets. Use sanitized fixtures, fakes, reserved names such as `example.test`, and loopback/local lab targets only when explicitly authorized. Reserved names are test data, not permission to make DNS/network requests.

## Testing pyramid

1. **Unit tests:** parsers, Pydantic models, configuration/error handling, centralized scope policy, state transitions, action validation, deduplication, argv construction, budgets, and planner schema handling. These constitute most tests.
2. **Fixture-based adapter tests:** stored sanitized sample outputs exercise parse/normalization, provenance, partial/malformed/truncated output, and version variations. No real binary is needed.
3. **Provider tests:** deterministic fake Groq/provider responses test schemas, retries, malformed output, policy rejection, and prompt injection without API calls or credentials.
4. **Execution tests:** injected fake subprocess/process runners model return codes, missing binary, timeout, cancellation/cleanup, large output, and concurrency. Fake tests remain the default execution logic checks. M1-T03 also includes an isolated `local_process`-marked module using only harmless local `sys.executable` children; these offline checks are included in the default suite.
5. **Offline orchestration/storage integration:** fake tools/providers plus local temporary SQLite prove session cycles, stop conditions, traceability, and resume. Mark separately from network/binary integration.
6. **Opt-in external/lab integration:** explicitly marked tests requiring binaries or network targets; selected only through a deliberate command/configuration gate and explicit authorized scope. They are excluded from normal tests and CI by default.

## Markers and fixture governance

Pytest defaults to `tests/unit` and excludes `external` and `network` markers. Registered markers are `local_process` (harmless local interpreter only), `integration` (offline fixtures/fakes), `external` (external binaries/lab requirements), and `network` (network/live targets/provider APIs). Integration tests require an explicit path; external/network tests additionally require an explicit marker selection and authorized environment. Marker filtering is a selection gate, not a network sandbox. Future test modules must have no external activity at import/collection time. No integration tests exist yet. Fixtures never include API keys, real credentials, unsanitized private target data, or content capable of changing test policy. Record format/version/source context. Fake runners must assert no prohibited dispatch occurred, not just that a rejection message exists.

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

Coverage uses package source `recon_agent`, branch measurement and missing-line reporting; tests are not production coverage. Empty package markers are omitted from the displayed report, not from source measurement. No minimum percentage gate is imposed during foundation work. M0-T03 adds offline configuration tests; focused validation is `.venv/bin/python -m pytest tests/unit/test_config.py`. M0-T04 adds deterministic domain construction/validation/serialization tests; focused validation is `.venv/bin/python -m pytest tests/unit/test_domain.py`. M0-T05 adds error/result hierarchy, diagnostic safety, generic typing and boundary integration tests; focused validation is `.venv/bin/python -m pytest tests/unit/test_errors.py tests/unit/test_results.py`, plus config/domain regression suites. `.venv/bin/python -m mypy src/recon_agent tests/unit/test_results.py` additionally proves generic payload narrowing. M0-T06 focused validation is `.venv/bin/python -m pytest tests/unit/test_logging_audit.py`: fixed aware timestamps, captured streams, JSON parsing, redaction/evidence-preservation, idempotent project setup, error/failure and import guards. Logger state is isolated/restored; no remote telemetry tests or future producers are introduced. M1-T01 focused validation is `.venv/bin/python -m pytest tests/unit -k scope`,
covering declaration membership, normalization, exclusions, IP/CIDR boundaries,
URL authority, private gating, redirect candidates, structured failures and purity.
M1-T02 adds the dedicated corpus under `tests/unit/policy`; run it with
`.venv/bin/python -m pytest tests/unit/policy`.
A current coverage result does not imply future reconnaissance coverage.

Build uses standard setuptools and emits both sdist and wheel. Inspect archive contents/metadata and ensure artifacts are ignored. When packaging/entry-point behavior changes, install the built wheel into a fresh environment outside the checkout and repeat import/console smoke to detect editable-install masking.

Initial validation environment: Python 3.14.6, Ruff 0.16.10, Mypy 2.4.0, Pytest 9.1.1, coverage 7.16.2, build 1.6.1, isolated setuptools 84.0.0. Python >=3.12 is the declared compatibility target; this run did not execute under Python 3.12. Compatible dependency ranges are defined in pyproject, with no exact/transitive lock or bit-for-bit reproducibility claim. Standard environment creation and installation are reproducible procedures; resolved versions may vary.

Installation/build isolation can provision dependencies from a package index; afterward default tests need neither connectivity nor credentials. M0-T02 also verified its unit test with Groq key absent and socket connection/DNS functions blocked, and verified marker filtering using temporary non-network fixtures. These checks do not implement a future production scope engine or scanner.

### Later task closeout

Run focused checks, then all documented complete baseline commands, inspect diff, update task/state/history/docs, and recheck acceptance and final diff. Report commands and actual results; disclose unavailable checks as blockers where required. Broaden checks only for material new changes/failures. Integration tasks remain explicit opt-in and require fixture/fake alternatives for default tests.

## Authorization regression corpus

The M1-T02 corpus uses independently specified outcomes from the scope contract
and ADR 0002. Two modules cover names/URLs/derived candidates and addresses/rules/
structured decisions. Parameterized adversarial inputs include suffix lookalikes,
unsupported encodings, userinfo, malformed authorities, alternate IP forms, CIDR
boundaries, private gates and exclusions. Invalid declarations are tested alongside
valid rules so a partially compiled permissive policy cannot go unnoticed.

Small deterministic generated checks exhaust name prefixes and IPv4 documentation
range members, sample IPv6 boundaries, and permute overlapping/duplicate rules.
CIDR expectations come from mathematical `ipaddress` membership; declaration order
must preserve complete outcomes, including match reporting. These checks need no
Hypothesis dependency or random seed. Regression tests also verify serialized
outcomes, canonical scope reason codes and parity with ScopeRejectedError.

An autouse fixture blocks socket construction and DNS/connection helpers throughout
the dedicated corpus. Closeout additionally runs the complete suite with socket
contact and DNS functions blocked and the Groq key absent. Test-only mock contact
consumers call `require_allowed` before recording a redirect/discovered candidate;
rejection must leave the mock untouched. This proves boundary usage locally, without
adding a production dispatcher or claiming future adapters enforce it already.

## CI intent

Eventually CI runs lint, types, unit tests, offline integration, and build without Groq credentials or reconnaissance binaries. Controlled lab MVP testing is a separate explicitly authorized activity, never a default CI step.

## Execution runner regressions (M1-T03)

Run `.venv/bin/python -m pytest tests/unit/execution` first. test_runner.py injects
fake process handles for deterministic argv/API, return-code, per-stream bounds,
spawn/capture failures, timeout, kill escalation, spawn/exit/cancellation races and
repeated cancellation cleanup. test_local_process.py is explicitly marked
`local_process`, runs only `sys.executable` in non-interactive isolated mode, requires
no scanners, shell utilities, credentials or network, and uses tmp_path for artifacts.
Select fakes alone with `-m 'not local_process'`, or local children with
`-m local_process`. No new third-party async test dependency is required.

Local cases prove literal shell metacharacters/substitutions/wildcards/quotes and no
sentinel side effects, empty/multiline/Unicode/invalid byte streams, non-zero exits,
missing executable, stdin EOF, large alternating stdout/stderr without deadlock,
bounded retention/truncation, timeout and cancellation direct-child cleanup/reaping.
POSIX adds waitpid evidence that the child has already been reaped. Full suite runs
with parent socket contact/DNS functions blocked and Groq key absent; child scripts
are reviewed to contain no network activity. This guard does not sandbox arbitrary
child programs. No descendant-tree termination claim is made. Fresh-wheel guarded
cold imports verify that importing execution does not launch processes or configure
logging; installed-wheel local execution and inert CLI are checked separately.

## Capability registry regressions (M1-T04)

Run `.venv/bin/python -m pytest tests/unit/tools` first, then existing domain tests
and the full baseline. Test-only FakeAdapter/DnsInput/DnsOutput classes perform no
reconnaissance or execution. Autouse guards block DNS/socket construction, subprocess
entry points and AsyncProcessRunner.run; import/lookup guards also prohibit dynamic
imports, filesystem scanning/writes and logging startup. No real binary is probed.

Cases cover explicit composition, strict input/output model references, finite known
identities versus registration/availability, canonical unknown/unavailable outcomes,
duplicate IDs/conflicting mappings/malformed definitions, stable lexical enumeration,
immutable mappings/returned collections/snapshots, ActionRequest compatibility and
nested executable/import-key rejection. Planner-safe catalog tests deliberately put
private paths/argv/environment/runner values on fake adapters and prove no leakage.
Unexpected execution/import/runtime fields in descriptors are rejected. Full-suite
contact/DNS blocking and fresh-wheel cold import/composition checks remain required.

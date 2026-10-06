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

## Action policy regressions (M1-T05)

Run `.venv/bin/python -m pytest tests/unit/policy/test_action_policy.py`, followed
by registry/scope regressions and the full baseline. Fixtures use only trusted fake
schemas/adapters and permitting/denying eligibility services; no scanner models or
production completed-action permitting stub exists; M1-T08 supplies real dedup
eligibility. M1-T06 supplies real budget checks. Guards block socket/DNS/subprocess/runner,
registry adapter resolution, dynamic imports and logging. Tests cover canonical
approvals, malformed/unknown/unavailable/disallowed intent, strict/extra/executable
parameters, every declared secondary target/default, missing target semantics,
unsupported target representations, missing eligibility and malformed outcomes.
Planner metadata cannot change denials. Test-only dispatch rechecks stale approval
and remains untouched on rejection. Full contact/DNS-blocked suite and guarded
fresh-wheel imports/policy checks are required. No production dispatch or
concrete-address contact guarantee is claimed; M1-T08 separately tests deduplication.
M1-T06 separately supplies resource reservations.

## Budget regressions (M1-T06)

Run `.venv/bin/python -m pytest tests/unit/test_budgets.py` plus configuration/action
policy regressions, then the full baseline and contact/DNS-blocked suite. Injected
clock values advance without sleep. Offline simultaneous contenders test each
reservation dimension under a shared ledger, without scanner tasks or a worker pool.
Real asyncio cancellation is exercised only against Event-based fake owned work;
no runner/adapter is invoked. Runtime guards forbid subprocess/network/DNS/runner,
registry adapter resolution, dynamic loading and logging startup where relevant.

Cases cover initial/read-only state, exact action/rate/time/output boundaries,
no underflow/partial consumption, independent sessions/capabilities/hosts,
canonical DNS/URL/IP/IPv6 representations, secondary/default targets and duplicate
host accounting, fail-closed CIDRs/unknown/malformed inputs, bad/regressing clocks,
failure/retry/cancellation/timeout charges and idempotent/non-nested permit ownership.
Configuration tests cover strict invalid/new fields, loading/snapshots and planner
metadata/field isolation. Fresh-wheel guarded imports/composition/reservations,
artifact/secret/source inspection and inert CLI remain required. No claims about
running-work cancellation or future internal scanner traffic follow from these tests.


## Controlled state regressions (M1-T07)

Run `.venv/bin/python -m pytest tests/unit/test_state.py tests/unit/test_domain.py tests/unit/test_errors.py tests/unit/test_budgets.py`, then all required
full baseline/contact-DNS-blocked/build/wheel checks.
Tests use caller-supplied UTC times, fake records and local synchronous contenders;
no scanner/provider/runner work occurs. Guards prohibit socket/DNS/subprocess/runner,
registry execution resolution, dynamic imports and logging startup. Fresh-wheel
cold imports and state transitions also run with runtime startup/contact prohibited.

The 81-edge lifecycle matrix covers allowed paths, every invalid edge and terminal
re-entry with byte-identical rollback. Additional cases cover malformed/revalidated
initial snapshots, exact history metadata and result/ID/time/execution correlation,
atomic fact batches/failed-result preservation, missing/conflicting provenance,
known unsuccessful execution observation denial, subject ownership, planner lineage
without authorization, nested input/output alias isolation, simultaneous commits,
nonempty budget bucket Python/JSON round trips and no enforcement duplication.
Original domain fixtures now use strict tuple collections and explicit coherent
lifecycle history; permissive list mutation is deliberately rejected. Default budget
and execution regressions remain required. M1-T08 tests semantic dedup separately;
no session loop is tested.

## Action deduplication regressions (M1-T08)

Run `.venv/bin/python -m pytest tests/unit/policy/test_dedup.py tests/unit/policy/test_action_policy.py tests/unit/test_state.py -q`, then the complete baseline,
contact/DNS-blocked suite, fresh-wheel cold imports/composition and artifact checks.
Fixtures use only trusted strict schemas, local histories and explicit UTC times.
Runtime guards forbid DNS/sockets/subprocess/runner/adapter resolution/dynamic import/
logging. Simultaneous local contenders test shared-state atomic new/retry admission
without scanning or an orchestration loop.

Cases cover cosmetic planner repetition, key order, nested JSON types, defaults,
serialization exclusions, meaningful changes, existing target aliases, preserved URL
semantics, every lifecycle, zero/configured retry limits, retryability flags,
reconstructed-history bounds, terminal-ID replay, malformed history fail-closed,
lookup/input alias isolation, validated callback detachment/rollback, and real policy/
budget composition with no authorization/resource/execution effects from dedup.

## Native DNS regressions (M2-T01)

Run `.venv/bin/python -m pytest tests/unit/tools/test_dns.py tests/unit/tools/test_registry.py -q`
first, then the complete baseline, network/DNS-blocked suite, fresh-wheel checks and
artifact/secret review. Sanitized tests/fixtures/dns/answers.json contains DNS
presentation RDATA, including non-UTF-8/multipart/instruction-like TXT data. Injected
fake messages and mocked native UDP exercise six record types, multiple/negative/alias
answers, provenance, normalization order, malformed envelopes/rcode failures, strict
input and authorized infrastructure, no follow-up authority, shared resolver host
budgets, aggregate record/output bounds, cancellation/session/whole-action deadlines
and existing state/dedup composition. Socket contact/DNS/subprocess guards assert no
real activity. No local DNS server/live integration is needed. Fresh-wheel imports
and composition include native DNS under guarded contact/process/startup checks.

## Subfinder regressions (M2-T02)

Run `.venv/bin/python -m pytest tests/unit/tools/test_subfinder.py tests/unit/tools/test_registry.py tests/unit/execution -q`
first, then the full baseline, network/DNS-blocked suite, fresh-wheel cold imports/
fake composition, artifacts/secrets and final whitespace review. Sanitized JSONL
fixture records Subfinder 2.9.0 -json -cs host/input/sources format for HackerTarget.
Availability/PATH/version probes and enumeration use injected fake ProcessRunner
outputs under socket/DNS/process guards; default tests never detect/run Subfinder.
Tests assert exact argv, isolated environment/config paths, denied roots/extra fields
with no dispatch, sorted duplicates/single/empty results, canonical/malformed/outside
records, safe provenance, unchanged scope/no follow-up, structured missing/nonzero/
timeout/truncation errors, resources, session expiry and cancellation/temp cleanup.
Runner regressions validate the bounded environment contract and use only a harmless
local interpreter child to prove ambient secrets/config variables are excluded and
shell syntax remains literal. No live-binary or provider tests are added. Fresh-wheel
checks include explicit Subfinder registration and real policy/budget/dedup with fake
execution; imports remain inert. resolve_dns regressions remain unchanged; DNSX
verification is implemented separately in M2-T03.

## DNSX regressions (M2-T03)

Run `.venv/bin/python -m pytest tests/unit/tools/test_dnsx.py tests/unit/tools/test_registry.py tests/unit/tools/test_dns.py tests/unit/tools/test_subfinder.py -q`, then the complete
baseline, network/DNS-blocked suite, coverage/build/fresh-wheel/inert CLI and artifact/
secret/diff checks. Sanitized source-shaped JSONL/RR fixtures and fake runners require
no DNSX/network. Cases cover exact argv/environment/input, single/multiple/duplicate
canonical candidates, whole-batch pre-input rejection, independent resolver scope,
six record types/TTL/owners/MX/TXT/provenance, wildcard/section ambiguity, malformed/
partial/empty/conflicting output, availability/version/nonzero/timeout/cancellation
and shared resource/output/session limits. Guards block network/process contact;
fresh-wheel guarded imports and fake DNSX composition verify installed packaging.
Compatibility is reviewed DNSX 1.2.2 source/fixtures, not a live-binary test. Existing
native DNS/Subfinder behavior is protected; no later adapter tests imply implementation.

## HTTPX regressions (M2-T04)

Run `.venv/bin/python -m pytest tests/unit/tools/test_httpx.py tests/unit/tools/test_registry.py tests/unit/tools/test_dns.py tests/unit/tools/test_subfinder.py tests/unit/tools/test_dnsx.py -q`,
then the full baseline, network/DNS-blocked suite, coverage/build/fresh-wheel/inert CLI
and artifact/secret/diff checks. Reserved source-shaped JSONL fixtures and guarded
fake runners require no HTTPX/network. Tests assert exact fixed argv/environment,
authorized host/IP/URL forms, independent contact/resolver scope, mixed rejection
before temporary input, no-follow redirects/no derived authority, optional metadata,
technology/provenance, duplicate/conflict order, malformed/partial/empty output,
availability/version/nonzero/timeout/cancellation and resource/output/session bounds.
Guarded fresh-wheel imports/composition exercise installed HTTPX code with fakes.
Compatibility is reviewed HTTPX 1.9.0 source/fixtures, with no live binary test.

## Naabu regressions (M2-T05)

Run `.venv/bin/python -m pytest tests/unit/tools/test_naabu.py tests/unit/tools/test_registry.py tests/unit/tools/test_dns.py tests/unit/tools/test_subfinder.py tests/unit/tools/test_dnsx.py tests/unit/tools/test_httpx.py -q`,
then the full baseline, network/DNS-blocked suite, coverage/build/fresh-wheel/inert CLI
and artifact/secret/diff checks. Reserved source-shaped Naabu 2.3.5 JSONL and guarded
fake runners need no real binary/network. Cases cover exact argv/numeric-only input,
operator finite-range boundaries/overlap/limits, authorized name/IP, mixed/unsupported/
contact/excluded denials before input, strict planner flag rejection, open generic
Host/Service/Observation/Evidence/state lineage, deterministic duplicates/hash, malformed/
partial/empty records, availability/missing/nonzero/timeout/cancellation and existing
rate/host/action/concurrency/output/session bounds. Installed-wheel cold imports and
real registry/policy/budget/dedup with fake execution stay under startup/contact guards.
Compatibility is source/fixture review only; no live Naabu or Nmap runs.

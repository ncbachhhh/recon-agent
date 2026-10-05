# Task history

Append-only project history. Add completed task entries and later corrections at the end; never rewrite earlier completed entries.

## 2026-10-05 — M0-T01 — Repository governance and planning scaffold

Status: DONE

Objective: Establish disciplined repository truth, task lifecycle, security boundaries, design documentation and the complete implementation roadmap without production reconnaissance functionality.

### Changes and decisions

Created seven root governance/readme/state/history/changelog files; PLAN contains all 92 specified tasks across M0–M13 with complete fields. Created seven subsystem design documents plus ADR template; the project maintenance skill plus two workflow references; eleven docstring-only Python package markers; and three empty tracked test-directory placeholders. The initial directory was empty, Git was absent, and no user changes existed to preserve. Initialized Git.

Decisions: capabilities rather than LLM shell commands; centralized deterministic policy/scope checks before contact; controlled argv adapters with limits; untrusted remote/model data; Groq isolated by provider abstraction; offline fakes/fixtures by default; SQLite planned, not implemented. Tool-internal redirects/crawls/derived destinations must be constrained before contact, not merely filtered after collection. No extra ADR or production code was needed.

### Validation performed

- Executed temporary direct-inspection validator (`python /tmp/recon_validate_bootstrap.py`): exact 32-file scaffold inventory; all 92 required unique IDs and 15 task fields; valid acyclic dependencies; pre-close phase statuses; Markdown heading/list/fence structure and 20 local links across 18 Markdown files; conceptual JSON examples parsed; eleven Python files verified by AST as docstring-only; empty test placeholders; credential-pattern inspection; ordered AGENTS startup and core governance checks. Passed.
- Executed skill-creator validator (`python /home/ncbachhhh/.codex/skills/.system/skill-creator/scripts/quick_validate.py .codex/skills/recon-project-maintainer`): “Skill is valid!” Passed.
- Inspected generated task specifications and design/governance documents against the requested layers, model entities, contracts, non-goals, trust hierarchy, injection examples, roadmap scope and acceptance requirements. No real credentials or production scanner/provider code was supplied.
- Git startup inspection established no existing repository/history/diff; only expected bootstrap paths were subsequently present. Closure-state and final staged diff/whitespace/tree checks are mandatory final gates; their actual execution result accompanies this task's final handoff/containing commit.

These are scaffold/document checks. No Ruff/Mypy/Pytest/build/product smoke was executed: that tooling is M0-T02. No Internet, live target, reconnaissance binary or Groq call was used. Temporary validators/generators remain outside the repository and are not project infrastructure.

### Acceptance and handoff

Required files/layout, concise authoritative AGENTS, valid skill/references, architecture/security/contracts/config/testing/ADR documentation, complete roadmap, inert source, no credentials/unrelated work, and idle closure are represented in repository evidence. PLAN closes only M0-T01; M0-T02 is READY; every later task remains NOT STARTED. CURRENT_TASK says no active task. Known blockers: none. Follow-up: M0-T02 only; do not start it in this run.

Commit reference: the single focused bootstrap commit containing this entry, resolvable after creation with `git log --format=%H -- TASK_HISTORY.md`. No hash was available when writing this entry; the final handoff reports the actual hash. No amend, second task commit, or push is part of this bootstrap.

### Final gate evidence — 2026-10-05

Executed `python /tmp/recon_validate_bootstrap.py --closed`: all scaffold, complete task-specification/dependency/status, Markdown/link/JSON, inert-source, credential-pattern, ordered startup and closure-state/history checks passed. Re-executed the skill validator successfully. Inspected the staged governance/skill/state/history/source/test diff and the full file statistics. A temporary Git index check verified exactly 32 expected additions, no deletions/unrelated changes, staged bytes matching inspected files, and no unstaged edits. The initial whitespace check identified one extra blank line at PLAN EOF; removed it and re-executed `git diff --cached --check` successfully.

M0-T01 acceptance mapping:

| Criterion | Evidence/result |
| --- | --- |
| Required files/directories | Exact 32-file inventory passed; test directories retained with empty .gitkeep files |
| AGENTS operating/security rules | Ordered startup check and individual requirements/document inspection passed; 73-line authoritative file |
| Valid skill and references | Skill-creator validator passed; both referenced procedures exist and local links resolve |
| Required documentation coverage | Architecture layers, security trust boundaries/injection/fail-closed rules, tool/planner/data/testing/configuration contracts and ADR template inspected |
| Full roadmap | All 92 requested IDs present with 15 fields; no duplicates, missing/invalid dependencies or cycles |
| Required task statuses | M0-T01 DONE; M0-T02 READY; remaining 90 tasks NOT STARTED |
| Inert source only | AST inspection confirms eleven docstring-only modules and no production execution code |
| No credentials/unrelated work | Text/credential-pattern inspection and exact staged addition set passed; original directory was empty |
| Idle closure | PROJECT_STATE active None; CURRENT_TASK explicitly says no active task; history/changelog reconciled |
| Single focused commit/no push | Authorized initial commit is the one containing this entry; actual hash and post-commit clean tree verified in final handoff; no push action performed |


## 2026-10-05 — M0-T02 — Python project and developer tooling baseline

Status: DONE

Objective: Establish a standard installable Python >=3.12 package and trustworthy developer validation without reconnaissance functionality.

Changes: Created pyproject.toml, .gitignore, src/recon_agent/cli/main.py and tests/unit/test_cli.py. Updated README, architecture/testing docs, CHANGELOG and task/state files. Existing package markers and M0-T01 history are preserved. Startup verified a clean tree/index, no active task, M0-T01 DONE at `cbb978c24f148372229a1c956bcdd1cafc180248`, M0-T02 READY, and all later tasks NOT STARTED before recording M0-T02 IN PROGRESS.

Decisions: setuptools build backend; initial version 0.1.0; zero runtime dependencies; five developer tools with compatible ranges and no transitive/exact pins or dependency-manager requirement; no invented license/author metadata; Ruff lint/import sorting/format; strict production-only Mypy; standalone package/branch coverage without an artificial minimum; unit-only default collection plus strict external/network markers. No CLI framework, version API or ADR was needed. Full resolved tool versions are in testing strategy; validation used Python 3.14.6, not a separate Python 3.12 run.

### Executed validation

Commands use the repository root and local .venv:

| Check | Actual command/result |
| --- | --- |
| Environment | `python --version`, `python -m venv .venv`, `.venv/bin/python --version`: Python 3.14.6; environment creation succeeded |
| Editable install | `.venv/bin/python -m pip install -e ".[dev]"`: succeeded; `.venv/bin/python -m pip check`: no broken requirements |
| Import/console | `.venv/bin/python -c "import recon_agent; print(recon_agent)"` and `.venv/bin/recon-agent`: succeeded; placeholder message/status accurate |
| Lint/format | `.venv/bin/python -m ruff check .` and `.venv/bin/python -m ruff format --check .`: passed; initial format check flagged trailing CLI blank line, corrected using targeted Ruff formatting and rechecked |
| Types | `.venv/bin/python -m mypy src/recon_agent`: no issues in 12 source files; strict config without broad suppression |
| Focused/default tests | `.venv/bin/python -m pytest tests/unit/test_cli.py` and `.venv/bin/python -m pytest`: one test passed; default tests also ran with GROQ_API_KEY removed |
| Coverage | `.venv/bin/python -m coverage run -m pytest` and `.venv/bin/python -m coverage report`: succeeded; 3 statements, 0 missing, 100%; 11 empty markers skipped in display; no test code counted |
| Standard build | `.venv/bin/python -m build`: produced sdist and wheel; wheel built from sdist with isolated setuptools 84.0.0; final README/CLI included |
| Clean wheel | Fresh temporary venv outside checkout; pip `install --no-index --no-deps` of built wheel; isolated import verified site-packages/version 0.1.0; console returned 0 with expected output and no stderr; temporary environment cleaned |
| Offline boundary | Temporary wrapper removed GROQ_API_KEY and blocked socket connection/DNS functions; actual placeholder unit test passed |
| Marker selection | Temporary non-network fixtures selected 1 offline/2 deselected by default; explicit external-or-network selection selected 2/1 deselected; no real integrations run |
| Hygiene/security/docs | Temporary validator inspected TOML, source AST/unchanged markers, credential patterns, Markdown links, append-only history, Git ignore rules and archive metadata/contents; passed. `git diff --check` passed; reviewed task-owned diff |

Security/scope: Source contains only existing docstrings plus a print/return CLI; no shell=True, imports of process/network/provider code, subprocess/scanner execution, HTTP/DNS traffic, Groq calls, API keys, .env or later-task functionality. Unit tests are deterministic/offline and need no credentials or reconnaissance binaries. Dependency provisioning and isolated build-backend installation accessed the package index; this is separate from the offline package/test/CLI behavior. Generated environments, caches, coverage and dist/egg-info output are ignored and excluded from the commit.

### Acceptance and closeout

All six PLAN criteria verified: src package metadata/install/build; installed inert console; full lint/format/type/offline test/build baseline; package coverage and explicit integration marker selection; documented standard dependency/environment workflow with tested versions; ignore rules protecting generated/local secrets while retaining required source/docs/fixtures/config files. README/configuration reality and architecture boundaries reconciled. No configuration/Groq/scanner support is claimed. PLAN closes M0-T02 and makes M0-T03 READY; remaining 89 tasks NOT STARTED; no active task; blockers none. Follow-up: M0-T03 only, not started in this run.

Commit reference: the single focused commit containing this entry, titled `chore(project): establish Python development baseline`. Resolve its actual hash after creation with `git log -1 --format=%H --grep="^chore(project): establish Python development baseline$"`. Following M0-T01 precedent, no circular hash is invented and no amendment/second commit is used; the final handoff reports the actual full hash and post-commit tree result. No push.

Final staged gate: exact 12-file task-owned index verified; staged bytes matched inspected files; no unrelated, unstaged or untracked nonignored work. PLAN differs from M0-T01 only in M0-T02 DONE and M0-T03 READY. Final state/README/history were re-read and reconciled. Initial staged whitespace review found extra blank EOF lines in new pyproject/.gitignore (untracked files were absent from earlier unstaged diff checks); stripped them and successfully re-ran both Git whitespace checks and both Ruff checks. No configuration semantics changed.

## 2026-10-05 — M0-T03 — Configuration foundation

Status: DONE

Objective: Establish typed validated configuration contracts, deterministic explicit sources and separate credentials without implementing operational subsystems.

Startup: Read the ordered governance/state/PLAN/docs/ADR/history/tooling/source evidence and maintenance skill/references. Verified M0-T01/M0-T02 DONE, M0-T03 READY, all later tasks NOT STARTED, no active task/blockers, clean tree/index, and HEAD `a9bca2b760ded7b06de115ad9d3d63537f605bdd`. Recorded only M0-T03 IN PROGRESS before implementation; no unrelated work was present.

### Changes and decisions

Added `src/recon_agent/core/config/{__init__,models,loader}.py`, `tests/unit/test_config.py`, `config.example.toml` and `docs/decisions/0001-configuration-sources.md`. Updated pyproject.toml, README.md, docs/configuration.md, docs/architecture.md, docs/security-model.md, docs/testing-strategy.md, CHANGELOG.md, PLAN.md, PROJECT_STATE.md, CURRENT_TASK.md and this append-only history. Existing CLI and all subsystem package markers remain unchanged.

Architecture: AppConfig composes strict scope, execution, planner, tools, persistence, logging and reporting models. Unknown fields fail; booleans are not numeric limits, seconds must be positive/finite, counts positive, default timeout must fit the session-duration budget, supported log levels/formats are explicit and formats unique. Planner/tools/persistence default disabled; enabling a planner preference requires an operator-selected model string. Scope contains preferences only, with no targets or grants. Tools contains only enabled: no commands, executable selection, argv, extra arguments or policy bypass.

ADR 0001 records TOML via standard-library tomllib, no automatic discovery/includes/dotenv, explicit defaults < file < namespaced environment < programmatic overrides, and effective merged validation. Environment uses RECON_AGENT_SECTION__FIELD, raw string/path values and typed JSON for boolean/numeric/list fields. Unknown/malformed namespaced variables fail. Paths stay relative without resolution/creation. Native OSError/ValidationError plus one narrow ConfigLoadError suffice; no M0-T05 hierarchy is introduced.

Pydantic `>=2.12,<3` is the sole added direct runtime dependency, used for actual model validation/serialization and SecretStr. No pydantic-settings/YAML/provider/network/scanner/persistence libraries are needed. Separate ProviderSecrets reads GROQ_API_KEY explicitly; absent/empty is acceptable, the field is hidden from repr and excluded from dumps. Normal configuration rejects credential fields; displayed errors omit raw input. Structured Pydantic error consumers are documented to use include_input=False.

### Executed validation

Commands ran from the repository root using the M0-T02 .venv unless noted:

| Check | Actual result |
| --- | --- |
| Interpreter | `python --version` and `.venv/bin/python --version`: Python 3.14.6 |
| Editable install | `.venv/bin/python -m pip install -e ".[dev]"` succeeded; resolved Pydantic 2.13.5 / pydantic-core 2.46.5; `.venv/bin/python -m pip check` passed |
| Focused tests | `.venv/bin/python -m pytest tests/unit/test_config.py`: 65 passed |
| Lint/format | `.venv/bin/python -m ruff check .` and `.venv/bin/python -m ruff format --check .`: passed |
| Types | `.venv/bin/python -m mypy src/recon_agent`: passed, 15 source files |
| Full tests | `.venv/bin/python -m pytest`: 66 passed |
| Coverage | `.venv/bin/python -m coverage run -m pytest`: 66 passed; `.venv/bin/python -m coverage report`: 100%, 142 statements / 34 branches, none missing |
| Build | `.venv/bin/python -m build`: sdist and wheel built successfully, isolated setuptools 84.0.0 |
| CLI | `.venv/bin/recon-agent`: unchanged placeholder, success |
| Fresh wheel | Created temporary venv outside checkout, installed built wheel with runtime dependencies, verified import under `python -I` from site-packages, explicit configuration loading with enabled preferences, no credential requirement, CLI placeholder and pip check; all passed |
| Offline/side effects | Temporary socket-blocking wrapper ran all 66 unit tests successfully. Fresh wheel audit blocked network/process/database/directory creation, application Path.open and logging startup while importing/loading; passed. Ordinary installed dependency entry-point metadata reads were allowed |
| Security/archives | Temporary AST/archive inspection verified no process/network/SQLite/Groq imports, unchanged docstring-only subsystem markers, packaged config modules, Python >=3.12 metadata, only Pydantic as direct runtime requirement, and no environment/secrets/caches in archives |
| Git/documentation | Inspected all changed/new source/tests/docs/examples; Git diff/check and staged/closure checks passed. Generated artifacts remain ignored; history prefix and local documentation links/statuses checked |

Initial focused JSON round-trip validation exposed strict Path handling in JSON mode; corrected and re-tested. Initial lint/type checks exposed import ordering and a default-factory literal annotation; corrected and passed. A first fresh-import guard blocked ordinary Pydantic installed-package entry-point metadata reads; inspected installed dependency code and refined the guard to permit only those metadata reads while still rejecting application file/runtime activity. No production side-effect allowance or acceptance requirement was weakened.

Python 3.12 was not separately executed. Dependency provisioning/build isolation accessed the package index; configuration, tests and CLI perform no network activity. No live target, external reconnaissance binary or real credential was used. Only a synthetic redaction-test value exists in tests; no .env/API keys were supplied.

### Acceptance and handoff

| PLAN criterion | Evidence |
| --- | --- |
| Deterministic sources/precedence | Defaults/file/environment/override tests show concurrency 1 < 2 < 3 < 4; partial merge retains independent file/default settings; input mappings remain unchanged |
| Malformed/unknown settings fail | Invalid types/limits/logs/formats, malformed TOML/UTF-8, section structures, typo max_concurency, missing files and unknown/ambiguous environment tests pass |
| Absent scope cannot authorize | ScopeConfig contains only two false-default preferences; targets/grants rejected; no target selection or authorization implementation exists |
| Separate secret supplied safely | Separate loader presence/absence and SecretStr tests prove raw credential absent from config/secret repr, JSON/Python dumps and displayed errors; no network validation |
| No network/tool loading activity | Socket-blocked full suite, guarded fresh imports/enabled-preference loading, temporary filesystem/logging guard and source inspection pass |

All additional packaging/quality/docs/scope requirements passed. No M0-T04 entities, M0-T05 taxonomy, M0-T06 audit logger, M1 scope engine, process runner, adapters, Groq client, planner, SQLite state or operational reports were implemented. Configuration contracts do not enforce operational policy/budgets. PLAN closes M0-T03, makes only M0-T04 READY, leaves remaining 88 tasks NOT STARTED and CURRENT_TASK idle. No blockers or new follow-up work; stop here.

Commit reference: the single focused commit containing this entry, titled `feat(config): establish typed configuration foundation`; resolve with `git log -1 --format=%H --grep="^feat(config): establish typed configuration foundation$"`. Following prior-task convention, no circular hash is invented, amendment or second task commit is made. Actual hash and clean post-commit tree are reported in the final handoff. No push.

## 2026-10-05 — M0-T04 — Core domain model foundation

Status: DONE

Objective: Establish pure typed domain data contracts, structural validation and deterministic portable serialization before policy, execution, orchestration or persistence.

Startup: Re-read ordered governance/state/PLAN/subsystem docs/ADRs/history, maintenance skill/references, source/tests and pyproject; inspected status, working/index diffs and log. Verified clean tree/index, no active task/blockers, M0-T01–M0-T03 DONE, M0-T04 READY, all later tasks NOT STARTED, and expected HEAD `494ab7dde65000e9cd5f1481c5adc503ab4e11a0`. Recorded only M0-T04 IN PROGRESS before implementation. No unrelated work existed.

### Changes and modeling decisions

Implemented the 13 required contracts: Target, Scope, Asset, Host, Service, Endpoint, Observation, Evidence, ActionRequest, ActionResult, PlannerDecision, ReconState and ReconSession. PLAN explicitly permits staging the associated Action/ToolExecution/Finding records; documentation stages them with M1-T07/M1-T08 lifecycle/identity work, M1-T03 runner metadata and M5-T04 interpreted finding normalization respectively. No placeholder classes or untyped future-state fields are added.

Models use existing Pydantic v2 only, strict types, extra=forbid, finite JSON values and structural constraints. Caller-supplied non-blank opaque IDs preserve lineage/restoration without a database or identity algorithm. Required aware timestamps are explicit and normalize to UTC; no random IDs/system clocks. Targets/URLs are preserved declaration text, not parsed/authorized; HTTP method token validation preserves case/extensions. Services validate ports 1–65535 and tcp/udp without inferring vulnerabilities.

Observations carry a source, collection time, asset and non-empty evidence references. Evidence has source/origin, time, opaque artifact/execution references, untrusted label and optional integrity/truncation/redaction metadata; no raw blobs or artifact I/O. Observation payloads/action parameters use finite recursive JsonValue data, not Any or executable objects. Request fields and nested parameters reject executable syntax keys; capability-specific validation and priority semantics remain future registry/policy/planner work. PlannerDecision is recommendation only. ActionResult terminal statuses and minimal failure/limitation reasons reject inconsistent success/failure claims; structured project errors remain M0-T05.

Record attributes are frozen with tuple references; nested JSON mappings remain ordinary data. ReconState/ReconSession are mutable typed containers with independent factories and validated assignment, not transition engines. In-place container edits require revalidation; nested model instances are revalidated on construction. These scoped contract choices are documented in data-model.md; no architectural departure or new ADR/runtime dependency was necessary. ADR 0001's follow-up was reconciled without changing its source/secret decision.

Files: modified domain/__init__.py; added domain/_base.py, targets.py, assets.py, observations.py, actions.py and sessions.py; added tests/unit/test_domain.py. Updated docs/data-model.md, architecture/security/configuration/testing docs, ADR 0001 follow-up, README, CHANGELOG, PLAN, PROJECT_STATE, CURRENT_TASK and this append-only history. Configuration code, pyproject/dependencies, CLI and prior tests/subsystem markers are unchanged.

### Executed validation

Commands used repository .venv unless noted:

| Check | Actual command/result |
| --- | --- |
| Interpreter/install | `python --version`: Python 3.14.6; `.venv/bin/python -m pip install -e ".[dev]"` succeeded using existing Pydantic 2.13.5; `.venv/bin/python -m pip check` passed |
| Focused models | `.venv/bin/python -m pytest tests/unit/test_domain.py`: 151 passed; includes all 13 construction/round trips, strict/unknown fields, aware UTC times, ports/transports, provenance, nested composition, executable rejection, data-only recommendations, independent aggregates and record mutability |
| Ruff | `.venv/bin/python -m ruff check .` / `.venv/bin/python -m ruff format --check .`: passed; targeted formatting/import sorting applied during development |
| Types | `.venv/bin/python -m mypy src/recon_agent`: passed, 21 production modules; no weakened settings, Any, casts or suppressions introduced |
| Full tests | `.venv/bin/python -m pytest`: 217 passed |
| Coverage | `.venv/bin/python -m coverage run -m pytest`: 217 passed; `.venv/bin/python -m coverage report`: 100%, 269 statements / 52 branches, none missing |
| Build/CLI | `.venv/bin/python -m build`: sdist/wheel succeeded with isolated setuptools 84.0.0; `.venv/bin/recon-agent`: unchanged placeholder, success |
| Clean wheel | Fresh external temporary venv installed built wheel with runtime dependencies; `python -I -B` verified site-packages domain exports/import, no config import, representative Service/ActionRequest/PlannerDecision/session construction/validation and nested JSON round trip; installed CLI and pip check passed |
| Side effects/offline | Temporary socket-blocking wrapper: all 217 tests passed. Fresh wheel audit blocked network/process/database/directory creation and application file/logging activity during imports/construction/serialization; ordinary installed dependency entry-point metadata reads allowed |
| Targeted model checks | In fresh wheel: port 443 accepted, ports 0/65536 rejected; shell_command field and parameters.command rejected; decision carries a valid action without execute behavior; ActionRequest JSON schema lacks shell_command; nested session round trip passed |
| Security/packaging | Temporary AST/archive inspection: domain imports only datetime/typing/Pydantic/domain, no eval/exec/process/network/env/config/scanner/provider/database behavior or command fields; unchanged protected source/tests/dependencies; archive domain bytes match inspected code, Python >=3.12 metadata and only Pydantic runtime requirement |
| Git/docs | Reviewed every changed/new source/test/doc; Git working/index diff, whitespace, exact staged path/content, append-only history, local link, task status and artifact/secret checks passed; generated files excluded |

No required final validation failed. Python 3.12 was not separately exercised; Python >=3.12 remains declared. Dependency provisioning/build isolation accessed the package index; domain construction/imports, CLI and default tests perform no network/scanner/Groq activity and require no credentials. No live target or real secret was used.

### Acceptance and handoff

| PLAN criterion | Evidence |
| --- | --- |
| Required models construct/serialize/round-trip and reject malformed fields | 13-model Python/JSON construction and round-trip matrix; invalid structural/unknown/nested tests and manual wheel checks passed |
| Observations/evidence/decisions remain distinct | Separate fact/reference/recommendation contracts; provenance mandatory for observations/evidence; finding kind and executable/credential fields rejected; data-model/security documentation reviewed |
| Pure side-effect-free domain imports | Domain dependency AST inspection and guarded fresh-wheel import/construction/serialization passed; no config/higher-layer imports or operational side effects |
| Staged entities explicit | Action/ToolExecution/Finding staging and owning tasks documented; public API exposes only 13 implemented models and tests confirm absence of staged classes |

No M0-T05 errors, M0-T06 logging, M1 authorization/runner/registry/policy/budgets/dedup/state-machine work, scanner adapters, Groq/planner runtime, loops, SQLite/persistence, reporting or real CLI commands were implemented. Scope declarations and planner recommendations grant no authorization; allowed JSON parameters still require future deterministic capability validation. PLAN closes M0-T04, makes only M0-T05 READY, leaves 87 later tasks NOT STARTED; CURRENT_TASK says No active task. Known blockers: none; no additional follow-up task discovered. Stop here without starting M0-T05.

Commit reference: the single focused commit containing this entry, titled `feat(domain): establish core reconnaissance models`; resolve with `git log -1 --format=%H --grep="^feat(domain): establish core reconnaissance models$"`. Following existing convention, no circular hash is invented, amendment or second task commit made. Final handoff reports actual hash and clean post-commit tree. No push.

## 2026-10-05 — M0-T05 — Error taxonomy and result model

Status: DONE

Objective: Establish stable structured application failures and typed explicit operation outcomes, with safe diagnostics and configuration/domain integration, before operational layers.

Startup: Re-read governance/state/PLAN, subsystem documentation, ADRs, append-only history, maintenance skill/references, source/tests and pyproject. Inspected clean working tree/index, diffs and recent log; verified predecessor HEAD `0c13869406dc7d3d064f692f1a585f71d856d81e`, M0-T01–M0-T04 DONE, only M0-T05 READY, no active task/blockers. Recorded M0-T05 as the only IN PROGRESS task before implementation. No unrelated changes existed.

### Contracts and integration

Added pure core/errors.py and core/results.py with deliberate public exports. ReconAgentError is the project catch boundary; PolicyError groups scope rejection/budget exhaustion, ToolError groups unavailable/timeout/execution/parser failures. ConfigurationError, ProviderError and PlannerValidationError have their own categories. CancelledError supplies structured information for the existing M0-T04 cancelled outcome; no cancellation machinery exists. Catch parents cannot be instantiated. Ten stable enum codes determine categories independently of human messages.

ErrorInfo contains code, bounded non-blank message, explicit retryable and typed ErrorContext. Context allows only reference/tool/provider/capability, timeout, exit code and configuration-source scalar fields; arbitrary objects, unknown fields, secrets/output/environment/traceback dumping fields and non-finite values fail. References are limited to 256 characters and messages to 1024 to prevent raw-output accumulation in diagnostics. Frozen records revalidate nested inputs. Categories derive from codes rather than independently supplied duplicate fields. Retryability defaults false; known transient tool/provider errors may explicitly set it true, while invalid input/rejection/cancellation cannot be retried unchanged. No automatic retry or authority is implied.

Exceptions expose explicit to_error_info conversion, omitting native causes/tracebacks; unknown exceptions have no speculative global mapper. Normal str/repr and diagnostic dumps contain only the intended contract. Caller-authored ordinary diagnostic text cannot be magically identified as secret. Chained native causes remain available for explicit debugging and may retain sensitive source material; documents direct routine diagnostics to ErrorInfo, not raw exception internals/tracebacks. Separate ProviderSecrets retains its excluded/redacted serializer, including inside typed success values.

OperationResult[T] is a status-discriminated union of frozen Success[T] (required typed value) and Failure (required ErrorInfo). Invalid tags, missing/mixed fields and exception objects fail. Generic typing/narrowing retains Service and ErrorInfo without Any/casts/suppression; JSON round trips preserve nested domain types. Exceptions remain appropriate at exceptional boundaries; explicit results are for intentionally inspected outcomes, not mandatory wrappers for every function.

Configuration loading now exposes the canonical ConfigurationError for source/read/parse/effective validation failures with fixed diagnostics/source labels and native chained causes. Removed ConfigLoadError rather than retaining competing types; precedence/defaults/strict valid behavior is unchanged. Direct domain/config model construction still raises Pydantic ValidationError. ActionResult replaces temporary failure_reason with ErrorInfo: completion forbids errors; non-completion requires one, with rejection/timeout/cancellation consistency and preserved partial/evidence distinction. Generic results do not duplicate action identity/status/provenance. Domain imports pure shared errors only, without configuration or operational dependencies. This contract refinement changes only the relevant existing regression assertions.

Files: added core/errors.py, core/results.py, tests/unit/test_errors.py, test_results.py and docs/error-model.md. Updated config loader/exports, domain/actions.py, relevant config/domain regression tests, README, architecture/configuration/data-model/security/testing docs, CHANGELOG, PLAN, PROJECT_STATE, CURRENT_TASK and this history. Dependencies, CLI, other domain modules and future subsystem markers remain unchanged. No architectural departure/new dependency or redundant ADR was necessary.

### Executed validation

Commands used the repository .venv unless noted:

| Check | Actual command/result |
| --- | --- |
| Interpreter/install | `python --version` / `.venv/bin/python --version`: Python 3.14.6; `.venv/bin/python -m pip install -e ".[dev]"` and pip check passed, existing Pydantic 2.13.5 |
| Focused contracts | `.venv/bin/python -m pytest tests/unit/test_errors.py tests/unit/test_results.py`: 113 passed |
| Focused regression | Same command with test_config.py/test_domain.py: 329 passed; existing 65 config and 151 domain cases remain covered |
| Lint/format | `.venv/bin/python -m ruff check .` and `.venv/bin/python -m ruff format --check .`: passed |
| Types | `.venv/bin/python -m mypy src/recon_agent`: 23 files passed; additionally checking tests/unit/test_results.py: 24 files passed with explicit assert_type narrowing |
| Full tests | `.venv/bin/python -m pytest`: 330 passed |
| Coverage | `.venv/bin/python -m coverage run -m pytest`: 330 passed; coverage report: 100%, 400 statements / 76 branches, none missing |
| Build/CLI | `.venv/bin/python -m build`: wheel/sdist built with isolated setuptools 84.0.0; `.venv/bin/recon-agent`: unchanged inert placeholder, success |
| Fresh wheel | External temporary venv installed the built wheel; isolated `python -I -B` verified imports from site-packages, typed success/failure/domain JSON round trips, config cause chaining, safe diagnostics and installed CLI/pip check |
| Offline/side effects | Full 330 tests passed with socket connection/DNS functions blocked and Groq key absent. Fresh-wheel audit blocked network/process/database/directory creation and application file/logging startup; only ordinary dependency entry-point metadata reads allowed |
| Targeted checks | Fresh wheel verified ToolTimeoutError parent, scope code, Success[int](5), rejection of Failure.value/ErrorInfo.api_key, configuration ValidationError cause, exclusion of synthetic secret from repr/dumps; automated tests cover all codes/hierarchy/retry/context/unknown fields/contradictory outcomes |
| Security/package/docs/Git | Temporary AST/archive inspection passed: no executable/network/DB/provider/logging behavior, dangerous context fields or Any/suppressions introduced, protected files unchanged, only Pydantic runtime metadata, archive source parity, no secrets/generated artifacts; inspected all changed files, diff/whitespace, status/history/local links and staged paths |

Development checks initially exposed a leftover legacy exception declaration and a Pydantic before-validator interaction with strict nested JSON tuples. Corrected the declaration and selected explicit string outcome tags without that validator; all focused/full/type/serialization checks then passed. A documentation code example required formatting; corrected and format check passed. No acceptance condition or type setting was weakened.

Python 3.12 was not separately executed. Dependency/build provisioning may access the package index; product imports/contract construction, default tests and CLI do not. No real credential, scanner binary or live target was used. Synthetic redaction-test text is data only, with no .env or stored API key.

### Acceptance and handoff

All required categories have concrete types/codes; hierarchy/category tests establish message-independent branching. ErrorInfo/context are strict portable safe diagnostic data with explicit limitations. Success/Failure and ActionResult reject contradictory or misleading success/rejection/error structures; partial evidence remains distinct. Configuration failures use the canonical boundary and native chaining; direct structural domain validation remains Pydantic. Quality/build/fresh-wheel/security/documentation checks passed.

No M0-T06 logging/audit implementation, scope policy, process runner, availability detector, registry/adapters, budget/retry enforcement, scanners, Groq/provider/planner runtime, orchestration, SQLite, reporting or real CLI was implemented. PLAN closes only M0-T05, makes M0-T06 READY and leaves 86 later tasks NOT STARTED; CURRENT_TASK says No active task. No blockers or additional follow-up discovered. Stop at M0-T05.

Commit reference: the single focused commit containing this entry, titled `feat(core): establish error and result contracts`; resolve with `git log -1 --format=%H --grep="^feat(core): establish error and result contracts$"`. Following the established convention, no circular hash, amendment or second task commit is created. Actual hash and clean post-commit tree are reported in the final handoff. No push.

## 2026-10-05 — M0-T06 — Logging and audit-event foundation

Status: DONE

Objective: Establish explicit local diagnostics and strict correlated audit records for future autonomous reconnaissance operations, with bounded secret-safe output and no operational producers.

Startup: Re-read AGENTS/state/CURRENT_TASK, complete M0-T06 specification, subsystem docs/ADR, history, maintenance skill/references, source/tests and pyproject. Inspected clean working tree/index, both diffs and recent log; verified predecessor HEAD `8b580d37722200715ee4915551561db70e3ba308`, M0-T01–M0-T05 DONE, only M0-T06 READY, no active task/blockers. Recorded M0-T06 as the only IN PROGRESS task before implementation. No unrelated changes existed.

### Logging and audit architecture

Added core/audit.py, core/redaction.py and core/diagnostics.py with deliberate module public exports. AuditEvent is strict frozen data: explicit opaque event/session IDs, aware timestamp normalized to UTC, standard severity, concise message, bounded JSON context, optional action/execution/planner-decision/asset IDs and existing ErrorInfo. Sixteen stable enum codes cover session lifecycle, subject/fact records, planner decision/action requests, policy approval/rejection, execution outcomes and budget exhaustion. These are contracts without producers, authority, replay or new Finding/ToolExecution entities. Context is revalidated/redacted on serialization/emission, including nested edits; source evidence remains unchanged.

Explicit configure_logging consumes the existing LoggingConfig level/structured fields. Standard-library logging uses recon_agent and recon_agent.audit, with stderr or caller-supplied streams. Repeated setup replaces only the owned recon_agent.console handler, retains other project handlers and leaves root/third-party logging unchanged. Human mode prefixes severity/logger to escaped JSON; structured mode emits deterministic sorted compact JSON lines. Ordinary LogRecord timestamps use UTC; audit timestamps come from the supplied record. Both formats escape control characters/newlines and bound text/context. No implicit config/secret loading, file sink, rotating logs, remote upload, thread or startup occurs.

Context accepts JSON data and masks sensitive key suffixes and SecretStr/SecretBytes wrappers. Explicitly registered local secret values are removed from output strings, IDs, ErrorInfo and printf arguments; no environment discovery or raw credential model dump occurs. Context limits (1024-character text, 256-character keys, 64-item containers, depth eight, 8192 encoded bytes) prevent raw artifact accumulation. Raw output/environment/native exception/command/private-reasoning/transcript keys are rejected, not executed. Ordinary evidence-like words and metadata such as password_policy/token_count are preserved; diagnostic copying never modifies observations. Unknown free-text secrets cannot be magically inferred and require producer discipline.

ErrorInfo integrates without native causes, exc_info or stack_info serialization. Malformed records yield fixed omission output. Stream failures raise a fixed ConfigurationError with context suppressed, avoiding standard logging's raw-record debug fallback. No guaranteed delivery, persistence or automatic recovery is claimed. Application producers will explicitly record concise planner summaries, requested capabilities, policy outcomes and execution references; no chat architecture, transcript or hidden chain-of-thought model is introduced.

Files: added three core modules, tests/unit/test_logging_audit.py and docs/logging-and-audit.md; updated README, CHANGELOG, architecture/configuration/data-model/error-model/security/testing docs, PLAN, PROJECT_STATE, CURRENT_TASK and this append-only history. Existing production modules, prior tests, dependencies/pyproject, CLI and later subsystem markers remain byte-for-byte unchanged. No new runtime dependency or redundant ADR was needed.

### Executed validation

Commands used repository .venv unless noted:

| Check | Actual command/result |
| --- | --- |
| Interpreter/install | Python 3.14.6; `.venv/bin/python -m pip install -e ".[dev]"` succeeded with existing Pydantic 2.13.5; `.venv/bin/python -m pip check` passed |
| Focused tests | `.venv/bin/python -m pytest tests/unit/test_logging_audit.py`: 116 passed; all event codes/round trips, correlations, strict/unknown fields, UTC, bounds, remote data, redaction, formatting, severity, setup/emission and safe failure paths covered |
| Ruff | `.venv/bin/python -m ruff check .` / `.venv/bin/python -m ruff format --check .`: passed; 53 Python files formatted |
| Types | `.venv/bin/python -m mypy src/recon_agent`: 26 modules passed; additional existing generic result typing test passed via `mypy src/recon_agent tests/unit/test_results.py` (27 files); no Any, casts, ignores or weakened type settings introduced |
| Full tests | `.venv/bin/python -m pytest`: 446 passed |
| Coverage | `.venv/bin/python -m coverage run -m pytest`: 446 passed; coverage report: 100%, 621 statements / 150 branches, none missing |
| Offline | Temporary socket connection/DNS blocking wrapper with Groq key removed: all 446 tests passed; no scanner, provider, database or live target required |
| Build/CLI | `.venv/bin/python -m build`: isolated sdist/wheel build succeeded; `.venv/bin/recon-agent` unchanged placeholder, success |
| Fresh wheel | External temporary venv installed the built wheel; isolated python -I -B cold imports, pure event/ErrorInfo JSON round trips, explicit local logging/emission, duplicate-handler safety, UTC/correlation, redaction, installed CLI and pip check passed |
| Runtime guards | Fresh wheel blocked socket/process/database/directory creation, application Path file access, global logging setup and thread starts; only installed dependency entry-point metadata reads permitted; no project logger existed after cold imports |
| Security/package | Temporary AST/field/archive inspection passed: no executable/network/Groq/SQLite/remote collector behavior, private reasoning/chat/command/secret fields or domain-to-logging dependency; protected files unchanged, sole Pydantic runtime metadata and wheel/sdist source parity |
| Review | Inspected all changed/new source, tests and subsystem docs; working/index diff and artifact/secret checks performed; final status/history/local-link/whitespace/staged-path reconciliation accompanies this focused closeout |

Development checks exposed a handler marker typing mismatch and an import-test logging guard that outlived its context. Replaced the marker with the public handler name and scoped test guards correctly; subsequent focused/full/type checks passed. Security review additionally identified stdlib sink failure's raw-record fallback, so it now raises a fixed safe error and has a captured-output regression test. A manual wheel check initially used the wrong temporary venv path; rerunning against the installed venv passed. No acceptance criteria or validation settings were weakened.

Python 3.12 was not separately exercised. Installation/build provisioning may access the package index; product imports, contract construction, local logging, tests and CLI require no network or credentials. Only obvious synthetic secret text was used, with no real key or .env file.

### Acceptance and handoff

| PLAN criterion | Evidence |
| --- | --- |
| Listed events serialize with correlation/timestamps | All sixteen event types pass Python/JSON round trips with explicit IDs and UTC; captured audit sink and guarded wheel checks passed |
| Secret settings/error contexts redacted | ProviderSecrets wrappers/exclusions, sensitive-key and registered-value tests, ErrorInfo and printf/sink failure tests passed; free-text limitations documented |
| Untrusted text bounded/escaped | Context/string/depth/item/byte limits, control/newline escaping, invalid record omission and unchanged source Observation tests passed |
| Local logging needs no credentials/network or policy changes | Explicit project-only setup/import guards, severity/repeated-handler tests, network-blocked suite and fresh wheel guards passed; events have no execution/authorization behavior |

M0-T06 adds infrastructure only. No scope enforcement, process runner, registry, scanner adapter, Groq/provider/planner runtime, autonomous loop, persistence, operational report or real CLI was implemented. No future event producer or private reasoning/chat model exists. PLAN closes M0-T06, makes only M1-T01 READY and leaves 85 later tasks NOT STARTED; CURRENT_TASK says No active task. Known blockers: none; no additional follow-up discovered. Stop without beginning M1-T01.

Commit reference: the single focused commit containing this entry, titled `feat(core): establish logging and audit foundation`; resolve with `git log -1 --format=%H --grep="^feat(core): establish logging and audit foundation$"`. Following the existing convention, no circular hash is invented and no amendment or second task commit is made. Final handoff reports the actual hash and post-commit clean tree. No push.

## 2026-10-05 — M1-T01 — Scope model and validator

Status: DONE

Objective: Establish centralized deterministic fail-closed declaration membership for every supplied target and derived destination, without network activity or executable capabilities.

Startup: Read AGENTS/state/CURRENT_TASK, complete M1-T01 PLAN specification, required subsystem docs/ADR/history, maintenance skill/references, current source/tests and pyproject. Inspected clean tree/index, both diffs and recent log; verified predecessor HEAD and ancestor `823fc3eda3ae02b1e7b3eab0c0ba46c03c1d4fa2`, M0-T01–M0-T06 DONE, only M1-T01 READY, no active task/blockers. Recorded M1-T01 as the only IN PROGRESS task before implementation. No unrelated user modifications existed.

### Authorization contracts

Added pure synchronous ScopeValidator and ScopeMatch in policy/scope.py with a small public policy API. Scope/Target remain unchanged data. The validator revalidates and compiles an immutable declaration snapshot; invalid roots/exclusions fail construction with canonical ScopeRejectedError, never ignored configuration. validate returns existing OperationResult[ScopeMatch] Success/Failure; require_allowed raises the same canonical policy exception. Canonical Target and matching declaration preserve IDs/kinds. Added ScopeRejectionReason and optional typed scope_reason/target_kind/normalized_candidate to existing ErrorContext; no duplicate result/error hierarchy. Decisions have no audit/logging side effects or execution/replay authority.

Domains authorize exact normalized names and optional proper label descendants; hostname/URL rules stay exact authorities. ASCII DNS normalization lowercases/removes one final dot, rejects malformed labels, numeric/alternate address spellings, whitespace/controls and unsupported Unicode/punycode. Parsed IPv4/IPv6 comparisons support equivalent spellings; aligned numeric-prefix CIDRs authorize contained addresses or ranges within a single root. Zones/mapped IPv6 and malformed/host-bit CIDRs fail closed. HTTP/HTTPS URL scope uses parsed actual authorities and validates brackets/ports; userinfo is rejected entirely, and path/query/fragment do not influence membership or appear in rejection context. Canonical successful URLs preserve those components' case/content.

Exclusions always win: domain exclusions cover descendants regardless of allow_subdomains; hostname/URL exclusions are exact; candidate ranges overlapping excluded IP/CIDR data are rejected in full. Deterministic match reporting uses canonical specificity/kind/value/ID, independent of declaration order. Private-address gating covers explicit RFC1918/IPv6 ULA networks and any overlapping candidate CIDR. Enabling the flag only permits otherwise declared membership; unrelated private networks remain rejected. Documentation ranges and other special categories do not infer authority or broader execution permission.

ADR 0002 resolves derived-address semantics: discovery does not imply authorization; planner recommendation does not imply authorization; every newly introduced network target requires deterministic validation before future execution. The same callable boundary accepts each absolute redirect/discovered name/supplied IP independently. No automatic scope expansion, DNS lookup or inherited origin authority exists. Future adapters must independently validate concrete addresses and constrain/pin approved contacts/revalidate changes; no resolver/rebinding/contact runtime is claimed today. Application preferences are applied only by future explicit trusted session assembly; the validator reads effective Scope flags, with no global config or implicit option combination.

Files: added policy/scope.py, tests/unit/test_scope.py, docs/scope-model.md and ADR 0002. Updated policy exports, shared errors and its one explicit export-set regression assertion; README, CHANGELOG, architecture/security/data/config/error/logging/tool/testing documentation; PLAN, PROJECT_STATE, CURRENT_TASK and this append-only history. Domain models, dependencies/pyproject, config loaders/models, audit/logging implementation, CLI, runner and other future subsystem markers remain unchanged.

### Executed validation

Commands used repository .venv unless stated:

| Check | Actual result |
| --- | --- |
| Interpreter/install | Python 3.14.6, Pydantic 2.13.5; `pip install -e ".[dev]"` and `pip check` passed |
| Focused scope | `pytest tests/unit -k scope`: final 122 passed, 432 deselected; includes 108 new implementation cases |
| Ruff | `ruff check .` and `ruff format --check .`: passed, 57 Python files formatted |
| Types | `mypy src/recon_agent`: 27 production modules passed; `mypy src/recon_agent tests/unit/test_results.py`: 28 files passed, no weakened checks/Any/ignores |
| Full tests | `pytest`: final 554 passed |
| Coverage | `coverage run -m pytest`: 554 passed; `coverage report`: 99%, 781 statements / 216 branches, two defensive policy lines unexecuted; no threshold/acceptance weakened |
| Offline full suite | Temporary socket connection/send/bind/listen and DNS-function blocking wrapper, Groq key absent: 554 passed |
| Build/CLI | Final `python -m build` succeeded (sdist/wheel, isolated setuptools 84.0.0); `recon-agent` unchanged inert message, successful exit |
| Fresh wheel | External temporary venv installed final wheel; isolated `python -I -B` guarded cold imports verified site-packages origin, declaration matching, scope errors/typed results and JSON round trips; installed CLI/pip check passed |
| Runtime guards | Wheel check blocked socket/DNS/process/database/directory/thread/global logging startup, application Path access and file writes; allowed normal dependency metadata/import reads; no project logger was created by imports |
| Manual security | Fresh-wheel exact/case/trailing-dot and lookalike cases; domain descendants on/off; authorized origin/out-of-scope redirect; userinfo confusion; independent supplied-IP rejection; IPv6 URL; private declared member on/off and unrelated private address rejection all passed |
| Source/package | AST and targeted searches showed no network/process/scanner/Groq/database behavior or broad permissive exception fallback in policy. The hostname suffix comparison includes explicit dot boundary. Sole runtime dependency remains Pydantic; wheel/sdist source bytes match checkout; no generated artifacts/secrets staged; protected files unchanged |
| Review/reconciliation | Reviewed every changed/new source/test/doc, scope/security/architecture contracts and state/history. Final Markdown links, task statuses/dependencies, append-only history, secret/artifact checks and working/staged Git diff/whitespace inspections passed before commit |

Development checks caught an initial test import of a non-exported config model, strict typing of URL IP union/range comparisons, and the existing explicit error export-set assertion. Corrected imports/types and updated that assertion to reflect the intended additive enum API. Review tightened alternate numeric hostname and bracketed URL authority rejection. Subsequent focused/full/offline/type/build/wheel checks passed. Python 3.12 was not separately executed; the explicit bracket-suffix check also defends older parser behavior. Unsupported-kind parsing is defensive behind Target revalidation. No artificial branches/tests or acceptance relaxation were introduced for coverage.

Installation/build provisioning can access the package index; product policy/imports/tests/CLI perform no network activity. No real credential, live target or reconnaissance binary was used. Synthetic token text only exercises safe diagnostic omission.

### Acceptance and handoff

| PLAN criterion | Evidence |
| --- | --- |
| Deterministic allow/deny, canonical targets and reasons | Existing Success/Failure plus canonical Target/matched declaration; ScopeRejectionReason/ErrorInfo; repeated/order-independent matches and Python/JSON tests passed |
| Lookalikes/malformed targets/ambiguous scope fail closed | Exact/label suffix, malformed DNS/IP/CIDR/URL, exclusion precedence, private gates, invalid declaration and parser failure tests; manual/wheel checks passed |
| Redirect/new names require new validation | Independent origin/redirect/discovered name/address cases rejected absent their own membership; pure callable boundary and docs introduce no origin exceptions |
| DNS/address semantics documented, no arbitrary IP expansion | ADR 0002/scope/security/tool contracts require independent concrete-address checks and constrained future contact; name-only scope rejects supplied IPs; no DNS/network code introduced |

M0-T01–M0-T06 and M1-T01 are DONE. M1-T02 dependency/prerequisite gate is satisfied and it alone becomes READY; 84 later tasks remain NOT STARTED. CURRENT_TASK says No active task. The broader M1-T02 corpus/property/fake dispatch work has not begun. No action policy, execution capability, scanner, provider/planner, orchestration, persistence or CLI behavior was added. Known blockers: none; documented future contact/address constraints belong to their existing owning tasks. Stop after M1-T01.

Commit reference: the single focused commit containing this entry, titled `feat(policy): implement deterministic scope validation`; resolve with `git log -1 --format=%H --grep="^feat(policy): implement deterministic scope validation$"`. Established convention avoids a circular self-hash, amendment or second task commit. Final handoff reports actual hash and clean post-commit tree. No push.

## 2026-10-05 — M1-T02 — Scope regression suite

Status: DONE

Objective: Prove the documented deterministic scope authorization boundary against confusing host/URL/IP representations before future network adapters depend on it.

Startup: Read AGENTS, PROJECT_STATE, CURRENT_TASK, full M1-T01/M1-T02 specification and M1-T03 boundary, README, scope/security/architecture/data/error/testing/tool docs, relevant ADRs, maintenance skill/references and recent history. Inspected clean working/index diffs and recent log; confirmed HEAD and predecessor commit `b54059ae9e5cd74d3d91ab566f2cd4801c75d824`, M0-T01–M0-T06/M1-T01 DONE, M1-T02 READY, no active task/blockers. Read current policy, scope tests, domain/config/error/result contracts and pyproject before marking only M1-T02 IN PROGRESS. No unrelated user changes existed.

### Regression coverage

Added two coherent test modules and a socket/DNS-blocking autouse fixture under tests/unit/policy. The independent expected outcomes follow scope-model.md and ADR 0002, rather than treating observed implementation behavior as the security specification:

- Exact/case/single-trailing-dot DNS identity, proper label descendants with/without explicit authorization, mandatory suffix/lookalike attacks, label/name length boundaries, malformed labels, unsupported Unicode/punycode and whitespace/control contamination.
- HTTP/HTTPS parsed authority, host-level valid ports, ordinary path/query/fragment preservation, userinfo rejection even on independently authorized actual hosts, malformed brackets/ports, unsupported schemes, percent-encoded authorities and backslashes.
- IPv4 exact neighbors, IPv6 equivalent representations/bracketed URLs, alternate IPv4 notations, mapped/scoped IPv6 rejection, IPv4/IPv6 CIDR boundaries and /0, /31, /32, /127, /128, strict malformed/unaligned prefixes and same-family full containment.
- RFC1918/ULA gates and boundaries, partial private CIDR overlap, unrelated private rejection with the option enabled, explicit special-address membership, exclusion precedence/subtree versus exact-authority semantics and overlapping candidate range rejection.
- Empty scopes, invalid declarations mixed with valid rules, strict unknown kinds/fields, duplicate and permuted overlapping rules, specific matching/stable ID tie reporting, repeat determinism and no union/subtraction widening.
- Stable `scope_rejected` and reason codes, canonical authority-only context, ErrorInfo/ScopeRejectedError parity, JSON success/failure round trips and specific ValueError/TypeError parser failures without permissive fallback or raw diagnostic leakage.
- Independent redirect matrix and provenance-labelled TLS SAN/DNS/robots/JavaScript/scanner candidates. Test-only mock consumers call require_allowed before contact; rejected candidates leave the mock untouched. Explicit IP redirect authorization is tested separately. Declarations remain unchanged.

Deterministic generated checks exhaust 155 small name prefixes (with allowed label-boundary controls), compare 2,322 IPv4 prefix/member combinations plus 30 IPv6 boundaries against ipaddress membership, and permute allow/exclude rules. These supply property/fuzz-style coverage without Hypothesis, randomness, remote fixtures or another dependency. No new ADR or scope semantic was needed.

No regression demonstrated a validator defect. Production source, existing tests, domain/config/error/result contracts, dependencies, CLI and future subsystem markers remain byte-for-byte unchanged. The existing boundary-aware endswith comparison is correct; URL authorization uses parsed hosts, unsupported userinfo is rejected, address membership precedes any allowance, and exclusions/private gates have deterministic precedence. The only remaining uncovered policy line is the unsupported-kind guard after strict Target revalidation; public forged-kind rejection is tested without bypassing that boundary just to increase coverage.

Files: added tests/unit/policy/conftest.py, test_scope_names_urls.py and test_scope_addresses_rules.py. Updated scope/security/testing docs, README, CHANGELOG, PLAN, PROJECT_STATE, CURRENT_TASK and this append-only history. Architecture/data/error/tool docs and ADR 0002 were reviewed and remain accurate; no production contract change required edits there.

### Executed validation

Commands used repository .venv (Python 3.14.6 / Pydantic 2.13.5) unless stated:

| Check | Actual command/result |
| --- | --- |
| Setup | `python --version`, `python -m pip install -e ".[dev]"` and `python -m pip check`: passed |
| Dedicated corpus | `python -m pytest tests/unit/policy`: final 343 passed (initial 334 passed before additional range/precedence/redirect cases) |
| Full tests | `python -m pytest`: 897 passed |
| Coverage | `python -m coverage run -m pytest`: 897 passed; `python -m coverage report`: 99%, 781 statements / 216 branches, one defensive line/branch unexecuted (scope.py:112), improved from two missing lines |
| Offline full suite | Temporary Python wrapper blocks socket connect/connect_ex/bind/listen/accept/send/recv families and DNS helpers before collection, removes Groq key: all 897 passed; dedicated corpus additionally blocks socket construction |
| Ruff/format | `python -m ruff check .` and `python -m ruff format --check .`: passed, 60 Python files formatted |
| Types | `python -m mypy src/recon_agent`: strict checks passed for 27 production modules; no typing/acceptance settings weakened |
| Build | `python -m build`: isolated setuptools 84.0.0 sdist/wheel build passed; final README metadata rebuild and archive parity checks performed before commit |
| CLI | `.venv/bin/recon-agent` and fresh-wheel console command: unchanged inert placeholder, exit 0 |
| Fresh wheel | New external temporary venv installed wheel; `python -I -B` cold imports resolved from site-packages, high-risk domain/userinfo/redirect/private/IPv6 cases and error/result JSON round trips passed; installed CLI and pip check passed |
| Runtime guards | Fresh-wheel check blocked socket/DNS/process/database/directory/thread/global logging startup, application Path access and writes; ordinary import/dependency metadata reads allowed; imports created no project logger |
| Security/package | Source byte parity with M1-T01, corpus AST imports and suffix/parser/fallback searches reviewed; wheel/sdist source parity and sole Pydantic runtime dependency passed; no generated artifacts, environment files or new secrets in visible/staged files |
| Reconciliation | Final task-status/dependency, append-only history, Markdown link, secret/artifact and Git working/index/whitespace inspections passed before the single commit |

Python 3.12 was not available on PATH or checked local interpreter locations; it was not executed and does not block this task. Python 3.14.6 is the only version actually tested. Package installation/build provisioning may access the package index; policy/tests/CLI and guarded imports require no network or credentials.

The initial broad secret-pattern check flagged the pre-existing synthetic `sensitive-test-value` invalid-config fixture. Verified its unchanged source and allowed only that exact known test match; subsequent archive/secret checks passed. An interpreter location glob also found no Python 3.12. Neither required a repository code change or acceptance relaxation. There were no failing regression tests and no production bugs fixed.

### Acceptance and handoff

| PLAN criterion | Evidence |
| --- | --- |
| Required edge-case groups have explicit expected outcomes | Dedicated name/URL/address/rule parameter tables plus independent generated suffix/CIDR checks and contract cases: 343 passed |
| Out-of-scope/lookalike/ambiguous targets denied | Suffix confusion, userinfo, parser/encoding/control, private/nonstandard address and malformed mixed declarations fail closed with canonical reason codes |
| Authorized canonical forms consistent | Case/trailing-dot/IPv6 normalization, CIDR identity/containment, stable match specificity/ties, duplicate/permutation/repeat and JSON outcomes passed |
| Fake dispatch shows no contact on rejection | Independent redirect and discovery mock consumers assert require_allowed rejection and assert_not_called; no production execution code added |
| Regression suite runs offline | Autouse network/DNS fixture and all 897 full-suite tests under contact/DNS blocking with Groq key absent |

M0-T01–M0-T06 and M1-T01–M1-T02 are DONE. M1-T03 prerequisites are satisfied and it alone becomes READY; all 83 later tasks stay NOT STARTED. CURRENT_TASK says No active task. Known blockers/follow-up work: none newly discovered; existing future contact enforcement remains owned by adapters/action policy/orchestration. No authorization widening, DNS/network runtime, scanner/subprocess runner, Groq, persistence, planner approval, automatic discovery expansion or origin-to-redirect trust was added. Stop after M1-T02; M1-T03 has not begun.

Commit reference: the single focused commit containing this entry, titled `test(policy): harden scope authorization regressions`; resolve with `git log -1 --format=%H --grep="^test(policy): harden scope authorization regressions$"`. Established convention avoids an invented circular self-hash, amendment or second task commit. Final handoff reports the actual full hash and clean post-commit tree. No push.

Closeout validation correction: temporary reconciliation checks initially parsed the multiword NOT STARTED status as one token, mistook historical `Success[int](5)` notation for a Markdown link, and decoded UTF-8 wheel README metadata through the email parser's ASCII text fallback. Corrected the temporary checks to read complete status lines, exclude code/type notation from links and compare original UTF-8 metadata bytes. Final checks passed: 8 DONE / 1 READY / 83 NOT STARTED, 63 local links, preserved historical prefix, and final wheel/sdist README/source parity. These were checker errors; repository states, documentation and artifacts required no correction.

## 2026-10-05 — M1-T03 — Execution runner abstraction

Status: DONE

Objective: Supply a safe internal awaitable local process primitive for future trusted adapters, without creating a terminal, AI tool, generic command product feature or reconnaissance dispatch.

Startup: Followed AGENTS/maintenance skill/references; read state/current task, complete M1-T03 and M1-T04 boundary, README and architecture/security/tool/error/data/logging/config/testing docs, ADRs and recent history, then Git/source/tests/pyproject. Verified clean working tree/index and predecessor HEAD/ancestor `c6c8669bb0940e65f0212b8d226e1581fccc8421`; M0-T01–M0-T06/M1-T01–M1-T02 DONE, only M1-T03 READY, no active task/blocker. Set only M1-T03 IN PROGRESS before implementation. No unrelated modifications existed.

### Implementation and boundaries

Added execution/models.py and runner.py with a small package API: strict frozen ProcessSpec (separate executable, tuple of literal argument strings, optional positive finite timeout), ProcessExecution (separate bounded raw stdout/stderr, truncation flags, return code, argument count, aware UTC timestamps and monotonic duration), ProcessRunner injection protocol and AsyncProcessRunner. No command string, parsing/splitting, shell, wrapper or planner-facing executable field. Empty executable/NUL/wrong argument types/invalid timeout/unknown fields fail structural validation before spawn; specs and configuration snapshots are revalidated. No new runtime dependency or ADR was needed.

Async design matches the planned concurrent engine without scheduling it. Production uses create_subprocess_exec, DEVNULL stdin, separate pipes with explicit 64 KiB flow-control limit, no TTY and inherited environment/cwd. An internal trusted ProcessHandle/spawn seam supports deterministic fake processes. Future adapters can inject a fixture runner via the minimal execution-neutral ProcessRunner protocol; no ToolAdapter/registry interface, capability mapping or executable allowlist was implemented.

ExecutionConfig.default_timeout_seconds is reused; a spec timeout overrides it. max_output_bytes is enforced while reading **per stream**: retain at most N stdout plus N stderr bytes, concurrently read in at most 16 KiB chunks, discard excess and set independent truncation flags. No communicate-then-truncate buffer exists. Bounded capture/conversion/transport overhead is documented; this is retention, not a total generated-byte/CPU/session budget. Raw bytes preserve malformed UTF-8; deliberate text decoding belongs to adapters and JSON uses URL-safe base64.

Ordinary exits, including non-zero/negative codes, return existing Success[ProcessExecution]; future adapters interpret tool semantics and normalize into domain ActionResult/observations. Missing/permission-denied executable yields canonical ToolUnavailableError-derived Failure. Other OS/encoding spawn or capture failures yield ToolExecutionError-derived Failure with fixed messages. Deadline yields ToolTimeoutError-derived Failure carrying effective timeout only. No native paths, OS details, arguments, environment or output enter ErrorInfo. Existing Failure has no payload: bounded partial output on timeout/capture failure is deliberately discarded, never stuffed into diagnostic context or a new outcome hierarchy.

On deadline/caller cancellation, lifecycle ownership is retained through spawn, terminate, up to 0.5-second graceful wait, kill escalation and direct-child reaping. Owned pipe/wait/stop tasks are cancelled/awaited where required; exit/signal races are handled. Shielding covers cancellation during spawn, repeated cancellation and cancellation during timeout cleanup. asyncio.CancelledError propagates after cleanup, never converted to successful execution or a domain failure. Direct-child guarantees are tested; no descendant/process-group containment or OS-stall hard deadline is claimed. Descendants may survive/hold pipes open, pending spawn must yield a handle/error, and reaping can extend cleanup time. Existing adapter reliability work/M11-T03 must account for these documented limits before integrating tools with descendants; no new future task was implemented.

The runner emits no logs/audit events and cannot claim authorization. Result metadata contains no executable/argv/environment; spec executable/args and output are excluded from repr, while explicit internal dumps still require producer discipline. Capability is not command: planner intent → future policy → future registry → future trusted adapter argv → implemented runner → process. No direct AI/Groq path, scope duplication/resolution/expansion, scanners, action policy, session budget/rate/concurrency scheduler, provider/planner runtime, orchestration, persistence, report or real CLI added. Protected core/config/error/result/audit/logging, domain, policy, CLI and future subsystem source are unchanged.

Files: added execution/models.py, execution/runner.py, tests/unit/execution/test_runner.py, test_local_process.py and docs/execution-model.md; updated execution exports, pyproject's local_process marker only, README/CHANGELOG and architecture/security/tool/data/error/config/logging/testing docs; reconciled PLAN/PROJECT_STATE/CURRENT_TASK and appended this history. No generated artifacts staged.

### Executed validation

Repository .venv used unless stated; Python 3.14.6 / Pydantic 2.13.5 only. Python 3.12 was not found on PATH or checked local interpreter locations and was not tested.

| Check | Actual command/result |
| --- | --- |
| Setup | `python --version`, `python -m pip install -e ".[dev]"`, `python -m pip check`: passed |
| Focused execution | `python -m pytest tests/unit/execution`: final 69 passed; initial 65/68 passed before additional cancellation/logging/concurrency/encoding coverage |
| Marker isolation | Same path with `-m local_process`: 17 passed / 52 deselected; with `-m 'not local_process'`: 52 passed / 17 deselected |
| Full suite | `python -m pytest`: final 966 passed |
| Coverage | `python -m coverage run -m pytest`: 966 passed; `coverage report`: 99% overall, 914 statements / 234 branches; execution models/runner/exports 100% statement/branch coverage; only existing scope.py:112 defensive branch uncovered |
| Offline full suite | Temporary `/tmp/recon-m1t03-validation/offline.py` blocks socket Internet/loopback contact/send/receive/bind/listen and DNS helpers, removes Groq key, checks guard rejection before pytest: final 966 passed. AF_UNIX event-loop self-pipes allowed; child scripts statically reviewed for no networking (guard is not a subprocess sandbox) |
| Ruff/format/types | `ruff check .`, `ruff format --check .`: passed (formatter reported 65 files); `mypy src/recon_agent`: strict checks passed for 29 production modules; no weakened typing or ignores |
| Build/CLI | `python -m build`: isolated setuptools 84.0.0 sdist/wheel succeeded; editable and fresh-wheel `recon-agent` emit unchanged inert placeholder and exit 0 |
| Fresh wheel | External temporary venv installed final wheel; `python -I -B /tmp/recon-m1t03-validation/wheel_checks.py`: guarded cold imports resolve to site-packages, no startup/logging, spec/result JSON round trips, unchanged action/planner fields, literal argv/sentinel, malformed bytes, large simultaneous bounded streams, missing program and timeout all passed; `pip check` passed |
| Import guards | Fresh-wheel script blocks socket/DNS/process/database/thread/directory/global logging startup, application Path access and writes; allows standard dependency metadata/import reads. No project logger created during imports/constructors |
| Manual/static security | Literal `hello; SHOULD_NOT_EXECUTE`, `$HOME`, substitutions, wildcards, `foo && bar`, quotes/spaces/operators remain one argv each; Python/shell-looking sentinel commands have no side effect. Searches/AST review found no forbidden shell/command parsing/evaluation APIs, planner/provider/scope imports, scanners or communicate buffering in runner; protected source byte parity passed |
| Resources | Fake timeout/kill/exit/spawn/capture/cancellation races and local timeout/cancellation direct-child tests passed. Local handle return codes and wait complete; POSIX waitpid raises ChildProcessError, proving reaped child. Large alternating stdout/stderr completes with each retained output <= configured cap and explicit truncation |
| Packaging/security | Temporary inspect.py verifies wheel/sdist source and README byte parity, sole Pydantic runtime dependency, no generated/cache artifacts, no private-key/provider-token patterns in visible files, scanner/registry/future runtime absence and Git whitespace; passed |
| Final review | Reviewed task-owned code/tests/docs, full working/index diff and each acceptance criterion; state/dependency/link/history/secret/artifact/staged path/whitespace reconciliation completed before the single commit |

Development checks caught an unused test import and required Ruff formatting; corrected only task-owned files. Final review added canonical handling/test for OS spawn encoding failure. Temporary validation commands initially used a checkout-relative interpreter while cwd was /tmp and an unmatched zsh interpreter glob; corrected to absolute interpreter and Python pathlib searches. The first fresh-wheel guard overblocked Pydantic's legitimate site-packages entry-point metadata reads; narrowed only read access to dependency metadata while keeping application reads/writes/startup blocked. Final guarded checks passed. An initial patch attempt used two operations on the same export file and was rejected without source changes; reapplied as a single update. No acceptance relaxation or product defect remains from these tooling errors.

Installation/build provisioning can access the package index; product imports/tests/local children/CLI require no network, credentials, live target or reconnaissance binary. No process-tree guarantee or Python 3.12 run is claimed.

### Acceptance and handoff

| PLAN criterion | Evidence |
| --- | --- |
| Approved internal argv only, no shell | Strict spec plus create_subprocess_exec; future adapter/policy ownership documented; malformed/string API rejection and real literal-argv/no-sentinel regressions passed |
| Bounded separate capture and status | Incremental concurrent readers, per-stream prefix caps/truncation, raw bytes and return-code/timing contracts; fake and marked local output/non-zero/invalid-byte/JSON cases passed |
| Timeout/cancel cleanup and metadata | Existing timeout Failure/context; graceful terminate/kill/reap, shielded spawn/repeated-cancel ownership; caller cancellation propagated; fake/local handle and POSIX reaping evidence passed |
| Unavailable/non-zero/overflow distinguished | Canonical unavailable/exec/timeout Failures versus Success exit facts and independent truncation flags; full matrix passed |
| No planner-facing execution API | Domain/planner source unchanged; runner imports no AI/domain/policy and emits no approval/audit; no CLI/registry/scanner path added; static and wheel contract checks passed |

M0-T01–M0-T06 and M1-T01–M1-T03 are DONE. M1-T04's prerequisite gate is satisfied and it alone becomes READY; all 82 later tasks remain NOT STARTED. CURRENT_TASK says No active task. Known blockers: none. Follow-up limits are documented under existing adapter/process reliability tasks; no new scope or future implementation begun. Stop after M1-T03.

Commit reference: the single focused commit containing this entry, titled `feat(execution): add safe subprocess runner`; resolve with `git log -1 --format=%H --grep="^feat(execution): add safe subprocess runner$"`. Existing convention avoids inventing a circular self-hash, amendment or second task commit. Final handoff reports actual full hash and verified clean tree. No push.

## 2026-10-05 — M1-T04 — Capability and Tool Registry

Status: DONE

Objective: Establish deterministic semantic capability → trusted adapter resolution,
typed schema metadata and sanitized availability catalog without reconnaissance or
action authorization.

Startup: Followed AGENTS and recon-project-maintainer skill/references; read repository
state/current task, full M1-T04 and adjacent boundaries, README, architecture/security/
tool/execution/data/error/planner/logging/config/testing docs, ADRs and recent history,
then clean Git/index/log and relevant source/tests/pyproject. Confirmed HEAD and expected
M1-T03 commit 2198fc345feb6ba18b76dc59dd71fd39e365d8ae, M0-T01–M0-T06/M1-T01–M1-T03
DONE, only M1-T04 READY, no active task/blockers. Set only M1-T04 IN PROGRESS before
implementation. No unrelated changes existed.

### Implementation and decisions

- domain/capabilities.py defines finite CapabilityId (10 previously documented semantic
  operations), RiskClass (passive/active_safe) and strict frozen CapabilityDescriptor.
  Conceptual membership is distinct from working adapter support. No arbitrary command
  identity exists. ActionRequest retains structural capability-name/provenance semantics
  so unknown intent is rejected at lookup; nested import_path/python_module are added to
  its existing executable-key denylist. No executable/argv/adapter field is introduced.
- tools/base.py supplies minimal ToolAdapter ABC with read-only definition, strict frozen
  AdapterDefinition (stable distinct adapter ID, semantic descriptor, strict extra-forbid
  input/output Pydantic model classes), frozen AdapterRegistration and declared
  AdapterAvailability. Schema classes are internal trusted code and excluded from dumps.
  Execution/parse/probing methods and real capability-specific models await adapter tasks.
- tools/registry.py composes immutable snapshotted metadata/mapping proxies from explicit
  trusted registrations. No runtime registration, mutable globals, dynamic imports,
  plugin/PATH scanning or configuration command definitions. One selected adapter per
  capability; duplicate IDs (including same instance twice), conflicting capability
  owners and malformed metadata fail clearly with existing configuration_invalid.
  ADR 0003 records the choice and future alternative-composition boundary.
- resolve returns existing typed Success[InstanceOf[ToolAdapter]] or canonical Failure.
  Unknown capability → planner_validation_failed (no arbitrary input echoed); known but
  unregistered → tool_unavailable. Internal unknown adapter lookup also returns
  tool_unavailable. Registered availability defaults not_checked; unavailable/not_checked
  resolution fails closed. Available is an explicit trusted snapshot, not probing,
  enablement or permission. Future dispatch must recheck runtime facts.
- Lexical tuple listings/catalogs are deterministic across input permutations. Catalog
  entries have exactly capability/description/risk_class/availability; no adapter ID,
  executable/argv/template/import/environment/runner/instance/schema class. Descriptions
  are curated trusted semantic text; producer discipline still governs free text.
  Internal adapter resolution payloads are not planner serialization APIs.
- Registry operations are synchronous local facts: no scope/risk/parameter authorization,
  budgets, runner calls, audit events, network/DNS, binary discovery or Groq. Runner remains
  unchanged and lower-level. Trusted future adapters validate typed parameters and build
  explicit argv; no parameter-to-flags pass-through. Default registry is empty.

Files: added domain/capabilities.py, tools/base.py, tools/registry.py,
tests/unit/tools/test_registry.py and ADR 0003; updated tools exports and ActionRequest
reserved keys. Updated README/CHANGELOG and tool/architecture/security/planner/execution/
data/error/config/logging/testing docs; reconciled PLAN/PROJECT_STATE/CURRENT_TASK and
appended this history. Existing runner, core/config/errors/results/logging, scope policy,
CLI, dependencies and future subsystem code are unchanged. No generated artifacts staged.

### Executed validation

Repository .venv used unless stated; only Python 3.14.6 / Pydantic 2.13.5 was tested.
Python 3.12 was not available on PATH and was not tested.

| Check | Actual command/result |
| --- | --- |
| Setup | python --version; pip install -e ".[dev]"; pip check: passed |
| Focused registry | python -m pytest tests/unit/tools: 98 passed |
| Registry/domain regressions | python -m pytest tests/unit/tools tests/unit/test_domain.py: 249 passed |
| Full suite | python -m pytest: 1,064 passed |
| Coverage | coverage run -m pytest: 1,064 passed; coverage report: 99% overall, 1,024 statements / 254 branches; new capability/tools code 100%; existing defensive scope.py:112 only missing line/branch |
| Offline full suite | /tmp/recon-m1t04-validation/offline.py removes Groq key, blocks socket Internet/loopback contact and DNS before collection: 1,064 passed; AF_UNIX event-loop self-pipes allowed; child scripts contain no network, parent guard is not child sandbox |
| Ruff/format/types | ruff check .; ruff format --check .: passed (70 files); mypy src/recon_agent: strict checks passed, 32 production modules; no Any/cast/ignores or weakened settings in new source |
| Build/CLI | python -m build: isolated setuptools 84.0.0 sdist/wheel passed; editable and fresh-wheel console commands emit unchanged inert message, exit 0 |
| Fresh wheel | New /tmp/recon-m1t04-validation/wheel-venv installed built wheel; isolated python -I -B wheel_checks.py: guarded cold imports/site-packages origins, registry composition/typed schemas/resolution/safe catalog/unknown/unavailable outcomes and no runtime side effects passed; pip check passed |
| Runtime guards | Tests block socket construction/DNS/subprocess/AsyncProcessRunner.run and guarded lookup blocks import_module, filesystem scanning/writes and logging setup. Fresh-wheel cold import guards block socket/process/database/thread/directory/logging startup and application Path access/writes; dependency metadata reads allowed |
| Security/artifacts | artifact_checks.py plus targeted production searches/AST review: no dynamic imports/eval/exec/shell/binary lookup/network/Groq/policy imports or scanner classes in new code; protected source parity, unchanged Pydantic-only dependency, wheel/sdist source/README parity, secrets/artifact checks passed |
| Reconciliation/review | Reviewed every task-owned source/test/doc and working/staged diff; acceptance/status/dependency/Markdown/history-prefix/secret/artifact and Git whitespace checks before single commit |

Development required Ruff formatting only. The first offline validation attempt reused
the M1-T03 temporary directory containing inspect.py, which shadowed Python's stdlib
inspect import and ran the old task's checker. Moved the wrapper to a clean M1-T04
temporary directory; guarded full-suite validation passed. A second run captured complete
process completion explicitly. No product defect or acceptance relaxation resulted.
Installation/build provisioning may access a package index; registry/product imports,
tests and inert CLI require no network, keys, live targets or reconnaissance binaries.

### Acceptance and handoff

| PLAN criterion | Evidence |
| --- | --- |
| Known capability resolves only to configured registered adapter | Explicit trusted immutable composition; Success contains exact supplied instance; known unregistered/unavailable/not_checked cases fail; fake-only resolution and fresh-wheel checks passed |
| Unknown/invented capability rejected | Finite CapabilityId; run_command/binary/path/shell/import-shaped names return planner_validation_failed; ActionRequest wire intent stays data; no registration/import/runner call |
| Duplicate/conflicting entries fail clearly | Canonical ConfigurationError with safe identity context; same instance/duplicate ID/conflicting owner/permutations/malformed definition regressions passed |
| Unavailable tools structured outcomes | Existing ToolUnavailableError/ErrorInfo/Failure for unregistered, unknown adapter, unavailable/not_checked; declared availability catalog distinguishes states without probing |
| Catalog has no executable secret paths exposed | Explicit four-field projection, strict extra-field rejection, deliberately private fake internals excluded, stable JSON round trips/order and immutable returned tuples/models verified |

Additional user criteria: strict schema references and metadata, finite risk reporting
without enforcement, nested import-key rejection, immutable snapshots, no globals/
PATH discovery/dynamic imports/config-defined commands, and no registry execution
all verified. No action-policy approval, session budgets/rate/concurrency implementation,
real scanner/parser, Groq/planner runtime, orchestration, persistence/reporting or real
CLI added. No new follow-up task/blocker; descendant cleanup remains the documented
M1-T03 limitation in existing future work.

M0-T01–M0-T06 and M1-T01–M1-T04 are DONE. Both M1-T05 prerequisites are DONE and it
alone becomes READY; all 81 later tasks remain NOT STARTED. No active task/blockers.
Stop after M1-T04; M1-T05 has not begun.

Commit reference: the single focused commit containing this entry, titled
`feat(tools): establish capability and tool registry`; resolve with
`git log -1 --format=%H --grep="^feat(tools): establish capability and tool registry$"`.
Established convention avoids invented circular self-hash, amendment or second task
commit. Final handoff reports actual full hash and verified clean tree. No push.

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

## 2026-10-05 — M1-T05 — Action policy validator

Status: DONE

Objective: Decide action eligibility deterministically through trusted registry,
centralized scope, registered schemas and explicit capability/risk policy without
execution or planner authority.

Startup: Followed AGENTS and recon-project-maintainer skill/references; inspected
state/current task, M1-T05 and adjacent PLAN boundaries, security/architecture/tool/
planner/error/execution/scope/data/config/testing/audit docs, ADRs, recent history,
then Git status/working/index diff/log and relevant source/tests. HEAD matched
481d23fd0df84a7dbc5be4c12bb1274610377abe. M0-T01–M0-T06/M1-T01–M1-T04 DONE, only
M1-T05 READY, clean tree/index and no active task/blocker. Set only M1-T05 IN PROGRESS
before implementation; no unrelated changes existed.

### Implementation and decisions

- policy/actions.py adds explicit frozen ActionPolicyConfig (finite capability/risk
  allowlists, empty defaults), ActionPolicyValidator and internal ApprovedAction.
  validate revalidates ActionRequest, checks available registry facts, capability/
  risk allowlists, primary/secondary scope and registered strict parameter schema.
  No reason/priority/analysis/discovery field can grant permission.
- Reuses Success[ApprovedAction]/Failure/ErrorInfo and existing canonical error
  taxonomy. Invalid/unsupported/disallowed intent and missing completed-action
  semantics use planner_validation_failed; registry availability retains
  tool_unavailable; centralized scope failures retain scope_rejected/context;
  missing budget eligibility returns budget_exhausted. Messages are fixed, without
  planner text, raw inputs or native validation errors. Callers correlate Failure
  with their request; approval includes action_id/capability/matches.
- ToolRegistry.capability_definition supplies available snapshotted definition
  facts without resolving or accessing adapter objects. Existing resolve uses the
  same private availability lookup; registry semantics and catalog projection are
  preserved. No registration, probing, binary selection or dynamic loading.
- AdapterDefinition.parameter_target_fields records trusted secondary-target
  semantics. None (default) denies policy approval; explicit () asserts no secondary
  network inputs. Named fields must be unique schema fields, with validated string
  or list/tuple-of-string values; other target representations deny. Every value,
  including schema defaults, passes centralized scope. Future schema owners must
  declare all target inputs and keep nested/default validation strict and pure.
  No scanner-specific schema or destination guessing is added.
- ScopeValidator.validate_value classifies ActionRequest target text using syntax
  delimiters and invokes its existing parser/membership; no duplicated hostname/IP/
  CIDR/URL matching, DNS or authorization logic. Current ActionRequest always has a
  primary network target; no unsupported target-less capability exemption is invented.
- PLAN explicitly requires restrictive budget/completed-action interfaces now;
  ActionEligibility.check returns OperationResult[None]. Missing services deny and
  malformed outcomes reject. Permitting fakes exist only in tests. No budget
  accounting/rates/concurrency/reservation/session clocks (M1-T06) or canonical action
  identity/history/dedup/retry logic (M1-T08) is implemented. These are seams only.
- Approval contains a trusted typed parameter model excluded from dumps/repr and
  canonical scope matches; it is not a dispatch/replay token. Future dispatch must
  revalidate the original request against current policy/availability/scope and
  reserve resources atomically, then constrain/revalidate actual contact. Test-only
  dispatch models stale budget eligibility and proves rejected requests stay untouched.
- ADR 0004 records explicit policy injection, fail-closed parameter-target semantics,
  restrictive pending interfaces and current-eligibility versus dispatch boundary.
  No execution/network/DNS/Groq/logging/audit producer exists in validation; no
  tool.execution_started event. Domain wire contracts, configuration loader, error/
  result taxonomy, runner, CLI, dependencies and future subsystems are unchanged.

Files: added policy/actions.py, tests/unit/policy/test_action_policy.py and ADR 0004;
updated policy exports/scope text entry point, tools/base.py metadata and tools/
registry.py fact lookup. Updated security/architecture/tool/planner/execution/data/
error/scope/configuration/logging/testing documentation, README/CHANGELOG and lifecycle
files. TASK_HISTORY is appended only. No generated artifacts or unrelated files staged.

### Executed validation

Repository .venv used unless noted. Python 3.14.6 / Pydantic 2.13.5; no Python 3.12
run is claimed.

| Check | Actual command/result |
| --- | --- |
| Setup | `.venv/bin/python --version`; `pip install -e ".[dev]"`; `pip check`: passed |
| Focused policy | `pytest tests/unit/policy/test_action_policy.py`: initial 97 passed; final expanded module has 103 cases |
| Focused combined | `pytest tests/unit/policy/test_action_policy.py tests/unit/tools tests/unit/test_scope.py`: 309 passed (103 policy + 98 registry + 108 scope) |
| Full suite | `pytest`: 1,167 passed |
| Coverage | `coverage run -m pytest`: 1,167 passed; `coverage report`: 99% overall, 1,132 statements / 288 branches; new action policy/base/registry 100%; only existing scope.py:113 defensive unsupported-kind line/branch missing |
| Network/DNS-blocked | `/tmp/recon-m1t05-validation/offline.py`: 1,167 passed; Groq key removed, Internet/loopback contact and DNS blocked before collection, guard rejection self-checks passed |
| Ruff/format/types | `ruff check .`, `ruff format --check .`: passed (73 files); `mypy src/recon_agent`: strict pass, 33 production modules; no weakening, ignores or casts |
| Build/CLI | `python -m build`: setuptools 84.0.0 isolated sdist/wheel passed; rebuilt after final README state to preserve archive metadata parity. Editable/fresh-wheel `recon-agent` retain unchanged inert message, exit 0 |
| Fresh wheel | External new `/tmp/recon-m1t05-validation/wheel-venv`, wheel install and pip check; isolated `python -I -B wheel_checks.py`: guarded cold imports/site-packages origins, registry catalog, typed policy approval/denials/defaults/determinism and no startup/runner/network/provider activity passed |
| Security/artifacts | Temporary artifact_checks.py: policy AST has no execution/network/provider/dynamic-loading entry points; protected core/domain/runner/CLI/future subsystem byte parity; unchanged Pydantic-only dependency; no scanner implementations; secret/cache/generated-artifact scans; wheel/sdist source/README/dependency parity passed |
| Git/reconciliation | Working/index diff, `git diff --check`, task status/dependency/history-prefix/Markdown local-link and final staged task-owned-path inspection passed before single commit |

Development checks caught a Pytest reserved parametrization name and Mypy needing
an explicit result annotation after runtime eligibility-result revalidation; corrected
without changing acceptance or weakening typing. Ruff applied task-owned formatting.
Final target metadata defaults were tightened from implicit no-targets to explicit
unestablished/deny before final focused/full checks; regression covers missing facts.
No unresolved validation failure or product blocker remains.

The full-suite parent contact guard allows AF_UNIX event-loop self-pipes for existing
local runner tests; it does not sandbox children. Existing harmless interpreter child
scripts were inspected for no networking. Unit policy guards also block socket
construction, subprocess/async spawn/runner and registry adapter resolution; tests
block dynamic imports, adapter properties and logging in the snapshot check.
Fresh-wheel cold-import guards block process/network/DNS/database/thread/logging/
filesystem startup while allowing standard dependency metadata reads. Installation/
build provisioning may access package indexes; product validation needs no credentials,
live target or reconnaissance binaries.

### Acceptance and handoff

| PLAN criterion | Evidence |
| --- | --- |
| Unknown capability, outside target, invalid/extra parameters, forbidden risk, insufficient budget and needless repeat denied | Canonical registry/scope/schema/allowlist checks; fake denying budget/completed services and restrictive defaults; 103-case policy matrix and installed wheel checks passed. Budget/dedup implementations remain their owning tasks |
| Allowed action produces typed validated request | Success[ApprovedAction] includes ID/capability/canonical matches/registered Parameters model; deterministic repeated outcomes, snapshot/default/secondary-target cases passed |
| Fake execution never receives denied requests | Test-only dispatch receives nothing for unknown/outside/schema-invalid intent and stale eligibility; adapter/runner/process/network guards remain untouched |
| Pending budget/dedup interfaces restrictive until implemented | Missing budget/completed-action checks deny; no production allowing stub; malformed seam outcomes reject; no resource counters/canonical duplicate logic added |

Additional user criteria: primary/secondary/malformed/redirect/discovered candidates
check scope independently; permitted/disallowed capability/risk policies are explicit;
reason/priority/analysis variations cannot change denial; nested executable/import keys
reject after bypassed construction; actual domain source/AI-facing fields unchanged;
no execution/network/DNS/scanner/Groq/audit emission; no duplicate error/result system.
Focused, full, offline, lint/format/types/coverage/build/wheel/inert CLI/security checks
passed. Documentation distinguishes planner recommendation, registration and scope
membership from complete authorization and records future dispatch revalidation.

M0-T01–M0-T06 and M1-T01–M1-T05 are DONE. M1-T06 prerequisite gate is satisfied and
it alone becomes READY; all 80 later tasks remain NOT STARTED. No active task or
blockers. No new follow-up task; budgets/dedup/dispatch/contact constraints remain
assigned existing future work. Stop after M1-T05; M1-T06 has not begun.

Commit reference: the single focused commit containing this entry, titled
`feat(policy): validate reconnaissance actions`; resolve with
`git log -1 --format=%H --grep="^feat(policy): validate reconnaissance actions$"`.
No circular self-hash, amendment or second task commit. Final handoff reports actual
full commit hash and verified clean tree. No push.

## 2026-10-05 — M1-T06 — Execution budgets and rate limiting

Status: DONE

Objective: Bound work and traffic independently of planner recommendations through
local atomic resource reservations without scanners or autonomous orchestration.

Startup: Followed AGENTS, recon-project-maintainer skill and its lifecycle/validation
references. Read state/current task, M1-T06/adjacent PLAN boundaries, architecture/
security/config/tool/execution/policy/error/result/audit/scope/data/planner/testing
docs, ADRs and recent history before inspecting Git status, both diffs/log and
relevant source/tests. HEAD matched 6ee48a7b675c37c4fa12fcedae1e154278d7f860; clean
tree/index, all prerequisites DONE, only M1-T06 READY, no active task/blocker.
Marked only M1-T06 IN PROGRESS before implementation. No unrelated changes existed.

### Implementation and decisions

- Added policy/budgets.py: frozen strict ExecutionBudget limits, detached frozen
  BudgetState snapshots, explicitly composed session-local BudgetController,
  synchronous BudgetPermit ownership and finite ReservationOutcome counters.
  No global ledger, config reads, reset/refund/limit-update API or state import.
- Extended ExecutionConfig/example with positive max_actions_per_host (10),
  capability_rate_actions (1), capability_rate_window_seconds (1.0) and
  max_session_output_bytes (16 MiB). Existing source precedence/validation is reused.
  ExecutionBudget.from_config revalidates/snapshots all relevant execution settings;
  later config edits cannot raise the controller's limits. No planner fields changed.
- ActionPolicyValidator budget seam now uses BudgetEligibility.check(ApprovedAction),
  consuming already validated canonical primary/secondary matches including schema
  defaults, without repeating registry/schema/scope authorization. Completed-action
  ActionEligibility remains request-based and restrictive until M1-T08. Approval
  instance revalidation is enabled. Policy authorization != budget availability.
- ScopeMatch.host_identity reuses centralized parsing: DNS case/trailing dots, URL
  scheme/port/path variants and canonical IP/IPv6 URL literals share host accounting.
  No DNS/address equivalence is inferred. All distinct declared hosts count once
  per permitted attempt. CIDRs fail closed without concrete-host accounting; future
  range adapters must bound independently authorized concrete work, never one range
  bucket. Existing scope membership and domain wire contracts are unchanged.
- check is advisory and consumes nothing. reserve rechecks action/concurrency/host/
  rolling capability rate/time/output allowance under one local lock without await.
  Buckets exist only for explicitly registered capabilities. One selected registry
  adapter per capability gives a per-tool execution-rate foundation; no request/
  packet-rate or scanner-specific traffic guarantee is claimed. Exact window
  boundary expires entries in (now-window, now]; injectable monotonic clock avoids
  real waiting. Invalid/backward/error clocks permanently exhaust session time.
- Granted reservations permanently charge one permitted attempt, each distinct host,
  one capability timestamp and two per-stream worst-case output allowances. Rejected
  requests/checks charge nothing. Aborted/failed/cancelled/timed-out attempts retain
  charges; every retry must reserve/pay again. Only concurrency is released.
  Conservative counting prevents failures from replenishing traffic/output budgets.
- Context exit releases concurrency once on normal/exception/timeout/cancellation
  paths and records typed outcome counts. Cleanup is synchronous and cannot be
  interrupted by repeated task cancellation at an await. Explicit release is
  idempotent; invalid outcomes and released/nested context entry reject. Abandoned
  ownership is a caller error, not an implicit GC refund. Tests exercise real async
  cancellation only against Event-based fake work, not a scanner/runner.
- State supplies expired/remaining_seconds without timers or running-work interrupts.
  M1-T03 capture is unchanged. M1-T06 reserves aggregate output allowance only;
  future dispatch must use same/smaller stream bounds, remaining-time deadlines,
  immediate permit ownership and one reservation per execution. Default output
  envelope permits eight full allowances independent of the 100-attempt ceiling.
  Positive too-small envelopes reject all work without expanding limits.
- Existing Success/Failure/ErrorInfo/BudgetExhaustedError encode resource outcomes;
  fixed safe messages and conservative retryable=false are retained. Invalid initial
  controller limits/clock use ConfigurationError. No new errors/audit producer,
  process/network/DNS/scanner/Groq/dynamic loading/shell, deduplication/state machine,
  worker/orchestrator, persistence/reporting or operational CLI is added. A permit
  is resource ownership, never authorization; future dispatch revalidates policy.
- ADR 0005 documents atomicity, permanent attempt/output accounting, rolling windows,
  normalized target seam and ownership choices. ADR 0004 notes the budget-seam
  evolution without rewriting its initial decision. Relevant docs, README, changelog,
  state/current task and PLAN are reconciled; history is appended only.

Files: new policy/budgets.py, tests/unit/test_budgets.py (78 cases),
docs/execution-budgets.md and ADR 0005; updated config model/example, policy exports/
actions/scope, ADR 0004, architecture/security/config/execution/tool/data/error/scope/
planner/audit/testing docs and lifecycle/README/changelog. Registry, runner, shared
error/result/audit contracts, config loader, domain/planner wire models, CLI, runtime
dependencies and future subsystem source are unchanged. No artifacts/secrets staged.

### Executed validation

Repository .venv unless noted; Python 3.14.6 / Pydantic 2.13.5. Python 3.12 was not
executed; no broader runtime compatibility claim is made.

| Check | Actual command/result |
| --- | --- |
| Setup | `.venv/bin/python --version`; `pip install -e ".[dev]"`; `pip check`: passed |
| Focused final | `pytest tests/unit/test_budgets.py tests/unit/policy/test_action_policy.py tests/unit/test_config.py -q`: 246 passed (78 budget + 103 action policy + 65 config) |
| Full final | `pytest -q`: 1,245 passed |
| Coverage final | `coverage run -m pytest -q`: 1,245 passed; `coverage report`: 99% overall, 1,355 statements / 336 branches; budget and action policy 100%; only existing defensive scope.py:121 unsupported-kind line/branch missing |
| Network/DNS-blocked final | `/tmp/recon-m1t06-validation/offline.py`: 1,245 passed; key absent, Internet/loopback contact and DNS blocked before collection; guard self-checks passed |
| Lint/format/types | `ruff check .`, `ruff format --check .`: passed, 77 files; `mypy src/recon_agent`: strict pass, 34 modules; no suppressions or weakened checks |
| Build/CLI | `python -m build`: isolated sdist/wheel passed; rebuilt after final README state; editable and external installed-wheel `recon-agent`: unchanged inert message, exit 0 |
| Fresh wheel | New external `/tmp/recon-m1t06-validation/wheel-venv`; wheel install and pip check passed. Isolated `python -I -B wheel_checks.py`: guarded cold imports/site-packages origins, policy/registry and real budget snapshot/check/reservation/release/exhaustion passed; final rebuilt wheel reinstalled/rechecked |
| Security/artifacts | Temporary artifact_checks.py: policy/resource AST no execution/network/provider/dynamic imports/global ledger/timer/thread startup, protected-source byte parity, no new planner fields/scanners, unchanged Pydantic-only direct dependency, secret/generated-artifact scans and wheel/sdist source/README/dependency parity passed |
| Git/reconciliation | Working/index/final diffs and whitespace, exact authorized PLAN transitions/dependencies, append-only history, coherent state/current task, local Markdown links/fences and task-owned staged paths inspected before the single commit |

Development checks caught a forward annotation, typed callable tuple, overly narrow
annotation for a runtime malformed-input guard, test fixtures using tuple data where
ActionRequest requires JSON lists, and an interfering host limit in a rate-specific
fixture. Corrected within scope without relaxing acceptance. Documentation diff
inspection caught an editing script's inherited buffer; original reference contents
were restored and only their task sections applied. Final checks above supersede
those development failures; no unresolved validation failure/blocker remains.

Network guard permits AF_UNIX event-loop self-pipes for existing harmless local
runner tests and fake async ownership tests. Parent guards do not sandbox children;
existing local interpreter scripts were reviewed for no networking. Fresh-wheel
cold-import guards prohibit network/DNS/process/database/thread/logging/filesystem
startup while allowing dependency metadata reads. Installation/build provisioning
may access package indexes; product validation needs no credentials/live targets.

### Acceptance and handoff

| PLAN criterion | Evidence |
| --- | --- |
| Every specified limit enforceable with documented counting | Strict frozen settings and locked action/concurrency/host/rate/time/output checks; exact boundary/read-only/retry/default-host/CIDR/output tests and budget docs/ADR |
| Concurrent requests cannot oversubscribe | Twelve simultaneous offline contenders per action/concurrency/host/rate/output dimension, all sharing one ledger; exactly three reservations granted and released |
| Exhaustion prevents dispatch | Canonical budget failures; policy-approved stale action rejected by reserve/current policy, unknown buckets deny, adapter/runner/process/contact guards untouched |
| Timeout/cancellation release/account correctly | Typed outcome counts, permanent attempt/host/rate/output charges, real repeated async cancellation, timeout/session expiry, exception/idempotent/non-nested cleanup tests; active count returns to zero |
| Planner cannot extend budgets | Frozen limits/controller/snapshots, config-copy isolation and no reset/refund API; reason/priority injection tests, unchanged planner/action fields and protected source checks |

All focused/full/offline/lint/types/coverage/build/wheel/inert CLI/artifact/secret/Git
checks passed. No process capture duplication; budget layer never executes anything.
No new follow-up task or blocker; future contact/running-work/dedup/state obligations
remain in existing owning tasks. M0-T01–M0-T06/M1-T01–M1-T06 DONE; M1-T07 alone READY
and unstarted; remaining 79 tasks NOT STARTED. No active task. Stop after M1-T06.

Commit reference: the single focused commit containing this entry, titled
`feat(policy): add execution budgets and rate limits`; resolve using
`git log -1 --format=%H --grep="^feat(policy): add execution budgets and rate limits$"`.
Final handoff reports its actual hash and verified clean tree. No amendment, second
task commit, history rewrite or push.


## 2026-10-05 — M1-T07 — ReconState state machine

Status: DONE. M1-T07 alone progressed READY → IN PROGRESS → DONE; M1-T08 alone
becomes READY, unstarted. Dependencies M1-T06/M0-T04 and predecessors were DONE.
Starting HEAD: 74e4f4c64671f3b6733364b070cd91571bacc2da; clean tree/index and no
active task/blocker. Startup followed AGENTS/maintenance skill and reviewed the
roadmap, subsystem docs/ADRs, history, current contracts/source/tests and Git evidence.
The interrupted run's implementation survived; resumed closeout preserved it and
reran required validation rather than reimplementing or starting M1-T08. The earlier
reported 1,407 full/offline count precedes the final integration test; final actual
full, coverage and network/DNS-blocked runs each contain 1,408 tests.

### Objective, changes and decisions

Own consistent authoritative in-memory state through explicit validated transitions,
with evidence/action/planner/budget histories and no operational execution.

- ReconState is a strict frozen tuple snapshot. ReconStateMachine owns one defensive
  copy and a local lock. Each operation validates a complete candidate and prepares
  detached committed/returned copies before atomic swap; failure leaves prior state
  unchanged. Initial/serialized/model-copy inputs revalidate the same invariants.
  Ordinary nested JSON in returned snapshots remains editable but cannot mutate the
  owner. No hidden global state, generated IDs/times or environment dependency exists.
- ActionLifecycle/ActionTransition/ActionPhase store explicit supplied UTC history:
  requested → approved → started → existing terminal outcomes, with documented
  rejection/cancellation branches. Partial remains distinct. Invalid/skipped/backward
  edges, terminal repeats, malformed metadata/times, orphan results and conflicting
  action/result/execution identities reject. One started action owns one execution
  identity and terminal result; retries/equivalence remain M1-T08 and are not added.
- Atomic related subject/observation/evidence ingestion validates known references,
  subject ownership and provenance. Terminal ActionResult/facts/history commit together;
  conflicting existing fact payloads reject. Failed/rejected/cancelled/timeout outcomes
  cannot claim observations. Known unfinished/unsuccessful execution provenance also
  cannot support observations indirectly through evidence. Unknown external provenance
  stays opaque; no scanner parsing, finding generation, DNS or scope expansion occurs.
- PlannerDecision recording adds a recommendation only, with input lineage. It cannot
  enqueue, approve, execute, stop sessions, change scope or consume/raise budgets.
  Explicit decision-linked requests must match supplied recommendations. Approval
  references/execution IDs are caller-authored historical facts, never replay tokens;
  future dispatch still validates policy and reserves resources independently.
- Existing BudgetState/ReservationOutcome pure contracts move to domain and remain
  re-exported from policy. Strict frozen structural validation and timestamped
  BudgetSnapshot preserve caller-sampled facts. State records samples and canonical
  budget rejection results; it does not call/reset/restore controllers or infer counts.
  ExecutionBudget, BudgetController, BudgetPermit, _Usage and clock/denial enforcement
  AST are identical to the preceding commit. M1-T06 retains all resource arithmetic.
- Minimal canonical StateTransitionError extends ReconAgentError with one state code/
  category, fixed safe transition messages and non-retryable Failure/ErrorInfo results.
  Invalid initial state raises the same error with native cause chaining; state errors
  cannot masquerade as failed/partial tool results. No parallel error hierarchy or
  error-context/audit event field is added; domain produces no logs/audit side effects.
- ADR 0006 documents ownership/atomicity/alias isolation, explicit history and pure
  budget recording. Python legacy list snapshots now require tuple conversion and
  explicit lifecycle records; no prior permission is inferred. Whole-state validation/
  copying favors integrity over large-session performance. ReconSession remains
  structural composition; session startup/stop/resume belongs to future orchestration.

Files: new domain/state.py, lifecycle.py, budgets.py, tests/unit/test_state.py (161
cases), docs/state-transitions.md and ADR 0006; updated domain session/action exports,
minimal core errors, policy budget imports, domain/error regressions, architecture/
data/security/error/budget/tool/audit/testing docs and README/changelog/task records.
Registry, scope policy, runner/process bounds, configuration, shared result/audit/
logging infrastructure, CLI, dependencies and future subsystem code are unchanged.
ActionRequest/PlannerDecision definitions are unchanged; identity/reference checks
are not semantic action deduplication. No scanner/provider/loop/persistence/reporting/
real CLI work or future-task implementation is present. No artifacts/secrets staged.

### Executed final validation

Repository .venv unless noted: Python 3.14.6 / Pydantic 2.13.5. Python 3.12 was not
executed; no broader runtime testing claim is made.

| Check | Actual command/result |
| --- | --- |
| Environment | `python --version`: 3.14.6; editable development environment and `pip check`: passed |
| Focused | `pytest tests/unit/test_state.py tests/unit/test_domain.py tests/unit/test_errors.py tests/unit/test_budgets.py -q`: 480 passed, including 161 state cases |
| Full | `pytest -q`: 1,408 passed |
| Coverage | `coverage run -m pytest -q`: 1,408 passed; `coverage report`: 99% overall, 1,622 statements / 456 branches. New state/lifecycle/budget-snapshot and session validation modules 100%; budget/action policy 100%; only existing scope.py:121 defensive unsupported-kind line/branch missing |
| Network/DNS blocked | `/tmp/recon-m1t07-validation/offline.py`: 1,408 passed; key absent, Internet/loopback contact and DNS blocked before collection; contact/DNS guard self-checks passed |
| Lint/format/types | `ruff check .`, `ruff format --check .`: passed (83 files); `mypy src/recon_agent`: strict pass, 37 source modules; no weakened settings/suppressions |
| Build/CLI | `python -m build`: isolated sdist/wheel passed after final README lifecycle reconciliation; editable and external installed-wheel `recon-agent`: unchanged inert message, exit 0 |
| Fresh wheel | External `/tmp/recon-m1t07-validation/wheel-venv`; wheel install/pip check passed; final wheel reinstalled after rebuild. Isolated `python -I -B wheel_checks.py` from outside checkout: guarded cold imports/site-packages origins, registry/policy/budget and state lifecycle/rollback/serialization/alias checks passed |
| Security/artifacts | Temporary artifact_checks.py: operational import/call AST checks, unchanged planner wire definitions and budget enforcement AST, protected source parity, scanner/future implementation absence, Pydantic-only dependency, secret/generated-artifact scans and wheel/sdist source/README/metadata parity passed |
| Reconciliation/Git | Final working/index diffs, whitespace, exact authorized PLAN transitions/prerequisite gates, append-only history, local Markdown links/fences and task-owned paths inspected before the one focused commit |

Focused guards prohibit socket/DNS/subprocess/runner/adapter resolution/dynamic import/
logging startup. Full offline guard permits AF_UNIX event-loop self-pipes for existing
harmless local runner and fake async cancellation tests; it does not sandbox child
interpreters, whose existing scripts were reviewed for no networking. Fresh-wheel
cold-import guards prohibit process/contact/database/thread/logging/filesystem startup,
allowing dependency metadata reads. Installation/build provisioning may access indexes;
product checks require no scanner binaries, live targets or provider credentials.

Development checks corrected strict tuple/enum budget JSON/Python round trips, typed
validation annotations and test fixtures without weakening acceptance. Final results
above supersede development failures; no unresolved failure or blocker remains.

### Acceptance and handoff

| PLAN criterion | Evidence |
| --- | --- |
| Invalid transitions rejected | 81-edge lifecycle matrix, malformed initial/history/result cases, canonical structured failures and all-terminal re-entry protection |
| Successful observations retain provenance | Atomic related fact/result ingestion; preserved source/time/artifact/execution/evidence payloads, reference and subject ownership tests |
| Failed/rejected actions never become successful facts | Existing terminal result restrictions plus known unsuccessful/unfinished execution attribution denial, including indirect evidence; failed-result history preserved without observations |
| Assets/history/budgets update coherently | Whole candidate validation/rollback, nested alias isolation, simultaneous local commits, real policy/budget sampling and resource-denial integration with unchanged controller accounting |
| Serialization preserves distinctions | Deterministic Python/JSON round trips for complete failed/partial/rejected histories, planner input lineage and nonempty budget buckets; explicit UTC inputs |

All required focused/full/offline/lint/types/coverage/build/wheel/CLI/security/artifact/
secret/Git checks passed. State never invokes execution/network/DNS/scanner/Groq or
imports operational policy. Planner recording remains non-authoritative; no action
semantic deduplication or budget reimplementation is present. No new follow-up task
or blocker. M0-T01–M0-T06 and M1-T01–M1-T07 DONE; M1-T08 alone READY, unstarted;
remaining 78 tasks NOT STARTED. No active task. Stop after M1-T07.

Commit reference: the single focused commit containing this entry, titled
`feat(state): add controlled recon state transitions`; resolve using
`git log -1 --format=%H --grep="^feat(state): add controlled recon state transitions$"`.
Final handoff reports its actual hash and verified clean tree. No amendment, second
task commit, history rewrite or push.


## 2026-10-05 — M1-T08 — Action deduplication

Status: DONE. M1-T08 alone progressed READY → IN PROGRESS → DONE; M2-T01 alone
becomes READY and remains unstarted. Dependencies/predecessors were DONE.
Starting HEAD: f6ba31a18c85bf64d80806c92a4aa52c792cfcb0; clean working tree/index,
no active task/blocker. Startup followed AGENTS/maintenance skill and inspected
state/roadmap, subsystem docs/ADRs/history, Git and current contracts/source/tests.
Repository evidence matched the expected prerequisite state. No unrelated work existed.

### Objective, changes and decisions

Prevent unnecessary equivalent planner work through deterministic semantic identity,
existing authoritative history, explicit bounded failed retries and policy/state seams.

- Domain ActionIdentity encodes version action-v1, finite capability, canonical target
  kind/value and full sorted compact parameter JSON. Its key uses an unambiguous full
  JSON envelope, no digest collisions or delimiter/stringification tricks. New pure
  ActionDedupDecision/DedupReason provide typed normal outcomes inside existing
  Success/Failure; planner fields, IDs, timestamps and lineage metadata are excluded.
- ActionCanonicalizer shares strict registered-schema and primary/secondary scope
  validation with ActionPolicyValidator; no allowlist/approval/budget/adapter execution
  occurs. Actual validated defaults/nested fields are included even when serialized
  dumps exclude them. Object order collapses; ordered arrays and JSON scalar types,
  non-target text and execution-relevant changes stay distinct. Unsupported non-JSON,
  non-string keys and nonfinite values deny. Existing target case/dot/IP/CIDR/authority
  aliases collapse; URL resources and authorization semantics are unchanged, without DNS.
- ActionDeduplicator reads only existing ReconState request/lifecycle/result history;
  there is no second history, cache or retry counter. Requested/approved/started and
  completed equivalence denies. Rejected/partial/cancelled/timeout equivalence denies.
  Explicit trusted frozen ActionDedupConfig defaults max_failed_retries to zero.
  Only all-failed equivalents with every recorded ErrorInfo.retryable true may retry,
  at most one initial attempt plus N configured retries. New service instances/IDs/
  prose cannot reset that count. All failures and evidence distinctions remain intact.
- Read-only inspect returns canonical identity, sorted matching IDs, failed count,
  typed reason and computed duplicate/eligible. Retry eligibility remains equivalent
  work, not success or authorization. Historical same-capability requests that cannot
  canonicalize under fixed trusted contracts fail closed with fixed safe errors.
- Atomic record_request adds a pure eligibility callback to the existing state owner's
  request recording lock. Detached callback data and validated OperationResult[None]
  preserve ownership/rollback. Concurrent equivalent new/retry submissions admit one
  REQUESTED record, with no approval/execution/resources. Low-level raw state recording
  remains available for trusted rejection histories; state imports no operational policy.
- Existing completed_action_eligibility seam uses the real checker. Policy revalidation
  excludes only its own semantically unchanged requested/approved entry. Competing
  equivalents, changed same-ID semantics and all started/terminal IDs deny. Retry
  requests need new IDs and full current policy; actual future execution pays a new
  budget reservation. Dedup uses existing planner_validation_failed for policy denial;
  no error/result hierarchy or authorization token is introduced.
- ADR 0007 and the M1-T08 PLAN retry contract document the explicit conservative
  assignment where prior docs had no retry configuration. Broader recovery classes,
  timeout/partial/rejection reconsideration and automatic retries remain later work.
  No force-rerun/TTL/reset/remote-defined semantics, session startup or loop is added.

Files: new domain/identity.py, policy/dedup.py, tests/unit/policy/test_dedup.py (104
cases), docs/action-deduplication.md and ADR 0007; minimal shared policy input helper,
state admission and domain/policy exports; deliberate domain public API regression;
architecture/data/security/state/tool/planner/testing docs, README/changelog/task records.
Runner, registry/adapters, scope semantics, configuration/loader, budget enforcement,
shared errors/results/audit/logging, ActionRequest/PlannerDecision/ReconState schemas,
CLI/dependencies and all future subsystem source remain byte-identical to starting HEAD.
No M2-T01 or later implementation, new follow-up task, generated artifact or secret.

### Executed final validation

Repository .venv unless noted: Python 3.14.6 / Pydantic 2.13.5. Python 3.12 was not
executed; no broader runtime claim is made.

| Check | Actual command/result |
| --- | --- |
| Environment | `python --version` and `.venv/bin/python --version`: 3.14.6; `python -m pip install -e '.[dev]'` through .venv and pip check passed |
| Focused | `pytest tests/unit/policy/test_dedup.py tests/unit/policy/test_action_policy.py tests/unit/test_state.py -q`: 368 passed, including 104 new dedup cases |
| Full | `pytest -q`: 1,512 passed |
| Coverage | `coverage run -m pytest -q`: 1,512 passed; `coverage report`: 99%, 1,794 statements / 522 branches; identity/state/action-policy/budget 100%, dedup 99% |
| Network/DNS blocked | `/tmp/recon-m1t08-validation/offline.py`: 1,512 passed; Groq key absent, Internet/loopback contact and DNS blocked before collection; guard self-checks passed |
| Lint/format/types | `ruff check .`, `ruff format --check .`: passed (88 files); `mypy src/recon_agent`: strict pass, 39 production modules; no suppressions/settings weakened |
| Build/CLI | `python -m build`: isolated sdist/wheel passed; editable and external fresh-wheel recon-agent print unchanged inert status and exit 0 |
| Fresh wheel | New external `/tmp/recon-m1t08-validation/wheel-venv`, wheel install/pip check passed; isolated `python -I -B wheel_checks.py` from outside checkout verified guarded cold imports, installed module origins, canonical identity/dedup/failed retry and real policy/budget/state composition without runtime side effects |
| Security/artifacts | Temporary artifact_checks.py: operational import/call AST, planner-field exclusion, protected source/contract byte parity, absence of future implementations, Pydantic-only runtime dependency, artifact/secret scans, wheel/sdist source/README/metadata parity passed |
| Final reconciliation/Git | Task-owned working/index diff and whitespace review; exact authorized readiness/prerequisite gates, appended history and local Markdown link/fence checks before one focused commit |

Coverage's only uncovered new line/branch is dedup.py's defensive rejection of a
domain-kind action target, unreachable through current concrete ScopeValidator
classification; existing scope.py unsupported-kind guard also remains uncovered.
No coverage gate was weakened. Focused runtime guards forbid sockets/DNS/subprocess/
runner/adapter resolution/dynamic imports/logging. Full offline guards permit AF_UNIX
loop self-pipes only; they do not sandbox existing harmless local interpreter children,
whose scripts were statically checked to contain no networking. Fresh-wheel imports
prohibit process/contact/database/thread/logging/filesystem startup, permitting
read-only dependency metadata. Installation/build provisioning may access indexes.

Development runs exposed four malformed-admission error-code expectations and the
existing deliberate domain-export assertion. Service admission now revalidates
malformed intent with the existing planner boundary before entering the state owner;
its own state boundary/rollback remains unchanged. The export assertion includes the
three new intended public contracts. Review also prevented reuse of terminal IDs
under a configured failed retry. Final focused/full/coverage/offline/lint/type/build/
wheel/security checks passed after corrections; no unresolved validation failure.

### Acceptance and handoff

| PLAN criterion | Evidence |
| --- | --- |
| Equivalent authorized requests collapse despite representation/order | Shared strict policy input validation, canonical primary/secondary/default targets, cosmetic planner loop regression and nested/key-order/serialization tests |
| Distinct meaningful parameters remain distinct | JSON type/array/non-target text preservation; capability/target/count/secondary/options distinctions; hidden/default/nested schema tests |
| Completed/in-flight duplicates deny dispatch | Lifecycle table, policy denial with runtime guards, own pending revalidation/changed semantics/terminal replay tests; atomic new/retry contenders admit one request |
| Failed actions retry only within configured limits | Default-zero/strict explicit config, every lifecycle/error flag table, one initial plus N failure accounting, service reconstruction and shared-owner concurrent retry tests |
| No alternate target spelling policy bypass | Existing ScopeValidator only, accepted aliases dedup, malformed/outside primary/secondary failures and preserved URL distinctions; no DNS or scope widening |

Dedup does not authorize, consume resources or execute; real policy/budget isolation
and runtime/static guards prove those boundaries. All required validation passed.
M0-T01–M0-T06 and M1-T01–M1-T08 DONE: M0 and M1 complete. M2-T01 alone READY and
unstarted; remaining 77 tasks NOT STARTED. No active task/blocker. Stop after M1-T08.

Commit reference: the single focused commit containing this entry, titled
`feat(state): add deterministic action deduplication`; resolve with
`git log -1 --format=%H --grep="^feat(state): add deterministic action deduplication$"`.
Final handoff reports the actual hash and clean tree. No amendment, second task
commit, history rewrite or push.

Closeout crossed the local date boundary: work started 2026-10-05 and the final
reconciliation/commit handoff occurred 2026-10-06 (Asia/Ho_Chi_Minh). The entry's
2026-10-05 heading records the start date; no prior history entry is rewritten.

## 2026-10-06 — M2-T01 — DNS resolver capability

Status: DONE. M2-T01 alone progressed READY → IN PROGRESS → DONE; M2-T02 alone
becomes READY and remains unstarted. M0/M1 dependencies were DONE. Starting HEAD:
31cf476ed4974653d50ac043267c811c34b36076; clean working tree/index, no active task or
blocker. Ordered startup inspected AGENTS/maintenance skill, state/roadmap, relevant
architecture/security/tool/execution/scope/state/budget docs and ADRs, history, Git,
contracts/source/tests/config. Repository evidence matched the expected prerequisite
state; no unrelated changes existed.

### Objective, implementation and decisions

Implement the first operational resolve_dns capability, bounded and scope-aware,
through explicit existing ToolRegistry composition and normalized domain evidence.

- tools.dns.DnsAdapter is the trusted native_dns binding for resolve_dns with
  active_safe risk. The minimal ToolAdapter metadata contract and immutable registry
  logic remain unchanged; only the base docstring reflects implemented capability
  execution. Default registry remains empty. No dynamic loading/auto-registration.
- Strict DnsInput has only record_types: unique uppercase A/AAAA/CNAME/MX/NS/TXT,
  bounded to six and sorted/default-normalized for execution and semantic dedup.
  Primary ActionRequest.target passes centralized scope and must be a name. Extra
  fields, ANY/AXFR, command-like input and resolver internals cannot dispatch.
- Capability-specific async execute revalidates original request/context, binding,
  current ActionPolicyValidator and its shared BudgetController. Trusted DnsContext
  carries explicit asset/execution IDs and UTC time; action asset lineage must agree.
  Caller owns request admission and state lifecycle, not a new dispatcher/AI loop.
- Trusted numeric resolver endpoint independently passes ScopeValidator against
  explicit IP/CIDR membership in the same scope; exclusions/private gates apply.
  Missing resolver authorization denies without contact. Original name and resolver
  both enter existing atomic host/resource accounting. Shared resolver-host limits
  stop multiple-name evasion. ApprovedAction is never accepted as an execution token.
- NativeDnsResolver uses dnspython >=2.8,<3, the only new runtime dependency, for one
  fixed UDP/53 exchange per absolute original-name question. No system resolver,
  search suffixes, retry, TCP fallback, referral/alias query, dig, subprocess or shell.
  RD requests recursive service from the explicitly authorized upstream; its activity
  is outside client containment. The client never contacts discovered addresses/names.
  ADR 0008 documents this choice and its conservative infrastructure requirement.
- Existing budgets charge one attempt containing at most six sequential questions,
  both hosts, concurrency, rolling action rate and conservative two-stream output
  reservation. Whole-action/per-exchange timeout, remaining session time and bounded
  output apply. UDP wire is protocol-bounded, 256 pre-dedup records per question,
  256 normalized total, 8,192-character record values and final serialized UTF-8 output
  no larger than adapter/budget max_output_bytes. Failure retains charges; synchronous
  permit cleanup releases concurrency, with correct failed/timeout/cancelled outcomes.
- Internal strict DNS query/record/output schemas preserve query target, owner, type,
  canonical address/name value, TTL, MX preference and exact TXT character-string hex.
  TXT presentation is escaped, preserves boundaries and never becomes instructions.
  Per-query normalized records deduplicate/sort deterministically; alias answers already
  present in a packet are evidence only, never follow-up query targets.
- Existing Asset/Observation/Evidence contracts are unchanged. Every record or empty
  negative outcome produces kind=dns facts with native_dns source, original query and
  caller subject/time/execution/evidence lineage. Query snapshot memory references,
  locators and SHA-256 preserve provenance, without claiming a raw packet artifact or
  persistence. Newly discovered hosts/IPs remain observation data and do not alter Scope.
- NOERROR empty and NXDOMAIN are successful negative evidence. Legitimate NXDOMAIN
  CNAME chains can be retained without follow-up; contradictory non-CNAME answers deny.
  Malformed/mismatched/truncated/oversized answers use parse_failed; resolver rcode/OS
  failures use tool_execution_failed; deadlines use tool_timeout. Fixed ErrorInfo
  diagnostics omit remote values/native exception details, default retryable=false.
  Any failing selected question discards earlier facts; no partial-success invention.
- Native work bypasses no registry architecture and needs no ExecutionRunner. Existing
  scope/policy/budget/dedup/state/domain/runner/config/shared errors and registry logic
  remain byte-identical. No Subfinder/DNSX/HTTPX/Naabu/Nmap/Groq/planner/loop/persistence/
  reporting/real CLI or later capability is implemented. No new follow-up task/blocker.

Files: tools/dns.py, dns_models.py, native_dns.py and base interface docstring;
92-case tests/unit/tools/test_dns.py and sanitized tests/fixtures/dns/answers.json;
pyproject runtime dependency; docs/dns-resolver.md, ADR 0008, tool/architecture/data/
security/scope/execution/testing docs, README/changelog and task/state/history records.

### Executed final validation

Repository .venv unless noted: Python 3.14.6 / Pydantic 2.13.5 / dnspython 2.8.0.
Python 3.12 was not run; no wider interpreter claim is made.

| Check | Actual command/result |
| --- | --- |
| Environment | `python --version` and `.venv/bin/python --version`: Python 3.14.6; `python -m pip install -e '.[dev]'` via .venv and pip check passed |
| Focused | `python -m pytest tests/unit/tools/test_dns.py tests/unit/tools/test_registry.py -q`: 190 passed, including 92 new DNS cases |
| Full | `python -m pytest -q`: 1,604 passed |
| Coverage | `python -m coverage run -m pytest -q`: 1,604 passed; `coverage report`: 99% overall, 2,009 statements / 594 branches; DNS adapter 94%, DNS models/native seam 100% |
| Network/DNS blocked | `/tmp/recon-m2t01-validation/offline.py`: 1,604 passed; Groq key absent, contact/DNS blocked before collection, guard self-checks passed |
| Lint/format/types | `python -m ruff check .`, `ruff format --check .`: passed (94 files); strict `mypy src/recon_agent`: passed, 42 production modules; no settings/suppressions weakened |
| Build/CLI | `python -m build`: isolated sdist/wheel passed; editable and external fresh-wheel recon-agent retain inert baseline message and exit 0 |
| Fresh wheel | External fresh wheel-venv installation/pip check passed; isolated `python -I -B wheel_checks.py` outside checkout passed guarded cold imports/module origins, explicit registration, real policy/budget/dedup with fake DNS execution, portable provenance and discovered/outside target rejection |
| Security/artifacts | Temporary artifact_checks.py passed protected source parity, adapter AST/no shell/process/Groq/dynamic import, later-source absence, Pydantic+dnspython dependency inspection, wheel/sdist source/metadata parity and artifact/secret inspection |
| Reconciliation/Git | Task-scoped diff/whitespace review; only M2-T01 DONE and M2-T02 READY, later tasks pending; append-only history and local documentation links/fences checked before one focused commit |

Remaining DNS adapter coverage misses are defensive unsupported-record and scope/
pre-exchange deadline branches. Existing scope/dedup defensive guards remain uncovered.
No acceptance criterion/coverage gate changed. No tests require a DNS server, public
DNS, provider credentials or external reconnaissance binary. Offline socket guards
allow AF_UNIX loop self-pipes; existing harmless local interpreter child tests are
not sandboxed by the parent guard. Fresh-wheel cold imports prohibit contact/process/
database/thread/logging/filesystem startup while allowing dependency metadata reads.
Package-index use is limited to installation/build provisioning.

Development checks caught strict typing/import formatting, use of the existing
BudgetPermit.release API, and an incorrect CIDR test expectation (the existing policy
budget seam rejects non-single-host accounting before the DNS-only name check).
These were corrected. Review additionally covered legitimate NXDOMAIN aliases,
shared resolver-host limits, session expiry during exchange, aggregate record caps
and oversized TXT. Final required checks passed; no unresolved validation failure.
Only documentation changed after the full suite; packaging was rebuilt to keep
README metadata current and artifact parity/fresh-wheel checks verified it.

### Acceptance and handoff

| PLAN criterion | Evidence |
| --- | --- |
| Authorized names produce typed records/provenance through fake resolver | Six-record fixture tests, default/multiple answers, typed output round trips, exact subject/source/query/TTL/execution/evidence lineage and existing state ingestion |
| Missing/malformed/timeout answers are structured | NOERROR empty/NXDOMAIN/alias distinctions, resolver rcode/OS failures, mismatched/malformed/truncated response cases, canonical safe errors, outer/session deadlines and cancellation cleanup |
| Derived destinations do not automatically become actionable | Recorded outside CNAME/NS/MX/A/AAAA values fail independent ScopeValidator and subsequent execution; original-name-only fake calls, unchanged Scope and TXT injection evidence |
| Resolver network behavior bounded and documented | Fixed native UDP mock, independently scoped numeric endpoint, maximum six questions, no retry/fallback/follow-up/process, resource/host/output/record/cancellation tests, DNS contract and ADR 0008 |

All requested validation and security boundaries passed. M0 and M1 DONE; M2-T01 DONE;
M2-T02 alone READY/unstarted; remaining 76 tasks NOT STARTED. No active task or blocker.
Exactly one focused task commit is authorized; no amend, squash, history rewrite or push.
Stop after M2-T01.

Commit reference: the single focused commit containing this entry, titled
`feat(dns): add DNS resolver capability`; resolve with
`git log -1 --format=%H --grep="^feat(dns): add DNS resolver capability$"`.
Final handoff reports actual hash and verified clean working tree.

## 2026-10-06 — M2-T02 — Subfinder adapter

Status: DONE. M2-T02 alone progressed READY → IN PROGRESS → DONE; M2-T03 alone
becomes READY and remains unstarted. M0/M1/M2-T01 prerequisites were DONE. Starting
HEAD: 696c561eb0038d15982a4a0538e5711bc10ff994; clean tree/index, no active task/blocker.
Ordered AGENTS/maintenance skill/state/PLAN/subsystem docs/ADRs/history/Git/source/test
startup matched the prompt. No unrelated modifications existed or were overwritten.

### Objective, implementation and decisions

Implement passive enumerate_subdomains through trusted ToolAdapter → ExecutionRunner,
with current authorization/resources and generic normalized observations/evidence.

- tools.subfinder.SubfinderAdapter supplies subfinder identity, passive risk, strict
  empty SubfinderInput and internal SubdomainOutput/Context/Line schemas. Primary
  target is the sole authorized query root; no parent-domain promotion or extra flags.
  Explicit registration through unchanged ToolRegistry; default registry stays empty.
- Operator-only binary/path lookup and bounded no-target version probe through the
  runner detect Subfinder availability. Reviewed 2.9.0 only; missing/unknown versions
  fail closed without installing, guessing flags or falling back. Direct construction
  supports trusted offline fakes; real AVAILABLE declarations require detection.
- Fixed credential-free HackerTarget hostsearch source, JSONL/source attribution,
  silent/no-color/update-disabled output, one HTTP request/second, 10-second source
  timeout and one-minute tool maximum. Source selection/keys/proxies/resolvers/config
  paths/executable/argv/environment never become planner parameters/catalog fields.
  Explicit composition opts into third-party disclosure/use; service transport and
  collection completeness remain external behavior. No target probing occurs.
- Upstream review found goflags 0.1.74 ambient YAML can override default-valued false
  CLI flags, so -config alone cannot guarantee passive execution. ADR 0009 records
  the necessary scoped runner extension: bounded immutable complete environment tuple
  in internal ProcessSpec, with one env keyword at create_subprocess_exec. None keeps
  existing inheritance. No launch/capture/deadline/cleanup duplication or parent env
  mutation. Subfinder's fresh temporary HOME/config paths and null-device config
  inputs exclude ambient secrets/proxy/config variables and confine automatic default
  config creation; cleanup follows runner cleanup, including cancellation.
- execute revalidates original request/context/subject, current binding, capability,
  risk, scope/schema/dedup and shared BudgetController. Atomic reservations charge
  attempts/root-host/concurrency/action-rate/two-stream output; same/smaller capture
  allowance is required. Process timeout clamps to remaining session time. Runner
  failures persist; permit cleanup releases concurrency and retains charges.
- Strict UTF-8 JSONL requires unique keys and exact host/input/sources fields. Any
  malformed/banned/outside-root record rejects the whole output, not partial facts.
  Blank lines ignore; zero output succeeds with zero hosts/observations and evidence.
  Central ScopeValidator supplies canonical syntax and queried-root label membership
  in a parser-only declaration, never replacing/mutating operational scope. Proper
  descendants deduplicate/sort, including operationally excluded names as data.
  Bounds: 4,096 lines, 2,048 nonblank-line characters, 254 wire-name characters,
  1,024 distinct hosts and configured captured/serialized output limits.
- Existing root Asset, kind=metadata Observation and Evidence contracts remain pure
  and unchanged. Provenance includes subfinder/enumerate_subdomains, version/source,
  explicit subject/time/execution IDs and stable memory snapshot reference/SHA-256.
  Raw lines/stderr/config/native diagnostics are not returned. Discovered names never
  gain authority or undergo DNS/HTTP follow-up. No new top-level SubfinderResult.
- Canonical tool_unavailable/tool_execution_failed/tool_timeout/parse_failed and
  policy/budget failures are reused; nonzero exits retain safe exit_code. Cancellation
  propagates after existing runner cleanup. Empty discovery does not prove absence or
  upstream provider success: Subfinder can suppress provider errors with zero exit.
- 99 offline Subfinder cases plus 15 runner environment regressions (including one
  harmless local sys.executable case) cover availability, exact argv, scoped/denied
  dispatch, malicious/metacharacter parameters/data, parser outcomes, provenance,
  no scope expansion, resources/deadlines/cancellation/config isolation.

Files: tools/subfinder.py and subfinder_models.py; ProcessSpec.environment and runner
spawn keyword; base adapter docstring; tests/unit/tools/test_subfinder.py, sanitized
JSONL fixture and runner/local-process regressions; Subfinder contract/ADR 0009;
tool/architecture/security/data/execution/scope/testing/DNS docs, README/changelog and
PLAN/state/current/history. Domain/policy/scope/budget/dedup/state/config/shared errors,
registry logic/native DNS/CLI/dependencies and all later subsystems remain byte-identical
to starting HEAD. The only protected runtime change is the documented environment seam.
No DNSX, HTTPX, Naabu, Nmap, Groq/planner, loop, persistence/reporting/real CLI or future
task implementation. No new blocker/follow-up task beyond existing M2-T03.

### Executed final validation

Repository .venv unless noted: Python 3.14.6, Pydantic 2.13.5, dnspython 2.8.0.
Python 3.12 was not run; no wider interpreter/live-tool claim is made.

| Check | Actual command/result |
| --- | --- |
| Setup | `python --version` / `.venv/bin/python --version`: 3.14.6; `python -m pip install -e '.[dev]'` via .venv and pip check passed |
| Focused | `python -m pytest tests/unit/tools/test_subfinder.py tests/unit/tools/test_registry.py tests/unit/execution -q`: 281 passed; 99 new Subfinder and 15 new environment cases |
| Full | `python -m pytest -q`: 1,718 passed |
| Coverage | `python -m coverage run -m pytest -q`: 1,718 passed; `coverage report`: 99% overall, 2,196 statements / 654 branches; Subfinder 96%, its schemas and runner/models 100% |
| Network/DNS blocked | `python /tmp/recon-m2t02-validation/offline.py`: 1,718 passed; Groq key absent; guard self-checks/contact/DNS denial before collection |
| Lint/format/types | `python -m ruff check .`, `ruff format --check .`: passed, 99 files; `mypy src/recon_agent`: passed, 44 modules; no suppressions/settings/gates weakened |
| Build/CLI | `python -m build`: isolated sdist/wheel passed; editable and fresh-wheel recon-agent keep inert baseline message and exit 0 |
| Fresh wheel | External wheel-venv install/pip check passed; `python -I -B wheel_checks.py` outside checkout passed guarded cold imports/module origins, explicit DNS/Subfinder registration, real policy/budget/dedup with fake executions, literal argv/config environment/portable provenance and denied discovered targets/extra flags |
| Security/artifacts | Temporary artifact_checks.py passed protected source parity, scoped runner diff, adapter AST/no shell/Groq/dynamic import, later-source absence, unchanged Pydantic+dnspython metadata, source wheel/sdist parity and artifacts/secrets |
| Reconciliation/Git | Final task-owned diff/whitespace review; only M2-T02 DONE and M2-T03 READY, later tasks pending; append-only history and local documentation links/fences verified before one focused commit |

Coverage misses are Windows SystemRoot and defensive post-eligibility reservation/
pre-dispatch deadline/temp-setup failure paths; existing scope/dedup/DNS defensive
misses are unchanged. Tests use fake binary outputs; no Subfinder/network integration
was run or required. Offline socket guards allow AF_UNIX loop machinery and do not
sandbox reviewed harmless interpreter children. Cold imports prohibit contact/process/
logging/database/thread/availability/temp startup and allow dependency metadata reads.
Package-index use is limited to installation/build provisioning. Provider DNS/TLS/
redirects/accuracy and process descendant/OS containment limits are documented.

Development checks caught strict subprocess kwargs typing, inappropriate generic
Pydantic dataclass serialization for availability (corrected with InstanceOf), and
three test assumptions about existing reserved domain keys. The external cold-import
harness also captured its temporary-directory guard via from-import; the harness
restores that symbol before explicit runtime testing. Final required checks pass.
Final review added safe nonzero exit context and reran focused/full/coverage/offline/
build/wheel/artifact checks afterward. No unresolved validation failure or blocker.

### Acceptance and handoff

| PLAN criterion | Evidence |
| --- | --- |
| Known fixture output normalizes candidates/source/evidence | JSONL fixture, canonical duplicate/order/single/multiple tests, generic metadata/evidence IDs, version/provider/time/execution/subject lineage and snapshot hash |
| Malformed output/missing binary/timeout are structured | Strict JSONL adversarial cases, fake missing/version/timeout/nonzero/truncation outputs, safe shared errors/exit code and zero-result success |
| Argv honors limits and denies extra parameters | Exact adapter-owned argv, empty strict schema/domain-key denial, isolated environment, policy/scope/resource/session/cancellation guards and denied-call assertions |
| Outside names remain rejected/unactionable | Outside-query-root records fail atomically; discovered proper descendants/exclusions never alter Scope, fail subsequent authorization and produce no follow-up calls |
| Passive third-party data handling documented | Fixed HackerTarget source, operator disclosure/use, no provider credentials/active mode, configuration isolation, provider/runner transport limits, complete Subfinder contract and ADR 0009 |

All acceptance checks passed. M0 and M1 DONE; M2-T01–M2-T02 DONE; M2-T03 alone
READY/unstarted; remaining 75 tasks NOT STARTED. No active task/blocker. Stop here.

Commit reference: the single focused commit containing this entry, titled
`feat(subdomains): add Subfinder adapter`; resolve with
`git log -1 --format=%H --grep="^feat(subdomains): add Subfinder adapter$"`.
Final handoff reports actual hash and clean tree. No amend, squash, second task
commit, history rewrite or push.

## 2026-10-06 — M2-T03 — DNSX adapter — DONE

### Objective and repository evidence

Implement only bounded bulk verification/normalization of already discovered
independently authorized candidates. Startup read AGENTS/skill, state/current/PLAN,
DNS/Subfinder/tool/architecture/security/execution/scope/state/testing docs, relevant
ADRs/history, Git and source/tests. HEAD was exactly
3c59eae2e105ab725f49983671f49640ad21053f; clean tree, no active task/blocker;
M0/M1/M2-T01–M2-T02 DONE and M2-T03 READY. Recorded only M2-T03 IN PROGRESS before
implementation. No unrelated changes existed or were overwritten.

Repository catalog had no separate bulk verification identity, and native_dns
already owns resolve_dns. ADR 0010 adds verify_dns as the eleventh finite capability
rather than renaming/replacing native resolution or passive discovery. No duplicate
error hierarchy or new top-level scanner domain entities.

### Changes and boundaries

- tools/dnsx.py implements trusted DnsxAdapter, definition/registry composition,
  operator-only binary/numeric IPv4 resolver selection and bounded isolated local
  availability/version probe. Only source-reviewed/fixture-validated DNSX 1.2.2;
  unknown/prerelease/malformed/multiple reports fail. No real DNSX was required/run.
- Strict DnsxInput requires 1–64 candidates and one A/AAAA/CNAME/MX/NS/TXT mode.
  parameter_target_fields declares every candidate. Current registry/policy/scope/
  dedup/resources precede execution; every entry independently checks before
  canonicalization. Mixed, all-rejected and empty batches never write input or launch.
  URLs/IPs/CIDRs/single-label ASN-like values reject. Approved names deduplicate/sort,
  revalidate and enter a temporary absolute-name list only. Resolver independently
  passes scope and joins primary/candidate host-budget accounting.
- Adapter-owned literal argv selects JSONL/stream, one worker, one candidate/second,
  one attempt and one record type at one numeric UDP/53 resolver. DNSX's reviewed TCP
  truncation fallback contacts only that same resolver/port. No wildcard/trace/alias
  follow-up, hosts-file, CDN/ASN, brute-force/default-resolver modes. Cloud auth/update
  checks disabled. Existing ProcessRunner/ProcessSpec executes without shell/direct
  subprocess/command-string/raw flag API. No install, dig or fallback implementation.
- Fresh complete HOME/config/temp environment excludes ambient YAML/credentials/
  proxies/PDCP/config overrides; cleanup follows runner cleanup for success/failure/
  cancellation. Existing action/session deadlines, capture/truncation, nonzero exits,
  cancellation and direct-child ownership remain unchanged. Attempt/host/rate/output
  charges persist; concurrency releases. Partial output records existing FAILED budget
  outcome; caller separately preserves PARTIAL lifecycle/ActionResult.
- Bounded parser uses full RR strings, not lossy aggregated arrays/raw_resp/aggregate
  TTL. Existing internal DnsRecord retains owner/type/value/TTL/MX preference/TXT hex.
  Generic primary Asset/DNS Observations/Evidence retain per-query names, capability,
  dnsx/version, subject/time/execution/memory snapshot/hash/untrusted provenance.
  No new discovered assets or authority. Merged sections explicitly remain unspecified;
  unchecked wildcard/shared-address suspicion is recorded without extra probes or
  wildcard-free claims. Conflicting duplicates discard that host deterministically.
- Malformed query lines discard that query, preserving other valid lines with explicit
  partial status/count/ErrorInfo. Unreported candidates, including empty output, are
  partial rather than invented negatives. All-malformed/truncated/oversized output
  fails. Canonical unavailable/timeout/parser/nonzero/setup failures are preserved;
  safe nonzero exit_code retained. No automatic retries/scope expansion.
- Limits: 64 inputs, 256 wire lines, 65,536 bytes/line, 8,192 chars/RR, 256 RRs/line
  and 256 normalized RRs/action plus configured capture/serialized-output/resource
  limits. One mode bounds original questions to 64 UDP and at most 64 same-resolver
  TCP fallback exchanges, independently of tool candidate/action rates.
- 90 new offline DNSX cases assert trusted argv/list/environment, registry/schema,
  single/multiple/duplicates/order, pre-input mixed/all-rejected regression, scoped
  infrastructure, six record types, actual owners/provenance/no derived authority,
  wildcard/merged-section ambiguity, partial/malformed/empty/conflicting output,
  version/missing/nonzero/timeout/cancellation, planner injection and resource bounds.

Files: new tools/dnsx.py, dnsx_models.py, dnsx_parser.py; one CapabilityId member and
registry finite-count regression; tests/unit/tools/test_dnsx.py and sanitized JSONL
fixture; DNSX contract/ADR 0010; relevant tool/architecture/security/data/execution/
scope/state/testing/DNS/Subfinder docs, README/changelog and PLAN/state/current/history.
Native DNS/Subfinder source/tests, runner, registry logic/interface, policy/scope/
budgets/dedup/state/config/shared errors/CLI/dependencies and later subsystem source
remain byte-identical to starting HEAD, except the explicitly scoped capability enum
extension. No HTTPX, Naabu, Nmap, Groq/planner runtime, loop, persistence/reporting,
real CLI or later task implemented. No new follow-up task or blocker.

### Executed validation

Repository .venv unless noted; Python 3.14.6, Pydantic 2.13.5, dnspython 2.8.0.
Python 3.12 and live DNSX/network were not tested; compatibility is pinned source/
fixture review, not a wider version/interpreter guarantee.

| Check | Actual result |
| --- | --- |
| Setup | `python --version` and `.venv/bin/python --version`: 3.14.6; `python -m pip install -e '.[dev]'` and pip check passed |
| Focused | `python -m pytest tests/unit/tools/test_dnsx.py tests/unit/tools/test_registry.py tests/unit/tools/test_dns.py tests/unit/tools/test_subfinder.py -q`: 379 passed, including 90 new DNSX cases |
| Full | `python -m pytest -q`: 1,808 passed |
| Coverage | `python -m coverage run -m pytest -q`: 1,808 passed; `coverage report`: 98% overall, 2,492 statements / 752 branches; DNSX adapter 87%, parser 96%, schemas 100% |
| Network/DNS blocked | Offline socket/DNS guard script before collection, Groq key absent: 1,808 passed |
| Lint/format/types | `python -m ruff check .`, `ruff format --check .`: passed, 105 files; `mypy src/recon_agent`: passed, 47 modules |
| Build/CLI | `python -m build`: isolated sdist/wheel passed; editable and fresh-wheel recon-agent inert baseline message, exit 0 |
| Fresh wheel | New external /tmp wheel-venv install/pip check; `python -I -B wheel_checks.py` outside checkout passed guarded cold imports/module origins, empty default registry and explicit combined native DNS/Subfinder/DNSX composition, real policy/budget/dedup plus fake executions, literal argv/input, portable evidence/provenance and pre-contact mixed/discovered/extra-flag denial |
| Security/artifacts | artifact_checks.py passed protected source/runner/native DNS/Subfinder/policy/registry/config/CLI/later-source parity, sole enum extension, AST/no shell/subprocess/Groq/dynamic imports, unchanged dependency metadata, source wheel/sdist parity and artifacts/secrets |
| Reconciliation/Git | Final task-owned diff/whitespace and 92-task dependency/status review, append-only history and local docs links/fences verified before one focused commit |

Coverage misses cover defensive composition/reservation/deadline/setup/Windows paths
and unreachable selected-type/internal-parser branches; existing defensive native
DNS/scope/dedup misses remain unchanged. No coverage/lint/type/test settings or
acceptance criteria weakened. Offline guards permit AF_UNIX event-loop self-pipes
and do not sandbox reviewed harmless local interpreter children. Fresh-wheel cold
imports prohibit startup/contact/process/logging/database/thread/availability/temp
creation while allowing read-only dependency metadata. Package index use was only
installation/build provisioning. Upstream recursive-server/binary-integrity and
runner direct-child/OS resource limitations are documented.

Development checks caught two test assumptions (shell is schema-rejected rather
than a reserved domain key; budgets are Pydantic rather than dataclasses) and a
nonexistent PARTIAL budget enum, corrected without changing shared contracts.
Review found conflicting duplicate malformed counts depended on line order; counts
now discard/count all conflicting host lines and a permutation regression passes.
Fresh-wheel provisioning initially used a checkout-relative interpreter outside the
checkout; corrected to an absolute interpreter path and reran successfully. Final
README cleanup exposed a stale sdist README and trailing EOF blank line during artifact/
whitespace review; removed that blank, rebuilt artifacts and reinstalled/rechecked the
wheel, then artifact/parity/reconciliation/whitespace checks passed. All final focused/
full/coverage/offline/build/wheel/security checks passed after production changes;
no unresolved validation failure or blocker.

### Acceptance and handoff

| PLAN criterion | Concrete evidence |
| --- | --- |
| Only validated batch entries dispatch | Declared candidate target fields, current policy plus final scope checks; mixed/all-rejected/empty no-call/no-write regression; scoped numeric resolver |
| Name/address provenance retained | Six-mode full RR fixtures; query target/actual owner/type/value/TTL/MX/TXT, dnsx/version/capability and generic subject/time/execution/evidence/snapshot-hash tests |
| Batch/rate/output limits apply | Strict 64 input bound, fixed one-worker/rate/attempt/mode argv, shared budgets and per-host/rate tests, capture/truncation/parser/normalized/session/cancellation bounds |
| Wildcard/ambiguous answers flagged | No generated wildcard queries; not_checked/shared-address suspicion and explicit merged-section attribution, incidental-owner and deterministic conflict regressions; contract/ADR 0010 |
| Derived IPs/hostnames require validation | Subfinder discovery-to-verification rejection, resolver-independent scope, incidental aliases/addresses remain data and fail subsequent validation; no follow-up calls/scope mutation |

All acceptance criteria passed. M0/M1 DONE; M2-T01–M2-T03 DONE; only M2-T04 READY,
remaining 74 tasks NOT STARTED. No active task/blocker. Stop after M2-T03.

Commit reference: the single focused commit containing this entry, titled
`feat(dns): add DNSX verification adapter`; resolve with
`git log -1 --format=%H --grep="^feat(dns): add DNSX verification adapter$"`.
Final handoff reports actual hash and clean tree. No amend/squash/history rewrite,
second task commit or push.

## 2026-10-06 — M2-T04 — HTTPX adapter

Status: DONE. Objective: trusted probe_http HTTP endpoint probing and normalized
scoped HTTP metadata. Only M2-T04 was implemented; M2-T05 becomes READY/unstarted.

### Repository evidence and scope

Startup read AGENTS, maintenance skill/references, PROJECT_STATE, CURRENT_TASK,
M2-T04/M2-T05 PLAN specifications, relevant tool/execution/security/scope/state/data/
testing docs, contact/registry/policy/budget ADRs, recent append-only history, Git and
source/tests. Starting HEAD was the expected
9a9ef0c4bd6625759f58128a7f91aadc0273adf7; working/staged trees were clean.
M0/M1 and M2-T01–M2-T03 were DONE, M2-T04 READY, no active task/blocker.
Recorded M2-T04 IN PROGRESS before implementation. No unrelated work was present.

Protected existing production adapters, runner, registry/interface, domain, policy/
scope/budgets/dedup/state, config/shared errors, CLI and dependencies remain byte-identical
to starting HEAD. Only three new tools modules implement this capability. No Naabu,
Nmap, Katana, Feroxbuster/FFUF, Nuclei, Groq/planner runtime, autonomous loop, persistence,
reporting or operational CLI was introduced. No new follow-up task or blocker.

### Implementation and decisions

- tools.httpx.HttpxAdapter implements existing probe_http/active_safe identity with
  explicit immutable registry composition. Default registry remains empty. Strict
  HttpxInput exposes only optional candidates: omitted/empty probes the primary;
  nonempty lists are atomic batches of at most 64 entries. Every original member
  independently passes policy/scope before canonicalization/input. Rejected mixed
  batches never create a temporary directory/list or dispatch. Host/IP inputs select
  one explicit HTTPS root URL; supplied URLs retain path/query/nondefault port.
  Unsupported forms, fragments, commas, non-ASCII and unsafe encodings reject.
- Operator executable, numeric IPv4 resolver and finite immutable numeric IPv4/IPv6
  HTTP contact addresses are separate from planner input. All addresses/resolver
  independently pass centralized scope and join host-budget accounting, with final
  rechecks before writing approved URLs. Numeric candidates also need configured
  contact membership. No DNS/name-to-address authorization inference occurs.
- Source review pinned HTTPX 1.9.0 at f66e469116d8de3416dcdfa7b8f4083e7e7dc246.
  Its allow list reaches networkpolicy 0.1.34 and fastdialer 0.5.4, which checks concrete
  addresses before numeric socket dial. Changed DNS answers outside the checked set
  cannot connect. One scoped custom resolver disables system/public resolver and
  syscall fallback; retryabledns 1.0.113 resolves original names via A/AAAA only.
  Reviewed HTTPX 1.7.1 declared Allow/Deny without applying them; it is unsupported.
  ADR 0011 and the HTTPX contract record exact source links/assumptions/alternatives.
- Fixed GET/JSONL/stream argv: one worker/probe per second, zero configured HTTP
  retries, explicit scheme without fallback and 65,536-byte response read/save bounds.
  No follow-redirects/follow-host-redirects/HSTS, TLS/CSP discovery, favicon, headless,
  raw request, arbitrary headers/proxy/flags or authentication behavior. Fresh complete
  HOME/config/temp child environment plus null flag config exclude ambient secrets,
  proxies/YAML. Cloud auth/update and CDN checks are disabled. Bounded isolated
  no-target availability/version detection fails closed for other versions; no install.
- Existing ProcessRunner/ProcessSpec owns shell-free execution and bounded separate
  capture, direct-child timeout/cancellation cleanup. Adapter rechecks registry binding,
  current policy/dedup/resources and atomically reserves shared budgets. Session/action
  deadlines, capture truncation/nonzero/missing/timeout/setup failures use canonical
  contracts; attempts/hosts/rate/output remain charged while concurrency/temp release.
- Existing generic Asset/Endpoint/HTTP Observation/untrusted Evidence carry actual
  probed/final URL, scheme/host/port/status and optional title/server/type/length,
  redirect and technology hints. httpx/probe_http/1.9.0, caller asset/execution/time,
  evidence references and stable normalized snapshot/hash preserve provenance.
  Absent fields stay absent. Raw headers/body/ancillary DNS/CDN/CPE data are excluded.
- Relative/absolute Location is validated only as evidence with scope status;
  redirect_authorized is always false. Even allowed redirects need fresh name/IP/
  policy/budget checks before future use. No additional Endpoint/contact/action or
  vulnerability/scanner selection follows redirects or detected technologies.
- Bounded UTF-8 JSONL parser validates required facts and requested URL/contact lineage.
  Identical records/input/technology deduplicate and sort; conflicting URL duplicates
  discard all affected lines with order-independent counts. Partial malformed output
  retains valid facts with explicit parse_failed errors/unreported URLs. Empty output
  is partial and invents no live endpoint or negative fact. All-malformed/truncated/
  oversized output fails. Caller owns lifecycle/state ingestion.
- Parser limits: 256 lines, 65,536 bytes/line, 128 fields/object, 4,096-character hints,
  64 technology strings of 256 characters, plus configured serialized-output bounds.
  Tool probe rate is not a packet-level guarantee; bounded same-contact DNS/TLS/gzip
  repair behavior stays under runner deadline. Metadata sees a bounded body; reported
  content length is a tool measurement. No live binary, OS CPU/memory/process-tree or
  recursive resolver upstream containment/interpreter compatibility claim was added.

Files: new tools/httpx.py, httpx_models.py, httpx_parser.py; 111 offline tests in
 tests/unit/tools/test_httpx.py and reserved source-shaped probing.jsonl fixture;
HTTPX contract and ADR 0011; relevant architecture/tool/security/scope/execution/data/
state/testing docs, README/CHANGELOG, PLAN/PROJECT_STATE/CURRENT_TASK and this entry.

### Executed validation

Repository .venv unless noted; Python 3.14.6, Pydantic 2.13.5, dnspython 2.8.0.
Python 3.12 and live HTTPX/network were not tested. Index use was limited to install/
build provisioning; tests require no real HTTPX, scanner, network or Groq key.

| Check | Actual result |
| --- | --- |
| Setup | `python --version` and `.venv/bin/python --version`: 3.14.6; `.venv/bin/python -m pip install -e '.[dev]'` and pip check passed |
| Focused | `python -m pytest tests/unit/tools/test_httpx.py tests/unit/tools/test_registry.py tests/unit/tools/test_dns.py tests/unit/tools/test_subfinder.py tests/unit/tools/test_dnsx.py -q`: 490 passed, including 111 new HTTPX cases |
| Full | `python -m pytest -q`: 1,919 passed |
| Coverage | `python -m coverage run -m pytest -q`: 1,919 passed; `coverage report`: 98% overall, 2,791 statements / 854 branches; HTTPX adapter 94%, parser 99%, schemas 100% |
| Network/DNS blocked | `/tmp/recon-m2t04-validation/offline.py`, guards before collection, Groq key absent: 1,919 passed |
| Lint/format/types | `python -m ruff check .`, `ruff format --check .`: passed, 111 files; `mypy src/recon_agent`: passed, 50 modules |
| Build/CLI | `python -m build`: isolated sdist/wheel passed; editable and fresh-wheel recon-agent inert baseline message, exit 0 |
| Fresh wheel | New external /tmp wheel-venv install/pip check; `python -I -B wheel_checks.py` outside checkout passed guarded cold imports/origins, empty default registry, explicit DNS/Subfinder/DNSX/HTTPX composition, real policy/budget/dedup and fake execution, literal argv/input, portable evidence/provenance and pre-contact mixed/redirect/extra-mode denial |
| Security/artifacts | artifact_checks.py passed protected production/runner/native DNS/Subfinder/DNSX/policy/registry/config/domain/CLI/later-source parity, AST/no shell/subprocess/Groq/dynamic imports, unchanged runtime metadata, wheel/sdist source parity and artifact/secret inspection |
| Reconciliation/Git | reconcile.py passed 92-task status/dependency review (18 DONE, only M2-T05 READY, 73 NOT STARTED), idle state, append-only history, local Markdown links/fences; final task-owned diff/whitespace/staged paths reviewed before one commit |

Defensive availability/reservation/deadline/final-scope-recheck/Windows branches
account for HTTPX coverage misses; existing shared controls have independent regressions.
No validation setting/gate/acceptance criterion was weakened. Offline guards allow only
AF_UNIX event-loop plumbing and do not sandbox harmless local interpreter children.
Installed-wheel imports prohibit runtime startup/contact/process/availability/temp
creation while allowing dependency metadata reads. Temporary validation scripts/logs
are outside the checkout, following existing task practice.

Development tests initially used nonexistent PARSER_ERROR/PARSER_FAILED and budget
field names; corrected to existing PARSE_FAILED/permitted_actions and adapter-config
timeout without changing shared contracts. Those transient failures were resolved;
all final focused/full/coverage/offline/lint/type/build/wheel/security checks passed.
No unresolved validation failure or blocker remains.

### Acceptance and handoff

| PLAN criterion | Concrete evidence |
| --- | --- |
| Fixture metadata fields normalize consistently | test_registry_argv_metadata_redirect_and_provenance, primary host/IP/URL cases, optional absent metadata and technology tests; generic Endpoint/Observation/Evidence plus stable duplicate/hash/conflict permutations |
| Target/redirect scope before request | Current policy and final candidate checks; rejected-batch no-temp/no-input/no-call regression; independently checked finite HTTP address set/resolver; pinned pre-dial gate; no-follow flags and relative/inside/outside redirect evidence tests |
| Unknown/unsafe redirect behavior rejects | No follow-mode input fields; planner injection rejection, supported-version-only availability tests, unexpected final URL/chain parser rejection; isolated config/environment; ADR 0011 |
| Output/time/rate limits apply | Typed batch/hint/parser/capture/normalized bounds, exact worker/rate/retry/body argv, shared host/rate/action tests, runner timeout/nonzero/truncation and session/cancellation/resource cleanup tests |
| Failures/absent fields invent no facts | All-malformed canonical failures; explicit valid+malformed/empty/unreported partial results; optional metadata stays absent; technology implies no vulnerability or extra runner call |

User acceptance also verified: capability registration and trusted argv/provenance,
no arbitrary flags/shell, machine-readable deterministic parsing, no later capability,
offline default tests and all required focused/full/network-blocked/Ruff/format/Mypy/
coverage/build/fresh-wheel/inert CLI/artifact/secret/diff checks passed. All criteria
are satisfied. M0/M1 DONE; M2-T01–M2-T04 DONE; M2-T05 READY/unstarted. No active task,
blocker or added follow-up. Stop after M2-T04.

Commit reference: the single focused commit containing this entry, titled
`feat(http): add HTTPX probing adapter`; resolve with
`git log -1 --format=%H --grep="^feat(http): add HTTPX probing adapter$"`.
Final handoff reports actual hash and clean tree. No amend/squash/history rewrite,
second task commit or push.

## 2026-10-06 — M2-T05 — Naabu port discovery adapter

Status: DONE. Objective: trusted bounded discover_ports, deliberate approved TCP
port sets and generic open-port evidence. Startup followed AGENTS/maintenance skill;
HEAD was expected b59b9600ac6befc8c7059a4f3b03d90213ab389a with clean working/staged
tree, M0/M1 and M2-T01–M2-T04 DONE, only M2-T05 READY and no active task/blocker.
M2-T05 alone moved IN PROGRESS before implementation. No unrelated edits existed.

### Changes and decisions

- Added tools.naabu.NaabuAdapter, strict NaabuInput, operator-only NaabuSettings/
  ContactBinding, caller NaabuContext and PortDiscoveryOutput envelope; existing
  discover_ports/active_safe identity integrates explicit immutable ToolRegistry.
  Default registry stays empty. No production global configuration/domain/policy/
  runner/registry/earlier adapter/dependency/CLI changes; parity verified against HEAD.
- Current primary/member scope/schema/risk/dedup/resource checks precede dispatch.
  Optional batches are atomic; every original member validates before input creation.
  Names require operator numeric contact bindings, independently scoped and budgeted;
  direct numeric targets need no bindings. Final primary/member/address checks precede
  writing numeric-only input. No DNS resolution, resolver contact, implicit name-to-IP
  authority, CIDR/ASN/target expansion or rejected target input. ADR 0012 records this
  conservative contact choice; operator references never prove DNS.
- Operator typed inclusive integer TCP ranges default to 80/443; endpoints 1–65,535,
  1–16 ranges, each expansion bounded and at most 128 distinct ports after overlap
  deduplication. At most 64 distinct contacts / 4,096 host-port pairs per process.
  Planner accepts only candidates, never port text/profile/command/extra_args/rate/
  interface/source IP/proxy/executable/service/Nmap flags. Reason/priority cannot
  override limits. Trusted immutable settings detach nested input models.
- Source-reviewed Naabu 2.3.5 availability uses bounded isolated no-target version
  detection; unknown/missing binaries fail canonically, no install. Adapter owns
  absolute executable/literal argv; unchanged ProcessRunner/AsyncProcessRunner owns
  shell-free execution, separate stream bounds/deadline/direct-child cancellation.
- Fixed JSONL CONNECT stream mode uses one connection start per second, one concurrent
  connect and input worker; explicit port list/IPv4+IPv6/no stdin/update/auth. No retry
  rounds, verification/shuffling/host discovery/raw SYN/stealth/evasion/passive API/CDN/
  PTR/proxy/service/Nmap probes. Fresh complete HOME/config/temp environment and null
  flag config exclude ambient YAML/credentials/proxies/PDCP. Child temporary/resume data
  stays under disposable directories; cleanup follows runner cleanup on every outcome.
  Explicit 1s dial duration corrects source-reviewed goflags seconds-vs-Naabu-help
  milliseconds ambiguity. No TCP application payload or fingerprint is sent.
- Reuses one atomic shared budget reservation, including primary/member/contact hosts;
  deadlines clamp to config/session remainder, post-return expiry rejects facts. Attempts/
  rate/output/hosts remain charged on failure/cancellation; concurrency/temp release.
  Capture and serialized normalization bounds are enforced. Canonical missing/nonzero/
  timeout/setup/parser failures retain established error contracts/exit context.
- Bounded strict UTF-8 JSONL selects canonical requested IP/integer port/tcp/false TLS;
  optional host must equal numeric contact. Duplicate keys, wrong types/port values,
  unrequested ports/hosts and malformed/incomplete lines reject as untrusted evidence.
  8,192 lines, 4,096 bytes/nonblank line and 16 fields/object bound parsing. Timestamp/
  unknown bookkeeping is excluded. IP/port duplicates sort/dedup deterministically.
  Valid plus malformed lines yield explicit partial status/errors; all-malformed,
  truncated/oversized output fails. Empty zero-exit output adds evidence and zero facts,
  without inventing closed ports/liveness/exhaustive per-host completion.
- Existing Asset/numeric Host/Service(tcp)/service Observation/Evidence normalize open
  port facts with subject/candidate references/source/version/capability and explicit
  caller time/execution, generic lineage, memory reference/locator/snapshot SHA-256.
  Generic state ingestion is tested. Protocol/product/version stay absent; no scanner
  domain entity or new authority. Caller retains snapshot and preserves partial lifecycle.
- Naabu is fast bounded open-port discovery; Nmap remains deeper fingerprinting in
  M2-T06. No M2-T06+, deterministic pipeline, Groq/planner/loop, persistence/reporting
  or real CLI implementation. No blocker or newly discovered future task remains.

Files: tools/naabu.py, naabu_models.py, naabu_parser.py; 117 guarded offline cases in
 tests/unit/tools/test_naabu.py and source-shaped reserved ports.jsonl fixture;
Naabu contract/ADR 0012; architecture/tool/security/scope/execution/data/testing docs,
README/CHANGELOG and PLAN/PROJECT_STATE/CURRENT_TASK/TASK_HISTORY reconciliation.

### Executed validation

Repository .venv unless noted; Python 3.14.6, Pydantic 2.13.5, dnspython 2.8.0.
Python 3.12 and live Naabu/network compatibility were not tested. Source review fetched
pinned upstream runner/options/defaults/output/targets/scan/CDN/main/resume and
IPRanger/DNSX/goflags dependencies only; no scanner binary was installed or run.
Provisioning index use was limited to editable/build/fresh-wheel installs.

| Check | Actual result |
| --- | --- |
| Setup | `python --version`: 3.14.6; `.venv/bin/python -m pip install -e '.[dev]'` and pip check passed |
| Focused | `python -m pytest tests/unit/tools/test_naabu.py tests/unit/tools/test_registry.py tests/unit/tools/test_dns.py tests/unit/tools/test_subfinder.py tests/unit/tools/test_dnsx.py tests/unit/tools/test_httpx.py -q`: 607 passed, including 117 new Naabu cases |
| Full | `python -m pytest -q`: 2,036 passed |
| Coverage | `python -m coverage run -m pytest -q`: 2,036 passed; `coverage report`: 98% overall, 3,047 statements / 940 branches; Naabu adapter 95%, parser/schemas 100% |
| Network/DNS blocked | `/tmp/recon-m2t05-validation/offline.py`, guards before collection, Groq key absent: 2,036 passed |
| Lint/format/types | Ruff check and format check passed (117 files); strict Mypy passed (53 production modules) |
| Build/CLI | `python -m build`: isolated sdist/wheel passed; editable and fresh-wheel recon-agent inert baseline message, exit 0 |
| Fresh wheel | New external /tmp wheel-venv install/pip check; `python -I -B wheel_checks.py` outside checkout passed guarded cold imports/origins, empty default registry, explicit DNS/Subfinder/DNSX/HTTPX/Naabu composition, real policy/budget/dedup with fake execution, numeric argv/input, finite ports, generic state/provenance and pre-input mixed/name-only/injection denials |
| Security/artifacts | artifact_checks.py passed protected production/runner/earlier adapters/policy/registry/config/domain/CLI/later-source parity, AST/no shell/direct subprocess/Groq/dynamic imports, unchanged runtime metadata, wheel/sdist source parity and artifact/secret inspection |
| Reconciliation/Git | 92 tasks: 19 DONE, M2-T06 alone READY, 72 NOT STARTED; idle state, append-only history, local Markdown links/fences and final task-owned working/staged diff/whitespace reviewed before one commit |

No validation settings/gates/criteria weakened. Naabu coverage misses are defensive
SystemRoot/default runner/reservation/deadline branches, protected by existing shared
regressions. Offline guards allow AF_UNIX event-loop plumbing only and do not sandbox
reviewed harmless local interpreter children. Installed-wheel cold imports prohibit
startup/contact/process/availability/temp creation, permitting metadata reads. Existing
kernel TCP/direct-child/OS-resource limitations remain explicit. No packet-rate/OS CPU/
memory/process-tree/live binary or additional interpreter compatibility guarantee.
Temporary validation scripts/logs stay outside the checkout, following prior task practice.

Transient development failures involved injection tests constructing already-rejected
ActionRequest keys, a nonexistent state snapshot property, and a fresh-wheel name-only
check reusing a spent rate budget. Corrected tests/harness to revalidate copied malformed
requests, use existing state property and independent fresh controller; no shared
contracts changed. All final required validations pass; no unresolved failure/blocker.

### Acceptance and handoff

| PLAN criterion | Concrete evidence |
| --- | --- |
| No implicit full-range scan | NaabuSettings strict typed ranges/default 80/443/128 cap; invalid/boundary/overlap tests; exact explicit -p argv and no top-ports/default grammar |
| Only authorized targets and approved ranges dispatch | Current primary/member scope; independently scoped numeric bindings; atomic mixed/input rejection and final scope recheck tests; finite pair bounds; literal numeric-only execution input |
| Parser yields host/port/transport facts with evidence | Source-shaped JSONL, generic Host/Service/service Observations/untrusted Evidence, stable duplicate/hash tests, explicit provenance and real generic state ingestion |
| Missing binary/timeout/partial output explicit | Canonical availability/runner/nonzero/truncation/setup failures; partial valid+malformed and empty output tests; no partial payload invented on runner failure |
| Rate/concurrency settings enforced | Fixed rate=1 stream sized wait group=1 plus shared action/host/rolling rate/concurrency/output/session budgets, denial-before-dispatch, cleanup and deadline tests |

User criteria also verified: trusted operational capability; every contacted target
scope checked; no shell/arbitrary flags/automatic target expansion; bounded port-only
discovery; generic contracts/canonical failures/offline tests; focused/full/network-
blocked/Ruff/format/Mypy/coverage/build/fresh-wheel/inert CLI/artifact/secret/diff checks
passed. M0/M1 and M2-T01–M2-T05 DONE; M2-T06 READY/unstarted. No active task/blocker.
Stop after M2-T05.

Commit reference: the single focused commit containing this entry, titled
`feat(ports): add Naabu discovery adapter`; resolve with
`git log -1 --format=%H --grep="^feat(ports): add Naabu discovery adapter$"`.
Final handoff reports actual hash and clean tree. No amend/squash/history rewrite,
second task commit or push.

## 2026-10-06 — M2-T06 — Nmap service fingerprint adapter

Status: DONE. Objective: trusted bounded fingerprint_services on approved prior-discovered
TCP ports, with generic service metadata and provenance. Startup followed AGENTS and
recon-project-maintainer skill. HEAD was expected 953c56833fcbd1bb771bc64cc64d6ca11d37b6fe,
working/staged tree clean, M0/M1 and M2-T01–M2-T05 DONE, only M2-T06 READY, no active
task/blocker. M2-T06 alone moved IN PROGRESS before implementation. No unrelated work.

### Changes and decisions

- Added tools/nmap.py, nmap_models.py and nmap_parser.py for existing
  fingerprint_services/active_safe capability through explicit immutable registry
  composition. Existing domain/policy/runner/registry/config/previous adapters/dependencies/
  CLI and all future runtime source remain unchanged; protected parity checks passed.
- Official Nmap 7.95 source shows -sV automatically enables NSE version scripts.
  ADR 0013 therefore requires a binary compiled --without-liblua; fixed omitted script
  flags alone are insufficient. Bounded isolated no-target --version detection requires
  exact version and unambiguous compiled feature lines proving liblua absent. Unknown/
  standard Lua-enabled/missing binaries fail closed; undetected constructed adapters
  cannot execute even with AVAILABLE registration. No Nmap installed, compiled or run.
- Trusted immutable NmapSettings supplies absolute installation data path and up to
  64 unique DiscoveredPortSelection snapshots, each one numeric address/optional canonical
  hostname, 1–128 prior TCP ports and 1–128 nonempty evidence references. These are
  approved operator prior facts, separate from planner claims and scope. M2-T07 will own
  state-to-adapter coordination; no pipeline implemented. Local binary/databases/composition
  are trusted and must stay intact across availability/execution.
- Strict extra-forbid NmapInput requires 1–128 integer ports in 1–65,535; empty/missing/
  invalid/unapproved ports deny before reservation/setup/contact. Ports canonicalize in
  the registered schema, so duplicates/order cannot evade existing action deduplication.
  Exactly one selected subject/contact per action and a nonempty approved subset; no
  implicit 80/443/top/full-range defaults, batch expansion, ranges or planner flags.
- Current registry binding, policy/risk/schema/dedup and primary scope precede dispatch.
  Selected numeric contact independently passes ScopeValidator/exclusions/private gates,
  joins shared host budgets and rechecks with subject before runner execution. No name
  resolution, discovered permission, CIDR/ASN/UDP expansion or unauthorized target input.
- Fixed --unprivileged -sT -sV --version-intensity 2 -Pn -n --disable-arp-ping profile,
  max-parallelism=1, scan-delay=1s/max-rate=1/max-retries=0, XML stdout, explicit sorted
  integer -p and absolute datadir/versiondb/servicedb paths; -6 only for IPv6. -Pn skips
  discovery probes outside selected services. No NSE code in accepted builds, script
  options, OS/aggressive scan, shell, spoofing/decoys/interfaces/exploitation or broad scan.
  Native TLS stays on the same selected socket. Port-specific probes may run irrespective
  of intensity; native exclusions (printer ports) stay honored. Source-reviewed native
  version concurrency is one; scan rate flags do not constrain every version reconnect/
  write/kernel packet. Exact assumptions/limits documented, without live claims.
- Fresh complete HOME/config/temp environment excludes ambient NMAPDIR/NMAP_PRIVILEGED,
  credentials/proxies; explicit trusted databases prevent ambient user selection. Unchanged
  runner owns shell-free argv, DEVNULL stdin, bounded separate streams, timeout/cancellation/
  direct-child cleanup. Atomic shared budgets charge attempts/host/rate/output, release
  concurrency, clamp execution/session deadlines and discard post-expiry facts. Capture,
  serialized normalization and fixed XML byte bounds enforced; temp cleanup on all outcomes.
- Safe local strict UTF-8 XML accepts only exact harmless Nmap DOCTYPE; external DTDs,
  internal subsets/entities/alternate encodings/CDATA reject before ElementTree. No resource
  lookup/execution. 1 MiB / 8,192 elements / depth 12 / 32 attributes / 4,096-char text/
  attribute / 16 CPE bounds. Only source envelope/version/success marker, selected numeric
  address/requested TCP ports/known state/valid confidence and unambiguous records accepted.
  NSE/OS/traceroute output rejects. Identical duplicates sort/dedup; conflicts/malformed/
  truncated XML fail atomically. Missing optional service data stays absent. Valid missing/
  empty/compressed records yield explicit partial/unreported_ports and canonical errors,
  never inferred states. Missing/nonzero/timeout/setup/capture preserve shared canonical
  failures and exit context; cancelled/failed runner has no invented partial payload.
- Generic Asset/numeric Host/Service/service Observation/untrusted Evidence preserve
  subject/contact/port/state/service name/product/version/extra_info/service_fingerprint/
  tunnel/method/confidence/CPEs, nmap/fingerprint_services/7.95, prior-discovery references
  and explicit caller time/execution/memory locator/stable snapshot SHA-256. Only open
  ports become Services; other states remain Observations. Unknown banners/instructions
  remain verbatim data; no vulnerabilities inferred. Generic state lineage/JSON round trip
  validated; caller owns lifecycle/ingestion/evidence retention and partial status.
- Added 135 guarded offline Nmap cases and source-shaped reserved services.xml; Nmap
  contract/ADR 0013, architecture/tool/security/data/execution/scope/testing docs and
  README/CHANGELOG updated. Naabu discovery vs Nmap fingerprinting explicitly documented.
  No M2-T07+, protocol-specific recon, Nuclei, planner/loop/persistence/reporting/real CLI.

### Executed validation

Repository .venv unless noted; Python 3.14.6, Pydantic 2.13.5, dnspython 2.8.0.
Python 3.12 and live Nmap/network compatibility not tested. Official 7.95 source archive
was retrieved for review of configure/NOLUA/version/argv/database/native contact/concurrency/
XML behavior; no binary installation, compilation, real availability probe or scan.
Index access limited to editable/build/fresh-wheel provisioning. Temporary validation
scripts/logs remain outside checkout in /tmp/recon-m2t06-validation (offline guard reused
from /tmp/recon-m2t05-validation/offline.py).

| Check | Actual result |
| --- | --- |
| Setup | python and .venv Python 3.14.6; pip install -e '.[dev]' and pip check passed |
| Focused | Nmap/registry/Naabu/DNS/Subfinder/DNSX/HTTPX: 742 passed, including 135 new Nmap cases |
| Full | python -m pytest -q: 2,171 passed |
| Network/DNS blocked | Guards installed before collection, Groq key absent: 2,171 passed |
| Coverage | coverage run -m pytest -q: 2,171 passed; report 98% overall, 3,332 statements / 1,046 branches; Nmap adapter 96%, parser 98%, schemas 100% |
| Lint/format/types | Ruff check/format passed (123 files); strict Mypy passed (56 production modules) |
| Build/CLI | python -m build isolated sdist/wheel passed; editable and fresh-wheel recon-agent inert message, exit 0 |
| Fresh wheel | New external venv wheel install/pip check; isolated -I -B guarded cold imports/origins, default registry, prior adapters and detected no-NSE Nmap composition with real registry/policy/budget/dedup + fake runner passed; numeric argv/bounded ports/generic state/metadata/provenance/no-contact denial verified |
| Artifacts/security | Protected source parity, adapter AST/no shell/direct subprocess/Groq/dynamic import, unchanged dependencies, wheel/sdist source parity and tracked/untracked artifact/secret checks passed |
| Final reconciliation | 92 tasks: 20 DONE, M2-T07 alone READY, 71 NOT STARTED; no active task; history append-only, local Markdown links/fences, task-owned working/staged diff and whitespace checked before commit |

No gates/criteria weakened. Nmap adapter uncovered branches are defensive SystemRoot,
registry-binding/atomic reservation/deadline paths; parser fixed byte cap is also
uncovered when the equal default capture bound rejects first. Existing shared runner/
policy/budget regressions independently protect those seams. Network guard allows
AF_UNIX event-loop plumbing only; reviewed harmless local interpreter children are not
sandboxed. Cold imports prohibit contact/process/availability/temp/runtime startup while
allowing installed metadata reads. No OS CPU/memory/process-tree/global native packet-
rate/live binary/additional interpreter compatibility claim.

Development failures exposed canonical constructor wrapping for invalid trusted addresses
and a pre-dedup CPE bound; corrected production handling. Test harness corrections used
existing record_facts and tuple host_actions contracts, supported budget fields and
separate detection/cancellation phases. Final source then passed all required checks;
no unresolved failure, blocker or new follow-up task remains.

### Acceptance and handoff

| PLAN criterion | Concrete evidence |
| --- | --- |
| Only validated hosts and approved discovered ports dispatch | Trusted finite prior selections, strict required subset, primary/numeric scope and final recheck tests; exact numeric-only target and requested-port argv regression |
| Safe profile excludes arbitrary scripts/options | Detected 7.95 no-Lua gate including undetected AVAILABLE denial, adapter-owned literal profile/paths; extra flags/scripts/OS/command injection rejection and AST checks |
| Machine-readable fixtures normalize services/provenance | Reserved XML fixtures, metadata/unknown/banner/state/duplicates tests, generic Service/Observation/Evidence IDs/source/time/hash/discovery refs and state/wheel round trips |
| Malformed/partial output remains explicit | Entity/DTD/hostile/malformed/conflicting XML atomic canonical failures; valid empty/unreported/compressed-port partial status/errors without invented facts |
| Timeout/output limits work | Canonical fake timeout/nonzero/missing/capture/normalized/session failures, deadline clamp, existing charged budgets, cancellation/concurrency/temp cleanup and full runner regressions |

User acceptance verified: fingerprint_services operational via trusted adapter/runner,
central scope and finite ports, safe XML, no vulnerability inference, shell/NSE/OS/
aggressive/unrestricted scan, canonical failures, offline tests and every required
validation gate passed. M0/M1 and M2-T01–M2-T06 DONE; M2-T07 READY/unstarted; no active
task/blocker. Stop after M2-T06.

Commit reference: the single focused commit containing this entry, titled
`feat(services): add Nmap fingerprint adapter`; resolve via
`git log -1 --format=%H --grep="^feat(services): add Nmap fingerprint adapter$"`.
Final handoff reports actual hash/clean tree. No amend/squash/history rewrite,
second task commit or push.


## 2026-10-06 — M2-T07 — Initial deterministic discovery pipeline

### Objective and repository evidence

Prove the six M2 adapters populate ReconState under one explicit deterministic
workflow before AI planning. Startup followed AGENTS/maintenance skill and inspected
PLAN/state/current task, architecture/security/state/tools/execution/budget/dedup,
all M2 contracts and ADRs/history, then Git and source/tests. HEAD matched
183afc8c5980d837e9dd1c6f678f1a870de62360; clean working/staged tree, M0/M1 and
M2-T01–M2-T06 DONE, M2-T07 alone READY, no active task/blocker. Recorded M2-T07
IN PROGRESS before implementation; no unrelated work existed or was included.

### Implementation and decisions

- Added DiscoveryRequest/DiscoveryWorkflow/DiscoveryReport under orchestration with
  finite resolve_dns → enumerate_subdomains → verify_dns → probe_http → discover_ports
  → fingerprint_services stages. Real current action policy, atomic dedup admission,
  registry selection, shared charged budgets and existing adapters/runners are used.
  No provider/PlannerDecision generation, retry scheduler or autonomous loop.
- Scope-filter discovered names independently before executable batches; outside
  discoveries stay original evidence plus policy audit, never contact inputs. DNS
  answers/CNAME/MX/NS and HTTP redirects grant no bindings or authorization. Existing
  operator numeric contacts/resolvers and every final adapter scope gate remain intact.
- At most 64 batch names and 64 service contacts/128 ports/128 refs per contact. Fixed
  five initial actions and one sorted fingerprint action per discovered numeric contact;
  zero ports schedule no fingerprint. Overflow stops, never silently truncates. Expected
  unavailable/timeout/parser/execution failures and partial/empty results preserve their
  distinctions; independent stages continue. Fatal policy/resource/state errors stop.
- Four necessary integration fixes, documented in ADR 0014: optional trusted
  post-reservation/pre-contact start callbacks across six adapters; atomic optional
  terminal subject batches in ReconStateMachine; exactly tool_unavailable as pre-start
  ActionResult rejection; immutable Nmap.with_selections snapshots for recorded Naabu
  ports, preserving detected no-Lua installation, runner, effective limits/data path.
  Registry snapshots stay immutable; policy/budget/dedup/runner arithmetic is unchanged.
  No double reservation or weakening of pending-only dedup revalidation.
- Requested/approved/started/terminal state records remain correlated. Invalid terminal
  facts commit nothing, retain prior pending state and stop with state_transition_invalid.
  Start-hook failure prevents contact and releases concurrency while retaining charges.
  Post-start final policy abort uses existing cancellation plus original denial in audit
  and returned Failure. Caller cancellation records terminal state and propagates after
  adapter cleanup. Duplicate attempts skip with no history admission/contact/spending.
- Detached reports preserve state, normalized output envelopes for memory evidence refs,
  safe correlated AuditEvents and skipped IDs. No raw output/commands/remote text in audit
  summaries, implicit logger setup or persistence. Only completed/partial adapter action
  results supply discovery candidates/selections; standalone raw facts cannot select work.
- Added 48 guarded offline tests with actual M2 adapters, fake DNS/process contacts and
  real policy/budget/dedup/state; deterministic full flow, scope, all missing tools,
  rate/budget exhaustion, timeout/unavailable/parse/partial/empty outcomes, immutable
  Nmap detection, start-hook failure for every adapter, atomic rollback and cancellation.
  Updated pipeline/ADR, architecture/state/data/error/tools/security/execution/testing/
  six adapter docs, README/CHANGELOG and governance state. Protected profiles/parsers,
  policy/core/runner/registry/dependencies/CLI/later subsystems remain unchanged.

### Executed validation

Repository .venv unless noted; Python 3.14.6, Pydantic 2.13.5, dnspython 2.8.0.
Python 3.12/live binaries/network compatibility not tested. Provisioning used package
index access only for editable/build/fresh-wheel dependencies, never reconnaissance.
Logs/scripts reside outside checkout under /tmp/recon-m2t07-validation and
/tmp/recon-m2t07-*.log; reused pre-collection guard from
/tmp/recon-m2t05-validation/offline.py.

| Check | Actual result |
| --- | --- |
| Setup | python and .venv Python 3.14.6; pip install -e '.[dev]' and pip check passed |
| Focused | Pipeline alone 48 passed; pipeline/state/domain/all tools 1,102 passed |
| Full | python -m pytest -q: 2,219 passed |
| Network/DNS blocked | Guards installed before collection, Groq key absent: 2,219 passed |
| Coverage | coverage run -m pytest -q: 2,219 passed; report 97% overall, 3,606 statements / 1,152 branches; workflow 92%, lifecycle helper 100% |
| Lint/format/types | Ruff check and format passed (128 files); strict Mypy passed (58 production modules) |
| Build/CLI | Isolated sdist/wheel build passed; editable and fresh-wheel inert recon-agent message, exit 0 |
| Fresh wheel | New external venv wheel/pytest install and pip check; isolated -I -B guarded cold imports/origins, six actual adapter fake compositions and installed pipeline full/repeated/dedup/scope/empty-partial flow passed |
| Artifacts/security | Protected source parity, AST/no shell/direct subprocess/provider/dynamic import, unchanged dependency metadata, wheel/sdist source parity and tracked/untracked artifacts/secrets passed |
| Final reconciliation | 92 tasks: 21 DONE, M3-T01 alone READY, 70 NOT STARTED; no active task; append-only history, Markdown links/fences, task-owned working/staged diff/whitespace reviewed |

No gates/criteria weakened. Defensive workflow binding/transition/malformed-input/
aggregate-history branches remain uncovered locally; shared policy/adapter/state
regressions independently exercise underlying failures. Network guard permits AF_UNIX
loop plumbing, not Internet/loopback traffic; harmless local interpreter children are
not sandboxed. Cold imports prohibit runtime/contact/process/availability/temp startup.
Existing binary/infrastructure/native-rate/OS/process-tree limits remain documented.

Development harness corrections: strict policy allowlists use frozensets, newly created
asset references cannot precede atomic fact ingestion, and a scope-check test initially
reentered the state lock during pure dedup admission. A timed diagnostic identified the
harness deadlock; replaced it with a detached injected flag. Final source/tests passed
every required check. No unresolved validation failure, blocker or new follow-up task.

### Acceptance and handoff

| PLAN criterion | Concrete evidence |
| --- | --- |
| Offline workflow produces traceable assets/services/observations | Full six actual adapter fake flow, products/endpoints/ports, canonical state round trip and provenance/normalized report tests |
| No action skips policy | Workflow current validator plus adapters' repeated validation; real dedup admission, exactly one charged reservation and finite registry-selected M2 branches |
| Outside discoveries never dispatch | Excluded subdomain retained as evidence and omitted from DNS/HTTP/port inputs; outside resolved IP/CNAME/MX/NS/redirect remain evidence; independent resolver/bound-IP denial and final scope abort tests |
| Failures/rejections remain recorded | Every missing capability, timeout/unavailable/parser, partial/empty, policy/cancellation and failed-transition rollback regressions; canonical result/audit lineage |
| Budgets/dedup prevent repeats | Deterministic repeated flow skips six actions without state/charges/contact; action/host/output budgets and rolling rate exhaustion stop with unstarted rejection; all start-hook aborts release permits |
| No provider required | Import/runtime guards, empty planner records, actual offline/fresh-wheel composition, no provider/planner imports/calls or new dependencies |

M0/M1/M2 DONE; M3-T01 READY/unstarted; no active task/blocker. M2 pipeline is a
deterministic integration proof; M6/M7 AI planning/autonomous loop remain future work.
No M3 capability, Groq/AI/planner, persistence/reporting/real CLI or public target test.
Stop after M2-T07.

Commit reference: the single focused commit containing this entry, titled
`feat(discovery): integrate deterministic recon pipeline`; resolve via
`git log -1 --format=%H --grep="^feat(discovery): integrate deterministic recon pipeline$"`.
Final handoff reports actual hash/clean tree. No amend/squash/history rewrite,
second task commit or push.

## 2026-10-07 — M3-T01 — Common-file inspector

Status: DONE.

Objective: collect fixed safe common web metadata without executing remote instructions.

### Startup and scope

Verified M2-T07 DONE, M3-T01 READY, no active task/blocker, expected HEAD
`e6e077c71dbf01ef60330ce3cc0f3885f8be14a3`, clean working/staged tree and recent log.
Reviewed governance/skill, roadmap, architecture/security/scope/tools/execution/state/
HTTPX/pipeline/budgets/testing contracts, relevant ADRs/history and source/tests.
Recorded only M3-T01 IN PROGRESS before implementation. No unrelated user changes.
Reconciled configuration documentation's stale sole-Pydantic claim with existing
native DNS and the new minimal h11 framing dependency. No configuration schema change.

### Changes and decisions

- Added inspect_common_files finite capability and explicitly registered
  native_common_files/active_safe adapter with strict empty planner input. Trusted
  catalog alone selects /robots.txt, /sitemap.xml, /.well-known/security.txt GETs.
  No arbitrary planner paths/URL/header/proxy/method/body/extra_args input.
- Immutable operator canonical host/numeric contact bindings independently pass
  ScopeValidator and shared host accounting, including possible unused redirect
  contacts. Actual URL/IP scope rechecks occur after pacing immediately before
  every request. No DNS/address inference or scope expansion.
- Native asyncio/SSL sockets pin numeric contact while preserving Host/TLS SNI and
  certificate verification. h11 >=0.16,<0.17 supplies typed sans-I/O framing as the
  sole added runtime dependency. ADR 0015 documents alternatives and limits.
  No subprocess, curl/wget, proxy, cookies/authentication, retries or scheme fallback.
- At most two independently scope/binding-checked redirect hops/file; same catalog
  path only, no query/fragment/userinfo/HTTPS downgrade. Rejected destinations, loops
  and limits retain bounded untrusted lineage without contact. Truncated redirects
  stop. Scoped names never imply numeric address permission.
- Body cap 16,384 bytes/file reduced by configured/shared allowance; header/parser
  cap 16,384 (including complete trailers); 4,096-byte reads; wire cap body + 65,536; four interim responses/no
  upgrade. Sequential GET completion pacing >=1 second or stricter capability rate.
  Ten-second request and remaining action/session deadlines; complete serialized
  output bound. Exact overflow/incomplete prefixes remain marked evidence. Finally
  synchronously closes/aborts streams; cancellation propagates and permits release.
  Attempts/host/rate/output charges are never refunded.
- Ordered bounded User-agent/Allow/Disallow/Sitemap metadata; sorted deduplicated
  sitemap/index URL strings without crawling/recursion; selected security field/value
  metadata and bounded text without contacting mail/external URLs. DTD/entity and
  alternate XML encodings reject before ElementTree; node/depth/entry/value bounds.
  Remote instruction-like text stays untrusted data. No discovery grants permission.
- Typed common facts project into existing web_resource Asset/HTTP Observation/
  untrusted Evidence with source/capability, caller identity/UTC time, evidence IDs,
  memory locator and normalized-fact SHA-256. 404/403/other ordinary statuses are
  facts. Timeout/connection/malformed/unsupported/truncated/rejected redirects preserve
  explicit partial collection errors; whole-action timeout/scope abort has no payload.
  Rejection policy details remain evidence with parse_failed collection errors so
  existing ActionResult partial/state ingestion rules remain intact.
- Added four production files, two test modules and three sanitized fixture files;
  extended only CapabilityId and the finite-enum regression count. Updated common
  contract/ADR, architecture/security/scope/data/config/execution/state/tools/testing,
  README/CHANGELOG and task governance. Existing policy/core/config schema/registry/
  runner/M2 adapters/pipeline/CLI and all future subsystem code remain unchanged.

### Executed validation

Repository .venv unless noted; Python 3.14.6, Pydantic 2.13.5, dnspython 2.8.0,
h11 0.16.0. Python 3.12/live-network compatibility not tested. Installation/build
provisioning accessed the package index only, never a reconnaissance target.
Logs/scripts: /tmp/recon-m3t01-validation (outside checkout).

| Check | Actual result |
| --- | --- |
| Setup | python --version; pip install -e '.[dev]' and pip check passed |
| Focused | Common/native/registry 197 passed; 99 new common/native cases |
| Full | python -m pytest -q: 2,318 passed |
| Network/DNS blocked | Guarded before collection, Groq key absent: 2,318 passed |
| Coverage | coverage run -m pytest -q: 2,318 passed; report 97% overall, 4,047 statements / 1,324 branches; adapter 93%, parser 97%, models 100%, transport 90% |
| Lint/format/types | Ruff check/format passed (136 files); strict Mypy passed (62 modules) |
| Build/CLI | Isolated wheel/sdist build, editable and fresh-wheel inert recon-agent, exit 0 |
| Fresh wheel | New external wheel venv/pytest install/pip check; -I -B guarded cold imports/origins, empty registry/inert construction; 99 network-blocked installed-wheel adapter/native-stream/state/dedup tests passed |
| Artifacts/security | Protected source parity, AST/no shell/direct process/provider/dynamic imports, artifact/secret checks, wheel/sdist source and three-dependency metadata parity passed |
| Closeout | 92 tasks: 22 DONE, M3-T02 alone READY, 69 NOT STARTED; no active task; append-only history, Markdown links/fences, acceptance and final working/staged diff/whitespace reviewed |

Development corrections: aligned test lifecycle names with existing state API,
updated the capability-count regression for the new identity, used existing permit
outcomes, preserved redirect policy details as evidence rather than invalid partial
policy errors, and corrected a wire-bound fixture to exercise aggregate overhead.
Final review added explicit complete-trailer size enforcement and its regression;
full/coverage/network-blocked suites, build and installed-wheel checks were rerun.
Final checks passed; no outstanding failure/blocker or weakened gate. Remaining
coverage gaps concern defensive malformed-composition/framing/structure branches.
Network guards allow AF_UNIX event-loop plumbing only; harmless local interpreter
children are not sandboxed. No real scanner, server or public-target test.

### Acceptance and handoff

| Criterion | Concrete evidence |
| --- | --- |
| Only explicit common paths on scoped services | Empty input injection denials; constant catalog; URL/name/address preflight and per-contact checks; pinned numeric native stream assertions |
| Body/time/redirect budgets hold | Fake native Content-Length/chunked/EOF, prefix/header/wire limits; per-request/whole-action/session/pacing/output/host/action/cancellation cases; finite two-hop redirects |
| Injection text stays evidence | Robots/security instruction-like fixtures, exact base64/text and trust/source/capability/hash/time lineage tests; no execution/provider path |
| Outside links remain non-actionable | Outside/unbound/numeric/arbitrary-path/downgrade redirects cause zero destination contact; robots and sitemap/index URLs never fetched |
| Parsing errors/partial bodies recorded | Unsupported/malformed/XXE-like/alternate encoding/structure bounds, native incomplete/oversized prefixes, timeout/connection and normal HTTP outcomes; atomic completed/partial state ingestion |

M0/M1/M2 and M3-T01 DONE; M3-T02 READY/unstarted; no active task/blocker.
No TLSX/M3-T02+, Katana/crawling, Ferox/FFUF/fuzzing, planner/Groq/loop,
persistence/reporting/real CLI or M2 pipeline extension. Stop after M3-T01.

Commit reference: the single focused commit containing this entry, titled
`feat(web): add common-file inspection`; resolve via
`git log -1 --format=%H --grep="^feat(web): add common-file inspection$"`.
Final handoff reports actual hash/clean tree. No amend/squash/history rewrite,
second task commit or push.


## 2026-10-07 — M3-T02 — TLSX adapter

Status: DONE. Objective: trusted bounded inspect_tls with generic untrusted certificate
metadata; no certificate-derived authorization or later task implementation.

### Repository evidence and scope

- Startup followed AGENTS/maintenance skill order; reviewed state/current task/PLAN,
  architecture/security/tools/execution/scope/budgets/state/HTTPX/M2/M3 docs, relevant
  ADRs/history and source/tests. Expected prior HEAD matched exactly:
  1d59c19e7478c41af5ae5448d662b8e0bbd55bbb. Working/staged diffs were clean;
  M0/M1/M2/M3-T01 DONE, M3-T02 READY, no active task/blocker. No discrepancy.
- Recorded M3-T02 IN PROGRESS before implementation. Protected all existing production
  Python, dependencies, core/domain/policy/runner/registry/CLI/common-file/M2 workflow
  and later subsystems. No unrelated modifications/future implementation added.

### Changes and decisions

- Added tlsx.py/tlsx_models.py/tlsx_parser.py for existing inspect_tls. Explicit
  successful detected Linux TLSX 1.4.0 enables AVAILABLE execution. Planner schema
  permits finite typed candidates and optional 1–65535 port; operator finite ports
  and canonical name/numeric bindings authorize nothing. Complete independent
  primary/batch/address scope precedes reservation/files/contact; per-process
  revalidation and atomic mixed-batch containment apply.
- Reviewed TLSX source commit ffe1cfef11fc71fd7b73e41c603c18bebfb28258,
  fastdialer 0.5.18 eff51d62312508fb146a5314e52dd2fdc01091b2 and goflags 0.1.76
  c2b50c5141a365283151dc487b288fc223e62b8c. No binary install/live handshake.
  Native ctls/JSON/probe-status, concurrency one, one logical attempt, five-second
  handshake cap and one-second input delay; no revocation/CRL/OCSP, enumeration,
  cloud/update/CT logs/PTR/random SNI or certificate-derived contact. PATH isolation
  prevents ambient OpenSSL initialization. Trusted SNI file avoids hostname-as-file
  interpretation; groups prevent SNI cross products. Same-peer dialer TCP-failure
  fallback can attempt once more; contract explicitly limits connection/packet/heap/
  process-tree claims. Version detection is not binary attestation.
- Reused existing runner timeout/cancellation/capture contracts, one shared remaining
  action/session deadline/reservation, permanent attempt/output charges and concurrency
  cleanup. Cumulative captured streams and serialized normalized output are bounded.
  Canonical unavailable/timeout/nonzero/setup/parser failures; handshake/empty/malformed
  subsets and invalid validity preserve explicit partial observations/limitations.
- Normalized original host/address/port, protocol/cipher/key exchange, subject/issuer/
  CN/DNS SANs/organizations, serial/fingerprints/validity/expiration metadata into generic
  TLS Observation/untrusted Evidence. Stable source/version/capability/caller UTC/asset/
  execution/evidence IDs/memory locator/SHA-256; no new TLSX domain entity or derived
  Asset/Endpoint/Host/Service/Finding. Remote instructions stay strings. Existing atomic
  state lifecycle/terminal ingestion and history dedup work without contract changes.
- Added one guarded offline test module (125 cases), two reserved source-shaped JSONL
  fixtures, TLSX contract/ADR 0016, relevant subsystem docs/README/CHANGELOG and task
  governance. No dependency, existing production file or later capability changed.

### Executed validation

Repository .venv unless noted: Python 3.14.6, Pydantic 2.13.5, dnspython 2.8.0,
h11 0.16.0. Python 3.12/live TLSX/network compatibility not tested. Package provisioning
accessed the package index; source review accessed public upstream repositories;
no reconnaissance target or scanner binary was contacted/run.
Logs/scripts: /tmp/recon-m3t02-validation (outside checkout).

| Check | Actual result |
| --- | --- |
| Setup | python --version; pip install -e '.[dev]' and pip check passed |
| Focused | TLSX/registry 223 passed; 125 new TLSX cases |
| Full | python -m pytest -q: 2,443 passed |
| Network/DNS blocked | Guarded before collection, Groq key absent: 2,443 passed |
| Coverage | coverage run -m pytest -q: 2,443 passed; report 97% overall, 4,439 statements / 1,472 branches; adapter 94%, parser 99%, models 100% |
| Lint/format/types | Ruff check/format passed (142 files); strict Mypy passed (65 modules) |
| Build/CLI | Isolated sdist/wheel build, editable and installed-wheel inert recon-agent, exit 0 |
| Fresh wheel | New external wheel venv/pytest install/pip check; -I -B guarded cold imports/origins/empty registry/inert TLSX construction; 125 installed-wheel network/DNS-blocked fake-runner/state/dedup tests passed |
| Artifacts/security | All existing production Python byte parity, AST/no shell/direct process/provider/dynamic imports, artifacts/secrets and wheel/sdist source/three-dependency metadata parity passed |
| Closeout | 92 tasks: 23 DONE, M3-T03 alone READY, 68 NOT STARTED; no active task; append-only history, Markdown links/fences, acceptance and final working/staged diff/whitespace reviewed |

Development corrections: removed a test-helper tuple, corrected optional validity/
line-limit expectations and test clock mutation during detection, and adapted the
state start callback to existing Success[None]. Source review justified Linux-only
containment and the documented same-peer fallback limit. All final required checks
passed, no outstanding failure/blocker or weakened gate. Remaining coverage branches
are defensive composition/setup/deadline/representation/optional environment paths.
Guards allow AF_UNIX loop plumbing only; harmless local interpreter children are
not sandboxed. No TLSX/live server/public-target test or runtime startup.

### Acceptance and handoff

| Criterion | Concrete evidence |
| --- | --- |
| Trusted TLS capability/argv | Detected version gate and registry/composition cases; exact fixed argv/private environment/PATH/numeric/SNI assertions; strict flag/file/injection denials |
| Every contact scoped/batches contained | Name/IP/HTTPS/port operator allowlist tests, numeric binding-only scope rejection, mixed-batch no temp/input/dispatch, final and later-group revalidation, 64-contact bound |
| Certificate metadata normalized | CN/multiple SANs/subject/issuer/serial/fingerprint/validity/TLS/cipher/key exchange fixtures; generic provenance/serialization/actual state lifecycle/dedup tests |
| Invalid/expired/malformed limitations | Expiration observed without Finding, invalid/missing/reversed dates partial, duplicate/conflict/hostile JSON/empty/partial and handshake structured outcomes |
| Discovery never authorizes contact | Instruction-like CN/SAN/issuer/organization remain plain data; outside SAN action rejected, scope unchanged, no extra asset or contact |
| Resources/canonical errors | Shared action/rate/host/concurrency/deadline/cumulative/normalized capture bounds, timeout/missing/nonzero/setup/cancellation/temp cleanup and start-hook abort |

M0/M1/M2 and M3-T01–M3-T02 DONE; M3-T03 READY/unstarted; no active task/blocker.
No Katana/M3-T03+, content discovery, Ferox/FFUF, protocol recon/Nuclei,
Groq/planner/loop, persistence/reporting/real CLI or M2 workflow extension.
Stop after M3-T02.

Commit reference: the single focused commit containing this entry, titled
`feat(tls): add TLSX inspection adapter`; resolve via
`git log -1 --format=%H --grep="^feat(tls): add TLSX inspection adapter$"`.
Final handoff reports actual hash/clean tree. No amend/squash/history rewrite,
second task commit or push.

## 2026-10-07 — M3-T03 — Katana crawler adapter

Status: DONE. Objective: scope-constrained bounded crawl_web through trusted Katana,
with generic untrusted URL/endpoint/form/JS evidence. Stop after M3-T03.

### Repository evidence, scope and decisions

Startup followed AGENTS/maintenance skill order: state/current task/PLAN, subsystem
architecture/security/tools/execution/scope/budget/dedup/state docs, relevant ADRs/history,
Git and source/tests. Expected HEAD matched 56f166ace42edf378f42b988f62eebc5581cecf4;
working/staged diffs clean; M0/M1/M2/M3-T01–M3-T02 DONE, M3-T03 READY, idle/no blocker.
Recorded IN PROGRESS before implementation. No stale-state discrepancy or unrelated work.

Reviewed Katana 1.8.0 commit 35267ac5c8ff1db9694a319d0eb466ed97b0969f and fastdialer
0.5.23 commit 7f2e2647063cd76f9aa8f652f744b5a9ed41d90c. Ordinary Katana recursion
can issue htmx POST/PUT/PATCH without automatic form filling; CLI URL scope cannot
constrain hostname DNS answers to independently authorized addresses. ADR 0017 chooses
numeric HTTP(S) seeds and depth-zero single-page extraction with positive duration:
Enqueue emits all child discoveries before queue admission, including self-links/htmx.
No hidden recursive/redirect/form contact. Supported operational profile is deliberately
numeric-only; hostname modes fail closed before spending/contact. No acceptance relaxed.

Task-owned source: katana.py/katana_models.py/katana_parser.py; strict empty planner
schema and frozen operator depth/page/discovery bounds; detected available registry
binding, current action policy/dedup/scope and shared reservation. Adapter owns finite
sorted same-origin hyperlink/script-resource GET graph, every next URL/address recheck
post-pacing, common action/session timeout and cumulative/normalized output caps. Form/
htmx/JS-extracted endpoint/redirect/outside host discoveries remain non-authoritative data.
No arbitrary flags/headers/proxy/files/JS execution/shell or scope expansion.

Source review also found unconditional relative katana_field cleanup. Necessary task-local
existing production changes are optional bounded absolute ProcessSpec.working_directory
and literal runner cwd forwarding; no global chdir, omitted cwd preserves old behavior.
New runner regressions verify validation, literal forwarding and actual harmless child
cwd/parent isolation. All other pre-existing production Python files are byte-identical;
core/policy/domain/registry/config/dependencies/CLI/previous adapters/M2 workflow protected.

Existing generic Asset/Endpoint/HTTP Observation/untrusted Evidence preserve method,
URL/path/query/source page/type/forms/resources, caller UTC/subject/execution/references,
source/capability/version and deterministic memory snapshot SHA-256. Exact duplicates
collapse; different source lineage remains; sorted normalization and conflict rejection
are deterministic. Partial malformed/empty/depth/page limits retain explicit parser
errors; missing binary/timeout/nonzero/setup/cancellation/resources use existing contracts.
Caller owns lifecycle/state/snapshot; real state ingestion/dedup tests pass without changes.

Added reserved source-shaped JSONL fixture, 91 guarded Katana tests and 8 runner cwd
cases, contract/ADR 0017, relevant docs/README/CHANGELOG and task governance. No later
capability, generic web dedup, planner/runtime/loop, persistence/reporting or real CLI.
Tool logical GET/page rates do not bound packets/fallback attempts; upstream drains excess
body bytes, so parsing prefix is not a total-download/Go-heap/OS-process-tree guarantee.
HTTPS metadata is not certificate authenticity evidence. These limits are documented.

### Executed validation

Python 3.14.6 in repository .venv. No Python 3.12 or live Katana/network compatibility
claim. Package provisioning and primary upstream source review accessed the Internet;
no scanner installed/run and no reconnaissance target contacted. Validation artifacts
and scripts are outside checkout at /tmp/recon-m3t03-validation.

| Check | Actual result |
| --- | --- |
| Setup | python --version; editable pip install -e '.[dev]'; pip check passed |
| Focused | Katana/registry/execution 281 passed; 91 Katana + 8 new cwd cases |
| Full | pytest: 2,542 passed |
| Network/DNS blocked | Guards before collection, Groq key absent: 2,542 passed |
| Coverage | coverage run -m pytest: 2,542 passed; report 97% overall (4,792 statements / 1,616 branches), adapter 89%, parser 95%, models 100% |
| Lint/format/types | Ruff check/format passed (149 files); strict Mypy passed (68 modules) |
| Build/CLI | Isolated sdist/wheel and editable/fresh-wheel inert recon-agent passed |
| Fresh wheel | New external wheel venv/pip check; guarded cold imports/origins/empty registry/inert Katana; 99 installed-wheel network-blocked fake/state/dedup/cwd cases passed |
| Artifacts/security | All old production byte parity except reviewed two-file cwd seam; AST execution boundary, artifact/secrets, wheel/sdist source/three-dependency metadata parity passed |
| Closeout | Acceptance/diffs/whitespace, append-only history/Markdown and 92-task readiness checks passed; 24 DONE, M3-T04 alone READY, 67 NOT STARTED |

Development checks initially exposed test-helper assumptions about existing registry,
budget/state field names and immutable scope patching, corrected against source without
production contract changes. Mypy required typed optional cwd kwargs. A copied fresh-wheel
test command initially used relative checkout paths from /tmp; corrected absolute copies
and executed all 99 cases successfully. Final required checks pass; no outstanding failure,
weakened gate or blocker. Remaining coverage branches are defensive malformed composition,
setup/detection/deadline and representation paths. Network guards allow AF_UNIX plumbing;
reviewed harmless local interpreter children are not network sandboxed.

### Acceptance mapping and handoff

| Criterion | Concrete evidence |
| --- | --- |
| Trusted operational crawl_web | Detected 1.8.0 registry binding and exact fixed argv/env/cwd graph fixture tests; empty planner schema/injection denials |
| Initial/contact scope before execution | Primary numeric URL + independent IP checks, rejected/no-call cases, post-pacing/final scope changes and cross-origin no-contact graph |
| Containment rejects unsafe modes | Numeric-only preflight rejects hostname/bare forms; depth-zero source boundary prevents htmx/self/JS/outside links; redirects disabled |
| Bounded depth/count/rate/time/output | Strict operator bounds, depth/page/fact/capture/normalization limits, pacing/shared budgets/session/action timeout and cancellation cleanup tests |
| Deterministic provenance and normalization | Duplicate/order fixture equality, method/source/form/JS data, generic endpoint/evidence hash/time/execution refs and real state/dedup ingestion |
| No state-changing forms or JS actions | Forms submitted=false; POST/htmx/JS endpoints/outside/redirect instructions retained as data, absent from execution/contact set |
| Canonical offline errors | Fake missing/timeout/nonzero/malformed/partial/empty/output/resource tests; full guarded and installed-wheel validation |

M0/M1/M2 and M3-T01–M3-T03 DONE; M3-T04 READY/unstarted; no active task/blocker.
No Ferox/FFUF or later implementation begun. No additional follow-up task needed to
close this supported profile; hostname containment remains an explicitly unavailable mode.

Commit reference: the single focused commit containing this entry, titled
`feat(web): add Katana crawler adapter`; resolve with
`git log -1 --format=%H --grep="^feat(web): add Katana crawler adapter$"`.
Final response reports actual hash/clean tree. No amend/squash/history rewrite/second
task commit or push.


## 2026-10-07 — M3-T04 — Feroxbuster content-discovery adapter

Status: DONE. Objective: trusted bounded recursive content path discovery with small
approved wordlist, strict request/depth/rate/thread/time/output and contact containment.
Startup confirmed HEAD d103418d5705e8035cf9e39f920c29a8e65f4a5c, clean working/staged
tree, M0/M1/M2 and M3-T01–M3-T03 DONE, M3-T04 READY, no active task/blocker.
M3-T04 alone transitioned IN PROGRESS and now DONE; M3-T05 only becomes READY.

### Changes and decisions

- New tools/feroxbuster.py, feroxbuster_models.py and feroxbuster_parser.py implement
  existing discover_content/active_safe without changing base registry/capability enums.
- Detected Linux Feroxbuster 2.13.1, source commit
  aa8e1335801e91d98ce0d4fd148c2159a667a83b. Numeric HTTP(S) directories only; original
  representations, every generated URL and independent numeric address revalidate.
- Strict empty planner input. Trusted frozen settings and built-in four-path small-v1
  profile/hash; private adapter-created wordlist or admitted prefix only. No arbitrary
  paths/flags/headers/proxy/files/methods/shell; no automatic installation.
- Tool no-recursion/no-extraction/no-redirect/no-wildcard/no-state fixed GET profile.
  Adapter finite sorted 2xx directory queue, max depth 3/directories 8/logical starts 56;
  three startup/base GETs count per call. Token rate 1–4, threads 1–2, startup burst
  and inter-process completion pacing documented. Reqwest 0.12.22 same-URL HTTP/2
  protocol repair (up to two retries) shares original timeout; logical counts are not
  strict packet/transport-attempt rates. No status-based retry or origin widening.
- Private environment/cwd and rejection of global/resolved-binary scanner config
  prevent ambient true options which cannot be disabled by safe defaults.
- Generic Asset/Endpoint/HTTP Observation/untrusted Evidence preserve URL/status/length/
  Location/method/source directory/body completeness, subject/UTC/execution/hash lineage.
  Redirect membership is evidence only. No path/status implies vulnerability or scope.
- Deterministic duplicate/order/conflict, partial/malformed/empty/unreported and canonical
  unavailable/nonzero/timeout/setup/resource contracts. Shared atomic policy/dedup/budgets,
  aggregate two-stream output and existing runner deadline/cancellation; state ingestion
  demonstrated without adding orchestration or changing existing contracts.
- 121 offline guarded cases and reserved source-shaped fixture/README. Feroxbuster
  contract + ADR 0018; configuration/data/security/tool/testing/architecture/README,
  relevant HTTPX/common-file/Katana/TLSX role comparisons, CHANGELOG and lifecycle docs.
  All existing production Python files, dependencies, CLI and M2 pipeline byte unchanged.

### Actual validation

Python 3.14.6, repository .venv; no Python 3.12 or live scanner/target run. Package
provisioning and upstream primary source review used network; no reconnaissance target
contact or Feroxbuster install/run. Host ambient scanner config is present: fakes
simulate an isolated operator filesystem and separately prove config rejection;
production rejects that unsupported ambient mode. Logs/scripts outside checkout:
/tmp/recon-m3t04-validation.

| Check | Actual result |
| --- | --- |
| Setup | Python version, editable pip install -e '.[dev]' and pip check passed |
| Focused | Feroxbuster/registry: 219 passed; 121 new Feroxbuster cases |
| Full | pytest: 2,663 passed |
| Network/DNS blocked | Pre-collection guards, Groq key absent: 2,663 passed |
| Coverage | coverage run pytest: 2,663 passed; overall 96%, 5,135 statements / 1,740 branches; adapter 93%, parser 94%, models 100% |
| Lint/format/types | Ruff check and format (156 files); strict Mypy (71 source modules) passed |
| Build/CLI | Isolated sdist/wheel and editable/fresh-wheel inert recon-agent passed |
| Fresh wheel | External venv/pip check, guarded cold imports/origins/empty registry/inert composition; 121 installed-wheel network-blocked cases passed |
| Artifacts/security | All existing production source byte parity, AST execution boundary, artifact/secrets, wheel/sdist source/three-dependency metadata parity passed |
| Closeout | Individual acceptance/diff/whitespace, append-only history, Markdown and 92-task readiness passed; 25 DONE, M3-T05 alone READY, 66 NOT STARTED |

Initial focused development exposed host-global config presence and an original empty
fragment lost by scope canonicalization. Fake filesystem isolation and explicit global
config-rejection tests corrected fixture assumptions; original target representation is
now checked before conversion. A test helper duplicate URL argument was corrected.
Final focused/full gates passed; no criterion weakened or unresolved validation failure.
Remaining new coverage branches are defensive/optional composition/representation and
repeat/aggregate/deadline guards. Parent network guards allow AF_UNIX event-loop plumbing;
reviewed harmless interpreter subprocess tests are not OS network sandboxed.

### Acceptance mapping and handoff

| Criterion | Evidence |
| --- | --- |
| Operational trusted discover_content | Explicit detected registry instance, fixed executable/argv and generic output; exact profile/registry fixture test |
| Scoped service/contact containment | Numeric URL/IP and each generated URL checks before write/call; excluded/outside/unsupported/start-hook/post-pacing denials with untouched fake runner |
| Only approved wordlist/modes | Empty strict planner schema, operator bounded literal small-v1, private wordlist contents/hash and flag/path/profile injection tests |
| Request/depth/rate/concurrency/time bounds | Three-start overhead/prefix budgets, depth 0–3 finite queue, directory/request caps, fixed positive tool depth, rate/threads/pacing, shared budgets/deadline/cancellation tests |
| Defaults avoid massive scans | Four literal approved words, four directories / 28 logical GET upper bound; no wildcard/extraction/collection/native recursion |
| Outside redirects prevented | Fixed no-follow/no-extraction source profile; same/external Location retained without scheduling and redirect_authorized=false |
| Normalized evidence and limitations | 200/204/301/403/404 fixtures, source/GET/length/Location and caller IDs/time/hash, deterministic duplicates/conflicts/partial/empty/body limits; real state ingestion/dedup |
| Canonical offline failures | Missing/unverified/config/nonzero/timeout/malformed/setup/output/budget/cancellation guards; full guarded and installed-wheel tests |
| Task boundary | Existing production source protected byte-for-byte; no FFUF/M3-T05/M3-T06/later planner/loop/persistence/reporting/real CLI |

M0/M1/M2 and M3-T01–M3-T04 DONE; M3-T05 READY/unstarted; no active task/blocker.
No added future task needed for supported numeric profile. Hostname/ambient-config
modes remain unavailable, with rate/transport/local-installation limits explicit.

Commit reference: the single focused commit containing this entry, titled
`feat(web): add Feroxbuster content discovery`; resolve with
`git log -1 --format=%H --grep="^feat(web): add Feroxbuster content discovery$"`.
Final response reports actual hash/clean tree. No amend/squash/history rewrite/second
task commit or push. Stop after M3-T04.


## 2026-10-07 — M3-T05 — FFUF adapter

Status: DONE. Objective: specialized explicitly safe FFUF discovery complementary
to default recursive Feroxbuster. Startup confirmed HEAD
1cab0c13d0ae8f5cb8fd3fecb95f42b6f77c969f, clean working/staged tree,
M0/M1/M2 and M3-T01–M3-T04 DONE, M3-T05 READY, no active task/blocker.
M3-T05 alone transitioned IN PROGRESS and now DONE; M3-T06 only becomes READY.

### Changes and decisions

- New tools/ffuf.py, ffuf_models.py and ffuf_parser.py implement existing
  discover_content/active_safe with mandatory profile=vhost_names. PLAN/docs define
  no separate FFUF capability or mandatory mode list; ADR 0019 selects one narrowly
  safe specialized purpose. No new capability enum/registry architecture.
- Detected Linux FFUF 2.1.0 release. Numeric HTTP(S) endpoint and independent IP,
  original representation and operator suffix scope-check before reservation and
  each invocation after pacing. Candidate Host values are data at the numeric peer;
  no DNS/separate vhost contact, hostname URL/SNI fuzzing or new authorization.
- HEAD-only internal Host: FUZZ with fixed four-label application catalog
  www/api/static/dev plus scoped canonical operator suffix. Private one-candidate
  wordlists and catalog hash/admitted prefix provenance. Planner cannot supply raw
  flags/files/headers/templates/wordlists/FUZZ positions or request/body/method options.
- No content_paths overlap, parameter_names, authentication/credentials/spraying,
  POST/body fuzzing, recursive jobs/calibration/scrapers/proxy/replay/redirect contact.
  Registry permits only one selected discover_content adapter; Ferox remains default
  recursive discovery, FFUF explicit specialized composition. Existing semantic
  state/history dedup denies repeats; no automatic fallback or M3-T06 implementation.
- Source-reviewed FFUF retries failed Execute once outside its rate ticker. One
  candidate per child counts two attempts; max_requests 2–8 admits a bounded prefix.
  One worker and at most four sequential children, positive rate 1–4, inter-group
  completion pacing 2/R or stricter shared interval. Retry burst/same-peer Go transport
  repair/packet/OS limits are documented. One existing atomic budget permit and
  aggregate two-stream capture/normalized-output/action/session deadline apply.
- Private complete environment/cwd isolate ambient ffufrc/legacy HOME/history/scraper/
  proxy/credential state. Absolute executable/literal argv use existing runner only;
  no shell, installation or dependency change. Cleanup/cancellation canonical contracts.
- Generic web_resource Asset/contact HEAD Endpoint/HTTP Observations/untrusted Evidence
  retain path/candidate/status/HEAD header length/type/Location/profile/tool/capability/
  version/time/execution/subject/hash. No contacted hostname subjects or vhost/vulnerability
  inference. HEAD word/line body counts omitted as unreliable. Redirect membership
  remains data with explicit false authority. Partial/unreported/malformed/conflicting/
  empty/structured failures retain evidence/state semantics.
- 115 guarded offline FFUF cases, source-shaped base64-input JSONL and fixture README.
  FFUF contract/ADR and role/subsystem/security/config/data/testing/lifecycle docs,
  README/CHANGELOG. All prior production Python files, dependencies, policy/runner/
  registry/domain/CLI/M2 workflow remain byte-for-byte unchanged.

### Actual validation

Python 3.14.6; no Python 3.12 or live FFUF/target run. Upstream primary source review
and package provisioning used network, never reconnaissance target contact. No scanner
installed or executed. Logs/scripts outside checkout: /tmp/recon-m3t05-validation.

| Check | Actual result |
| --- | --- |
| Setup | Python version, editable pip install -e '.[dev]' and pip check passed |
| Focused | FFUF/registry: 213 passed; 115 new FFUF cases |
| Full | pytest: 2,778 passed |
| Network/DNS blocked | Pre-collection socket/DNS guards, Groq key absent: 2,778 passed |
| Coverage | coverage run pytest: 2,778 passed; overall 96%, 5,446 statements / 1,854 branches; FFUF adapter 91%, parser 97%, models 100% |
| Lint/format/types | Ruff check and format (163 files); strict Mypy (74 source modules) passed |
| Build/CLI | Isolated sdist/wheel and editable/fresh-wheel inert recon-agent passed |
| Fresh wheel | External venv/pip check, guarded cold imports/origins/empty registry/inert composition; 115 installed-wheel network-blocked cases passed |
| Artifacts/security | Existing production source byte parity, AST execution boundary, artifact/secrets, wheel/sdist source and unchanged three-runtime-dependency metadata parity passed |
| Closeout | Individual acceptance/final diff/whitespace, append-only history, changed Markdown and 92-task dependency/readiness passed; 26 DONE, M3-T06 alone READY, 65 NOT STARTED |

Initial development checks exposed strict Literal[1] accepting bool, a wrong test Scope
field name and a normalized-size fixture threshold assumption. Concurrency now uses
strict int bounded to exactly one; fixtures/imports/threshold were corrected. All
final required checks passed; no acceptance gate weakened or unresolved blocker.
Remaining coverage branches are defensive composition/detection/representation,
optional environment and repeated/aggregate/deadline guards. Network guards allow
AF_UNIX event-loop plumbing; reviewed harmless local interpreter children are not
OS network sandboxed. Supported compatibility is source/fixture review only.

### Acceptance mapping and handoff

| Criterion | Evidence |
| --- | --- |
| Trusted operational FFUF capability | Explicit detected registry binding, adapter-owned exact argv/env/cwd and fixture normalization |
| Explicit safe modes/purpose/limits | Required vhost_names schema, HEAD/Host catalog contract/ADR; all other profiles/templates/flags/files denied before fake runner |
| Complement Ferox without default duplication | One-selected-adapter registry conflict test, no empty/default/path FFUF profile or fallback; unchanged Ferox/pipeline and real repeated-action dedup test |
| Contact and scope containment | Original numeric URL + independent IP/suffix checks before setup/call; excluded/outside/unsupported/start-hook/post-pacing denials leave execution untouched |
| Bounded requests/rate/concurrency/time/output | Two-attempt candidate allowance, prefix caps, fixed one worker/sequential children, pacing/shared budgets, aggregate capture/normalization, timeout/cancellation cleanup cases |
| Planner cannot choose wordlists/FUZZ/credential behavior | Strict profile/extra-field denial, fixed catalog/suffix/private files, trusted settings bounds, no auth/credential/body/parameter/path mode tests |
| Generic evidence and discovery non-authority | Contact-only HEAD Endpoint, candidate/Location/status/length/source/caller/hash lineage, no vulnerability inference; unauthorized descendant/redirect and real state ingestion cases |
| Canonical parser/process outcomes offline | Duplicate/conflict/malformed/partial/empty/unavailable/nonzero/timeout/resource fixtures; full guarded and installed-wheel cases |

M0/M1/M2 and M3-T01–M3-T05 DONE; M3-T06 READY/unstarted; no active task/blocker.
No added future task required to close this supported mode. Numeric-only HEAD and
fixed catalog limits are explicit; no M3-T06/later code or planner/runtime begun.

Commit reference: the single focused commit containing this entry, titled
`feat(web): add FFUF specialized fuzzing adapter`; resolve with
`git log -1 --format=%H --grep="^feat(web): add FFUF specialized fuzzing adapter$"`.
Final response reports actual hash/clean tree. No amend/squash/history rewrite/second
task commit or push. Stop after M3-T05.


## 2026-10-08 — M3-T06 — Web asset deduplication and URL canonicalization

Status: DONE. Objective: deterministic shared web contact identity and deduplication
without changing authorization or adding scanner/runtime capabilities. Startup verified
HEAD 4a3844fae4e51934b115c0197bf52a8ef1215e71, clean working/staged tree,
M0/M1/M2 and M3-T01–M3-T05 DONE, M3-T06 READY, no active task/blocker.
Only M3-T06 transitioned IN PROGRESS and now DONE. M3 closes; M4-T01 READY only.

### Changes and decisions

- New domain/web.py defines pure canonical_web_url, portable WebAssetIdentity/web-v1
  (URL, exact method, optional explicit Host variant) and WebAssetDiscovery reference
  records. Reject malformed/unsupported authority, userinfo, authority percent escapes,
  alternate numeric IPv4, invalid IPv6 brackets/zones/mapped forms, unsupported encoding.
- Collapse scheme/host case, established DNS root-dot aliases, conventional numeric
  host spelling, decimal/default ports, empty paths and validated fragments. Preserve
  exact nonempty paths/slashes/dot segments, nondefault ports, query order/duplicates/
  bare keys/empty values/explicit empty query, and percent escape spelling/case/octets.
  No decoding, query sorting, browser navigation repair, DNS or authorization.
- New domain/web_state.py and opt-in Endpoint.web_identity / ReconState.web_assets /
  find_web_asset derive sorted provenance-preserving identities over actual existing
  M3 generic outputs. No raw record deletion/rewriting, second index/ledger, ownership
  change, contact inference from discovery alone, or loss of conflicting source facts.
  Known source response fields support reported contact; sitemap discoveries and
  endpoints alone remain seen. FFUF candidate Host and HEAD/GET/case distinctions survive.
- Existing policy/dedup.py reuses shared URL identity for primary and declared secondary
  URL fields of probe_http, inspect_common_files, crawl_web and discover_content only.
  Original scope/schema checks precede normalization; original strings preserve empty
  query markers. All non-web target semantics and M1-T08 capability/schema/default/
  array/scalar/lifecycle/retry/atomic admission rules remain unchanged. Adapter-specific
  scanner profiles/contact checks and finite internal queues are unchanged.
- New offline URL/method/Host/state/cross-normalizer tests; existing action tables now
  verify intended default-port/fragment equivalence, conservative distinctions, non-web
  parity and malformed-encoding denial. All five actual adapters reject equivalent
  requests before fake runner/transport calls with explicit dedup diagnostic, canonical
  error and unchanged spending counters (elapsed remaining session time accounted for).
  Domain public-export expectation updated for the three deliberate new exports.
- Precise normative web identity contract / ADR 0020; architecture/data/security/state/
  dedup/tool/config/testing and five adapter docs, CHANGELOG and task lifecycle records.
  Reconciled obsolete documentation claiming M3-T06 remained unimplemented.
- All production source outside six task-owned domain/policy files remains byte-identical
  to startup, including ScopeValidator, adapters/parsers/native transports, runner,
  registry, budgets/config/dependencies, M2 orchestration, provider/CLI and future modules.
  No scanner capability, Groq/planner/loop/persistence/reporting/real CLI or M4 source work.

### Actual validation

Python 3.14.6; no Python 3.12/live scanner/target/Groq run. Dependency provisioning and
isolated build may use package-index network; canonicalization/tests perform no target
contact. Logs/scripts outside checkout: /tmp/recon-m3t06-validation.

| Check | Actual result |
| --- | --- |
| Setup | Python version, editable pip install -e '.[dev]' and pip check passed |
| Focused | URL/action/five-web-adapter/domain: 879 passed |
| Full | pytest: 2,887 passed |
| Network/DNS blocked | Guards before collection, Groq key absent: 2,887 passed |
| Coverage | coverage run pytest: 2,887 passed; overall 96%, 5,619 statements / 1,924 branches; web.py 97%, web_state.py 92% |
| Lint/format/types | Ruff check/format (168 files); strict Mypy (76 source modules) passed |
| Build/CLI | Isolated sdist/wheel and editable/fresh-wheel inert recon-agent passed |
| Fresh wheel | External venv/pip check, guarded cold imports/origins/empty registry/inert composition/shared identity/state reconstruction; 879 installed-wheel network-blocked tests passed |
| Artifacts/security | Protected source parity, AST execution boundary, artifact/secrets, wheel/sdist source and unchanged runtime dependency metadata parity passed |
| Closeout | Individual acceptance/final diff/whitespace, append-only history, Markdown links/fences and 92-task readiness passed; 27 DONE, M4-T01 alone READY, 64 NOT STARTED |

Development checks exposed incorrect new budget snapshot assertions (time sampling,
then dataclass access), required formatting and the old public-export expectation.
Corrected assertions to verify every spending counter, and updated the expected API;
all final checks pass. No criterion or validation gate weakened; no unresolved blocker.
Remaining uncovered new branches are defensive unsupported composition/data forms.
Network guards allow AF_UNIX event-loop plumbing; reviewed harmless interpreter children
in the existing runner suite are not OS network sandboxed. Scanner compatibility and
transport/containment limitations remain those of the previously completed adapters.

### Acceptance mapping and handoff

| Criterion | Evidence |
| --- | --- |
| Equivalent URLs collapse deterministically | Shared canonical table/idempotence, full JSON key, cross-five-normalizer state grouping and reverse-order/reconstructed-state equality |
| Meaningful path/query/method distinctions survive | Scheme/nondefault port/path case/slashes/dot segments/query order/duplicate/bare/empty/escape tables, exact method case and FFUF Host variants |
| Malformed/ambiguous authority fails closed | Userinfo/encoded host/suffix/bracket/zone/mapped/alternate IPv4/port/escape cases; invalid whole projection and atomic action admission leave raw state untouched |
| Canonicalization cannot authorize outside host | Explicit original/canonical ScopeValidator outside/suffix/IP rejection, forbidden scope calls during identity, DNS/socket/process guards and byte-identical scope implementation |
| Repeated equivalent crawl/fuzz actions do not dispatch | Katana/Feroxbuster/FFUF (plus HTTPX/common-file) real registry/policy/state/dedup alias tests: explicit dedup Failure before fake call/spending |
| Shared M3 integration without raw-evidence mutation | Actual five normalizers, Endpoint/Observation provenance, seen/contact separation, portable derived records and unchanged raw dumps/hashes |
| Task boundary and closure | No new scanner/runtime capability, all baseline/wheel/security checks pass; M3 DONE, M4-T01 READY/unstarted, no active task/blocker |

No added follow-up task is needed. Fixed supported grammar and advisory contact claims
are documented; future scheduling must use current scope/policy/budgets and existing
atomic admission. Stop after M3-T06.

Commit reference: the single focused commit containing this entry, titled
`feat(web): canonicalize and deduplicate web assets`; resolve with
`git log -1 --format=%H --grep="^feat(web): canonicalize and deduplicate web assets$"`.
Final response reports actual hash/clean tree. No amend/squash/history rewrite/second
task commit or push.

## 2026-10-08 — M4-T01 — Protocol capability framework

Status: DONE. Objective: deterministic normalized Service → protocol metadata
capability contracts, without collectors or execution. Startup verified HEAD
624c7cb0bee630b230c4396f186214105a561fdb and clean working/staged tree,
M0/M1/M2/M3 DONE, M4-T01 READY, no active task/blocker. Only M4-T01 transitioned
IN PROGRESS → DONE; only dependent M4-T02 becomes READY/unstarted.

### Changes and decisions

- domain/protocols.py: finite SSH/SMB/FTP/SMTP/database ProtocolFamily; strict frozen
  ProtocolMetadataInput (family/port/tcp only); bounded ProtocolMetadataOutput with
  existing Service/metadata Observation/untrusted Evidence. Unique IDs, capability,
  asset/source/execution/evidence linkage validation; no facts or lineage invented.
- tools/protocols.py: frozen ProtocolCapabilityContract and sorted finite catalog,
  pure select_protocol_capability(Service). Revalidates constructed/copied records;
  exact recognized ASCII case-insensitive TCP name required on every port. Explicit
  normalized aliases; exact recognized products only veto conflicts, including DB
  identity disagreements. Unknown/composite/unreviewed/UDP/malformed services return
  None. No port-only fallback or product/version/banner substring inference.
- Existing PLAN/CapabilityId inspect_protocol is retained with semantic family
  parameters. Share CapabilityDescriptor/active_safe and strict AdapterDefinition
  schema conventions; contract catalog contains no availability and registers no
  adapters. Default operational registry remains empty; known missing adapter returns
  tool_unavailable through current ActionPolicyValidator. One adapter per capability
  remains the existing cardinality; future protocol composition/profile checks stay
  with M4-T02+. Relevance never authorizes or triggers any action.
- 115 new offline normalized Service/schema/provenance cases, immutable/deterministic
  catalog and hostile/conflicting/unknown/port precedence rules. Runtime guards and
  forbidden policy/scope/resource/state calls prove pure selection. Test-only metadata
  schema adapter (no execute/collector) exercises current unavailable/allowlist/scope/
  parameter/budget/history denials without dispatch or spending. Hostile evidence text
  remains data, preserving original source, time, execution and artifact references.
- Normative protocol contract and ADR 0021; architecture/tool/security/data/state/
  testing docs, CHANGELOG, PLAN clarification and lifecycle reconciliation. Explicit
  user abstraction-only instruction overrides initial PLAN scoped-dispatch/fake-module
  wording: no production dispatch or operational fake modules were introduced.
- Every previously tracked production file is byte-identical to startup. Registry,
  policy/scope/budgets/dedup/state, adapters/parsers/runner/workflow/config/dependencies,
  CLI/provider/persistence/reporting are protected and unchanged. No M4-T02+ work.

### Actual validation

Python 3.14.6; no Python 3.12 or live scanner/target/Groq run. Package installation and
isolated build may provision dependencies from package indexes; framework/tests make
no network contact. Logs/scripts are outside checkout: /tmp/recon-m4t01-validation.

| Check | Actual result |
| --- | --- |
| Setup | python --version: 3.14.6; system editable install initially refused OS PEP 668; documented .venv editable dev install and pip check passed |
| Focused | Protocol/registry: 213 passed (115 new protocol cases) |
| Full | pytest: 3,002 passed |
| Network/DNS blocked | Pre-collection guards, Groq key absent: 3,002 passed |
| Coverage | coverage run pytest: 3,002 passed; report: 96% overall, 5,684 statements / 1,944 branches; both new modules 100% |
| Lint/format/types | Ruff check and format (173 files), strict Mypy (78 source modules) passed |
| Build/CLI | Isolated sdist/wheel build, editable/fresh-wheel inert recon-agent passed |
| Fresh wheel | External venv/pip check; guarded cold imports/origins/empty registry/protocol and shared web semantics passed; 213 copied installed-wheel blocked cases passed outside checkout |
| Additional wheel run | Initial wheel tool-suite command used checkout cwd: 1,418 passed; focused copied tests then confirmed outside checkout |
| Artifacts/security | Protected source parity, AST no execution/provider boundary, artifact/secrets, wheel/sdist source and unchanged dependency metadata parity passed |
| Closeout | Individual acceptance/final diff/whitespace, append-only history, Markdown links/fences and 92-task readiness passed; 28 DONE, M4-T02 alone READY, 63 NOT STARTED |

No validation gate or acceptance criterion weakened; all required final checks pass.
Network guards permit AF_UNIX event-loop plumbing; existing harmless local interpreter
children are reviewed but not OS network sandboxed. Selection does not assert remote
protocol truth or that a safe DB exchange exists. Future profiles must revalidate
service relevance, current policy/scope/history/resources and actual numeric contact.

### Acceptance mapping and handoff

| Criterion | Evidence |
| --- | --- |
| Only predefined relevant capabilities selected | Finite exact-name TCP mapping and five typed contracts under existing inspect_protocol; deterministic normalized fixtures |
| Unknown/ambiguous protocols create no executable modules | None for missing/unsupported/composite/conflicting/malformed records; no product/port fallback, adapter or dispatcher |
| Every request still passes scope/budgets | Existing validator untouched; explicit test-only binding scope/schema/budget/history/availability denials with unchanged counters and no resolution/runner calls |
| Metadata results retain source/evidence | Common output lineage validator and round-trip fixture preserve source/execution/time/evidence/untrusted hostile text |
| Fake framework runs offline | Test-only schema composition and normalized Service/metadata fixtures under runtime/contact guards; full/blocked/installed-wheel passes |
| User security/registry boundary | No credentials/auth/commands/exchanges/Groq/network/process or automatic actions; no false future adapter availability; existing source parity |
| Complete validation and lifecycle | All required final checks pass; M0/M1/M2/M3 DONE, M4-T01 DONE, M4-T02 READY/unstarted; no active task/blocker |

No additional follow-up task or blocker. Protocol exchange/profile/router choices are
future owning tasks, not implemented here. Stop after M4-T01.

Commit reference: the single focused commit containing this entry, titled
`feat(protocols): establish protocol capability framework`; resolve with
`git log -1 --format=%H --grep="^feat(protocols): establish protocol capability framework$"`.
Final response reports actual hash and clean tree. No amend/squash/history rewrite,
second task commit or push.

## 2026-10-08 — M4-T02 — SSH metadata capability

Status: DONE. Objective: operational trusted unauthenticated SSH metadata under
inspect_protocol/family=ssh, without login or command execution. Startup verified
HEAD 422c380338ffeca494be2a131a155dcae197104c, clean working/staged tree,
M0/M1/M2/M3 and M4-T01 DONE, M4-T02 READY, no active task/blocker.
Only M4-T02 transitioned IN PROGRESS → DONE; M4-T03 alone becomes READY/unstarted.

### Changes and decisions

- tools/ssh.py: standalone SshAdapter/native_ssh using M4-T01 inspect_protocol SSH
  descriptor and specialized strict semantic schema. Immutable 1–64 trusted observed
  Service/host/numeric bindings validate SSH relevance and unique subject/port; request
  asset/port/family/transport must match. Numeric subjects cannot substitute addresses.
- Current registry binding and ActionPolicyValidator/risk/schema/real dedup/shared
  budget eligibility, independent subject/contact ScopeValidator and one atomic charged
  reservation gate every action. Recheck current registry/name/address scope after
  trusted on_started, immediately before one connection. No scope mutation or DNS.
- tools/native_ssh.py: injected SshBannerTransport/native receive-only asyncio stream
  with explicit numeric host/service flags/family, one-byte reads, finite application
  capture/line/preamble limits, timeout and synchronous close/abort on every outcome.
  Zero application bytes sent; no client identification, binary packet reader/writer,
  KEX, host-key/algorithm collection, auth/credential/key-file/session/command path.
- tools/ssh_parser.py and ssh_models.py: RFC-shaped bounded identification grammar,
  exact raw/banner/software/protocol/comment/preamble data; explicit complete OpenSSH/
  dropbear hint grammar. Valid 2.0/1.99 identification completes this narrow profile;
  other numeric protocol versions retain partial metadata with parse_failed. Malformed/
  oversized/incomplete data, refused/unreachable/empty close, deadline and cancellation
  preserve existing canonical failure/cleanup semantics without raw exception leakage.
- SshOutput extends common ProtocolMetadataOutput: original Service, generic metadata
  Observation/untrusted Evidence, subject/port/profile/capability, caller UTC time/
  execution, raw base64, memory snapshot/hash and collected-field limitations. No
  vulnerability, authentication, host-key fingerprint or negotiated algorithm is inferred.
  Caller owns lifecycle/terminal ActionResult/atomic ingestion; actual state/dedup
  regression proves completed aliases deny before a second contact or reservation.
- Two new offline test modules (116 SSH/native cases), synthetic escaped-JSON fixture
  greetings/README. Fake streams forbid every write/writelines/drain; unread KEX/userauth
  bytes and transport authentication/send sentinels explicitly prove no authentication.
  Scope/name/address/service/port/credential/raw-option/registry/risk/budget/history
  denials, errors, provenance, bounds, cancellation and deadline regressions pass.
- SSH profile contract and ADR 0022; protocol/tool/security/architecture/data/execution/
  state/testing docs, CHANGELOG, precise PLAN profile and lifecycle records. Native
  receive-only inspection was chosen because no SSH implementation was previously
  decided; a full client/library/KEX profile would expand the required minimum.
- All previously tracked production files remain byte-identical to startup, including
  M4-T01 framework/domain, registry/policy/scope/budgets/dedup/state, runner/previous
  adapters/parsers/native transports, discovery/config/dependencies/CLI/providers.
  No generic router, future protocol, Groq/planner/loop/storage/reporting/real CLI work.

### Actual validation

Python 3.14.6. Editable install uses the documented .venv; package provisioning/build
isolation may access package indexes, but tests never contact targets or Groq. RFC
4253 sections 4.2/5.1 and local asyncio numeric-resolution implementation were reviewed;
no live SSH/server/binary/library or Python 3.12 run. Logs/scripts are outside checkout
under /tmp/recon-m4t02-validation.

| Check | Actual result |
| --- | --- |
| Setup | Python 3.14.6; editable pip install -e '.[dev]' and pip check passed |
| Focused | SSH/native/framework/registry: 329 passed (116 new cases) |
| Full | pytest: 3,118 passed |
| Network/DNS blocked | Pre-collection guards, Groq key absent: 3,118 passed |
| Coverage | coverage run pytest: 3,118 passed; report: 96% overall, 5,932 statements / 2,028 branches; native/parser 100%, adapter 95%, models 92% |
| Lint/format/types | Ruff check and format (182 files), strict Mypy (82 source modules) passed |
| Build/CLI | Isolated sdist/wheel, editable/fresh-wheel inert recon-agent passed |
| Fresh wheel | External venv/pip check, guarded cold imports/origins/empty registry/inert SSH-only composition; 329 copied installed-wheel blocked cases passed outside checkout |
| Artifacts/security | Protected source parity, AST no writes/auth/process/provider boundary, artifact/secrets, wheel/sdist source and unchanged runtime dependency metadata parity passed |
| Closeout | Individual acceptance/final diff/whitespace, append-only history, Markdown links/fences and 92-task readiness passed; 29 DONE, M4-T03 alone READY, 62 NOT STARTED |

Development checks exposed a new test syntax error, incorrectly chosen output-overflow
threshold, and dedup assertions initially seeing the earlier budget rate rejection or
wrong expected error wording. Corrected the tests to check actual fixed contracts and
use explicit test-only rate capacity for dedup isolation; default rate/host/action/output
admission is tested separately. Git would normalize initial raw CRLF text fixtures;
escaped JSON now preserves exact wire bytes across checkouts. Final focused/full/
blocked/coverage checks use that portable fixture form; no criterion or gate weakened.

Uncovered adapter/model branches concern defensive malformed trusted metadata, stale
constructed service/binding/reservation and inconsistent constructed output. No missing
network or authentication path is hidden by coverage. Standard asyncio/OS buffering and
in-flight connect cleanup limits are explicit; AF_UNIX is permitted for test loop plumbing
and existing harmless interpreter children are not OS network sandboxed. No live
compatibility claim; servers waiting on client identification time out without fallback.

### Acceptance mapping and handoff

| Criterion | Evidence |
| --- | --- |
| Operational SSH-only capability | Explicit native_ssh inspect_protocol registration; real policy/resources and injected native stream exchange, fresh-wheel composition/tests |
| Validated target/port/service and scope | Strict SshInput; exact observed SSH host/port binding; separate numeric ScopeValidator; exclusions/unknown/mismatch/malformed/credential/option denials before contact/spending |
| Only approved unauthenticated metadata | server_identification_v1 is receive-only; write/drain/auth sentinels, unread KEX/userauth bytes, no client/auth/session/command/key API or library |
| Generic normalized untrusted provenance | Existing Service unchanged, common metadata envelope, deterministic banner/raw/source/time/execution/service/evidence/hash and actual state-ingestion/dedup tests |
| Canonical malformed/closed/timeout/partial failures | Fake malformed/oversized/refused/EOF/deadline cases; unsupported versions explicit partial parse_failed, bounded retention and cancellation cleanup |
| Full baseline and task boundary | All required final checks pass; earlier production byte parity; M0/M1/M2/M3 and M4-T01–M4-T02 DONE, M4-T03 READY/unstarted; no active task/blocker |

No new follow-up task or blocker. Profile explicitly does not collect keys/algorithms
or complete SSH negotiation; no broad client/authentication fallback is planned by
this task. Future protocols/composition belong to M4-T03+. Stop after M4-T02.

Commit reference: the single focused commit containing this entry, titled
`feat(protocols): add SSH metadata inspection`; resolve with
`git log -1 --format=%H --grep="^feat(protocols): add SSH metadata inspection$"`.
Final response reports actual hash and clean tree. No amend/squash/history rewrite,
second task commit or push.

## 2026-10-08 — M4-T03 — SMB metadata capability

Status: DONE. Objective: trusted bounded safe SMB metadata through existing
inspect_protocol/family=smb, without authentication or remote modification. Startup
verified HEAD ce1942e5642809007e3e20219d4d90d47a787cb2, clean working/staged tree,
M0/M1/M2/M3 and M4-T01–M4-T02 DONE, M4-T03 READY, no active task or blocker.
M4-T03 alone transitioned IN PROGRESS → DONE; only M4-T04 becomes READY/unstarted.

### Changes and decisions

- tools/smb.py: standalone SmbAdapter/native_smb using existing SMB descriptor,
  strict family/port/tcp schema, immutable finite observed-Service/subject/numeric
  bindings, exact relevance and unique host/port. Mismatched service/asset/port/family,
  port 139/netbios-ssn, credentials/operations/options reject before contact/spending.
- Current registry binding, ActionPolicyValidator risk/schema/allowlists/real dedup/
  budget eligibility, independent subject/contact ScopeValidator and one shared atomic
  reservation gate execution; recheck registry/scope after trusted start notification.
  Numeric subjects cannot substitute an address; discovery/bindings confer no permission.
- tools/native_smb.py: one numeric Direct TCP connection, exactly one fixed 112-byte
  SMB2 NEGOTIATE frame and one bounded response, then synchronous close/abort. No
  session setup/authentication (including anonymous), credential/hash/key loading,
  shares/RPC/files/read/write/delete/commands, relay/exploitation or retry/fallback.
  Fixed dialect offer 2.0.2/2.1/3.0/3.0.2 and generated client GUID are adapter-owned,
  never planner-controlled wire flags. Stream write is negotiation, never SMB WRITE.
- tools/smb_parser.py/models.py: strict framing/header/command/session/compound/transform/
  dialect/signing/buffer bounds, validated canonical protocol/access-required failures,
  deterministic selected dialect/signing/GUID/config size/raw FILETIME/opaque response
  metadata. SMB1/3.1.1/full dialect inventory/names/domain/workgroup/shares uncollected.
  No negative support claims, authenticated signing/identity verification or Findings.
- Existing Service/common ProtocolMetadataOutput/generic metadata Observation/untrusted
  Evidence preserve target/port/host/service/source/caller UTC/execution/links/base64/
  memory snapshot/hash. No raw exception leakage, state mutation, DNS or follow-up.
  Real state ingestion/completed-history dedup denies a second equivalent contact.
- Two new offline modules, 151 cases; synthetic independent hex fixtures/README.
  Exact outbound vector checks command 0/session 0 and forbids second/auth/file packets.
  Real native adapter through fake streams and real policy/scope/resources, malformed/
  denied/unavailable/timeout/cancellation/bounds/provenance/hostile values all tested.
- docs/smb-adapter.md and ADR 0023 establish reviewed finite profile (PLAN explicitly
  assigned that choice). Anonymous share/name visibility is not approved. Updated
  protocol/SSH/security/tool/architecture/data/execution/state/testing docs, CHANGELOG
  and lifecycle. SSH/SMB remain explicit alternatives under one selected adapter per
  capability; no router/default registration or fake future availability.
- Every previously tracked production file remains byte-identical, including protocol
  framework/SSH/domain/registry/scope/policy/budgets/dedup/state/runner/earlier adapters/
  workflow/config/dependencies/providers/CLI. No M4-T04+, planner/loop/storage/reporting
  or generic client work. No new dependency, binary or live target execution.

### Actual validation

Python 3.14.6, documented .venv. Package install/build provisioning may contact indexes;
default tests never contact targets/Groq. Primary Microsoft MS-SMB2 transport, synchronous
header, fixed negotiate request/response, error and SMB2-only negotiation specifications
reviewed; source links in SMB contract. No live SMB/SSH server, client/binary/library or
Python 3.12 execution. Logs/scripts outside checkout: /tmp/recon-m4t03-validation.

| Check | Actual result |
| --- | --- |
| Setup | Python 3.14.6; editable install -e '.[dev]' and pip check passed |
| Focused | SMB/native/framework/registry: 364 passed (151 new cases) |
| Full | pytest: 3,269 passed |
| Network/DNS blocked | Pre-collection guards, Groq key absent: 3,269 passed |
| Coverage | coverage run pytest: 3,269 passed; 96% overall, 6,173 statements / 2,106 branches; native/models 100%, adapter 95%, parser 98% |
| Lint/format/types | Ruff check/format (191 files), strict Mypy (86 source modules) passed |
| Build/CLI | Isolated wheel/sdist and editable/fresh-wheel inert recon-agent passed |
| Fresh wheel | External venv/pip check, guarded all-module cold imports/origins/empty registry/inert SMB-only composition; 364 copied installed-wheel blocked tests passed outside checkout |
| Artifact/security | Earlier production byte parity; fixed sole negotiate AST boundary; artifact/secret, wheel/sdist source and unchanged runtime dependency metadata parity passed |
| Closeout | Individual acceptance/final working/staged diff/whitespace, append-only history/Markdown and 92-task readiness checks passed: 30 DONE, M4-T04 alone READY, 61 NOT STARTED |

Development checks initially exposed a nonexistent test budget counter and duplicate
keyword construction in native invalid-input fixtures. Fixed test assertions/input
construction; a first text replacement missed formatter indentation and was corrected
with an explicit patch. Mypy found dialect Literal typing and an optional normalized
service-name dereference; added explicit shared dialect typing and None guard.
Final required checks all pass; no acceptance/test gate weakened. Remaining coverage
branches are defensive malformed trusted composition/stale binding/reservation/error
shapes, not an untested auth/write path. Guards precede collection and allow AF_UNIX;
existing harmless interpreter children are not OS network sandboxed. Standard asyncio
connect/OS buffering/rate limitations and no live compatibility guarantee are documented.

### Acceptance mapping and handoff

| Criterion | Evidence |
| --- | --- |
| Only named approved metadata operations | smb2_negotiate_v1 fixed NEGOTIATE builder/native sole-write assertion and independent exact vector; no generic operation input/router |
| Operational scoped validated SMB capability | Explicit real native_smb registry/schema; exact observed binding; current policy, numeric ScopeValidator and atomic budget checks; rejected inputs do not contact/spend |
| No credentials/attacks/remote modification | Strict extra-forbid schemas; no auth/session/share/file/command API; no second packet/auth/write dispatch in fakes/native adapter; no third-party client |
| Inaccessible/auth-dependent data is a limitation | Valid access/logon/more-processing/unsupported errors return fixed canonical failures; no retry/escalation; domain/workgroup/shares and unoffered dialects explicitly unknown/uncollected |
| Scope/time/request/output limits | One pinned numeric contact/request; framing bound before body read; outer/native/session deadlines and cancellation/socket/permit cleanup; host/rate/action/output denials |
| Traceable generic untrusted evidence | Original Service unchanged, exact metadata/base64/source/caller time/execution/port/snapshot hash; generic state ingestion and real history dedup regression |
| Full baseline and boundaries | All final required checks pass; earlier production source protected; M0/M1/M2/M3 and M4-T01–M4-T03 DONE; M4-T04 READY/unstarted, no active task |

No new blocker/follow-up task. Profile excludes authentication/shares/files/names/SMB1/
3.1.1/NetBIOS; no fallback/expanded client is planned by this task. Stop after M4-T03.

Commit reference: the single focused commit containing this entry, titled
`feat(protocols): add SMB metadata inspection`; resolve through Git log. Final response
reports actual hash and clean tree. No second task commit, amend/squash or push.

## 2026-10-08 — M4-T04 — FTP metadata capability

Status: DONE. Objective: bounded trusted FTP pre-authentication metadata through
inspect_protocol/family=ftp without credentials, login or file operations. Startup
verified expected HEAD dc9edb20282e1ae3b15f3bcd6a76aca98798d49f, clean working/staged
tree, M0/M1/M2/M3 and M4-T01–M4-T03 DONE, M4-T04 READY, no active task or blocker.
M4-T04 alone transitioned READY → IN PROGRESS → DONE; only M4-T05 becomes READY.

### Changes and decisions

- tools/ftp.py: explicit standalone FtpAdapter/native_ftp with strict family/port/tcp
  schema, finite immutable prior Service/subject/numeric-contact bindings, exact FTP
  relevance and asset/port matching. Current registry/policy/risk/schema/dedup and
  independent centralized subject/contact scope precede shared atomic budgets.
  Registry/scope recheck after start notification; denials do not contact or spend.
- tools/native_ftp.py: one pinned numeric control connection, initial greeting, only
  valid 220 enables one fixed argument-free FEAT, one feature reply, synchronous abort.
  No authentication (including anonymous), usernames/passwords/credentials/brute force,
  LIST/RETR/STOR/DELE/writable testing, data connections/PORT/PASV, command execution,
  arbitrary protocol options, TLS negotiation, retry/fallback or generic FTP client.
- tools/ftp_parser.py/models.py: strict bounded CRLF reply framing, UTF-8 greeting and
  ASCII feature syntax, 8192 aggregate bytes/512 line bytes/64 lines per reply, native/
  outer/session deadlines and serialized-output limit. Valid unsupported greeting or
  unavailable/auth-required/malformed FEAT preserves partial banner with canonical
  parse_failed limitation. Refused/unreachable/empty close/malformed greeting/timeout
  use existing Failure/ErrorInfo; no exception/raw diagnostic leakage or fallback.
- Original Service/common ProtocolMetadataOutput/generic metadata Observation and
  untrusted Evidence retain target/host/service/asset/port, exact banner/features/raw
  base64, narrow full-banner product/version hints, source/caller UTC/execution/links/
  memory locator/hash. AUTH TLS advertisement is true or unknown, never a TLS test
  or vulnerability inference. Unknown/instruction-like features are data, not commands.
- tests/unit/tools/test_ftp.py and test_native_ftp.py add 164 offline cases with
  synthetic escaped-JSON fixtures. Independent exact outbound vector forbids every
  login/file/data command, even when remote text advertises USER anonymous or STOR.
  Actual native adapter/fake streams/real policy/budget and generic completed/partial
  state ingestion/dedup verify authorization, provenance, failures, deadlines and cleanup.
- docs/ftp-adapter.md / ADR 0024 define the reviewed greeting_feat_v1 choice assigned
  by PLAN, exact limits and prohibited operations. Updated architecture/protocol/
  security/tool/data/execution/state/testing/SSH/SMB docs, CHANGELOG and lifecycle.
  FTP capability = unauthenticated metadata only. Explicit FTP/SSH/SMB alternatives
  respect one selected adapter per capability; no router/default registration.
- Every previously tracked production file is byte-identical, including domain/
  protocol framework/SSH/SMB/registry/policy/scope/budgets/dedup/state/runner/config/
  dependencies/workflow/provider/CLI. No SMTP/database/planner/autonomous-loop/
  persistence/reporting/real CLI or M4-T05+ implementation; no new dependency.

### Actual validation

Python 3.14.6 in documented .venv. Install/build provisioning may contact package
indexes; default tests never contact targets/Groq. Primary RFC 959 framing, RFC 2389
FEAT and RFC 4217 TLS-advertisement sources reviewed and linked in FTP contract.
No live FTP server/client/scanner/library or Python 3.12 execution. Temporary logs/
scripts: /tmp/recon-m4t04-validation, outside checkout.

| Check | Actual result |
| --- | --- |
| Setup | Python 3.14.6; editable -e '.[dev]' and pip check passed |
| Focused | FTP/native/framework/registry: 377 passed, including 164 new FTP cases |
| Full | pytest: 3,433 passed |
| Network/DNS blocked | Guards installed before collection, Groq key absent: 3,433 passed |
| Coverage | coverage run pytest: 3,433 passed; 96% overall, 6,480 statements / 2,220 branches; native/models 100%, adapter 95%, parser 98% |
| Lint/format/types | Ruff check, format (200 files), strict Mypy (90 source modules) passed |
| Build/CLI | Isolated sdist/wheel; editable and fresh-wheel inert recon-agent passed |
| Fresh wheel | External venv/pip check; guarded all-module cold imports/origins/empty registry/inert FTP composition; 377 copied installed-wheel blocked tests passed outside checkout |
| Artifact/security | Protected earlier source byte parity, sole FEAT write AST and immutable vector, artifact/secret, wheel/sdist source and unchanged runtime dependency parity passed |
| Closeout | Individual acceptance/final working/staged diff/whitespace, append-only history and Markdown/task readiness checks passed: 31 DONE, only M4-T05 READY, 60 NOT STARTED |

Development checks caught Mypy's heterogeneous **kwargs typing and a stale copied
fixture name, then a Ruff import/format issue. Corrected with explicit TypedDict,
FTP fixture naming and formatting; final required checks pass without weakened gates.
Remaining uncovered adapter/parser branches are defensive stale/composition/error
shapes, not authentication or file operations. Parent network guards allow AF_UNIX
plumbing; existing harmless interpreter children are not OS network sandboxed.
Asyncio/OS buffering and connection-rate limits, implicit FTPS and absent TLS/auth
metadata are explicit. Overflow discards malformed feature bytes but retains the
valid greeting; timeout/connection failure retains no partial payload.

### Acceptance mapping and handoff

| Criterion | Evidence |
| --- | --- |
| Operational scoped validated FTP | Explicit native_ftp registry/schema; prior observed Service/port binding; real current policy and independent numeric scope; no-contact/no-spend denial assertions |
| Only documented pre-authentication exchanges | Sole fixed FEAT after valid 220; independent fake-stream outbound vector, no second/request/auth/file dispatch; valid 120 yields banner-only partial |
| No credentials/login/file operations | Strict extra-forbid schema, no client/credential/data/command APIs or library; credential/anonymous/paths/options rejection and exact native byte regression |
| Structured malformed/timeout/unsupported/partial outcomes | Canonical ErrorInfo/Failure and explicit partial FtpOutput; greeting/feature malformed/denied/EOF/refused/unreachable/bounds/deadline/cancellation cases |
| Generic traceable untrusted facts and limits | Original Service intact; banner/hints/features/unknown TLS/source/time/execution/port/base64/hash; actual generic completed and partial state ingestion/history dedup |
| Full baseline and task boundary | All final required validation passes; earlier production unchanged; M0/M1/M2/M3 and M4-T01–M4-T04 DONE; only M4-T05 READY; no active task/blocker |

No new blocker/follow-up task. M4-T05 READY is lifecycle bookkeeping only; no SMTP
or later work begun. Stop after M4-T04.

Commit reference: the single focused commit containing this entry, titled
`feat(protocols): add FTP metadata inspection`; resolve through Git log. Final response
reports actual hash and clean tree. No second task commit/amend/squash/history rewrite/push.

## 2026-10-08 — M4-T05 — SMTP metadata capability

Status: DONE. Objective: safe SMTP greeting/ESMTP advertisements through
inspect_protocol/family=smtp, without authentication, mail or enumeration. Startup
verified expected HEAD abf1a69f5ff5f97fbdbe7896a4de91e2a8b25405, clean working/staged
tree, M0/M1/M2/M3 and M4-T01–M4-T04 DONE, M4-T05 READY, no active task or blocker.
M4-T05 alone transitioned READY → IN PROGRESS → DONE; only M4-T06 becomes READY.

### Changes and decisions

- tools/smtp.py: explicit standalone SmtpAdapter/native_smtp with immutable finite
  prior Service/subject/numeric-contact bindings, strict family/port/tcp input and
  exact SMTP/submission relevance. Current selected registry/policy/schema/dedup,
  asset/observed-port matching and independent centralized subject/contact scope
  precede shared atomic budgets. Scope/registry recheck immediately before contact;
  denial does not contact or spend. smtps and port 465 reject before contact.
- tools/native_smtp.py: one numeric plaintext connection, bounded greeting, only
  valid 220 enables the sole fixed 18-byte EHLO [192.0.2.1] request, one reply, then
  synchronous socket close/abort. Synthetic documentation-address inspection label
  avoids local hostname/DNS or planner/remote client-identity substitution. A server
  rejecting it yields partial metadata, no HELO/retry/fallback. No generic client.
- No AUTH/credentials/username/password/guessing, MAIL/RCPT/DATA/BDAT/mail sending,
  relay tests, VRFY/EXPN/user/recipient enumeration, arbitrary SMTP commands/options,
  STARTTLS handshake/QUIT or exploitation path. AUTH mechanism names and STARTTLS
  are advertisements only. No smtplib, subprocess, shell or new runtime dependency.
- tools/smtp_parser.py/models.py: strict bounded SMTP CRLF/multiline same-code
  framing, UTF-8 greeting and ASCII ESMTP extensions. First EHLO line is server text,
  never an extension; preserve exact ordered unknown/repeated extensions, conservative
  narrow Postfix/Exim version hints, advertised AUTH names, STARTTLS true-or-unknown,
  optional SIZE limit. No verified identity/functionality or vulnerability inference.
  8192 aggregate bytes/512 per line/64 lines per reply, native/outer/session deadlines,
  serialized-output bound and socket/permit cancellation cleanup apply.
- Original Service/common ProtocolMetadataOutput/generic Observation and untrusted
  Evidence retain target/host/service/asset/port, exact banner/extensions/raw base64,
  source/caller UTC/execution/links/memory locator/snapshot SHA256. Unsupported or
  malformed/incomplete EHLO retains partial banner with canonical parse_failed;
  malformed greeting/refused/unreachable/timeout use existing Failure/ErrorInfo.
  Overflow discards malformed EHLO bytes but preserves valid greeting; timeout and
  connection failures discard partial payload. Fixed diagnostics omit remote errors.
- tests/unit/tools/test_smtp.py and test_native_smtp.py add 206 offline cases with
  synthetic escaped-JSON fixtures. Independent exact native write-vector regression
  proves no auth/mail/enumeration/TLS request, even when remote text advertises these
  operations; subsequent authentication prompts are unread. Real policy/budget/state/
  dedup and injected streams verify provenance, completed/partial ingestion, strict
  parameter denials, current scope, failures, bounds/deadlines/cancellation/cleanup.
- docs/smtp-adapter.md / ADR 0025 define reviewed greeting_ehlo_v1 assigned by PLAN.
  SMTP capability = greeting + safe ESMTP metadata only. Protocol/security/tool/data/
  execution/state/testing/architecture and reference-adapter docs, CHANGELOG and task
  lifecycle updated. Explicit SMTP/SSH/SMB/FTP alternatives respect the existing one
  selected adapter per capability; no router or default registration.
- All earlier production source remains byte-identical, including framework/domain/
  scope/policy/budgets/dedup/state/registry/runner/config/workflow/provider/CLI. No
  database/M4-T06+, planner/Groq/autonomous loop/persistence/reporting/real CLI work.

### Actual validation

Python 3.14.6 in documented .venv. Install/build provisioning may contact package
indexes; default tests never contact targets/Groq. Primary RFC 5321/3207/4954/1870/
5737/4422 sources reviewed and linked in contract. No live SMTP server/client/scanner
or Python 3.12 execution. Temporary logs/scripts: /tmp/recon-m4t05-validation.

| Check | Actual result |
| --- | --- |
| Setup | Python 3.14.6; editable -e '.[dev]' and pip check passed |
| Focused | SMTP/native/framework/registry: 419 passed, including 206 new cases |
| Full | pytest: 3,639 passed |
| Network/DNS blocked | Guards installed before collection, Groq key absent: 3,639 passed |
| Coverage | coverage run pytest: 3,639 passed; 96% overall, 6,811 statements / 2,344 branches; native/models 100%, adapter 95%, parser 99% |
| Lint/format/types | Ruff check, format (209 files), strict Mypy (94 source modules) passed |
| Build/CLI | Isolated sdist/wheel; editable and fresh-wheel inert recon-agent passed |
| Fresh wheel | External venv/pip check; guarded all-module cold imports/origins/empty registry/inert SMTP composition; 419 copied installed-wheel blocked tests passed outside checkout |
| Artifact/security | Earlier source byte parity, sole EHLO write AST/independent immutable vector, artifact/secret and wheel/sdist source/unchanged dependency parity passed |
| Closeout | Individual acceptance/final working/staged diff/whitespace, append-only history and Markdown/task readiness checks passed: 32 DONE, only M4-T06 READY, 59 NOT STARTED |

Development tests caught copied FTP fixture/product spellings and stale native parser
expectations; corrected SMTP naming and reply vectors. Ruff import/format corrections
completed before final baseline. All required final checks pass without weakened gates.
Remaining uncovered adapter/parser paths are defensive malformed/stale composition
and parser shapes, not auth/mail operations. Parent network guards allow AF_UNIX
plumbing; harmless local interpreter children are not OS network sandboxed. Asyncio/
OS buffering and connection-rate limits and fixed EHLO identity/implicit TLS/absent
metadata are explicit in contract/ADR; advertised mechanisms are not exercised.

### Acceptance mapping and handoff

| Criterion | Evidence |
| --- | --- |
| Operational scoped validated SMTP | Explicit native_smtp registry/schema; prior Service/port/asset binding; real policy and independent numeric scope; no-contact/no-spend denial tests |
| Only safe metadata commands | Sole immutable EHLO after 220, independent exact outbound vector and unread next prompts; no HELO/STARTTLS/fallback/generic command API |
| No authentication/mail/relay/enumeration | Strict extra-forbid typed schema rejects credentials/message/sender/recipient/options; absent client APIs and regression forbidding AUTH/MAIL/RCPT/DATA/BDAT/VRFY/EXPN |
| Structured failures and partial metadata | Canonical Failure/ErrorInfo plus explicit partial SmtpOutput; greeting/multiline/malformed/refused/unreachable/timeout/EOF/denial/bound/cancellation fixtures |
| Traceable untrusted normalization | Original Service intact; banner/hints/extensions/AUTH/STARTTLS/SIZE/port/source/time/execution/base64/hash; actual generic completed/partial state ingestion and history dedup |
| Full baseline and task boundary | All required final checks pass; earlier production unchanged; M0/M1/M2/M3 and M4-T01–M4-T05 DONE; only M4-T06 READY; no active task/blocker |

No new blocker/follow-up task. M4-T06 READY is lifecycle bookkeeping only; no database
or later work begun. Stop after M4-T05.

Commit reference: the single focused commit containing this entry, titled
`feat(protocols): add SMTP metadata inspection`; resolve through Git log. Final response
reports actual hash and clean tree. No second task commit/amend/squash/history rewrite/push.

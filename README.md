# recon-agent

`recon-agent` is a planned CLI-first, async-capable Python platform for AI-assisted **authorized reconnaissance and evidence collection**. It will organize deterministic tool results into traceable state and use a Groq-hosted LLM to recommend useful next actions within an operator-defined scope.

The problem is coordinating discovery, follow-up metadata collection, and evidence without losing track of what was observed, what was inferred, and which actions are allowed. Scope enforcement and deterministic validation will make accidental out-of-scope scanning difficult.

## Current status

**Foundation contracts, local logging, deterministic scope membership and internal process execution.** M0-T01 provides governance and design; M0-T02 provides an installable Python >=3.12 package, developer tooling, and an inert `recon-agent` console entry point. M0-T03 adds typed Pydantic configuration with defaults, explicit TOML loading, environment/programmatic overrides and separate redacted credentials. See the [configuration reference](docs/configuration.md) and [safe example](config.example.toml). The command still only prints `recon-agent is not yet implemented (development baseline only).` and exits successfully. M0-T04 adds pure typed domain data models with provenance and safe capability-intent contracts; see the [data model](docs/data-model.md). M0-T05 adds shared operational errors, serializable diagnostic failures and typed explicit outcomes; see [error/result contracts](docs/error-model.md). M0-T06 adds explicit local diagnostic logging, typed audit records and redaction; see [logging/audit contracts](docs/logging-and-audit.md). M1-T01 adds local deterministic scope membership; see [scope semantics](docs/scope-model.md). M1-T02 adds an independent offline scope regression corpus with generated boundary checks and mock contact consumers. M1-T03 adds the internal async argv-only process runner with bounded per-stream output and timeout/cancellation cleanup; see the [execution model](docs/execution-model.md). M1-T04 adds finite capability identities, an immutable explicit ToolRegistry, trusted adapter interface, typed schema references and a planner-safe declared-availability catalog; see [tool contracts](docs/tool-contracts.md). The default registry is empty; conceptual capability names do not imply scanner support. M1-T05 adds deterministic local action eligibility with explicit capability/risk allowlists, strict registered parameter validation, primary/secondary scope checks and structured shared decisions. Missing budget/completed-action services deny. M1-T06 adds immutable resource limits, atomic local reservations, per-capability rolling rates, canonical host budgets, monotonic session time and aggregate output allowances; see [budget contracts](docs/execution-budgets.md). M1-T07 adds controlled recon state ownership, explicit action history, atomic fact updates and read-only budget snapshots; see [state contracts](docs/state-transitions.md). M1-T08 adds canonical semantic action identity, deterministic history deduplication, conservative bounded failed retries and atomic request admission; see [dedup contracts](docs/action-deduplication.md). M2-T01 adds operational native resolve_dns with typed A/AAAA/CNAME/MX/NS/TXT evidence, scoped numeric resolver infrastructure and policy/budget enforcement; see the [DNS contract](docs/dns-resolver.md). M2-T02 adds enumerate_subdomains through a trusted Subfinder adapter with isolated configuration, fixed passive source, bounded runner execution and normalized discovery evidence; see the [Subfinder contract](docs/subfinder-adapter.md). M2-T03 adds verify_dns through bounded isolated DNSX bulk verification; see the [DNSX contract](docs/dnsx-adapter.md). M2-T04 adds probe_http through constrained HTTPX metadata probing with no redirect following; see the [HTTPX contract](docs/httpx-adapter.md). Generic dispatch, later external adapters, Groq client, planner, database and operational reporting remain unimplemented; conceptual examples below describe future behavior.

## Adaptive architecture

```text
Target
→ Scope validation
→ Asset discovery
→ Service discovery
→ Normalization
→ Recon state
→ Groq planner
→ Policy validation
→ Tool execution
→ New observations
→ repeat
→ report
```

This is adaptive, not a fixed sequence. The core loop is OBSERVE → NORMALIZE → REASON → PLAN → POLICY VALIDATE → EXECUTE ALLOWED CAPABILITY → NORMALIZE → UPDATE STATE → REASON AGAIN. Policy and scope checks also gate initial discovery and every follow-up action.

For example, if Nmap observes ports 22, 80, and 445, the planner may recommend SSH metadata collection, HTTP enumeration, and SMB metadata enumeration. Each allowed result returns to state; the planner chooses the next useful action from collected evidence. These capabilities collect metadata without exploitation or authentication attacks.

Groq is planned as the first hosted reasoning provider so analysis/planning can evolve independently of deterministic execution. A provider abstraction will keep that choice out of domain and orchestration logic. Groq receives bounded normalized evidence and selects predefined capabilities. It cannot directly execute shell commands: every recommendation passes strict schema, scope, capability, parameter, risk, deduplication, and budget validation. Tool adapters construct approved argument arrays.

## Authorized use

Assess only systems for which the operator has explicit authorization. Configure the scope before starting; a discovered hostname, redirect, IP, or certificate name does not grant authorization. Remote text and model output are untrusted data. See the [security model](docs/security-model.md) and [architecture](docs/architecture.md).

## Repository layout

```text
AGENTS.md              Engineering operating rules
PLAN.md                Full task roadmap and acceptance criteria
PROJECT_STATE.md       Concise current state
CURRENT_TASK.md        Active task only
TASK_HISTORY.md        Append-only completed work
CHANGELOG.md           User-visible changes
.codex/skills/         Repository maintenance workflow
pyproject.toml         Package/build and developer tool configuration
src/recon_agent/       Typed foundations, scope policy, internal runner, local logging and inert CLI
  core/ domain/ policy/ execution/ tools/ providers/
  orchestration/ persistence/ reporting/ cli/
tests/                 unit/, integration/, fixtures/
docs/                  Architecture, contracts, security, testing, configuration, ADRs
```

Start repository work with the startup sequence in [AGENTS.md](AGENTS.md). See [PLAN.md](PLAN.md) for the roadmap, [PROJECT_STATE.md](PROJECT_STATE.md) for implementation reality, and [testing strategy](docs/testing-strategy.md) for phase-specific validation. The state files record completed tasks, current work and the next readiness gate. Development proceeds one implementation task at a time.

## Development baseline

From the repository root, use a Python **3.12+** interpreter. The commands below use the local environment directly; activation is unnecessary.

```bash
python --version
python -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/python -c "import recon_agent; print(recon_agent)"
.venv/bin/recon-agent
```

Run complete validation:

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

The build produces `dist/recon_agent-0.1.0.tar.gz` and `dist/recon_agent-0.1.0-py3-none-any.whl`. Environments, caches, coverage and build outputs are ignored by Git. Installation and isolated build-backend provisioning may access the package index; imports, CLI and default tests perform no network activity and require no credentials or reconnaissance binaries. Native DNS makes contact only on explicit authorized execution.

Pydantic and dnspython are the direct runtime dependencies. dnspython supplies only bounded native DNS exchanges; Pydantic supplies configuration/domain/error/result validation, serialization and redacted credential types. The explicit loader uses standard-library TOML/JSON parsing; no settings framework, provider/scanner library or YAML parser is needed. The `dev` extra contains Ruff, Mypy, Pytest, coverage and build with compatible version ranges; no transitive dependencies are pinned. Standard pip/venv and the [setuptools backend](https://setuptools.pypa.io/en/stable/userguide/pyproject_config.html) keep setup independent of a dependency manager. No lockfile is introduced at this stage: these commands reproduce the workflow, while exact resolved versions may change. Tested versions and the full validation contract are recorded in [testing strategy](docs/testing-strategy.md).

Ruff handles lint/import sorting and formatting; Mypy checks production code strictly. Default Pytest collects `tests/unit` only and excludes `external`/`network` markers. Integration tests must be selected explicitly and obey the same marker/authorization rules. Coverage measures `recon_agent`, reports missing lines and has no minimum percentage gate during foundation work. No license or author/ownership metadata has been invented.

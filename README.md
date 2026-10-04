# recon-agent

`recon-agent` is a planned CLI-first, async-capable Python platform for AI-assisted **authorized reconnaissance and evidence collection**. It will organize deterministic tool results into traceable state and use a Groq-hosted LLM to recommend useful next actions within an operator-defined scope.

The problem is coordinating discovery, follow-up metadata collection, and evidence without losing track of what was observed, what was inferred, and which actions are allowed. Scope enforcement and deterministic validation will make accidental out-of-scope scanning difficult.

## Current status

**Foundation/planning only.** M0-T01 provides governance, design documents, the roadmap, and empty package boundaries. There is no working scanner, Groq client, CLI command, configuration loader, database, or installable project yet. Python 3.12+, Pydantic models, SQLite persistence, and Groq as the first provider are planned. Developer tooling is M0-T02; do not treat conceptual examples as executable instructions.

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
src/recon_agent/       Inert future Python package boundaries
  core/ domain/ policy/ execution/ tools/ providers/
  orchestration/ persistence/ reporting/ cli/
tests/                 unit/, integration/, fixtures/
docs/                  Architecture, contracts, security, testing, configuration, ADRs
```

Start repository work with the startup sequence in [AGENTS.md](AGENTS.md). See [PLAN.md](PLAN.md) for the roadmap, [PROJECT_STATE.md](PROJECT_STATE.md) for implementation reality, and [testing strategy](docs/testing-strategy.md) for phase-specific validation. Current next READY task: M0-T02. Development proceeds one implementation task at a time.

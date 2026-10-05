# Planned architecture

Status: product architecture is design intent. M0-T02 adds setuptools packaging and an inert console placeholder; M0-T03 implements typed configuration in `core/config/`. M0-T04 adds pure typed domain data contracts; M0-T05 adds shared errors/results and their configuration/domain integrations; M0-T06 adds explicit local logging/audit infrastructure; M1-T01 implements local scope membership in policy/; M1-T03 implements the internal asynchronous process primitive in execution/. M1-T04 implements finite capability metadata and explicit immutable ToolRegistry with a minimum trusted ToolAdapter interface. M1-T05 implements pure deterministic ActionPolicyValidator. Scanner implementations and other operational source boundaries remain future work. The product is CLI-first, async-capable, Python 3.12+, with Pydantic used for configuration and domain boundaries. Library and protocol details not settled here should be decided through ADRs when implementation evidence exists.

## Domain layer — `domain/`

Pure data models with no process, network, provider, CLI, or database dependencies. Implemented data contracts include Target, Scope, Asset, Host, Service, Endpoint, Observation, Evidence, ActionRequest, ActionResult, ReconSession, ReconState and PlannerDecision. Action, ToolExecution and Finding are explicitly staged for later owning tasks. Domain validation checks structure only; there is no scope/policy enforcement, state machine or execution behavior. Observations describe collected facts; findings interpret evidence; planner recommendations are neither facts nor executable instructions. See [data model](data-model.md).

`core/config/` now provides strict typed section models, an explicit TOML/environment/programmatic loader and separate redacted provider secrets. See [configuration](configuration.md) and [ADR 0001](decisions/0001-configuration-sources.md). Loading only constructs contracts: scope authorization, budget enforcement and subsystem startup remain future work. `core/errors.py` and `core/results.py` implement pure structured failure and generic outcome contracts. Configuration loading uses the project ConfigurationError boundary; domain ActionResult uses shared ErrorInfo without importing configuration or operational layers. See [error/result contracts](error-model.md). `core/audit.py` provides pure event data; `core/redaction.py` bounds/sanitizes diagnostic copies; `core/diagnostics.py` explicitly configures project-local console logging and emits audit records. Domain models import no logging implementation. See [logging and audit](logging-and-audit.md).

## Policy layer — `policy/`

Deterministic authorization is independent of the model. Central responsibilities: scope validation; host/subdomain and IP/CIDR policy; URL/redirect validation; capability allowlist; parameter and planner-output validation; action deduplication; request budgets; rate/resource/execution limits. Policy defaults deny ambiguous or unknown requests. A scope change requires trusted operator input, never remote evidence or planner text.

Scope must be checked when planning, immediately before execution, and before following redirects or scheduling newly discovered targets. Network-capable adapters must prevent tools from silently following out-of-scope redirects, DNS-derived addresses, crawl links, or secondary targets. M1-T01 implements pure synchronous ScopeValidator over explicit Scope snapshots, with canonical Target matches and the existing OperationResult/ErrorInfo/ScopeRejectedError boundary. Exclusions win; domain descendants are explicit; URLs use parsed authorities. No global settings or logging side effects exist. See [scope model](scope-model.md) and [ADR 0002](decisions/0002-scope-and-derived-addresses.md). Domain membership never authorizes DNS answers; future adapters must independently validate and constrain actual addresses before contact and revalidate changes. Rebinding/contact enforcement remains unimplemented; denial is the fallback.

M1-T05 adds ActionPolicyValidator.validate(ActionRequest) using existing
Success[ApprovedAction]/Failure/ErrorInfo. It consumes ToolRegistry's available
metadata snapshot, the centralized ScopeValidator, registered strict parameter
schemas and explicitly injected frozen capability/risk allowlists (empty by default).
Trusted parameter_target_fields metadata identifies every secondary target; absent
semantics deny, explicit () means no secondary network inputs. validate_value is a
ScopeValidator text-classification entry point reusing its existing parser/matcher.
Planner metadata never authorizes; registry facts and scope matches are insufficient
alone. Budget/completed-action check interfaces default deny until M1-T06/M1-T08;
permitting fakes exist only in tests. No counters, dedup identity, dispatch, provider,
network or audit producer is implemented. Approval is current local eligibility,
never a replay token: future dispatch revalidates and reserves atomically. See
[policy contract](tool-contracts.md#action-policy-contract-m1-t05) and
[ADR 0004](decisions/0004-action-eligibility-boundary.md).

## Execution layer — `execution/`

M1-T03 implements `AsyncProcessRunner.run(ProcessSpec)` for trusted adapter-owned
executable/literal argument tuples. It uses the existing OperationResult with
ProcessExecution facts, per-stream bounded raw bytes, truncation flags, return code,
UTC timestamps and monotonic duration. Non-zero exits remain observable outcomes;
OS launch/capture failures and deadlines use canonical errors. Timeout and caller
cancellation terminate/reap the direct child, escalating to kill after 0.5 seconds;
cancellation propagates after cleanup. No shell, command-string API, planner access
or automatic logging exists. See [execution model](execution-model.md) for precise
failure, partial-output, injection and descendant-process limitations.

```text
Planner [future] → ActionPolicyValidator [M1-T05 local eligibility]
  → ToolRegistry [M1-T04] → ToolAdapter [interface; implementations future]
  → Execution Runner [M1-T03] → OS process
```

ProcessSpec grants no authority. Future dispatch must recheck approval/scope/budgets
and select trusted adapters. Registry lookup and local action policy exist; operational
adapter dispatch remains future work. The execution-neutral ProcessRunner protocol
allows future fixture runners;
an internal injected spawn seam already drives deterministic fake-process tests.

## Tool adapters — `tools/`

M1-T04 provides CapabilityId/CapabilityDescriptor/RiskClass and ToolRegistry. The
registry is explicitly composed, immutable and empty by default, with one selected
trusted adapter per capability. It reports declared availability without probing,
returns existing canonical outcomes, rejects unknown capabilities and conflicting
registrations, and exports only semantic planner-safe catalog metadata. ToolAdapter
currently exposes identity/metadata and strict typed input/output model references;
execution/parsers are future implementations. See [ADR 0003](decisions/0003-immutable-capability-registry.md).

The planner selects capabilities, never command strings. Adapters map validated typed requests to fixed tool options and normalize outputs; they do not decide authorization. Potential mappings:

| Capability | Potential implementation |
| --- | --- |
| resolve_dns | Native resolver or dnsx |
| enumerate_subdomains | subfinder |
| discover_ports | naabu |
| fingerprint_services | nmap |
| probe_http | httpx |
| inspect_tls | tlsx |
| crawl_web | katana |
| discover_content | feroxbuster or defined ffuf modes |
| inspect_protocol | Controlled SSH/SMB/FTP/SMTP/database modules |
| scan_templates | nuclei with named policy profiles |

These are candidates, not working integrations or locked implementation choices. Tool-specific nested behavior must obey scope/budgets, including subprocess-internal traffic. See [tool contracts](tool-contracts.md).

## Provider layer — `providers/`

A provider interface isolates Groq, the first planned LLM backend. It handles bounded requests, structured responses, provider failures, and secret-safe diagnostics. Provider-specific client code must not leak through orchestration or domain models. Models have no process/network tool granting unrestricted terminal access. See [planner contract](planner-contract.md).

## Orchestration layer — `orchestration/`

Implements observe → normalize → reason/plan → validate → execute → normalize → update state → stop or repeat. It coordinates domain, policy, adapter registry, provider, runner, budgets, and persistence through explicit interfaces. Rejections and failures remain auditable; neither opens a policy bypass. Initial deterministic workflows precede AI orchestration. Future application/orchestration services emit operational diagnostics and AuditEvents, linking recon sessions, internal planner decisions, policy outcomes and executions. Operators supply target/scope/config, rather than interacting through an AI chat loop. Only concise decision summaries/reasons are recorded; no private reasoning or transcript state is introduced. Audit records never authorize replay. The event contracts/sink exist; those producers and the recon loop do not.

## Persistence layer — `persistence/`

SQLite is planned behind repository interfaces. Store sessions, scopes/targets, assets, observations, actions, tool executions, findings, planner decisions, and evidence references. Traceable source and policy outcomes support resume without duplicate work. No database or migration code exists yet.

## Reporting layer — `reporting/`

Planned JSON, human-readable terminal summaries, and HTML reports. Reports separate scanner observations, interpreted findings, and AI recommendations, preserving evidence lineage. Escape remote content in renderers and redact secrets.

## CLI layer — `cli/`

The operator interface will validate configuration/scope, start/resume sessions, show tools/status, diagnose the environment, generate reports, and cancel safely. Configuration and explicit scope approval belong here, not in planner-derived text. M0-T02 installs `recon-agent` only as a status-printing placeholder with no command framework or reconnaissance behavior. The planned operator commands are specifications in PLAN and are not available today.

## Architectural constraints

Authorized reconnaissance/evidence collection only. Exclude arbitrary LLM-generated shell commands, unrestricted execution, exploitation, credential attacks, password spraying, brute-force authentication, destructive testing, remote persistence, evasion, stealth, malware, privilege escalation automation, automatic modification of remote systems, and scans outside authorized scope. Local SQLite persistence is distinct from prohibited remote persistence mechanisms.

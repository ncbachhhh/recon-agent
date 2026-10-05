# Planned architecture

Status: product architecture is design intent. M0-T02 adds setuptools packaging and an inert console placeholder; M0-T03 implements typed configuration in `core/config/`. M0-T04 adds pure typed domain data contracts; M0-T05 adds shared errors/results and their configuration/domain integrations; other source boundaries remain package markers. The product is CLI-first, async-capable, Python 3.12+, with Pydantic used for configuration and domain boundaries. Library and protocol details not settled here should be decided through ADRs when implementation evidence exists.

## Domain layer — `domain/`

Pure data models with no process, network, provider, CLI, or database dependencies. Implemented data contracts include Target, Scope, Asset, Host, Service, Endpoint, Observation, Evidence, ActionRequest, ActionResult, ReconSession, ReconState and PlannerDecision. Action, ToolExecution and Finding are explicitly staged for later owning tasks. Domain validation checks structure only; there is no scope/policy enforcement, state machine or execution behavior. Observations describe collected facts; findings interpret evidence; planner recommendations are neither facts nor executable instructions. See [data model](data-model.md).

`core/config/` now provides strict typed section models, an explicit TOML/environment/programmatic loader and separate redacted provider secrets. See [configuration](configuration.md) and [ADR 0001](decisions/0001-configuration-sources.md). Loading only constructs contracts: scope authorization, budget enforcement and subsystem startup remain future work. `core/errors.py` and `core/results.py` implement pure structured failure and generic outcome contracts. Configuration loading uses the project ConfigurationError boundary; domain ActionResult uses shared ErrorInfo without importing configuration or operational layers. See [error/result contracts](error-model.md). Audit primitives remain M0-T06 work.

## Policy layer — `policy/`

Deterministic authorization is independent of the model. Central responsibilities: scope validation; host/subdomain and IP/CIDR policy; URL/redirect validation; capability allowlist; parameter and planner-output validation; action deduplication; request budgets; rate/resource/execution limits. Policy defaults deny ambiguous or unknown requests. A scope change requires trusted operator input, never remote evidence or planner text.

Scope must be checked when planning, immediately before execution, and before following redirects or scheduling newly discovered targets. Network-capable adapters must prevent tools from silently following out-of-scope redirects, DNS-derived addresses, crawl links, or secondary targets. Domain/IP authorization semantics and rebinding protections are to be resolved in M1-T01; denial is the fallback.

## Execution layer — `execution/`

A controlled process runner will accept adapter-generated argv arrays. No shell, `shell=True`, or arbitrary command strings. It will support timeouts, stdout/stderr capture, exit codes, cancellation and child cleanup, bounded output, and structured execution metadata. It cannot provide an alternate route around policy. Fake runners allow offline adapter tests. Approval is rechecked at dispatch so stale authorization or exhausted budgets cannot permit execution.

## Tool adapters — `tools/`

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

Implements observe → normalize → reason/plan → validate → execute → normalize → update state → stop or repeat. It coordinates domain, policy, adapter registry, provider, runner, budgets, and persistence through explicit interfaces. Rejections and failures remain auditable; neither opens a policy bypass. Initial deterministic workflows precede AI orchestration.

## Persistence layer — `persistence/`

SQLite is planned behind repository interfaces. Store sessions, scopes/targets, assets, observations, actions, tool executions, findings, planner decisions, and evidence references. Traceable source and policy outcomes support resume without duplicate work. No database or migration code exists yet.

## Reporting layer — `reporting/`

Planned JSON, human-readable terminal summaries, and HTML reports. Reports separate scanner observations, interpreted findings, and AI recommendations, preserving evidence lineage. Escape remote content in renderers and redact secrets.

## CLI layer — `cli/`

The operator interface will validate configuration/scope, start/resume sessions, show tools/status, diagnose the environment, generate reports, and cancel safely. Configuration and explicit scope approval belong here, not in planner-derived text. M0-T02 installs `recon-agent` only as a status-printing placeholder with no command framework or reconnaissance behavior. The planned operator commands are specifications in PLAN and are not available today.

## Architectural constraints

Authorized reconnaissance/evidence collection only. Exclude arbitrary LLM-generated shell commands, unrestricted execution, exploitation, credential attacks, password spraying, brute-force authentication, destructive testing, remote persistence, evasion, stealth, malware, privilege escalation automation, automatic modification of remote systems, and scans outside authorized scope. Local SQLite persistence is distinct from prohibited remote persistence mechanisms.

# Planned architecture

Status: product architecture is design intent. M0-T02 adds setuptools packaging and an inert console placeholder; M0-T03 implements typed configuration in `core/config/`. M0-T04 adds pure typed domain data contracts; M0-T05 adds shared errors/results and their configuration/domain integrations; M0-T06 adds explicit local logging/audit infrastructure; M1-T01 implements local scope membership in policy/; M1-T03 implements the internal asynchronous process primitive in execution/. M1-T04 implements finite capability metadata and explicit immutable ToolRegistry with a minimum trusted ToolAdapter interface. M1-T05 implements pure deterministic ActionPolicyValidator; M1-T06 adds local atomic resource reservations; M1-T07 adds owned recon state transitions; M1-T08 adds deterministic semantic action identity, history eligibility and atomic request admission. M2-T01 adds the first operational capability, bounded native resolve_dns; M2-T02 adds passive enumerate_subdomains through isolated Subfinder; M2-T03 adds bulk verify_dns through isolated DNSX; M2-T04 adds constrained probe_http through isolated HTTPX; M2-T05 adds bounded discover_ports through isolated numeric Naabu; remaining operational source boundaries remain future work. The product is CLI-first, async-capable, Python 3.12+, with Pydantic used for configuration and domain boundaries. Library and protocol details not settled here should be decided through ADRs when implementation evidence exists.

## Domain layer — `domain/`

Pure data models with no process, network, provider, CLI, or database dependencies. Implemented data contracts include Target, Scope, Asset, Host, Service, Endpoint, Observation, Evidence, ActionRequest, ActionResult, ReconSession, ReconState and PlannerDecision. Action, ToolExecution and Finding are explicitly staged for later owning tasks. Individual records validate structure; M1-T07 adds whole-state lineage/lifecycle validation and a small local transition owner. Domain performs no scope/policy enforcement or execution. Observations describe collected facts; findings interpret evidence; planner recommendations are neither facts nor executable instructions. See [data model](data-model.md).

`core/config/` now provides strict typed section models, an explicit TOML/environment/programmatic loader and separate redacted provider secrets. See [configuration](configuration.md) and [ADR 0001](decisions/0001-configuration-sources.md). Loading only constructs contracts: explicit consumers implement scope authorization and budgets; subsystem startup remains future work. `core/errors.py` and `core/results.py` implement pure structured failure and generic outcome contracts. Configuration loading uses the project ConfigurationError boundary; domain ActionResult uses shared ErrorInfo without importing configuration or operational layers. See [error/result contracts](error-model.md). `core/audit.py` provides pure event data; `core/redaction.py` bounds/sanitizes diagnostic copies; `core/diagnostics.py` explicitly configures project-local console logging and emits audit records. Domain models import no logging implementation. See [logging and audit](logging-and-audit.md).

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
alone. Missing budget/completed-action check interfaces default deny. M1-T06 now
supplies the budget controller; M1-T08 supplies ActionDeduplicator through the
existing eligibility seam. No dispatch, provider, network or audit producer is
implemented. Approval is current local eligibility,
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
  → BudgetController atomic reservation [M1-T06; resources only]
  → ToolRegistry [M1-T04] → ToolAdapter
      → NativeDnsResolver → approved numeric resolver [M2-T01]
      → Execution Runner → OS process [M2-T02 Subfinder; M1-T03 runner]
```

ProcessSpec grants no authority. Future dispatch must recheck approval/scope/budgets
and select trusted adapters. Registry lookup and local action policy exist; native DNS and Subfinder implement capability-specific dispatch; generic dispatch remains future work. The execution-neutral ProcessRunner protocol
allows future fixture runners;
an internal injected spawn seam already drives deterministic fake-process tests.

## Tool adapters — `tools/`

M1-T04 provides CapabilityId/CapabilityDescriptor/RiskClass and ToolRegistry. The
registry is explicitly composed, immutable and empty by default, with one selected
trusted adapter per capability. It reports declared availability without probing,
returns existing canonical outcomes, rejects unknown capabilities and conflicting
registrations, and exports only semantic planner-safe catalog metadata. ToolAdapter
exposes identity/metadata and strict typed input/output model references; M2-T01
adds a capability-specific native DNS execution/parser implementation. See [ADR 0003](decisions/0003-immutable-capability-registry.md).

The planner selects capabilities, never command strings. Adapters map validated typed requests to fixed tool options and normalize outputs; they do not decide authorization. Potential mappings:

| Capability | Potential implementation |
| --- | --- |
| resolve_dns | Implemented direct native dnspython resolution (M2-T01) |
| verify_dns | Implemented bulk authorized-candidate DNSX verification (M2-T03) |
| enumerate_subdomains | Implemented passive Subfinder adapter (M2-T02) |
| discover_ports | Implemented bounded Naabu CONNECT discovery (M2-T05) |
| fingerprint_services | nmap |
| probe_http | Implemented constrained HTTPX metadata probing (M2-T04) |
| inspect_tls | tlsx |
| crawl_web | katana |
| discover_content | feroxbuster or defined ffuf modes |
| inspect_protocol | Controlled SSH/SMB/FTP/SMTP/database modules |
| scan_templates | nuclei with named policy profiles |

Except for implemented resolve_dns, verify_dns, enumerate_subdomains, probe_http and discover_ports, these are candidates and future integrations. Tool-specific nested behavior must obey scope/budgets, including subprocess-internal traffic. See [tool contracts](tool-contracts.md).

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

## Local resource controller (M1-T06)

BudgetController implements the normalized ApprovedAction budget eligibility seam
and atomic reservations over frozen ExecutionBudget limits, a local locked ledger
and an injected monotonic clock. BudgetState snapshots cannot reset that ledger.
Granted attempts permanently consume action/host/rate/output allowances; rejected
requests consume nothing. Rolling per-capability rates map to the registry's one
selected adapter per capability. All primary/secondary hosts share canonical
accounting. BudgetPermit releases concurrency synchronously on normal exit,
exception, timeout and cancellation; outcome counters are separate from ReconState.
Session time is queried without timers. Aggregate output reserves two bounded
streams per attempt; the existing runner still owns per-process capture.

Policy authorization != budget availability. AI planner cannot raise resource
limits. Future dispatch revalidates current policy, reserves atomically and owns
actual traffic/time/output containment. No worker/orchestrator or M1-T07/M1-T08 work
is added. See [budget contract](execution-budgets.md) and
[ADR 0005](decisions/0005-budget-reservations.md).

## Controlled session state (M1-T07)

ReconStateMachine explicitly owns the authoritative in-memory ReconState. Frozen
tuple snapshots, validated action history and detached copies prevent bypass through
exposed collections/nested JSON. A local lock protects complete candidate validation
and atomic commit; failure leaves prior state intact. Inputs supply identities/times.
Planner records do not enqueue/approve actions or produce evidence. Atomic normalized
fact/result ingestion preserves lineage and unsuccessful/partial outcome distinctions.

Responsibilities stay separate: ReconState records state; PlannerDecision records
recommendations; ActionPolicyValidator authorizes; BudgetController enforces resources;
ExecutionRunner executes processes. BudgetState/ReservationOutcome pure data move to
domain with preserved policy exports and timestamped BudgetSnapshot recording. No
budget arithmetic or live controller enters the state owner. ReconSession's status
fields remain structural; startup/stop/resume are future orchestration. M1-T08 adds
semantic action deduplication/retry eligibility in policy with an atomic admission
seam in this owner. See [state contract](state-transitions.md).

## Semantic action eligibility (M1-T08)

Action identity = execution-relevant semantic identity. Planner explanation !=
action identity. ActionCanonicalizer shares registered strict schema/scope input
validation with ActionPolicyValidator. ActionDeduplicator reads existing state and
returns typed decisions, with default-zero explicit failed retries. Atomic
record_request admission uses the state owner's lock and detached pure callback,
without a second ledger or authorization/resource/execution side effects.
Future dispatch still requires current policy, lifecycle and charged reservations.
See [identity/retry contract](action-deduplication.md) and
[ADR 0007](decisions/0007-action-identity-and-retries.md).

## Operational native DNS (M2-T01)

Explicit ToolRegistry registration selects DnsAdapter. Its capability-specific execute
revalidates current policy/scope/dedup, checks independently authorized numeric resolver
infrastructure, atomically reserves existing budgets, then exchanges fixed bounded DNS
questions through NativeDnsResolver. This native path uses no ExecutionRunner/process.
Typed results normalize into existing Asset/Observation/Evidence; caller owns lifecycle
and fact ingestion. No generic dispatcher or later adapter exists; DNSX is implemented separately in M2-T03; enumeration is implemented in M2-T02.
See [resolver contract](dns-resolver.md) and [ADR 0008](decisions/0008-bounded-native-dns.md).

## Passive enumeration (M2-T02)

SubfinderAdapter implements enumerate_subdomains using the existing ToolAdapter →
ExecutionRunner boundary. Explicit local binary/version probing, isolated child
configuration and fixed credential-free HackerTarget source prevent planner/ambient
configuration from selecting execution. Current scope/policy/dedup and atomic budgets
precede one bounded process. Generic root-owned metadata observations and untrusted
snapshot evidence record sorted discovery, never DNS verification or follow-up
permission. Provider transport is an explicit external service boundary; Python does
not pin its HTTP destination packets. resolve_dns remains implemented; DNSX
verification is implemented as verify_dns (M2-T03). See [contract](subfinder-adapter.md) and
[ADR 0009](decisions/0009-isolated-passive-subfinder.md).

## Bulk DNS verification (M2-T03)

Discovery feeds candidate data, never authorization. DnsxAdapter implements the new
verify_dns capability for already supplied authorized batches, alongside direct
resolve_dns and passive enumerate_subdomains. Existing centralized policy checks
every primary/secondary candidate; mixed batches fail before input/child execution.
Numeric resolver scope and shared budgets precede fixed isolated runner execution.
Generic observations/evidence retain actual RR owners, provenance, ambiguity and
partial limits. Default registry stays empty; no generic dispatcher or later adapter.
See [DNSX contract](dnsx-adapter.md) and [ADR 0010](decisions/0010-scoped-bulk-dnsx.md).

## HTTP endpoint probing (M2-T04)

HttpxAdapter supplies capability-specific probe_http execution through the existing
registry/policy/shared budgets/runner. Approved host/IP/URL candidates, independently
scoped resolver/contact addresses and trusted isolated HTTPX 1.9.0 configuration
precede one bounded process. The upstream concrete-IP allow gate constrains resolution
changes; redirects and discovery probes are disabled. Generic endpoints/HTTP facts/
untrusted evidence normalize deterministically, with explicit partial/error limits.
Caller owns lifecycle and ingestion; no orchestration/CLI startup is added. HTTPX
probing, future Katana crawling and future Feroxbuster/FFUF content discovery are
separate capabilities. See [contract](httpx-adapter.md) and
[ADR 0011](decisions/0011-constrained-httpx-probing.md).

## Bounded port discovery (M2-T05)

NaabuAdapter implements discover_ports through current registry/policy/dedup/shared
budgets and the unchanged runner. Operator finite TCP ranges and independently scoped
numeric hostname bindings constrain all contacts before input; fixed isolated CONNECT
stream mode prevents DNS/target expansion and fingerprinting. Generic Host/Service/
service Observation/untrusted Evidence preserve provenance and partial limits. Naabu
is fast bounded open-port discovery; Nmap remains future deeper service fingerprinting.
See [contract](naabu-adapter.md) and [ADR 0012](decisions/0012-numeric-bounded-naabu.md).

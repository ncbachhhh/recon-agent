# Project state

Project phase: M3 — M3-T01–M3-T03 DONE; M3-T04 READY; M0/M1/M2 DONE

Completed:

- M0-T01 — Repository governance and planning scaffold (DONE)
- M0-T02 — Python project and developer tooling baseline (DONE)
- M0-T03 — Configuration foundation (DONE)
- M0-T04 — Core domain model foundation (DONE)
- M0-T05 — Error taxonomy and result model (DONE)
- M0-T06 — Logging and audit-event foundation (DONE)
- M1-T01 — Scope model and validator (DONE)
- M1-T02 — Scope regression suite (DONE)
- M1-T03 — Execution runner abstraction (DONE)
- M1-T04 — Capability and Tool Registry (DONE)
- M1-T05 — Action policy validator (DONE)
- M1-T06 — Execution budgets and rate limiting (DONE)
- M1-T07 — ReconState state machine (DONE)
- M1-T08 — Action deduplication (DONE)
- M2-T01 — DNS resolver capability (DONE)
- M2-T02 — Subfinder adapter (DONE)
- M2-T03 — DNSX adapter (DONE)
- M2-T04 — HTTPX adapter (DONE)
- M2-T05 — Naabu port discovery adapter (DONE)
- M2-T06 — Nmap service fingerprint adapter (DONE)
- M2-T07 — Initial deterministic discovery pipeline (DONE)
- M3-T01 — Common-file inspector (DONE)
- M3-T02 — TLSX adapter (DONE)
- M3-T03 — Katana crawler adapter (DONE)

Active task: None.

Next ready task:

- M3-T04 — Feroxbuster content-discovery adapter (READY; not started).

## Implementation reality

The 92-task roadmap, governance, maintenance skill and design documentation exist. `recon-agent` 0.1.0 installs through setuptools with Python >=3.12 metadata. Pydantic, dnspython and h11 are the direct runtime dependencies; developer tooling and inert CLI are unchanged.

`core/config/` implements strict seven-section settings, defaults < explicit TOML < namespaced environment < programmatic precedence, and separate excluded/redacted credentials. Configuration source/effective validation failures use ConfigurationError with fixed diagnostics and native cause chaining. Direct model construction raises Pydantic ValidationError. Loading preferences grants no authorization or runtime startup.

`domain/` retains the original 13 pure typed data contracts and adds lifecycle/state/budget snapshot contracts with explicit opaque IDs, aware UTC timestamps, structural validation, evidence provenance and portable serialization. Targets/scopes are declarations; planner decisions/action requests are unapproved data. ActionResult uses shared ErrorInfo and validates consistent completed/partial/rejected/failed/cancelled/timeout outcomes. ReconState is a frozen tuple-based snapshot with whole-state validation; ReconStateMachine owns explicit atomic transitions and detached copies. ReconSession remains structural mutable composition. Domain depends on pure shared errors/results, never logging/configuration/operational layers.

`core/errors.py` supplies stable codes, category catch boundaries and concrete configuration/policy/tool/parser/provider/planner/budget/cancellation/state exceptions, with bounded allowlisted scalar context and explicit conservative retryability. ErrorInfo omits native causes/tracebacks/credentials. `core/results.py` provides typed Success[T]/Failure and the status-discriminated OperationResult[T] union; ActionResult retains its action/evidence role. Caller-authored diagnostics require safe selection; chained causes remain explicit debugging data, not routine dumps.

M0-T06 adds pure `core/audit.py` with 16 stable event types, explicit UTC time/session IDs and optional action/execution/decision/asset correlation. `core/redaction.py` copies and bounds diagnostic JSON, masks known sensitive keys/wrappers and accepts explicitly registered secret values. `core/diagnostics.py` explicitly configures only the project logger, replaces its owned console handler, supports escaped human/JSON output and emits revalidated records through recon_agent.audit. Existing LoggingConfig and ErrorInfo are reused. Native causes/stacks are omitted; malformed records produce fixed omission output and sink failures raise fixed ConfigurationError without raw-record fallback. Imports and data constructors do not configure logging. See docs/logging-and-audit.md for precise redaction and delivery limits.

M1-T01 adds pure synchronous `policy/ScopeValidator` compiled from an explicit immutable Scope snapshot. Exact DNS names, optional domain descendants, IPv4/IPv6, aligned CIDRs and host-level HTTP/HTTPS URLs use deterministic comparisons; exclusions always win. Canonical Target/matched-rule data use existing Success/Failure outcomes; canonical ScopeRejectedError/ErrorInfo carries typed scope reason and safe authority context. RFC1918/IPv6 ULA gating never grants authorization. Unicode/IDN, scoped/mapped IPv6 and ambiguous representations fail closed. No declaration mutation, global config read, audit producer, DNS or contact occurs. See docs/scope-model.md and ADR 0002 for independent concrete-address authorization and future contact/rebinding obligations.

M1-T02 adds 343 independent regression cases under tests/unit/policy, with socket/DNS guards, deterministic generated suffix/CIDR membership checks, rule permutations and test-only mock contact checks for redirects/discovery. No validator defect was demonstrated; production code and dependencies are unchanged. The corpus verifies the documented boundary, not future production contact enforcement.

M1-T03 adds execution/ProcessSpec, ProcessExecution, ProcessRunner protocol and
AsyncProcessRunner. The internal async primitive launches trusted adapter-owned
executable/argument tuples through create_subprocess_exec, with DEVNULL stdin,
separate raw byte streams, per-stream max_output_bytes retention while concurrently
draining/discarding excess, explicit truncation, return code, UTC wall timestamps
and monotonic duration. Non-zero exits remain Success process facts; canonical
ToolUnavailableError/ToolExecutionError/ToolTimeoutError supply existing Failures.
Spec timeout overrides the snapshotted configured default. Timeout/cancellation
terminate/reap the direct child and escalate to kill after 0.5 seconds; shielded
ownership handles spawn/repeated cancellation races. Python cancellation propagates.
Failure has no partial-output payload; bytes are discarded on failure/cancellation.
JSON raw bytes use URL-safe base64. No argv/executable/environment is returned as
metadata, and the runner emits no logs/audit events or authorization. See
[execution model](docs/execution-model.md) for descendant/OS cleanup limitations.
M1-T03 added no process-tree containment, action policy, rate/concurrency/session
budget runtime, scanner, provider/planner or command CLI. The upstream registry
foundation is now implemented separately in M1-T04.

M1-T04 adds finite CapabilityId/RiskClass enums and strict frozen CapabilityDescriptor
in domain/capabilities.py. The original 10 conceptual identities (11 with M2-T03 verify_dns) do not imply operational tools.
ActionRequest retains unapproved lowercase-name wire semantics; it adds nested
import_path/python_module rejection without exposing implementation selection.

tools/ implements minimal ToolAdapter abstract identity/definition, AdapterDefinition
with strict extra-forbid Pydantic input/output schema classes, explicit
AdapterRegistration availability snapshots and immutable ToolRegistry. Construction
revalidates/snapshots metadata and rejects duplicate IDs/conflicting capabilities with
canonical ConfigurationError. One explicitly selected trusted adapter per capability;
no globals, dynamic imports, discovery, runtime registration or probing. Default
ToolRegistry is empty. Synchronous lookups return existing Success/Failure: unknown
capability is planner_validation_failed; known unregistered capability/unknown adapter
or unavailable/not_checked registration is tool_unavailable. Only explicit available
registrations resolve; registration/availability grant no authorization. Lexically
sorted tuple catalogs expose only capability, description, risk_class and availability;
internal schema classes/adapter objects are excluded from planner projection. No
runner invocation, scope/budget enforcement, execution/policy audit or config consumption.
See tool-contracts.md and ADR 0003 for trust/lifecycle and future adapter boundaries.

M1-T05 adds pure synchronous ActionPolicyValidator.validate(ActionRequest). It
revalidates action structure, consumes available registry metadata via
capability_definition (no adapter access), applies explicit frozen empty-default
ActionPolicyConfig capability/risk allowlists, checks primary and declared secondary
targets through ScopeValidator and validates the registered strict input schema.
AdapterDefinition.parameter_target_fields is trusted internal metadata: absent None
fails closed; explicit () declares no secondary targets; unique named input fields
support strings/lists/tuples only. Defaults are independently checked. ScopeValidator's
validate_value classifies text then reuses its existing parsing/membership rules.

Existing Success[ApprovedAction]/Failure/ErrorInfo encode outcomes. Approval has
request ID/capability, scope matches and an internal typed parameter model excluded
from dumps/repr, never a reusable permission token. Unknown, unavailable, malformed,
unsupported, disallowed and schema-invalid requests reject with existing canonical
codes. Planner reason/priority/analysis and discovery confer no authority. Explicit
missing budget/completed-action eligibility services default deny; completed-action
permitting stubs exist only in tests. M1-T06 supplies budget checks/reservations;
M1-T08 now supplies the real dedup eligibility service; no execution, network/DNS,
Groq, dynamic loading or audit producer. Future dispatch must revalidate current facts,
reserve resources atomically and constrain/recheck actual contact. See tool-contracts
and ADR 0004. Existing configuration loader, domain wire fields, errors/results,
runner, CLI, dependencies and future runtime subsystems are unchanged.

M1-T06 adds policy/ExecutionBudget, BudgetController and BudgetPermit, with shared
BudgetState/ReservationOutcome contracts (now pure domain types, re-exported by policy).
Strict execution settings add per-host counts, per-capability
rolling rate windows and aggregate output allowances. Frozen explicit limits are
separate from the local locked ledger and injected monotonic clock. Policy's budget
seam consumes ApprovedAction with canonical primary/secondary ScopeMatches;
ScopeMatch.host_identity reuses centralized parsing without DNS or duplicate scope
logic. Unsupported CIDR accounting and unknown/unregistered/malformed inputs deny.

Read-only checks consume nothing; atomic reservations recheck all dimensions and
permanently charge one permitted attempt, distinct hosts, rate entry and two-stream
worst-case output allowance. Rejections spend nothing; retry/failure/cancellation/
timeout/abort retain charges. Only concurrency is released. Synchronous idempotent
context cleanup records typed outcomes and survives cancellation without awaits.
Detached immutable snapshots cannot reset counters; no reset/refund/limit-update API.
Exact session deadlines and bad/regressing clocks fail closed. No running-work timer,
background worker, orchestration, persistence or audit producer is implemented.
M1-T03 capture remains unchanged; future dispatch must obey the same/smaller stream
bounds and remaining time, constrain contact and reserve each execution. Default
aggregate output envelope permits eight full allowances; budgets are independent
upper limits rather than a promised action count. See execution-budgets.md and ADR
0005. Policy authorization != budget availability; AI planner cannot raise limits.

M1-T07 adds domain/ReconStateMachine, ActionLifecycle/ActionTransition/ActionPhase
and BudgetSnapshot. One local owner validates and defensively copies complete frozen
tuple snapshots before atomic commit. Requested/approved/started and existing
terminal outcomes have explicit nonregressing UTC history; invalid transitions and
terminal re-entry fail with canonical StateTransitionError/Failure without mutation.
Related facts/results ingest atomically with reference, subject and execution lineage
validation. Known unfinished/unsuccessful actions cannot support observations, directly
or through evidence; partial/error/rejection histories retain their distinctions.

PlannerDecision recording adds only recommendations, never action requests, approval,
scope changes, consumption or execution. Read-only caller-sampled budget facts retain
M1-T06 enforcement ownership; BudgetController arithmetic and permit logic are unchanged.
Detached input/output copies prevent nested JSON edits from corrupting owned state.
Supplied initial state and Python/JSON dumps validate the same rules. Approval references
are trusted caller history, never dispatch tokens; future dispatch revalidates current
policy and reserves resources. See state-transitions.md and ADR 0006. M1-T08 adds
semantic action equivalence/retry eligibility in policy and a pure atomic admission
seam in this owner. Session startup/stop/resume remains future work.

M1-T08 adds domain/ActionIdentity, ActionDedupDecision and DedupReason plus
policy/ActionCanonicalizer, ActionDedupConfig and ActionDeduplicator. Full versioned
canonical JSON represents capability, existing scope-normalized target kind/value
and actual validated registered-schema fields/defaults. Planner reason/priority/
IDs/times are excluded; sorted nested object keys, preserved arrays/scalar types
and declared secondary target normalization prevent cosmetic evasion. Non-JSON/
nonfinite values and uncanonicalizable same-capability history fail closed.

Read-only typed lookup and the existing policy seam derive all eligibility from
ReconState, without a second history/cache/retry counter. Requested/approved/started/
completed equivalents deny; partial/rejected/cancelled/timeout equivalents deny.
Trusted explicit max_failed_retries defaults to zero: only all-failed history with
all errors explicitly retryable may retry, within one initial attempt plus N retries.
Retries need new action IDs; own pending policy revalidation excludes only unchanged
requested/approved semantics, never started/terminal IDs. There is no force rerun.

Atomic record_request consults history inside the existing ReconStateMachine lock
via a trusted pure detached-data admission callback, validates the check result and
records REQUESTED only. Failed admission leaves state unchanged. Dedup grants no
authorization, consumes no budgets and executes nothing. The policy validator shares
existing scope/schema normalization; no raw parameters become argv. See
[action identity/retry contract](docs/action-deduplication.md) and ADR 0007.
Runner, registry, scope, configuration, budget enforcement, shared errors/results,
planner wire models, CLI/dependencies and future subsystem code are unchanged.

M2-T01 adds tools.dns.DnsAdapter with native_dns identity for resolve_dns. The base
registry/interface stays explicit and empty by default. Capability-specific execute
rechecks current registry binding and ActionPolicyValidator, strict record-type input,
primary name scope and independent numeric resolver IP scope, then atomically reserves
the existing shared BudgetController. Name and resolver hosts both count. NativeDnsResolver
uses dnspython for up to six absolute original-name UDP/53 questions, no retries,
system resolver/search, fallback or discovered-destination queries. Whole-action and
per-exchange timeouts, remaining session time, 256-record bounds and serialized output
limits apply. Failure/cancellation keep charges and release concurrency.

A/AAAA/CNAME/MX/NS/TXT normalize through strict internal DNS schemas into existing
Asset/Observation/Evidence, with canonical values/TTL/MX preference and exact TXT chunk
hex. Negative answers are explicit successful evidence; malformed/truncated, resolver
and timeout failures use canonical errors. Caller time/execution/subject identity and
stable memory snapshot references/hashes preserve provenance. TXT remains untrusted.
Discovered hosts/IPs never change Scope or gain authority. Caller owns lifecycle and
state ingestion; no generic dispatcher, later adapter, planner/loop,
persistence/reporting or operational CLI. See docs/dns-resolver.md and ADR 0008.

M2-T02 adds tools.subfinder.SubfinderAdapter for enumerate_subdomains, passive risk,
strict empty planner parameters and explicit immutable registry composition. Default
registry remains empty. Trusted binary/PATH lookup plus an isolated no-target version
probe establishes availability; only reviewed Subfinder 2.9.0 is accepted. Operator
composition opts into credential-free HackerTarget hostsearch, fixed JSONL/source
attribution and one HTTP request/second. No all/default sources, active resolution,
provider credentials, proxies, arbitrary flags or executable fields enter planner
input. Current registry/policy/root scope/dedup/shared budgets precede one process.

Upstream goflags can apply ambient YAML despite false-valued CLI flags. ADR 0009
adds one internal bounded immutable complete ProcessSpec.environment snapshot,
passed only by the runner to create_subprocess_exec. Default inheritance and all
existing capture/deadline/cancellation behavior remain unchanged. Subfinder supplies
fresh temporary HOME/config paths, null-device config/provider inputs and no ambient
secrets/proxy/config variables. Cleanup follows runner cleanup on every outcome.
Other protected domain/policy/config/error contracts and registry logic are unchanged.

Strict UTF-8 host/input/sources JSONL validates canonical proper descendants through
centralized syntax/membership, sorts/deduplicates deterministically and bounds lines,
hosts/capture/normalized output. Malformed/outside-root/truncated output fails
atomically; empty output succeeds with zero observations and untrusted empty evidence.
Generic root-owned metadata Observations and Evidence retain source subfinder,
enumerate_subdomains, source_version/provider_sources, explicit subject/time/execution
and normalized snapshot memory reference/SHA-256. Excluded/unauthorized descendants
remain data, never contact authority. Shared canonical failures retain nonzero exit
codes; deadlines/cancellation/resources follow runner/budget contracts.

Provider HTTP DNS/TLS/redirect behavior and completeness are external service
behavior, not Python packet containment; the reviewed source performs no target
probing and grants no target membership. No real binary/provider test or public
contact occurs. resolve_dns is already implemented; DNS verification through DNSX
is implemented separately as verify_dns in M2-T03. No generic dispatch, later adapter, planner/runtime/loop,
persistence/reporting or operational CLI is added. See docs/subfinder-adapter.md.

M2-T03 adds tools.dnsx.DnsxAdapter for the new separate verify_dns/active_safe
capability, preserving native resolve_dns and passive enumerate_subdomains. Trusted
composition reviews/pins DNSX 1.2.2 and uses bounded isolated no-target detection.
Strict 1–64 dotted hostname candidates plus one A/AAAA/CNAME/MX/NS/TXT mode declare
every candidate as a policy target. Mixed/empty/all-rejected batches never write
input or dispatch. Canonical approved names deduplicate/sort; final scope rechecks
precede the temporary absolute-name list. One operator numeric IPv4 resolver needs
independent scope membership and host-budget charges.

Existing runner/policy/budget/registry logic is unchanged. Fixed JSONL/stream mode,
one worker/candidate per second/attempt and record mode disable discovery/wildcard/
trace/hosts/CDN/ASN contact expansion. Same-resolver TCP fallback is explicit;
whole-action/session/capture/cancellation bounds remain runner-owned. Complete
fresh HOME/config/temp environment excludes ambient YAML/credentials/proxy/PDCP,
with auth/update disabled and cleanup after every process outcome.

Full RR strings retain actual owner/type/value/TTL/MX/TXT data in existing internal
DnsRecord and generic primary Asset/DNS Observations/untrusted Evidence. DNSX merges
sections: attribution remains unspecified, wildcard status unchecked or conservatively
suspected for shared addresses. Malformed query lines preserve other valid lines;
conflicting duplicates discard that host with deterministic counts. Partial/empty
output explicitly lists unreported candidates/errors; all-malformed/truncated/oversized
output fails. Missing/nonzero/timeout failures retain canonical codes/exit context.
Source/version/subject/time/execution and stable normalized snapshot/hash preserve
provenance. Caller owns partial lifecycle/ingestion. Results never grant authorization.
No later adapter, generic dispatcher, planner/loop/persistence/reporting/real CLI.
See docs/dnsx-adapter.md and ADR 0010. The sole protected production change is one
finite verify_dns enum member; no new dependencies or configuration fields.

M2-T04 adds tools.httpx.HttpxAdapter for the existing probe_http/active_safe
capability, with explicit registry composition and strict optional candidate batches.
All primary/member targets independently pass current policy/scope; mixed batches
reject before temporary input or dispatch. Operator numeric IPv4 resolver and finite
1–64 numeric IPv4/IPv6 contact addresses independently pass scope and join shared
host budgets. Reviewed HTTPX 1.9.0 applies this checked allow set at the fastdialer
concrete-IP gate; changed DNS answers cannot contact outside it. Custom resolver
excludes ambient/public/system lookup fallback. No DNS authorization inference.

Fixed GET/JSONL/stream argv uses one worker/probe per second, zero configured HTTP
retries, explicit scheme, bounded bodies and no redirects/HSTS/CDN/discovery probes.
Fresh HOME/config/temp child environment and null flag config exclude ambient secrets,
proxies and YAML mode overrides. Availability checks pin 1.9.0 with a bounded isolated
no-target version probe; unknown versions fail closed. Existing runner/policy/budget/
registry/domain/config/dependencies/CLI remain unchanged. Deadline/cancellation/capture/
nonzero/setup failures preserve canonical contracts and release local concurrency/temp.

Existing generic Endpoint/HTTP Observation/untrusted Evidence preserve httpx/probe_http/
version, subject/execution/time/reference/hash lineage. Optional title/server/type/length,
relative/absolute redirect and technology hints remain tool facts; absent fields stay
absent. Redirect scope status never grants permission or creates another endpoint/action.
No vulnerabilities/scanners inferred. Deterministic URL/technology/input dedup and
order-independent conflict discard, bounded JSONL and explicit malformed/unreported/
empty partial status preserve evidence limits. Caller owns lifecycle and ingestion.
Source/fixtures are reviewed without live HTTPX contact. See docs/httpx-adapter.md and
ADR 0011 for compatibility, body/rate/direct-child/recursive-infrastructure limits.
M2-T04 added no crawling, Naabu or later capability, generic dispatcher, planner/loop/persistence/
reporting or real CLI. M2-T04 closed without blocker or new follow-up task.

M2-T05 adds tools.naabu.NaabuAdapter for discover_ports/active_safe through explicit
registry composition. Naabu 2.3.5 is source/fixture-reviewed, with isolated bounded
no-target version detection and fail-closed unknown/missing binaries. Strict optional
candidate batches pass current policy/scope; mixed batches reject before input.
Hostname targets need operator numeric contact bindings plus independent IP scope;
only numeric IPv4/IPv6 contacts reach Naabu. No DNS/target expansion or inferred
address permission. All names/contacts recheck before input and share host budgets.

Operator-only immutable typed inclusive TCP ranges default to 80/443, at most 128
ports; 64 distinct contacts and 4,096 pairs cap one process. Fixed isolated CONNECT
stream mode uses one concurrent connection/start per second, explicit 1s dial timeout,
no retry rounds/verification/host discovery/passive API/CDN/PTR/proxy/service/Nmap.
Null config and fresh complete HOME/config/temp environment exclude ambient overrides,
credentials/proxies/cloud. Existing runner/policy/budgets/registry/domain/global config/
previous adapters/dependencies/CLI are unchanged. Canonical errors retain missing/
nonzero/timeout/truncation/setup context; action/session/capture/normalized bounds and
cancellation cleanup use existing contracts. Attempts stay charged; concurrency releases.

Generic Asset/numeric Host/Service(tcp)/service Observations/untrusted Evidence preserve
primary/member/contact/port/source/version/time/execution and snapshot/hash lineage.
Operator references do not prove DNS; protocol/product/version remain absent. Sorted
IP/port facts deduplicate; valid+malformed lines return explicit partial status/errors;
all-malformed/truncated/oversized output fails. Empty output gives evidence without
open/closed/liveness/completeness facts. Existing generic state accepts the lineage.
No Nmap/M2-T06+, pipeline, planner/runtime/loop/persistence/reporting/real CLI work.
See docs/naabu-adapter.md and ADR 0012. No blocker or new follow-up; stop after M2-T05.

M2-T06 adds tools.nmap.NmapAdapter for fingerprint_services/active_safe through
explicit registry composition. Source-reviewed Nmap 7.95 must be compiled without Lua:
ordinary -sV invokes version NSE scripts. Isolated bounded no-target detection verifies
version/features; undetected instances cannot execute even if registered AVAILABLE.
No install/build/fallback. Operator trusted installation/database paths and immutable
prior-discovery selections provide one numeric contact/optional hostname, 1–128 TCP
ports and evidence references. Required strict integer requested ports must be a subset;
no default ports. Registered-schema sorting/dedup prevents cosmetic port-set replay.

Current registry/policy/risk/schema/dedup, independently scoped primary/contact,
atomic shared charged budgets and final scope rechecks precede numeric-only argv.
Fixed unprivileged CONNECT/native version intensity 2/no DNS/no host discovery/ARP/XML
profile uses bounded scan rate/concurrency/no retries, explicit database paths and
fresh complete environment. Native version concurrency is one; initial scan rate
flags do not govern every version-probe reconnect/write. Existing runner/session/
capture/normalization/cancellation/temp cleanup and canonical failures remain intact.

Safe bounded UTF-8 XML permits only harmless Nmap DOCTYPE, rejects entity/external
DTD/internal subset/alternate encoding and unsupported scan-mode output. Selected
IP/TCP ports/state/metadata normalize to generic Asset/Host/Service/Observation/Evidence;
only open ports become Services, other states remain observations. Identical duplicates
sort/dedup; conflicts/malformed/truncated XML fail atomically. Valid missing/empty
records preserve explicit partial/unreported_ports. Optional name/product/version/
extra_info/service_fingerprint/tunnel/method/confidence/CPE metadata remains untrusted,
with no vulnerability inference. Source/capability/version/prior refs/time/execution/
memory locator/snapshot hash preserve provenance and generic state lineage. Caller
owns lifecycle/ingestion/retention. Naabu discovers ports; Nmap fingerprints selected
services. No pipeline/M2-T07+, planner/loop/persistence/reporting/real CLI work.
See docs/nmap-adapter.md and ADR 0013. Protected existing production/contracts/deps
remain unchanged. No blocker or added follow-up; stop after M2-T06.

M2-T07 adds orchestration/DiscoveryWorkflow, the first deterministic end-to-end
integration of all six M2 capabilities with current ActionPolicyValidator, atomic
ActionDeduplicator admission, ToolRegistry, shared adapter-owned BudgetController
and atomic ReconState results. Finite root DNS → passive enumeration → scoped batch
verification → HTTP → port discovery → numeric service fingerprinting; at most 64
candidates/contacts and 128 ports/address. Failed tool branches continue independently;
fatal scope/policy/resources/state errors stop. Duplicates skip without admission,
contact or charges. Normalized outputs and correlated audit records remain in memory.

Integration fixes add optional post-reservation/pre-contact start notifications,
terminal subject ingestion in the existing state commit, exactly tool_unavailable
pre-start rejection, and detached Nmap selection snapshots preserving detection/
installation/limits. Nmap selections derive from recorded completed/partial Naabu
open-port actions. No address binding is inferred from DNS; contacts/resolvers remain
independently authorized and rechecked by existing adapters. Failed transitions leave
prior state intact. State/data contracts otherwise retain their existing semantics.
See docs/deterministic-discovery.md and ADR 0014 for limits and failure mappings.
M2 pipeline = deterministic integration proof; M6/M7 = future AI planning/autonomous
loop. No provider/PlannerDecision generation, Groq, M3 capability, retry scheduling,
persistence/reporting/real CLI or live scanner added. M0/M1/M2 DONE.

Audit events describe autonomous recon operations and confer no authorization. Autonomous event
producers, generic Action/ToolExecution/Finding entities, later scanners, Groq/provider/planner
runtime, automatic retry scheduling, autonomous loop, persistence and operational
reports remain unimplemented. No chat transcript or private reasoning contract exists.
Only M3-T04 is READY; remaining 67 tasks are NOT STARTED.

M3-T01 adds standalone tools.common_files.CommonFilesAdapter for inspect_common_files,
active_safe, strict empty planner parameters and the fixed robots/sitemap/security
catalog. Operator canonical name/numeric contact bindings independently pass scope
and shared host budgets. Native asyncio/SSL sockets pin contacts with original
Host/SNI/certificate verification; h11 0.16 supplies bounded sans-I/O framing. No
DNS/proxy/cookie/auth/retry/shell client. At most two same-path/no-query/no-downgrade
redirect hops independently revalidate URL/IP scope before contact. Body/header/wire,
request/action/session deadlines, paced GETs and normalized output bounds hold;
close/abort/cancellation retain charges and release concurrency.

Bounded UTF-8 robots directives, sitemap/index URLs and security fields/text project
into generic Asset/HTTP Observation/untrusted Evidence with caller time/IDs, source/
capability, memory locator and fact SHA-256. XML DTD/entity/alternate-encoding input
rejects before parsing; no external resolution or sitemap recursion. Discoveries/
remote instruction text never grant scope/contact. Ordinary HTTP statuses are facts;
request errors/unsupported/truncated/malformed/rejected redirects retain explicit
partial collection limits. Existing state/dedup ingestion works without contract
changes. Protected policy/runner/registry/config/CLI/M2 adapters/pipeline and all later
subsystems remain unchanged; only the finite capability enum gains one identity.
See docs/common-file-inspector.md and ADR 0015. M3-T01 DONE.

M3-T02 adds standalone tools.tlsx.TlsxAdapter for existing inspect_tls/active_safe.
Successful explicit Linux TLSX 1.4.0 detection enables execution; canonical original
names/IPs/HTTPS authorities and numeric bindings independently pass scope. Strict
finite candidate/port input and operator port allowlist reject whole mixed batches
before files/contact. Private PATH/config/home/environment exclude OpenSSL startup/
ambient credentials. Adapter-owned numeric/SNI files and fixed native ctls/JSON argv
use sequential SNI groups, no global SNI cross product, revocation/cloud/update/
enumeration/derived contact. One shared reservation/deadline and existing runner
capture/cancellation cleanup apply; aggregate and normalized output bounds hold.

Bounded deterministic JSONL normalizes subject/issuer/CN/DNS SANs/fingerprints/serial/
validity/protocol/cipher/key exchange and explicit incomplete/handshake limitations
into generic TLS Observations/untrusted Evidence. Source/version/capability/caller
UTC/subject/execution/memory locator/SHA-256 preserve provenance. No certificate-
derived asset/Finding or authorization; existing state lifecycle/dedup unchanged.
No runtime dependency/core/policy/domain/runner/registry/common-file/M2/pipeline/CLI
change. Source review includes same-peer fastdialer failure fallback (up to two dial
attempts/logical probe), not a packet/heap/process-tree guarantee. See docs/tlsx-adapter.md
and ADR 0016. M3-T02 DONE; standalone crawling follows below.

M3-T03 adds standalone tools.katana.KatanaAdapter for existing crawl_web/active_safe.
Detected Linux Katana 1.8.0 performs one numeric HTTP(S) GET with depth zero and
positive duration; child discoveries are emitted before queue admission. Fixed no-
redirect/form-fill/headless profile prevents hidden htmx state-changing contacts.
Hostname modes fail closed: reviewed CLI has no independent resolved-address allow
boundary. Adapter owns a finite sorted same-origin hyperlink/script-resource GET graph,
fresh URL/address scope checks, shared budgets/deadline/pacing/output limits and cleanup.
Operator depth 0–3/pages 1–16/discoveries 1–256; planner parameters are strict empty.

Generic Endpoint/HTTP Observation/untrusted Evidence retain URL/method/source page,
path/query/source type/forms/JS metadata with caller subject/UTC/execution/hash lineage.
Remote forms/JS endpoints/redirects/outside hosts remain data without authorization or
follow-up actions. Deterministic duplicate/order and canonical malformed/partial/empty/
missing/timeout/nonzero/resource errors; existing state/dedup integration unchanged.
Only existing production change is optional trusted absolute ProcessSpec child cwd and
literal runner forwarding, required for Katana's relative katana_field cleanup isolation.
Core/policy/domain/registry/config/dependencies/CLI/previous adapters/M2 pipeline unchanged.
No future capability/planner/loop/persistence/reporting. See docs/katana-adapter.md and
ADR 0017. M3-T04 READY; no active task/blocker. Stop after M3-T03.

## Major architecture decisions

- ADR 0017 selects numeric depth-zero Katana extraction, adapter-owned finite freshly scoped GET graph and isolated trusted child cwd; hostname/recursive/redirect/form/JS endpoint modes fail closed.

- ADR 0016 selects detected Linux TLSX 1.4.0, independently scoped numeric contact/original SNI, isolated configuration/PATH and bounded generic untrusted TLS evidence.

- ADR 0015 selects a fixed common-file catalog, scoped numeric native HTTP/SSL with h11 framing, narrow independently checked redirects and untrusted bounded text/XML metadata.

- ADR 0014 selects bounded deterministic M2 integration, adapter-owned reservations/start callbacks, atomic terminal subjects and immutable evidence-derived Nmap snapshots; no AI loop.

- ADR 0013 selects detected Nmap 7.95 without Lua, trusted prior-discovery port selections, independently scoped numeric contact and bounded native service/XML evidence; no NSE or pipeline.

- ADR 0012 selects independently scoped numeric hostname bindings, operator finite TCP ranges and isolated Naabu CONNECT stream discovery; no DNS expansion or fingerprinting.

- ADR 0011 selects reviewed HTTPX 1.9.0 with independently scoped numeric contact/resolver constraints, isolated fixed probing and no redirect following; metadata/technology remain untrusted evidence.

- ADR 0010 selects a separate verify_dns capability, atomic scoped batches, numeric resolver, fixed isolated DNSX and explicit merged-section/wildcard/partial evidence limits.

- ADR 0009 selects reviewed passive Subfinder, one explicit credential-free source and enforced temporary child configuration through a minimal trusted runner environment seam; discovered data grants no authority.

- ADR 0008 selects bounded native dnspython UDP with explicit independently scoped resolver infrastructure, fixed questions, no alias/fallback/retry and existing policy/budget/domain boundaries.

- ADR 0007 selects versioned full semantic JSON identity, existing state history, atomic admission and explicit default-zero bounded failed retries; eligibility never authorizes or executes.

- ADR 0006 selects validated frozen state snapshots, defensive ownership, atomic local transitions, explicit history/times and read-only budget recording; policy/resources/execution remain independent.

- Capability intent never becomes LLM-generated shell/argv. Immutable trusted registry supplies facts; local action policy checks eligibility and trusted adapters own executable construction.
- ADR 0005 selects atomic local reservations, permanent attempt/output charges, rolling monotonic rates and synchronous concurrency ownership without runtime dispatch.
- ADR 0003 selects explicit immutable composition, one selected adapter per capability and semantic-only planner catalog; declared availability defaults fail closed.
- Pure centralized scope/action eligibility and capability-specific DNS/Subfinder/DNSX/HTTPX/Naabu/Nmap enforcement are implemented; generic dispatch and future adapter containment remain future work. Discovery/planner recommendations grant no authority.
- ADR 0002 requires independently declared address membership, constrained/pinned approved contacts and revalidation on address/destination changes; native DNS contacts only independently approved numeric resolver infrastructure, with no implicit name-to-IP authorization.
- Remote evidence and model recommendations remain non-authoritative data with provenance. Audit records do not authorize replay.
- Pure domain/error models never emit logs. Future application/orchestration services emit concise decision summaries, policy outcomes and execution records, without private reasoning or transcript state.
- Explicit local standard-library logging leaves root/third-party handlers alone, performs no remote upload/file persistence and needs no new runtime dependency or ADR.
- Bounded diagnostics exclude raw environment/output/native causes/commands. Registered secrets and key-labelled secret values are masked; arbitrary unregistered free-text secrets require producer discipline. Source evidence is never mutated.
- Exceptions handle application boundaries; ErrorInfo is portable failure data; generic results support intentionally inspected outcomes. Retryability grants no authority.
- ADR 0001's explicit TOML and separate-secret choice is unchanged. Explicit IDs/times and controlled state mutation remain separate from semantic canonical identity and execution. Groq/SQLite remain planned; default tests are deterministic offline checks.

## Validation

M3-T03: Python 3.14.6. Editable dev install/pip check, Ruff lint/format (149 files),
strict Mypy (68 modules), isolated wheel/sdist build and editable/fresh-wheel inert CLI
passed. Focused Katana/registry/execution: 281 passed (91 Katana + 8 new cwd cases).
Full, coverage and pre-collection network/DNS-blocked suites each: 2,542 passed.
Coverage 97% overall (4,792 statements / 1,616 branches), Katana adapter 89%, parser
95%, models 100%; defensive setup/composition/detection/bound branches remain.
Fresh external wheel venv/pip check, guarded cold imports/origins/empty registry/inert
Katana construction and 99 installed-wheel network-blocked Katana/cwd cases passed.
Artifact/secret/source/dependency wheel/sdist parity, protected source parity except
reviewed runner cwd seam, AST boundary, append-only history, readiness/Markdown/final
diff/whitespace checks passed. Logs/scripts: /tmp/recon-m3t03-validation. Guards precede
collection and allow AF_UNIX plumbing; harmless interpreter children are not sandboxed.
Python 3.12 and live Katana/network behavior not tested; no scanner installed/run.
No gates weakened, no blocker or later work started. Numeric-only containment and
transport/download/OS limits are explicit in contract/ADR. M3-T04 READY.


M3-T02: Python 3.14.6 / Pydantic 2.13.5 / dnspython 2.8.0 / h11 0.16.0;
Python 3.12 and live TLSX/targets not tested. Editable dev install/pip check passed.
Focused TLSX/registry: 223 passed (125 new TLSX cases). Full, coverage and pre-collection
network/DNS-blocked suites each: 2,443 passed. Ruff lint/format (142 files), strict Mypy
(65 modules), isolated wheel/sdist build and editable/fresh-wheel inert CLI passed.
Fresh external wheel venv/pip check, guarded cold imports/origins/empty registry/inert
TLSX construction and 125 installed-wheel network-blocked fake-runner/state/dedup
cases passed. Coverage 97% overall (4,439 statements / 1,472 branches), TLSX adapter
94%, parser 99%, models 100%; remaining adapter branches are defensive malformed
composition/setup/deadline/unsupported representation and optional environment seams.
No gates weakened. Every existing production Python file remains byte-for-byte
unchanged. AST execution boundary, artifact/secret, source/dependency wheel/sdist
parity, append-only history, 92-task dependency/readiness, Markdown and final diff/
whitespace checks passed. Logs/scripts are outside checkout under
/tmp/recon-m3t02-validation. Guards precede collection and permit AF_UNIX plumbing
only; harmless local interpreter children are not network sandboxed. No blocker or
added future work. TLSX compatibility is pinned source/fixtures only, with limits in
contract/ADR; no scanner installed or public-target test.

M3-T01: Python 3.14.6 / Pydantic 2.13.5 / dnspython 2.8.0 / h11 0.16.0; Python 3.12
and live targets not tested. Editable dev install/pip check passed. Focused common-file/
native/registry suite: 197 passed (99 new common-file/native cases). Full, coverage and
pre-collection network/DNS-blocked suites each: 2,318 passed. Ruff lint/format (136
files), strict Mypy (62 modules), isolated wheel/sdist build and editable/fresh-wheel
inert CLI passed. Fresh external wheel venv/pip check, guarded cold imports/package
origins/inert composition and 99 installed-wheel network-blocked fake-transport/native-
stream/state/dedup cases passed. Coverage 97% overall (4,047 statements / 1,324 branches),
common adapter 93%, parser 97%, models 100%, native transport 90%; remaining branches
are malformed composition/defensive framing/aggregate structure bounds. No gates weakened.
Protected source parity/AST execution boundaries, artifacts/secrets, wheel/sdist source/
dependency parity, append-only history and final task/diff/whitespace checks passed.
Validation logs/scripts are outside the checkout under /tmp/recon-m3t01-validation.
Network guards precede collection and permit AF_UNIX loop plumbing only; harmless
local interpreter children are not network sandboxed. No blocker/new follow-up task.


M2-T07: Python 3.14.6 / Pydantic 2.13.5 / dnspython 2.8.0; Python 3.12 not tested.
Editable dev install/pip check passed. Pipeline: 48 passed; focused pipeline/state/
domain/all tools: 1,102 passed. Full, coverage and pre-collection network/DNS-blocked
suites: each 2,219 passed. Ruff lint/format (128 files), strict Mypy (58 production
modules), isolated sdist/wheel build and editable/fresh-wheel inert CLI passed.
Fresh external wheel venv/pip check, guarded cold imports and six-adapter fake
composition plus installed pipeline full/repeated/dedup/scope/empty-partial flow passed.
Coverage: 97% overall (3,606 statements / 1,152 branches); workflow 92%, start helper
100%. No validation settings/gates weakened. Uncovered workflow branches are defensive
binding/transition/malformed-input/aggregate-history bounds; shared adapter/state tests
also protect underlying boundaries. No live scanner or additional interpreter claim.

Protected policy/core/registry/parsers/runner/config/CLI/later subsystem parity,
AST/no shell/direct subprocess/provider/dynamic import, unchanged dependencies,
wheel/sdist source parity and artifact/secret checks passed. Append-only history,
92-task readiness, Markdown links/fences and final working/staged whitespace/diff
checked at closeout. Network guards precede collection and allow AF_UNIX event-loop
plumbing only; harmless local interpreter children are not sandboxed. Fresh-wheel
imports prohibit contact/process/availability/temp/runtime startup. Existing third-
party Subfinder, recursive resolver, supported binary/OS/native packet-rate and
process-tree limits remain unchanged; no public target or scanner binary was used.

Known blockers: None.

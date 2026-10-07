# Capability and tool contracts

M1-T04 implements finite semantic metadata in `domain/capabilities.py` and explicit,
immutable registry composition in `tools/`. M2-T01 adds an operational native DNS adapter;
M2-T02 adds passive Subfinder; M2-T03 adds bulk verify_dns through DNSX; M2-T04 adds constrained probe_http through HTTPX; M3-T01 adds fixed native inspect_common_files; M3-T02 adds bounded inspect_tls through TLSX; M3-T03 adds bounded numeric crawl_web through Katana; M3-T04 adds bounded numeric discover_content through Feroxbuster. Later scanner adapters remain unimplemented.
The default `ToolRegistry()` is empty; importing `recon_agent.tools` registers nothing.

## Capability, adapter and execution details

A **Capability** is the semantic operation the planner may request. `CapabilityId`
is a finite string enum: resolve_dns, verify_dns, enumerate_subdomains, discover_ports,
fingerprint_services, probe_http, inspect_common_files, inspect_tls, crawl_web, discover_content,
inspect_protocol and scan_templates. These conceptual identities do not imply
working integrations. There is no run_command, execute_shell or arbitrary binary
capability. Extending the catalog requires reviewed application code.

A **Tool** is an external program or other implementation mechanism. A
**ToolAdapter** is trusted application code implementing a capability; its stable
adapter ID is distinct from capability identity and executable path. A
**ToolRegistry** is a deterministic mapping/catalog of those explicitly supplied
trusted instances. A **ProcessSpec** is internal executable/literal argument data
constructed by trusted adapters for the M1-T03 runner. None of these is a shell
command or planner-supplied execution instruction.

```text
Planner selects capability                 [future runtime]
  → deterministic action policy            [M1-T05, implemented local eligibility]
  → ToolRegistry selects trusted adapter    [implemented foundation]
  → ToolAdapter validates/prepares execution
      → bounded native DNS → normalized observations [M2-T01, implemented]
      → ProcessSpec → AsyncProcessRunner → Subfinder [M2-T02, implemented]
```

Operators will supply target, authorized scope and configuration to the autonomous
session. Registry lookup needs no chat interaction or per-action user confirmation.
Capability existence, registration, availability and installation grant no action
authorization. M1-T05 combines scope/parameter/risk checks; M1-T06 owns budgets.

## Strict semantic metadata and schemas

`CapabilityDescriptor` is frozen/strict/extra-forbid: capability enum, bounded
non-blank description and `RiskClass` (`passive`, `active_safe`). Risk is supplied
by trusted definitions and reported only; the registry does not authorize it.
Descriptions must be curated semantic text, never copied from paths, flags,
environment or remote evidence. No automatic metadata redaction can make arbitrary
trusted free text safe; producers own its contents.

`AdapterDefinition` is a frozen strict internal model with adapter_id (lowercase
ASCII identifier, underscores/hyphens, at most 64 characters), descriptor,
input_schema and output_schema. Schemas are trusted Pydantic model **classes**,
required to be strict and extra-forbid. They are excluded from ordinary dumps/repr;
lookup returns the classes internally for policy/adapter validation. M1-T05 validates
ActionRequest.parameters against input_schema; the primary target is checked
separately. DNS/Subfinder schemas are internal to their implemented adapters; later scanner schemas remain future work.

`ToolAdapter` is a minimal abstract base class with a read-only `definition`
property. Its base API remains unchanged. M2-T01 adds capability-specific async
DnsAdapter.execute with strict input, current policy/resources, native resolver
injection and normalized domain output. M2-T02 adds Subfinder binary/version detection, isolated configuration, trusted argv and injected ProcessRunner execution.

Planner parameters must flow through capability-specific typed validation to a
trusted adapter. No dictionary-to-flags translation or argv pass-through is allowed.
Schema classes, adapter instances and implementations never come from planner JSON,
remote content, arbitrary config imports or deserialized requests. Subfinder paths are trusted operator composition inputs and cannot appear in planner contracts. Current ToolsConfig has only enabled; it is not consumed by the registry
and cannot introduce commands or registrations.

## Explicit composition and deterministic selection

Construct `ToolRegistry(iterable_of_AdapterRegistration)` in trusted application
code. Each registration supplies a ToolAdapter instance and explicit availability
snapshot. Definitions are revalidated/snapshotted before committing constructor
state. There are no mutable global registries, register methods, entry points,
package discovery, dynamic imports, PATH lookup or fallback adapters.

There is **one selected adapter per capability** in each registry. Different trusted
application compositions can choose alternatives later; no AI adapter selection is
introduced. Duplicate adapter IDs (even the same object twice) and conflicting
capability mappings (even identical metadata) raise canonical ConfigurationError
with configuration_invalid and safe identity context; nothing silently overwrites.
Malformed trusted registrations/definitions use the same startup error boundary.
Direct metadata construction retains Pydantic ValidationError. See
[ADR 0003](decisions/0003-immutable-capability-registry.md).

The registry and private mappings are immutable; public collections are tuples and
metadata records are frozen. Instances/schema classes remain trusted code objects,
not a sandbox against application code deliberately mutating itself. Definition
metadata is snapshotted; adapter implementations must keep their definition stable.

| API | Meaning |
| --- | --- |
| is_known_capability(name) | Finite conceptual catalog membership |
| has_capability(name) | An adapter is registered for this capability, independent of availability |
| has_adapter(id) | Adapter identity registered internally |
| list_capabilities() / list_adapters() | Registered identities sorted lexicographically, immutable tuples |
| capability_definition(name) | Available snapshotted AdapterDefinition facts without adapter access; canonical unknown/unavailable failures |
| definition(id) | Existing OperationResult[AdapterDefinition], internal schema/metadata lookup |
| resolve(name) | Existing OperationResult[InstanceOf[ToolAdapter]], selected trusted object or Failure |
| catalog() | Sorted tuple of planner-safe CapabilityCatalogEntry values |

Unknown/invented capability returns PlannerValidationError-derived Failure
(planner_validation_failed); its raw name is not echoed. Known but unregistered
capability returns ToolUnavailableError-derived Failure (tool_unavailable). Unknown
adapter ID also returns tool_unavailable without interpreting the ID as a binary.
Lookups never authorize targets, enforce budgets, invoke runner methods or emit
execution/policy audit events. All operations are synchronous local facts.

## Availability and safe catalog

AdapterAvailability has not_checked (default), available and unavailable. These
are explicit trusted snapshots, **never probes performed by the registry**.
Registration is distinct from external dependency availability. Future composition
may declare available only after adapter-owned checks; dispatch must recheck stale
runtime facts. Unavailable/not_checked registrations still appear in the catalog,
but resolve returns canonical tool_unavailable Failure with safe capability/adapter
references. enabled is an operator preference reserved for future composition;
registry registration does not implement enablement.

`CapabilityCatalogEntry` contains exactly capability, description, risk_class and
availability. Enum values serialize to stable JSON strings; ordering is lexical by
capability. This is the only planner-safe projection. It includes no adapter ID,
instance, implementation/model classes, input JSON-schema dump, executable, argv,
command/template/script, import path, environment, runner or secrets. Unexpected
fields are rejected. Internal resolution Success contains a trusted Python object
and is not a planner serialization API. Never serialize it into planner input.
Future planner input must bound/filter this catalog using policy and validated
semantic parameter summaries in their owning tasks.

ActionRequest retains its lowercase capability-name syntax to preserve unapproved
wire intent and provenance; well-formed unknown names may be represented as data.
Registry resolution interprets them only against CapabilityId. No unknown name
becomes a program, dynamic import or newly constructed adapter. Top-level execution
fields and nested reserved executable/import keys are rejected. Structured parameters
require ActionPolicyValidator capability-specific validation and are never process flags.

## Scope validation boundary

M1-T01 now supplies `ScopeValidator.validate(Target)` / `require_allowed(Target)`
for local membership only; see [scope model](scope-model.md) and
[ADR 0002](decisions/0002-scope-and-derived-addresses.md). Future adapters must check
each absolute redirect destination, discovered hostname and concrete resolved
address independently before contact, pin/constrain approved addresses and recheck
changes. Native DNS and passive Subfinder have capability-specific execution; HTTPX supplies constrained no-follow probing; generic dispatch, redirect following and later scanner adapters remain future work.

## Normalized outputs

Outputs should include source adapter/version, target, timestamp, execution reference, evidence reference, and typed facts. Service observations include port, transport, service/protocol, and optional product/version. DNS observations include name/type/value and resolution context. HTTP observations include URL, status, title, server, content type, redirect destination, and technology hints with provenance. TLS observations include certificate fields and SAN names; discovered names remain unactionable until validated. Web outputs include canonical endpoints and bounded metadata. Template results become findings with supporting evidence.

Conceptual observation:

```json
{
  "kind": "service",
  "asset_id": "asset-example",
  "source": "nmap",
  "data": {
    "port": 443,
    "transport": "tcp",
    "service": "https",
    "product": "nginx"
  }
}
```

Identifiers are placeholders. Product text is tool evidence, not a verified vulnerability or trusted instruction. The final model also carries evidence/execution references as specified in [data model](data-model.md).

## Result and failure semantics

Keep execution success separate from parser validity and useful observation count. Preserve non-zero exit, timeout, cancellation, truncation, partial output, missing binary, and parser failure in structured results. Partial evidence must identify its limits. Never manufacture a successful fact from malformed output or silently switch to broader scans.

Every adapter needs sanitized fixture parsers, argv checks, fake-runner tests, scope/limit rejection tests, and an explicit opt-in integration marker for real binaries. See [testing strategy](testing-strategy.md).

## Implemented process boundary (M1-T03)

Capability is not a command. Future ToolAdapter implementations own executable
selection and
literal argv construction after deterministic policy and registry dispatch.
ExecutionRunner only launches that internal ProcessSpec; the planner never supplies
executable names/argv or calls it directly. ActionRequest/PlannerDecision have no
execution fields; ActionRequest also rejects
planner-controlled import keys.
`ProcessRunner.run` is awaitable and returns existing OperationResult with bounded
raw ProcessExecution facts; fixture runners can implement the same small protocol.
M1-T04 now supplies the upstream interface/registry described above; Subfinder owns external execution; generic dispatch remains future work.

Adapters must interpret non-zero exits, decode bytes, check independent stdout/stderr
truncation flags, and convert facts into observations/ActionResult. The retained-byte
cap is per stream; excess is drained/discarded. Timeout returns canonical Failure
without partial output, since the existing Failure has no payload. Cancellation
re-raises asyncio.CancelledError after direct-child cleanup. Descendant supervision
is not supplied: tools spawning descendants require further containment before
safe integration. Spec and output dumps are internal evidence, never automatic logs.

## Action policy contract (M1-T05)

```text
Planner request
  ↓
ActionPolicyValidator.validate(ActionRequest)
  ↓ only approved actions may continue; dispatch must revalidate
ToolRegistry / trusted Adapter / Runner [DNS/Subfinder capability execution; generic dispatch future]
```

The validator consumes immutable registry metadata, not adapter instances, plus an
explicit ScopeValidator and frozen ActionPolicyConfig. Empty capability/risk
allowlists deny all. Finite CapabilityId/RiskClass values prevent introducing arbitrary
operations. ToolsConfig.enabled is not consumed here and grants no permission.
Registry availability must be confirmed; registration/availability alone cannot
approve anything. Scope membership alone is also insufficient.

Parameters are validated with the registered strict extra-forbid input_schema,
never converted to flags. ActionRequest is revalidated to reject mutated/copied or
constructed malformed records and reserved nested executable/import keys. Fixed
errors omit raw parameter values and native validation errors. Trusted schemas must
validate defaults and preserve strict nested contracts; schema validators are pure
local application code, never network or execution hooks.

AdapterDefinition.parameter_target_fields is trusted internal metadata, absent from
planner catalog. None defaults to unestablished semantics and denies policy approval.
An explicit () asserts that the parameter schema introduces no secondary network
targets. Otherwise every declared unique input field must contain a validated string
or list/tuple of strings. Defaults are checked too. Each value passes centralized
ScopeValidator.validate_value. Nested or other target representations reject; no
scanner-specific schema is introduced. Schema owners must declare every target
input; opaque non-target strings must never later be used as destinations. The
current ActionRequest always requires a primary target; there is no target-less
capability contract or exemption. See [ADR 0004](decisions/0004-action-eligibility-boundary.md).

ActionPolicyValidator.validate returns existing Success[ApprovedAction] or Failure.
Success is a current eligibility decision with action_id/capability, canonical primary
ScopeMatch, secondary matches and the trusted typed parameter model (excluded from
dumps/repr). It is internal data, not a reusable execution token or automatic audit
payload. Failure carries canonical ErrorInfo: planner_validation_failed for malformed,
unsupported, disallowed or schema-invalid intent; scope_rejected for scope failures;
tool_unavailable for missing/unavailable registrations; budget_exhausted for missing
budget eligibility. Callers correlate rejections with the supplied request; no new
failure envelope/taxonomy exists. Reasons are fixed policy text, never planner reasons.

BudgetEligibility.check(ApprovedAction) and the completed-action
ActionEligibility.check(ActionRequest) return OperationResult[None]. Missing services
deny; returned malformed outcomes also reject. M1-T06 evolves the budget seam to
consume canonical primary/secondary targets without repeating schema/scope checks
and supplies BudgetController. M1-T08 supplies ActionDeduplicator, reading existing
state history and explicitly bounded failed-retry limits. Permitting fakes remain
test-only; no production permitting stub exists.

Future dispatch must revalidate the original request against current scope, registry,
parameters, risk and eligibility; atomically reserve budgets and enforce deduplication.
An old approval, modified parameter model or deserialized record cannot skip checks.
Adapters must independently check newly introduced redirect/discovery/DNS destinations
and constrain actual contact. Policy validation is synchronous local checking only:
no registry mutation, adapter execution, binary selection, runner, network/DNS, Groq,
audit emission or tool.execution_started event.

## Resource reservations (M1-T06)

Policy authorization != budget availability. After current policy revalidation,
future dispatch calls BudgetController.reserve on the normalized ApprovedAction and
immediately enters the returned BudgetPermit. This atomically bounds permitted
attempts, all host buckets, selected-tool/capability rates, concurrency, session time
and two-stream output allowance; no adapter or runner is invoked. Context exit
releases only concurrency and records a typed outcome; retries need new charged
reservations. No implicit multi-process/tool-internal traffic allowance exists.
AI planner cannot raise resource limits. See [budget contract](execution-budgets.md)
for exact ownership, counting, CIDR rejection and future adapter obligations.


## State recording (M1-T07)

ReconStateMachine records explicit requested/approved/started/terminal history and
normalized evidence/observations. Policy references and execution IDs are historical
caller-supplied facts, never runner instructions or replay authorization. State does
not resolve adapters, approve via planner text, acquire budgets, build commands or
invoke execution. Future dispatch still revalidates policy/reserves resources before
contact and later records outcomes atomically. M1-T08 adds action equivalence and
bounded failed-retry eligibility with atomic REQUESTED admission; no dispatch is
added. See [state contract](state-transitions.md).

## Action deduplication (M1-T08)

ActionCanonicalizer reuses available registered input_schema and declared target
semantics with policy's shared scope/schema validation. Validated defaults/nested
fields define identity, including fields excluded from serialization. No parameters
become flags. ActionDeduplicator implements the existing ActionEligibility seam
without adapter resolution, approval, resource consumption or execution. The same
state owner atomically admits new/retry requests.
See [canonical identity, lifecycle rules and policy self-entry handling](action-deduplication.md).

## resolve_dns implementation (M2-T01)

The explicitly registered native_dns adapter implements resolve_dns for scoped
hostnames and A/AAAA/CNAME/MX/NS/TXT questions. DnsInput exposes only record_types;
resolver internals never enter planner input/catalog. DnsOutput returns typed query
outcomes and existing Asset/Observation/Evidence with exact untrusted provenance.
Native UDP exchanges are independently endpoint-authorized and bounded by existing
policy/budget settings; no process runner or dig is involved. Default registry remains
empty. Enumeration is implemented via Subfinder (M2-T02); DNSX verification is implemented separately as verify_dns (M2-T03). See the complete
[input/contact/normalization/error contract](dns-resolver.md) and
[ADR 0008](decisions/0008-bounded-native-dns.md).

## enumerate_subdomains implementation (M2-T02)

The explicitly registered subfinder adapter supplies strict empty SubfinderInput,
operator-only binary/version detection and capability-specific execute. It rechecks
current registry/policy/scope/dedup/budgets, uses an isolated child environment and
fixed passive HackerTarget JSONL argv, and normalizes generic metadata observations
and untrusted evidence. Missing/nonzero/timeout/truncated/malformed outputs use shared
failures; empty discovery succeeds. No discovered name gains authorization or gets
contacted. Default registry remains empty. See [complete Subfinder contract](subfinder-adapter.md)
and [ADR 0009](decisions/0009-isolated-passive-subfinder.md). resolve_dns is already
implemented; DNS verification is implemented separately as verify_dns (M2-T03).

## Bulk verification contract (M2-T03)

verify_dns is an explicit separate active_safe capability selected through trusted
DnsxAdapter/ToolRegistry composition. Its strict candidates parameter is declared
as secondary targets; every entry is checked before the whole approved batch can
reach DNSX. An unauthorized entry rejects the batch before any input-file write.
Native resolve_dns and passive enumerate_subdomains keep their existing contracts.
One independently scoped numeric resolver, bounded sorted/deduplicated names, fixed
argv and isolated configuration use the existing runner/resources. Full RR entries
preserve owners/types/TTL; merged sections/wildcard ambiguity and incomplete output
are explicit. Partial Success carries status/errors; callers must preserve partial
lifecycle. No derived value grants authority. See [DNSX contract](dnsx-adapter.md)
and [ADR 0010](decisions/0010-scoped-bulk-dnsx.md).

## HTTP probing contract (M2-T04)

Explicit HttpxAdapter registration implements probe_http/active_safe through reviewed
HTTPX 1.9.0. Strict optional candidates declare all secondary targets; mixed batches
reject before input. Operator numeric resolver and finite contact IPs independently
pass scope and host budgets. Fixed GET/JSONL/no-fallback, concrete-IP allow enforcement,
no redirects and isolated configuration constrain contact before execution. Only
adapter-owned argv reaches the existing runner. Canonical failures/partial output
preserve limits; generic Endpoint/HTTP Observation/untrusted Evidence retain provenance.
Technology/redirect evidence grants no authorization or scanner selection. HTTPX probes;
Katana provides bounded numeric crawling (M3-T03); Feroxbuster supplies bounded recursive path discovery (M3-T04); FFUF remains future specialized fuzzing. See
[HTTPX contract](httpx-adapter.md) and [ADR 0011](decisions/0011-constrained-httpx-probing.md).

## Port discovery contract (M2-T05)

Explicit NaabuAdapter registration supplies discover_ports/active_safe. Strict optional
candidates declare all secondary targets; primary/members and operator-bound numeric
contacts independently pass current scope and share host budgets. Mixed batches reject
before input. Operator-only typed TCP ranges default to 80/443, at most 128 ports;
64 contacts/4,096 pairs bound work. Fixed isolated numeric CONNECT stream argv, one
connection per second/concurrent connect, existing deadline/capture/cancellation and
atomic budgets precede parsing. Generic Host/Service/Observation/Evidence record open
facts with partial errors/empty uncertainty, without deeper service metadata or new
authority. Naabu discovers ports; Nmap fingerprinting is M2-T06. See [contract](naabu-adapter.md).

## Service fingerprint contract (M2-T06)

fingerprint_services/active_safe registers explicit NmapAdapter with required strict
ports (1–128 integers, 1–65,535). Operator approved DiscoveredPortSelection snapshots
provide original numeric contact/optional hostname, prior ports and evidence references;
requested ports must be a subset. Empty/missing ports or absent selection deny. Current
policy, independent primary/contact scope and atomic budgets precede exact numeric argv.
Only Nmap 7.95 compiled without Lua passes detection; registration cannot bypass the
no-NSE gate. Native CONNECT/version intensity 2/XML profile owns every option and path.
No DNS/host discovery/OS/aggressive/NSE/broad scan. Safe XML, deterministic generic
services/observations/untrusted evidence, canonical errors and explicit unreported/empty
partial results use existing boundaries. Naabu discovers ports; Nmap fingerprints them.
See [complete contract](nmap-adapter.md) for exact profile, version and resource limits.

## Deterministic M2 integration (M2-T07)

M2 pipeline = deterministic integration proof.
M6/M7 = future AI planning/autonomous loop.

The bounded explicit DiscoveryWorkflow now coordinates only the six M2 capabilities
through current policy, real dedup admission, registry and shared adapter-owned budgets.
Each adapter accepts an optional trusted post-reservation/pre-contact `on_started`
notification; failed notification prevents contact and releases its charged permit.
No policy/dedup bypass or second reservation exists. Terminal state ingestion now
accepts related assets/hosts/services/endpoints atomically with observations/evidence;
unsuccessful results cannot ingest those subjects. Exactly tool_unavailable may be
recorded as a pre-start rejection without an invented execution ID. Existing lifecycle
edges and all other failure restrictions remain unchanged.

Nmap selection snapshots derive only from recorded completed/partial Naabu actions;
`with_selections` preserves the same detected installation and limits in a detached
adapter/registry snapshot. Contact scope is independently rechecked by adapters.
Discovered subdomains, IPs, redirects and CNAME/MX/NS hosts grant no authorization.
No M3 scanner, provider/planner, autonomous loop, persistence, reporting or real CLI.
Safe correlated AuditEvents and normalized output envelopes remain in memory, with
no implicit log or runtime startup. See [pipeline contract](deterministic-discovery.md)
and [ADR 0014](decisions/0014-deterministic-discovery.md) for branching, failure mapping,
atomic rollback and unchanged infrastructure/compatibility limitations.

## inspect_common_files implementation (M3-T01)

Native CommonFilesAdapter is explicitly registered for inspect_common_files/active_safe
with a strict empty input schema. Only the fixed robots.txt/sitemap.xml/security.txt
catalog is executable; bounded native HTTP via h11 contacts independently scoped
operator numeric bindings with original Host/TLS identity. Two fresh scope-checked
redirect hops may follow only the same catalog path; outside/arbitrary paths stay
evidence. Current registry/policy/dedup/shared budgets precede contact. No process
runner, DNS/proxy/auth, crawling or fuzzing. Remote bodies/directives/discovered URLs
are bounded untrusted Observation/Evidence data and grant no authority. Caller owns
lifecycle and atomic completed/partial state ingestion. The default registry and M2
pipeline remain unchanged. Common-file inspection = fixed safe metadata retrieval;
Katana = bounded numeric crawling (M3-T03); Feroxbuster = bounded recursive path discovery (M3-T04); FFUF = future specialized fuzzing.
See [full contract](common-file-inspector.md) and [ADR 0015](decisions/0015-fixed-native-common-files.md).

## inspect_tls implementation (M3-T02)

Explicit detected TlsxAdapter supplies inspect_tls/active_safe with strict candidates
and optional bounded port; trusted operator numeric bindings/port allowlist supply
contacts. Whole-batch independent scope, current policy/dedup and one shared budget
reservation precede isolated fixed Linux TLSX 1.4.0 argv. Native ctls, original scoped
SNI, no revocation/follow-up/enumeration/cloud/update and numeric input preserve the
contact boundary. Generic TLS Observations/Evidence retain untrusted certificate
metadata and partial/handshake limitations, without derived assets/Findings. Imports/
registry/CLI and M2 workflow remain inert/unchanged. See [contract](tlsx-adapter.md)
and [ADR 0016](decisions/0016-numeric-tlsx-inspection.md).

## crawl_web implementation (M3-T03)

KatanaAdapter uses detected Linux Katana 1.8.0 for single-page extraction, with a
bounded adapter-owned numeric same-origin GET graph. Empty strict planner input;
operator depth/page/discovery settings; fresh URL/address scope and shared budgets.
Redirects/forms/htmx/JS endpoints remain data. Hostname modes fail closed. Generic
Endpoint/Observation/Evidence retain provenance; caller owns state/lifecycle.
See [Katana contract](katana-adapter.md) and [ADR 0017](decisions/0017-single-page-katana.md).

## discover_content implementation (M3-T04)

FeroxbusterAdapter selects detected Linux Feroxbuster 2.13.1, numeric directory URLs,
strict empty planner parameters and operator-only small-v1 wordlist/finite bounds.
The adapter owns recursive directory admission; tool recursion/link extraction/redirects
are disabled. Every generated URL/IP rechecks before runner execution; global/binary
config presence fails closed. Generic endpoint/HTTP/untrusted evidence, deterministic
partial/errors and existing state/dedup/shared budgets apply. Katana crawls linked
content; Feroxbuster discovers paths; FFUF is future specialized fuzzing. See the
[Feroxbuster contract](feroxbuster-adapter.md) and [ADR 0018](decisions/0018-bounded-feroxbuster.md).

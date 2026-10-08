# Domain data model

M0-T04 implements 13 Pydantic v2 contracts under `recon_agent.domain`. They describe
operator declarations, normalized subjects, collected facts, traceable evidence,
action intent/outcomes, planner recommendations and session/state composition.
They perform no configuration, process, network, provider, database or report I/O.

```python
from datetime import UTC, datetime
from recon_agent.domain import ReconSession, Scope, Service, Target

target = Target(id="target-1", kind="domain", value="example.test")
session = ReconSession(
    id="session-1",
    targets=(target,),
    scope=Scope(id="scope-1", roots=(target,)),
    created_at=datetime(2026, 10, 5, tzinfo=UTC),
)
service = Service(
    id="service-1", asset_id="asset-1", host_id="host-1", port=443, transport="tcp"
)
snapshot = session.model_dump(mode="json")
```

These are data examples, not scan authorization or runnable sessions.

## Common contracts

- Unknown fields are forbidden throughout nested models. Structural fields use
  strict types; numeric strings and booleans do not become ports/priorities.
- IDs and references are caller-supplied non-blank opaque strings. There are no
  generated IDs or database row keys. Existing IDs survive Python/JSON round trips.
  Producers own uniqueness; M1-T08 semantic action identity is separate from and
  preserves these lineage references.
- Required text must contain a non-whitespace character. Strings are preserved,
  not stripped or rewritten. Target kinds label declarations without validating
  their domain/IP/CIDR/URL syntax; M1-T01 policy owns parsing/canonicalization and authorization; domain constructors still preserve declarations.
- Evidence/observation collection times, decision/result recording times and session
  creation time are required caller-supplied aware datetimes. Values normalize to
  UTC; JSON emits ISO 8601 values with `Z`. No clocks or randomness run on construction.
  Python inputs require datetimes; JSON inputs use datetime strings with an offset.
- `model_dump()` preserves Python datetimes/tuples; `model_dump(mode="json")` and
  `model_dump_json()` produce portable strings/arrays/objects. Both dump forms can
  be validated back into the corresponding model. Ordinary model equality compares
  data, not a canonical deduplication identity.
- Record attributes (including ReconState; excluding ReconSession) are frozen, and
  reference collections use tuples. Observation data and action parameters are
  ordinary nested JSON dictionaries/lists, not deeply immutable objects. Aggregate
  ReconState collections are now tuples with validated lineage/lifecycle history.
  ReconStateMachine owns defensive copies and controlled atomic transitions; detached
  nested JSON edits cannot alter managed state. ReconSession remains structural
  mutable composition. Nested instances are revalidated at model boundaries.
- Optional metadata defaults to `None`; no inferred product/version, authority or
  timestamps are manufactured. Provider credentials have no domain field. Flexible
  evidence text can still contain sensitive remote content; future collection and
  report/provider layers must bound/redact it.

## Implemented entities

| Model | Fields and relationships | Meaning and boundary |
| --- | --- | --- |
| Target | `id`, `kind`, `value`; kinds `domain`, `hostname`, `ip`, `cidr`, `url` | Operator-declared starting subject; presence does not confer authorization, resolve DNS or classify syntax |
| Scope | `id`, `roots`/`exclusions` tuples of Target, false-default `allow_subdomains`/`allow_private_ips`, optional `authorization_context` | Declaration snapshot only. Empty roots are valid data and grant nothing; the separate M1-T01 ScopeValidator implements exact semantics; see [scope model](scope-model.md) |
| Asset | `id`, `kind` (`host`/`web_resource`), `value`, `observation_ids` | The discovered subject, independent of scanner identity; no raw stdout or computed scope/actionability flag |
| Host | `id`, `asset_id`, `value`, reported `addresses`, `observation_ids` | Network-host detail associated with an Asset; addresses are supplied text, not DNS results obtained by construction or IP authorization |
| Service | `id`, `asset_id`, `host_id`, `port`, `transport`, optional `protocol`/`product`/`version`, `observation_ids` | Observed network metadata. Port is a strict integer 1–65535; transport is `tcp`/`udp`; product/version never imply a vulnerability |
| Endpoint | `id`, `asset_id`, preserved `url`, `method` (default `GET`), optional `service_id`, `observation_ids` | URL/method identity data. Method must be a non-empty HTTP token and is preserved, including case/extension methods; URL text is not parsed, canonicalized, fetched or crawled |
| Evidence | `id`, `source`, `origin`, `artifact_reference`, `collected_at`, optional `execution_id`/`capability`/`locator`/`sha256`, `trust`, `truncated`/`redacted` flags | Traceable reference to source material. Trust is always `untrusted`; optional digest is 64 lowercase hexadecimal characters. No raw-output blob, artifact reads/writes, integrity verification or retention engine |
| Observation | `id`, `kind`, `asset_id`, `source`, `data`, `observed_at`, non-empty `evidence_ids`, optional `execution_id` | A collected/tool-reported fact with provenance. Kinds: `dns`, `service`, `http`, `tls`, `endpoint`, `metadata`; no interpreted Finding |
| ActionRequest | `id`, `capability`, `target`, `parameters`, `reason`, integer `priority` (default 0), optional `asset_id`/`decision_id` | Unapproved capability intent, never argv. Capability name has lowercase identifier shape; M1-T04 registry checks membership; priority bounds remain later validation work |
| ActionResult | `id`, `action_id`, terminal `status`, `recorded_at`, `observations`, `evidence`, `execution_ids`, optional structured `error` (shared ErrorInfo) | Outcome data, not process execution. Status is `completed`, `partial`, `rejected`, `failed`, `cancelled` or `timeout`; M0-T05 aligns outcomes with shared failure information |
| PlannerDecision | `id`, `analysis_summary`, `actions`, `finished`, `created_at`, optional `provider`/`model`, `input_observation_ids`/`input_evidence_ids` | Untrusted recommendation with input lineage. Provider metadata is text only; no Groq SDK, prompts, policy outcomes or authorization |
| ReconState | Frozen tuples of subjects, observations/evidence, requests/results, decisions, action lifecycles and budget snapshots | Empty by default; whole-state lineage/lifecycle validation. ReconStateMachine owns explicit atomic transitions and detached copies |
| ReconSession | `id`, non-empty `targets`, explicit `scope`, default empty `state`, `status`, `created_at`, optional `stop_reason` | Session composition only. Default status `created`; other structural statuses `running`, `completed`, `failed`, `cancelled`; no lifecycle enforcement, persistence, resume or execution |

## Provenance and relationships

A session owns starting targets, a scope declaration snapshot and aggregate state.
Assets represent subjects; hosts reference assets, services reference assets/hosts,
and endpoints reference assets and optionally services. Subject records may cite
supporting observation IDs. Observations require a source and at least one evidence
ID; evidence requires source/origin and an opaque artifact reference, optionally
with an execution ID, capability and record/line locator. Reference strings are
never opened or resolved by these models.

Action requests may cite an asset and source decision. Results cite an action,
may carry observations/evidence, and preserve opaque execution references.
Decisions cite the selected input observations/evidence. Individual record models
check structural shape; M1-T07's whole ReconState boundary checks in-memory reference
existence, ownership and identity uniqueness. Database/resume integrity remains
future storage work. No missing provenance is inferred.

## JSON payloads and action safety

Observation `data` and ActionRequest `parameters` use Pydantic `JsonValue` mappings
with non-blank top-level string keys: null, boolean, integer, finite float, string, arrays
and nested objects only. Arbitrary Python objects, bytes, datetimes and non-finite
numbers fail validation. No scanner-specific result hierarchy or unrestricted
`Any` payload is introduced.

ActionRequest has no command, shell, script or raw-argument field. Its parameter
schema also rejects these reserved executable keys, case-insensitively at any
nested object/list level: `command`, `shell_command`, `raw_command`,
`command_template`, `script`, `bash`, `raw_args`, `argv`, `extra_shell_args`,
`executable`, `executable_path`, `import_path`, `python_module`.

This is structural defense, not a capability policy validator. Other parameter
names/values remain unapproved JSON data. M1-T04 registry checks capability existence
only. M1-T05 validates registered parameter schemas, target scope and risk; future
dispatch/adapters must revalidate and enforce limits before constructing fixed argv. No string is evaluated or dispatched by the domain layer.
Remote instruction-like text in observations remains evidence; planner reasons and
summaries remain recommendations. Neither can redefine scope or create authority.
M6-T04 still owns priority bounds and planner validation semantics.

## Outcome and interpretation distinctions

Observation means a collected/tool-reported fact. Finding means an interpreted
security-relevant conclusion and is staged. For example, TCP 445 being open is a
service observation; any conclusion about exposure needs a future Finding and
supporting lineage. Normalization does not turn product/version metadata into
vulnerability claims or planner analysis into observations.

M0-T05 replaces ActionResult's temporary failure_reason with shared ErrorInfo.
A completed result forbids errors; all non-completed results require one.
Rejections require policy/planner errors or exactly tool_unavailable (M2-T07),
timeout requires tool_timeout and
cancellation requires cancelled. Failed/partial results cannot relabel a
policy/planner rejection or cancellation. Only completed/partial results may
carry observations; rejected/failed/cancelled/timeout results can preserve evidence
but cannot claim successful observations. A partial result's error explicitly
explains its limitation. These are structural outcome rules, not authorization,
retry or state transitions.

ErrorInfo is a pure shared primitive from core/errors; it imports no configuration,
domain or operational subsystem. Domain actions depend only on this primitive in
addition to domain/Pydantic types. Generic OperationResult[T] describes an operation
with success/failure, whereas ActionResult additionally records action identity,
terminal/partial status and evidence lineage. See [error/result contracts](error-model.md)
for codes, context, serialization and exception/result usage.

## Explicitly staged contracts and behavior

PLAN permits associated Action/ToolExecution/Finding models to be staged. M0-T04
established the 13 required models; M1-T07 extends the public exports with state,
lifecycle and budget records; M3-T06 adds web identity/projection records. The following ownership boundaries remain:

- **Action:** ActionRequest/ActionResult plus M1-T07 ActionLifecycle/ActionTransition
  supply intent, history and outcomes. No generic Action placeholder exists;
  M1-T08 adds separate ActionIdentity/ActionDedupDecision contracts and policy
  equivalence.
- **ToolExecution:** runner/adapter execution metadata belongs with M1-T03 and later
  adapter work. Current execution IDs are opaque provenance references only.
- **Finding:** interpreted conclusion records belong with M5-T04 finding
  normalization. ReconState deliberately has no untyped findings placeholder.
- **Session configuration/budgets, broader action policy outcomes, full finding deduplication, retention and
  stop/resume rules:** extended by their owning policy/orchestration/storage tasks;
  no generic executable configuration or operational startup exists here.

Scope data is distinct from ScopeValidator. ReconState is managed by the explicit ReconStateMachine transition owner. ReconSession is distinct from persistence. PlannerDecision is
non-authoritative recommendation data. None of these contracts implement scope
matching, process runners, registry/policy, scanners, Groq/provider communication,
AI reasoning, autonomous loops, SQLite, reporting or real CLI commands.

Run focused offline validation with
`.venv/bin/python -m pytest tests/unit/test_domain.py`, then the complete baseline
in [testing strategy](testing-strategy.md).

## Operational audit boundary

M0-T06 adds pure AuditEvent data under core/audit.py and an explicit local sink
outside domain. Application/orchestration producers will record event/session,
action, execution, decision and asset IDs plus bounded summaries/ErrorInfo. Subject,
observation and finding event types are forward contracts, not producers or new
Finding/ToolExecution entities. No domain constructor logs, and diagnostic copying
never mutates collected evidence. Events record decisions without authority or
execution/replay methods. See [logging and audit](logging-and-audit.md).

## Scope policy integration

M1-T01 implements a separate pure ScopeValidator; Target/Scope fields and constructors
are unchanged. It returns existing OperationResult with canonical Target/matched-root
data or shared ErrorInfo, and raises ScopeRejectedError at the require boundary.
Declaration IDs are preserved; source declarations are never rewritten. Host/CIDR
canonicalization here is comparison policy, not asset identity/deduplication. See
[scope semantics](scope-model.md) for exclusions, options and derived-address limits.

## Internal process facts (M1-T03)

The execution layer now defines ProcessSpec and ProcessExecution separately from
pure domain data. ProcessSpec is trusted adapter-owned executable/literal argv and
optional timeout; it is not ActionRequest or planner data. ProcessExecution carries
bounded raw stdout/stderr bytes, truncation flags, observed return code, argument
count, aware UTC timing and monotonic duration. It has no argv/executable metadata;
JSON preserves bytes through URL-safe base64. Existing OperationResult handles
normal exit versus canonical launch/capture/timeout Failure; non-zero exit remains
an observed process outcome. Timeout/cancellation partial output is not returned.
Future adapters normalize those facts into domain observations/ActionResult;
ToolExecution remains staged. See [execution model](execution-model.md).

## Capability metadata (M1-T04)

`domain/capabilities.py` adds finite CapabilityId and RiskClass string enums plus
strict frozen CapabilityDescriptor (capability, bounded semantic description,
risk_class). These are pure data, separate from the original 13 entity exports.
Conceptual enum membership does not claim scanner support or authorize actions.
ActionRequest/Evidence capability names retain structural string semantics for
unapproved intent/provenance; the internal registry resolves ActionRequest names
against the finite enum and rejects unknown values. It adds no adapter identity,
executable or argv to ActionRequest/PlannerDecision. Tool-specific typed input/output
schema references live in trusted AdapterDefinition, never planner data; see
[tool contracts](tool-contracts.md). No action-policy validation is implemented here.

## Action policy result (M1-T05)

ActionRequest and PlannerDecision wire fields remain unchanged. Policy now returns
shared Success[ApprovedAction]/Failure: ApprovedAction is an internal policy record
with action_id, finite capability, primary/secondary ScopeMatch records and a typed
parameter model excluded from dumps/repr. It is not a new domain ActionResult,
a persisted permission or a dispatch token. The original request must be revalidated
at future dispatch. See [policy contract](tool-contracts.md#action-policy-contract-m1-t05).

## Internal budget records (M1-T06)

policy/ now supplies frozen ExecutionBudget limits and detached frozen BudgetState
snapshots with attempted-action, active-concurrency, reserved-output, remaining-time,
canonical-host, capability-window and typed completion-outcome counts. These are
internal session-local resource records, separate from planner/action wire models.
M1-T07 records detached BudgetSnapshot samples in ReconState; enforcement remains
owned by BudgetController. BudgetPermit is opaque live resource ownership, never
a replay/serialization token. Existing Success/Failure/ErrorInfo carry checks and
reservations. M1-T06 added no state transition or persistent history; M1-T07 adds
only the in-memory recording boundary described below.
See [budget semantics](execution-budgets.md).

## Controlled state integration (M1-T07)

ReconState = authoritative in-memory session state, owned by ReconStateMachine.
PlannerDecision = recommendation record; ActionPolicyValidator = authorization;
budget layer = resource enforcement; ExecutionRunner = process execution.
The domain owner performs only explicit validated recording, including related fact
batches, action lifecycle history, terminal results and caller-sampled budgets.

ActionLifecycle/ActionTransition/ActionPhase add requested → approved → started
and the existing terminal outcome statuses. Policy references and execution IDs
record caller-supplied history, never authority/replay tokens. All terminal re-entry
rejects. StateTransitionError extends the existing Failure/ErrorInfo system with
one code/category, without a parallel hierarchy. Full initial/deserialized/live
snapshots enforce lineage and known unsuccessful-action observation protection.

BudgetState/ReservationOutcome move to pure domain contracts, preserving policy
re-exports; no enforcement arithmetic moves. BudgetSnapshot adds id/time to sampled
facts, separate from immutable configured limits. The owner cannot reset/consume
budgets, modify scope, run tools or turn planner text into facts. Python list-based
legacy snapshots require explicit tuple/lifecycle conversion; no history is inferred.
See [complete operations, lifecycle and ownership](state-transitions.md) and
[ADR 0006](decisions/0006-controlled-recon-state.md).

## Semantic action identity (M1-T08)

ActionIdentity adds a versioned capability/canonical target/parameter JSON record
and deterministic full JSON key. ActionDedupDecision adds identity, sorted matching
request IDs, failed_attempts and DedupReason; duplicate/eligible are computed normal
policy outcomes inside existing Success/Failure. These pure contracts do not own
history, authorize, consume budgets or execute. Planner prose/priority/IDs/times
are excluded; registered defaults and nested execution parameters are included.
Identity has portable Python/JSON round trips independent of opaque lineage IDs.
See [canonical semantics and conservative retries](action-deduplication.md).

## DNS normalization (M2-T01)

Operational DNS uses internal strict tools.dns_models query/record/context/output
schemas, preserving existing pure domain contracts. The queried Asset owns kind=dns
Observations; each carries canonical original query_target, query_type, outcome,
record owner/type/value/TTL, optional MX preference and exact TXT chunk hex.
Negative answers produce status observations. Evidence is untrusted with native_dns
source, resolve_dns capability, explicit caller time/execution identity and a memory
reference/hash to the returned normalized query snapshot, never a raw packet file.
Discovered names/addresses are data only; no new Scope or actionable flag is inferred.
Sorting/deduplication makes identical facts/context deterministic. Caller owns coherent
state lifecycle/ingestion and retention. See [full DNS contract](dns-resolver.md).

## Passive subdomain observations (M2-T02)

Internal tools.subfinder_models defines empty strict input, caller context, reviewed
JSONL fields and SubdomainOutput. No top-level domain/entity/Observation.kind changes.
The root Asset owns kind=metadata/source=subfinder observations with hostname,
query_target, status=discovered, enumerate_subdomains capability, source_version
and provider_sources. Generic Evidence is untrusted and references the returned
normalized discovery snapshot by memory reference/locator/SHA-256. Empty discovery
returns evidence with no observations. Sorted/deduplicated hosts grant no scope,
DNS verification or contact authority. See [normalization/provenance](subfinder-adapter.md).

## Bulk DNSX projections (M2-T03)

DnsxInput/Context/Query/Output are tools-local schemas, not scanner-specific domain
entities. verify_dns returns the existing primary Asset and generic DNS Observations
with per-query names, actual RR owners, supported typed values/TTL/MX preference/TXT
hex, status, resolver, source/version/capability and explicit section/wildcard ambiguity.
Evidence retains subject/time/execution/memory snapshot/hash/untrusted provenance.
Partial status, canonical errors, malformed counts and unreported candidates remain
explicit; missing output never creates NXDOMAIN or authorized assets. Caller-owned
ActionResult/lifecycle must preserve partial outcomes. See [DNSX](dnsx-adapter.md).

## HTTPX projections (M2-T04)

Existing Endpoint, Observation(kind=http), Evidence and primary Asset carry HTTP
probing data. The internal HttpProbeOutput envelope adds status/error/counts and
unreported URLs without a new HttpxResult domain entity. Each endpoint references
its HTTP observation and primary asset; observations reference untrusted evidence
with httpx/probe_http/version and caller execution/time lineage. Reported URL equals
the contacted final URL because redirects are disabled. Optional title/server/type/
length and sorted technology hints stay absent when unavailable. Relative/absolute
redirect destinations remain evidence with scope status and authorization=false;
they never become endpoints/assets/permissions automatically. Missing/malformed
records explicitly produce partial output; bounded bodies limit metadata completeness.
See [HTTPX contract](httpx-adapter.md) for snapshot/hash, field and conflict semantics.

## Open TCP port projections (M2-T05)

PortDiscoveryOutput is a tools-local envelope using existing Asset, numeric Host,
Service(transport=tcp), service Observation and untrusted Evidence. Each service links
its host/observation and primary asset; each observation links execution/time/evidence
and preserves numeric host/port/state=open, naabu/discover_ports/version and operator
candidate references. Binding references do not prove DNS. Protocol/product/version
remain absent. Empty results imply no closed-port/liveness/completeness fact. Snapshot
hash and partial parse errors preserve limits. Generic state lineage accepts the facts.
See [Naabu normalization](naabu-adapter.md).

## Service fingerprint projections (M2-T06)

Nmap reuses Asset/numeric Host/Service/service Observation/Evidence; no domain changes.
Only explicitly open TCP records become Services, with Nmap name in protocol and
optional product/version. Observations preserve host/port/transport/state, name/product/
version/extra_info/service_fingerprint/tunnel/method/confidence/CPEs and nmap/fingerprint_services/7.95,
logical subject and prior-discovery references. Closed/filtered/other states remain
observations. Missing metadata stays absent; names, CPEs and versions imply no finding.
Each observation cites its own untrusted Nmap evidence; discovery IDs are metadata,
not automatic permissions or dangling state evidence links. Snapshot SHA-256, explicit
caller IDs/time, memory locator and generic referential validation preserve lineage.
Missing individual records/empty output yield explicit partial unreported_ports; malformed
XML fails atomically. See [contract](nmap-adapter.md) for supported projections.

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

## Common-file normalized evidence (M3-T01)

No new domain result/state entity is added. Internal CommonFilesOutput/CommonFileFact
models project fixed-file HTTP outcomes, bounded base64/text prefixes, selected
directives/security fields, discovered URL strings, redirects and canonical errors
into existing web_resource Asset/HTTP Observation/untrusted Evidence. Caller supplies
UTC/execution/asset identity; source native_common_files/capability inspect_common_files,
locator/memory reference and fact SHA-256 preserve provenance. 404/403 stay observed
HTTP facts. Timeout/connection errors have no invented status. Rejected redirect
policy details are evidence; collection errors use parse_failed for valid partial
ActionResult ingestion. Discovered URLs create no new executable subject/permission.
Whole-action failures have no partial payload under the existing Result contract.
See [normalization contract](common-file-inspector.md).

## TLS/certificate normalized evidence (M3-T02)

TlsInspectionOutput is an internal adapter envelope, not a new domain model. It
projects original scoped host/address/port and selected protocol/certificate metadata
into generic TLS Observations on one caller-owned host Asset and untrusted Evidence.
Source tlsx/capability inspect_tls/version, caller UTC/subject/execution, evidence IDs,
memory locator and fact SHA-256 preserve provenance. CN/SANs/organization strings
stay plain discoveries; no derived asset or Finding is created. Validity, malformed/
unreported fields and handshake failures have explicit partial limits/canonical
ErrorInfo. Existing ActionResult and ReconState ingestion/dedup remain unchanged.
See [contract](tlsx-adapter.md) for supported fields and source limitations.

## Crawl projections (M3-T03)

CrawlOutput is an internal envelope of generic web_resource Asset, Endpoint, HTTP
Observation and untrusted Evidence. URL/method/source page/path/query/tag/type/form
metadata preserve Katana/version/execution/time/subject/snapshot provenance.
Contacted and discovered endpoints are explicit separate facts; neither grants
authority. No new domain schema or Finding. See [contract](katana-adapter.md).

## Content discovery projection (M3-T04)

ContentDiscoveryOutput uses existing Asset/Endpoint/HTTP Observation/untrusted Evidence
with URL/path/GET/status/tool length/Location/body prefix completeness/source endpoint.
Catalog ID/hash, request upper bound, scanned directories, unreported planned URLs and
partial limitations describe finite collection. No new domain entity/Finding/action or
redirect Endpoint is inferred. Source/version/capability/caller UTC/subject/execution/
memory snapshot SHA-256 retain lineage; discoveries grant no authorization.
See [Feroxbuster normalization](feroxbuster-adapter.md).

## Specialized FFUF facts (M3-T05)

No domain schema change. FuzzDiscoveryOutput contains generic web_resource Asset,
HEAD Endpoint at the numeric contact, HTTP Observations and untrusted Evidence.
Facts retain candidate_value, profile, URL/path, status, tool-reported HEAD content
length/type and Location/redirect membership, with false authorization fields.
HEAD words/lines are omitted as meaningless body counts. Candidate hostnames never
create contacted hostname subjects. Evidence keeps caller time/execution/subject,
capability/tool/version, memory snapshot/catalog hashes; partial/unreported/error
status survives atomic state ingestion. See [FFUF contract](ffuf-adapter.md).

## Canonical web contact data (M3-T06)

`WebAssetIdentity` is a frozen web-v1 URL/method/optional explicit Host-variant
record with full canonical JSON key. `WebAssetDiscovery` holds that identity plus
sorted endpoint/observation/evidence/reported-contact observation references.
`Endpoint.web_identity` and `ReconState.web_assets`/`find_web_asset` derive these
without rewriting stored URLs, source facts or evidence. Unsupported candidates
fail lookup closed. They are ordinary properties, absent from raw state dumps;
projections rebuild deterministically after Python/JSON reconstruction. Asset seed
labels are not substituted for actual endpoint identities. Exact URL/method/query/
encoding/contact semantics: [web identity](web-identity.md).

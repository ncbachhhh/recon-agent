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
  generated IDs, database row keys, scanner-derived identity rules or deduplication
  algorithms. Existing IDs survive Python/JSON round trips. Producers own uniqueness;
  later canonicalization/deduplication work must preserve these lineage references.
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
- Record attributes (all models except ReconState/ReconSession) are frozen, and
  reference collections use tuples. Observation data and action parameters are
  ordinary nested JSON dictionaries/lists, not deeply immutable objects. Aggregate
  containers are mutable with independent default factories and validated field
  assignment. In-place list/dict edits are not validation or approved transitions;
  nested instances are revalidated at model-construction boundaries. M1-T07 owns
  controlled mutation and concurrency semantics. Revalidate snapshots before use.
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
| ReconState | Independent lists of assets, hosts, services, endpoints, observations, evidence, action requests/results and planner decisions | Empty by default. Typed snapshot containers only; no apply/dedup/transition/budget/stop methods |
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
Decisions cite the selected input observations/evidence. The model layer checks
reference shape, not existence in a database or consistency across an entire
partial snapshot. Future ingestion/state/storage layers must keep links resolvable
and enforce ownership/uniqueness; M0-T04 does not infer missing provenance.

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
Rejections require policy/planner errors, timeout requires tool_timeout and
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
implements the 13 required models and exports only those models from the public
package; the following are absent, with ownership made explicit:

- **Action:** lifecycle/policy record and canonical action identity belong with
  M1-T07 state transitions / M1-T08 deduplication. ActionRequest/ActionResult supply
  the present intent/outcome data; no Action placeholder or transition API exists.
- **ToolExecution:** runner/adapter execution metadata belongs with M1-T03 and later
  adapter work. Current execution IDs are opaque provenance references only.
- **Finding:** interpreted conclusion records belong with M5-T04 finding
  normalization. ReconState deliberately has no untyped findings placeholder.
- **Session configuration/budgets, broader action policy outcomes, asset/action canonicalization, retention and
  stop/resume rules:** extended by their owning policy/orchestration/storage tasks;
  no generic executable configuration or budget/state-machine implementation here.

Scope data is distinct from ScopeValidator. ReconState data is distinct from a
state machine. ReconSession is distinct from persistence. PlannerDecision is
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

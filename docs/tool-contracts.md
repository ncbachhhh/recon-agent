# Capability and tool contracts

M1-T04 implements finite semantic metadata in `domain/capabilities.py` and explicit,
immutable registry composition in `tools/`. No production scanner adapters exist.
The default `ToolRegistry()` is empty; importing `recon_agent.tools` registers nothing.

## Capability, adapter and execution details

A **Capability** is the semantic operation the planner may request. `CapabilityId`
is a finite string enum: resolve_dns, enumerate_subdomains, discover_ports,
fingerprint_services, probe_http, inspect_tls, crawl_web, discover_content,
inspect_protocol and scan_templates. These conceptual identities do not imply
working integrations. There is no run_command, execute_shell or arbitrary binary
capability. Extending the catalog requires reviewed application code.

A **Tool** is an external program or other implementation mechanism. A
**ToolAdapter** is trusted application code implementing a capability; its stable
adapter ID is distinct from capability identity and executable path. A
**ToolRegistry** is a deterministic mapping/catalog of those explicitly supplied
trusted instances. A **ProcessSpec** is internal executable/literal argument data
constructed by future adapters for the M1-T03 runner. None of these is a shell
command or planner-supplied execution instruction.

```text
Planner selects capability                 [future runtime]
  → deterministic action policy            [M1-T05, implemented local eligibility]
  → ToolRegistry selects trusted adapter    [implemented foundation]
  → ToolAdapter validates/prepares execution [interface; implementations future]
  → ProcessSpec → AsyncProcessRunner        [M1-T03, implemented]
  → external tool → normalized observations [future adapters]
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
separately. Scanner-specific models remain future adapter work.

`ToolAdapter` is a minimal abstract base class with a read-only `definition`
property. This task adds no execute, parse or binary-probing methods. Future adapter
tasks will add capability-specific validated input, non-scanning availability checks,
trusted argv construction, injected ProcessRunner execution and normalized outputs.

Planner parameters must flow through capability-specific typed validation to a
trusted adapter. No dictionary-to-flags translation or argv pass-through is allowed.
Schema classes, adapter instances and implementations never come from planner JSON,
remote content, arbitrary config imports or deserialized requests. Tool paths, if
later supported, are trusted operator configuration and cannot appear in planner
contracts. Current ToolsConfig has only enabled; it is not consumed by the registry
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
changes. No scanner adapter, resolver, redirect follower or dispatch integration
exists yet.

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
M1-T04 now supplies the upstream interface/registry described above; no scanner
implementation or dispatch exists.

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
ToolRegistry / trusted Adapter / Runner [dispatch and adapters future]
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

Two injected ActionEligibility.check(ActionRequest) services return OperationResult[None]
for budget and completed-action eligibility. Missing services deny; allowing fakes
exist only in offline tests. Returned malformed outcomes also reject. This adds no
budget accounting, reservations, clock/rate checks or deduplication logic. M1-T06 and
M1-T08 own those implementations. No production permitting stub exists.

Future dispatch must revalidate the original request against current scope, registry,
parameters, risk and eligibility; atomically reserve budgets and enforce deduplication.
An old approval, modified parameter model or deserialized record cannot skip checks.
Adapters must independently check newly introduced redirect/discovery/DNS destinations
and constrain actual contact. Policy validation is synchronous local checking only:
no registry mutation, adapter execution, binary selection, runner, network/DNS, Groq,
audit emission or tool.execution_started event.

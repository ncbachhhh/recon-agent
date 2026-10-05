# Pure action eligibility and explicit target semantics

ADR 0004 — Action policy boundary

## Status

Accepted

## Date

2026-10-05

## Context

M1-T05 composes registry, scope, parameters and risk. PLAN additionally requires
restrictive budget/completed-action interfaces before their implementations in
M1-T06/M1-T08. Existing configuration has no risk/capability allowlists and registry
input schemas have no secondary-target semantics. ActionRequest.target is text.

## Decision

Inject a frozen ActionPolicyConfig with finite capability/risk allowlists (empty
by default), ScopeValidator and ToolRegistry explicitly. Do not extend the global
configuration loader or infer permission from ToolsConfig.enabled.

Add registry capability_definition lookup over the available metadata snapshot;
policy never resolves/accesses adapter instances. AdapterDefinition's trusted
parameter_target_fields names every secondary network-target input field. None
(default) means semantics unestablished and policy rejects. An explicit empty tuple
asserts no secondary targets. Nonempty declarations refer to unique schema fields
whose validated values must be strings or lists/tuples of strings. Nested/other
representations are unsupported and reject; future schema owners must declare
all target inputs or choose a reviewed extension in their own tasks.

ScopeValidator.validate_value classifies ActionRequest/parameter text into existing
Target kinds using syntax delimiters, then reuses the existing parser/membership
logic. No DNS, parsing fallback, inferred scope grant or target-less action exemption
exists. The current ActionRequest always requires a primary network target.

Return existing Success[ApprovedAction]/Failure/ErrorInfo. Approval includes the
request ID, capability, scope matches and an internal typed parameter model excluded
from dumps. No new result/error hierarchy or audit producer. Invalid recommendation,
risk/capability denial and unsupported semantics use planner_validation_failed;
scope/tool/budget checks preserve their existing canonical failures.

Budget and completed_action eligibility use a shared small local check protocol.
Missing services deny. Permitting services appear only in tests. No counters,
reservations, clock, canonical action identity, retry/dedup history or dispatch
implementation is added. Future dispatch must revalidate the original request
against current facts, atomically reserve resources and constrain contact.

## Alternatives Considered

- Implicit risk defaults or global config reads: permission becomes hidden state.
- Guess target parameters by key/text shape: misses encoded/nested destinations or
  misclassifies non-target strings; use trusted explicit schema semantics instead.
- Default undeclared target fields to no targets: missing policy data could allow
  secondary contact; explicit empty declaration is required.
- Implement budgets/dedup now or use permissive production stubs: violates owning
  task boundaries or allows unavailable policy state; restrictive placeholders win.
- Treat approval as a permanent token: ignores changed scope/resources/request data.

## Consequences

Available registered capabilities still reject until explicitly allowed and fully
specified, including real future eligibility services. No production operational
approval path exists today. Schema validators and injected checks are trusted local
application code, required to be pure; this boundary is not a sandbox for malicious
application code. Parameter models may contain mutable data, so approval cannot be
replayed, mutated or deserialized to skip policy at dispatch.

## Security Impact

Planner reason/priority/analysis grants no authority. Scope membership alone and
registration alone grant no complete action authorization. Validation performs no
execution, dynamic loading, network/DNS/provider calls or logging. All declared
secondary targets and defaults are independently scope-checked before eligibility.

## Testing Impact

Offline permitting/denying eligibility fakes, schema fixtures, unknown/unavailable
capabilities, malformed/outside/secondary targets, parameter injection, missing
policy facts, metadata changes and stale-approval rechecks with untouched mock dispatch.

## Follow-up

M1-T06 implements budgets/rates/reservations; M1-T08 implements deduplication.
Scanner and orchestration tasks enforce current-policy dispatch and contact
containment. None is started here. See [tool contracts](../tool-contracts.md).


M1-T06 update: BudgetEligibility now accepts normalized ApprovedAction so resource
accounting includes all validated secondary targets/defaults without duplicating
scope/schema logic. Completed-action eligibility remains ActionRequest-based and
default deny. See [ADR 0005](0005-budget-reservations.md) for reservation/counting
semantics; original M1-T05 choices above describe that task's initial boundary.

# Explicit immutable capability registry with one selected adapter

ADR 0003 — Capability registry composition

## Status

Accepted

## Date

2026-10-05

## Context

M1-T04 needs deterministic trusted resolution, schemas, risk and availability facts
without scanners or planner execution access. Existing design distinguishes semantic
capabilities from tools but leaves registry cardinality/composition undecided.

## Decision

Use finite CapabilityId identities, strict planner-safe descriptors and explicit
immutable ToolRegistry construction from trusted adapter instances. Select one
adapter per capability in a registry; reject duplicate adapter IDs and conflicting
capability ownership. Snapshot metadata and declared availability without probing.
Separate internal schema classes/adapter definitions from semantic catalog projection.
Default availability is not_checked and resolution fails closed until available.

## Alternatives Considered

- Multiple adapters per capability with priority/fallback selection: requires policy
  not assigned here; trusted composition can select alternatives in future tasks.
- Mutable registration/freezing: adds lifecycle states unnecessary for explicit
  constructor input. Import-time globals/plugin discovery make state implicit.
- Serialize adapter model/schema wholesale to planner: exposes implementation details
  and arbitrary schema metadata; explicit semantic projection has a smaller boundary.

## Consequences

Simple deterministic offline lookup and immutable public tuples. Catalog membership,
registration, enablement, runtime availability and authorization remain distinct.
No availability probe/execution/parser methods are defined until actual adapters
need them. Trusted adapter code must keep definitions stable; schema classes and
instances are application code, not a sandbox against deliberate trusted mutation.

## Security Impact

Planner selects capabilities, never implementation imports/executable details or
registrations. Unknown capability has canonical rejection; missing/unavailable
implementation fails without fallback. Metadata grants no scope/risk/budget authority.

## Testing Impact

Fake adapters only: conflicts, unknown/unavailable outcomes, schemas, permutation
ordering, immutability, safe serialization and side-effect guards; full baseline.

## Follow-up

M1-T05 consumes registry facts for authorization; M1-T06 owns budgets. M2 and later
adapter tasks supply concrete schemas, availability checks and runner/parser behavior.
No future task is started here. See [tool contracts](../tool-contracts.md) and
[PLAN](../../PLAN.md).

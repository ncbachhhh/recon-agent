# Bounded deterministic M2 integration with adapter-owned reservations

ADR 0014 — Deterministic discovery lifecycle and state composition

## Status

Accepted

## Date

2026-10-06

## Context

M2-T07 must integrate six existing capability-specific adapters without duplicating
policy, scope, budgets, dedup or execution. Adapters reserve their own resources and
revalidate policy. Marking STARTED before calling execute violates real dedup's
pending-only self-exclusion; reserving centrally would double-charge. Existing
terminal state ingestion cannot atomically add referenced assets/hosts/endpoints.
ActionResult forbids unavailable-tool rejection before STARTED. Nmap immutable
prior-discovery settings need a state-derived snapshot after Naabu succeeds.

## Decision

Use one finite explicit sequential library workflow, five initial actions followed
by at most 64 numeric service actions. Preserve operator infrastructure/contact
settings, existing schemas/profiles and independent centralized authorization.
No discovery grants permission; no provider/planner/retry/autonomous loop exists.

Add an optional trusted post-reservation/pre-contact callback to each M2 adapter.
Record STARTED only there; fail closed before contact on callback failure. Extend
existing terminal state ingestion with optional subject batches in the same atomic
commit. Permit exactly tool_unavailable as a pre-start rejection reason, retaining
all other lifecycle edges and failure restrictions. Post-start policy abort uses
existing cancellation, with original denial in audit/returned Failure.

Derive Nmap selections only from completed/partial Naabu action observations for
the original root. Clone the same detected trusted installation with those immutable
selections and explicitly compose a new registry snapshot; keep the shared budget
ledger/history and unchanged capability schemas. Retain normalized output envelopes
and safe AuditEvents in a detached in-memory report. No storage/log startup.

## Alternatives Considered

- Generic dispatch/base adapter redesign: larger API than six known M2 branches need.
- Bypass dedup on started requests or double-reserve: weakens established invariants.
- Stage lifecycle in another hidden state owner: observers miss actual active work.
- Insert subjects before result: cannot validate unfinished observations atomically.
- Invent a started execution for unavailable tools: false lifecycle evidence.
- Mutate Nmap settings/registry, or redetect every discovered address: breaks immutable
  composition or creates unnecessary executions outside the session budget.
- Treat DNS answers as bindings or gate ports on HTTP success: confuses evidence,
  authority and independent discovery stages.

## Consequences

Narrow existing-contract extensions are necessary for integration; profiles,
parsers, policy, resource arithmetic and process runner stay unchanged. Workflow is
single-owner, bounded, offline-testable and deliberately conservative. No rate waiting
or retries. Tool failure can coexist with workflow completion; fatal policy/resource/
state errors leave inspectable state and stop. Existing scanner compatibility and
infrastructure/OS/process-tree limits remain unchanged.

## Security Impact

All contact checks remain inside approved adapters. Every selected action also uses
current policy, real dedup admission and one shared charged reservation. Raw discoveries,
remote text, audit events and selection evidence grant no execution authorization.

## Testing Impact

Actual adapters with fake DNS/process outcomes exercise full state/lifecycle/evidence,
independent contact scope, duplicates, rate/budget exhaustion, unavailable tools,
timeouts/parse/partial/empty outcomes, atomic rollback and cancellation. Full baseline,
network/DNS-blocked and guarded installed-wheel tests remain required.

## Follow-up

M3-T01 becomes READY only on successful closeout and remains unstarted. M6/M7 own
future AI planning/autonomous loops. See [pipeline contract](../deterministic-discovery.md).

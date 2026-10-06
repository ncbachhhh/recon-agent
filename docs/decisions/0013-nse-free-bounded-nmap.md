# NSE-free Nmap with trusted discovered port selections

ADR 0013 — Nmap native service detection containment

## Status

Accepted

## Date

2026-10-06

## Context

M2-T06 must fingerprint already discovered approved services without NSE, OS detection,
arbitrary flags or broad scanning. ADR 0002 requires concrete-address authorization.
Source review of Nmap 7.95 shows `-sV` automatically loads NSE version scripts in
Lua-enabled builds even without `--script`. A fixed ordinary `-sV` argv alone cannot
satisfy this task's no-NSE invariant.

## Decision

Require source-reviewed Nmap 7.95 compiled `--without-liblua`. Isolated bounded
`--version` detection verifies version and compiled feature lines; only detected
instances execute even when explicitly registered AVAILABLE. Reject standard
NSE-enabled/unknown builds; no auto-install/build or fallback. Trusted operator binary
and 7.95 databases remain intact across availability/execution. Explicit trusted
absolute database paths and isolated environment prevent ambient selection.

Operator immutable DiscoveredPortSelection snapshots supply one numeric contact,
optional named subject, finite prior-discovered TCP ports and evidence references.
Required strict planner integer ports must be a nonempty subset; no default ports.
One subject/contact per action, at most 128 requested ports. Current policy, independent
name/IP scope, final scope rechecks and shared charged budgets precede dispatch.
No resolver/pipeline is implemented. Evidence grants no scope or execution authority.

Fix unprivileged CONNECT/native version intensity 2, no DNS/host discovery/ARP probes,
XML stdout and finite scan rate/concurrency/retry controls. Native version probes stay
on the selected contact/service sockets; max_parallelism also limits version work.
Document that scan delay/rate flags do not govern all native probe writes/reconnects.
Reject entity/DTD expansion, bound local XML, fail atomically on malformed output,
and preserve missing ports/empty results as explicit partial evidence.

## Alternatives Considered

- Standard `-sV` without script flags: automatic version scripts violate no NSE.
- Empty script selection/isolated script.db: script loader and implicit selection
  complicate proving no execution; excluding NSE at compilation is stronger.
- Name scanning then scope-check output: cannot undo out-of-scope DNS-derived contact.
- Planner claims of discovered ports: insufficient; trusted prior-discovery selections
  supply an independent finite eligibility envelope.
- Add a state-to-adapter discovery pipeline now: M2-T07 owns that orchestration.
- Infer missing states from compressed summaries or vulnerabilities from versions:
  invents individual facts and conclusions unsupported by the selected records.

## Consequences

Ordinary distributed Nmap builds can be unavailable for this adapter. Operators must
provide the supported no-Lua build and trusted databases; no live compatibility claim.
Existing runner/policy/registry/domain/config/previous adapters/dependencies/CLI stay
unchanged. Native TLS/service probes remain bounded evidence collection, with fixed
limits and the existing OS/direct-child constraints. Generic facts ingest into state.

## Security Impact

No NSE code exists in accepted builds. No shell, arbitrary flags, OS/aggressive/broad
scan or destination expansion. Every actual numeric contact is independently scoped;
discovered metadata remains untrusted and cannot authorize anything.

## Testing Impact

Guarded offline fake runner/XML fixtures cover exact argv, discovered-port subset,
no-Lua availability gate, scope/no-contact denials, hostile XML/text, normalization,
provenance, explicit missing records, canonical errors and resource/cancellation cleanup.
Full repository/network-blocked/wheel/build/CLI/artifact checks are required.
See the [adapter contract](../nmap-adapter.md) for source evidence and limitations.

## Follow-up

M2-T07 becomes READY only after closeout. No pipeline or later task starts here.

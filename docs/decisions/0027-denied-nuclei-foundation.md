# ADR 0027 — Denied Nuclei scans with independent offline ingestion

Status: Accepted. Date: 2026-10-09. Owning task: M5-T01.

PLAN separates foundation, safe profile policy, execution enforcement, Finding
normalization and deduplication into M5-T01–M5-T05. A placeholder safe profile or
fake-runner-only approved scan would imply authorization before template/destination
controls exist. Availability likewise cannot mean scans are permitted.

Provide an explicit ToolAdapter for scan_templates, a strict named-profile input,
and immutable deny-only profile/ProcessSpec interface. All scan dispatch remains
unconditionally disabled. The only runner wiring is an explicit isolated local
version probe. Captured ProcessExecution ingestion is a separate offline method,
requiring centralized query/reported-target scope checks and caller provenance.
It never executes, reserves or mutates state. Candidate metadata and generic
Observation/untrusted Evidence reuse existing models; Finding stays with M5-T04.

Rejected alternatives: a nominal safe/default catalog (M5-T02 scope), trusted
profile booleans or injectable permissive resolver (bypass enforcement), unrestricted
argv/template paths, scan runner calls hidden behind a fake flag, fabricated Finding
confidence and lossy deduplication. Preserve every duplicate/conflicting source line
and exact retained stdout/stderr instead. Missing optional metadata stays unknown.
Bounded non-zero/truncated captures may produce explicitly partial candidates, never
verified vulnerabilities. Failed ingestion retains bounded evidence without facts.

The tradeoff is intentional: this foundation provides no working vulnerability scan.
M5-T03 must implement actual reviewed template/secondary-destination/budget enforcement
before any scan argv or contact can exist. Ingestion scope checks do not retroactively
authorize source captures. No new dependency, credential, binary or template package
is required now. Existing M0–M4 contracts/CLI/workflow remain unchanged.

Offline tests assert accepted policy plus binary availability still cannot dispatch
or spend; raw flags/paths and hostile/malformed/scoped records fail deterministically,
with evidence/lineage intact. Full and installed-wheel validation remains mandatory.
See the [foundation contract](../nuclei-adapter.md) for pinned primary sources, argv,
output bounds, setup and limitations. No policy catalog or Finding work starts here.

# Isolated passive Subfinder with one explicit source

ADR 0009 — Subfinder execution and third-party data boundary

## Status

Accepted

## Date

2026-10-06

## Context

M2-T02 needs passive enumerate_subdomains through the existing process runner.
Subfinder's defaults use multiple services; ambient goflags YAML can enable active
resolution or alternate targets/output/proxies. In reviewed goflags 0.1.74, default-
valued CLI booleans do not reliably override YAML. The existing runner inherits the
whole environment and cannot isolate child configuration paths. PLAN requires
explicit sources and no credential/flag authority from planners.

## Decision

Review/pin Subfinder 2.9.0 behavior. Use only credential-free HackerTarget hostsearch
with fixed JSONL/source attribution, one HTTP request/second, internal source/action
limits and no active DNS/target contact. Trusted composition opts into disclosing
an authorized root to this third-party service. External provider transport/data
are a trusted service boundary; they grant no reconnaissance target membership.
We cannot enforce provider packet/redirect/IP pinning through this scanner process;
no target probing or returned-host follow-up is permitted here.

Add one optional internal ProcessSpec.environment field: immutable bounded string
pairs representing the complete child environment. None keeps existing inheritance;
empty means no inherited values. Only AsyncProcessRunner supplies env to
create_subprocess_exec. Planner/domain/catalog contracts are unchanged.

Subfinder uses fresh temporary HOME/config paths and no inherited secrets/proxy/
Subfinder configuration variables. Explicit flag/provider config inputs are the
OS null device. Default config creation is confined to temporary directories,
removed after runner cleanup. No new dependency, YAML parser, persistence or shell.
Explicit binary/PATH detection and a no-target version probe precede AVAILABLE
registration; no auto-install, unknown-version guessing or fallback.

Strict empty parameters use the authorized original root only. JSONL rejects
malformed/outside-root records atomically, deduplicates/sorts canonical hosts and
projects into existing root Asset, metadata Observations and untrusted Evidence.
Empty discovery succeeds with empty snapshot evidence, without claiming provider
completeness. Returned names remain data, including operationally excluded names.

## Alternatives Considered

- Default/all sources: unnecessary third-party disclosures and key requirements.
- crtsh only: reviewed source uses PostgreSQL before HTTP, so HTTP rate limits do
  not govern the full source behavior. One HTTP-only source is a smaller boundary.
- False active flags plus -config alone: goflags can still load ambient defaults.
- Document operator config hygiene only: active-contact safety would depend on
  unrelated mutable ambient files instead of enforced isolation.
- Launch inside the adapter: duplicates runner ownership and cleanup.
- Ambient environment mutation: races with other tasks/children and exposes secrets.
- New scanner-specific domain result/error hierarchy: generic contracts suffice.

## Consequences

Compatibility is intentionally limited to the reviewed version/source; new support
requires source/fixture review. Third-party results may be stale, incomplete or empty
on a suppressed source failure. The source never establishes DNS verification.
Existing process direct-child and OS cleanup limitations apply. Startup detection
is local and separately bounded; session budgets cover enumeration attempts.

## Security Impact

Current policy/scope/dedup/resources precede execution. Planner selects capability;
adapter owns binary/argv/environment; runner executes shell-free argv and cleans up.
No credentials, proxy settings, discovered-host traffic or new authorization.
Environment and argv remain internal and excluded from repr/planner projection.

## Testing Impact

Fake availability/process outputs, fixture JSONL, denied dispatch assertions,
provenance/scoping/resources/cancellation and actual harmless local interpreter
child-environment tests. Full offline/network-blocked/fresh-wheel checks use no
Subfinder or provider connectivity. See [adapter contract](../subfinder-adapter.md).

## Follow-up

M2-T03 becomes READY only after closeout and remains unstarted. DNSX, other adapters,
generic dispatch/audit/lifecycle orchestration, persistence/planner/CLI remain their
existing future tasks; no new task starts here.

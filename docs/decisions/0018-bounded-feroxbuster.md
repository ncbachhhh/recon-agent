# Adapter-owned bounded Feroxbuster directory discovery

ADR 0018 — Feroxbuster contact and request containment

## Status

Accepted

## Date

2026-10-07

## Context

M3-T04 requires small approved wordlists, bounded recursion/request/rate/time and
no outside contact. Feroxbuster 2.13.1 defaults to link extraction, depth zero means
unlimited recursion, and it performs startup/base GETs outside wordlist rate accounting.
Its scope option cannot establish independent DNS address authorization. Ambient
config merging has no disable flag and cannot undo true settings with false defaults.

## Decision

Use detected Linux 2.13.1 numeric HTTP(S) directory endpoints only. Disable tool
recursion, extraction, redirects and wildcard heuristics. Adapter owns a freshly
scoped finite same-origin 2xx directory queue, built-in four-entry small-v1 wordlist,
explicit three-start overhead per process, strict total request/depth/directory bounds,
positive bounded token-bucket rate/threads and completion pacing between processes.
Keep startup burst semantics explicit. Reuse registry/action policy/real dedup/shared
budgets/runner, aggregate capture/deadline and generic untrusted endpoint evidence.

Private environment/cwd exclude user configuration and secrets. Reject any global or
resolved-binary-adjacent Ferox config before detection/execution. No runner/core/policy/
registry/config/domain/dependency/CLI/M2 pipeline or existing adapter change is needed.

## Alternatives Considered

- Native recursive/link extraction modes require hidden response-derived contact and
  cannot enforce the finite request bound before execution.
- Hostname scope matching cannot pin independently authorized concrete addresses.
- Large external wordlists introduce provenance/size/local-path contracts unnecessary
  for this deliberately small default catalog.
- Cwd config overrides cannot clear earlier true or nondefault ambient values.
- Proxy containment/custom patched scanner introduces additional infrastructure and
  trust contracts outside this task.

## Consequences and security

Hostname, ambient-config and arbitrary fuzzing modes are unavailable. Supported
numeric discovery remains operational as an explicit library capability with bounded
recursive queue, no response-driven origin changes and no authorization propagation.
Three root/startup requests are counted even when output reports fewer responses.
Rate is a bounded token bucket with bounded startup burst, not uniform per-request
spacing. Logical requests are distinct from protocol repair/packets. Trusted local
installation stability and binary integrity remain operator responsibilities; existing
runner provides no OS process-tree/heap/network sandbox. See the
[contract](../feroxbuster-adapter.md) for exact bounds and primary source evidence.

## Testing impact and handoff

Offline fake-runner registry/policy/scope/argv/wordlist/recursion/request/rate/provenance/
parser/error/state/dedup tests and full/network-blocked/build/fresh-wheel validation.
M3-T05 becomes READY only on successful M3-T04 closeout. No FFUF, broad URL dedup,
planner/loop/persistence/reporting or real CLI is implemented.

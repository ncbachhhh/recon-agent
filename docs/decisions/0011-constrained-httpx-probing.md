# Constrained HTTPX probing without redirects

ADR 0011 — HTTPX addresses, redirects and evidence

## Status

Accepted

## Date

2026-10-06

## Context

M2-T04 requires active HTTP metadata while ADR 0002 independently scopes names
and concrete addresses. Starting-host approval cannot authorize DNS answers or
redirects; post-response filtering cannot undo outside contact. Ambient goflags
configuration can enable extra contacts. The HTTPX 1.7.1 source exposes an Allow
flag without applying it to its network policy constructor.

## Decision

Pin reviewed HTTPX 1.9.0, whose Allow list reaches networkpolicy and fastdialer.
Require operator-selected finite numeric contact addresses and numeric resolver,
each independently scoped and budgeted. Fixed allow membership constrains actual
resolved addresses before socket dial, including DNS changes. Custom resolver
disables ambient/public resolver and syscall fallback. No Python DNS inference.

Use fixed GET/JSONL, one worker/probe per second, zero configured HTTP retries,
bounded body/capture/parser/output and existing action/session/cancellation limits.
Hostname/IP inputs become explicit HTTPS root URLs; supplied URLs probe their
single path/query with no scheme fallback. Atomically reject mixed batches before
writing input. Isolate child HOME/config/temp environment, null flag configuration,
disable cloud auth/update and CDN behavior. No planner flags/executable/proxy/headers.

Disable all redirect following, including same-host following and HSTS. Locations
resolve/validate only as untrusted evidence; even in-scope redirects confer no
authorization or scheduling. Normalize existing Endpoint/Observation/Evidence with
provenance; technology hints remain observations. Deterministically preserve useful
valid records with explicit partial errors, missing URLs and duplicate conflicts.

## Alternatives Considered

- Rely on hostname scope alone: violates independent address authorization.
- Follow same-host redirects: IP changes and hidden secondary behavior need fresh
  checks; there is no scoped callback through this subprocess interface.
- Filter external final URLs after execution: cannot contain contact.
- Numeric URL rewriting plus custom Host/SNI: complicates per-host batch TLS/URL
  identity; reviewed concrete-IP allow enforcement preserves original authority.
- Resolve every hostname in Python first: adds new resolver orchestration and still
  needs tool-side containment against subsequent changes.
- HTTPX 1.7.1 Allow flags: source does not implement the advertised containment.
- Add arbitrary response headers/flags/options: expands the trusted surface without
  meeting additional PLAN acceptance requirements.

## Consequences

Domain-only scope cannot execute; operators supply independently scoped addresses
and resolver. Unknown versions reject. No live-binary/network verification is
claimed. Tool rate governs probe starts, with bounded same-contact DNS/TLS/transport
behavior under the existing runner deadline. Body-bounded evidence can omit hints
and HTTPX content-length is a tool measurement. Partial results require caller-owned
partial lifecycle handling. Existing direct-child/OS resource limits remain.

## Security Impact

Planner selects probe_http only; adapter builds trusted argv/config; runner executes
without shell. Address containment and no-follow configuration precede contact.
Discovery, redirects and technology hints never modify scope or start another tool.

## Testing Impact

Source-shaped JSONL and fake runners verify approved host/IP/URL, every contact
declaration, exact argv, pre-input batch rejection, redirects and provenance,
canonical failures, partial/empty/conflicting records and resource/cancellation
cleanup. Repository-wide offline, wheel, build, CLI and security checks are required.
See the [HTTPX contract](../httpx-adapter.md).

## Follow-up

M2-T05 becomes READY only after closeout; no Naabu or later task begins.
Generic dispatch/state integration/planner/runtime/persistence remain future tasks.

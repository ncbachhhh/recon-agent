# Numeric contact bindings and bounded Naabu CONNECT discovery

ADR 0012 — Naabu contacts, ports and evidence

## Status

Accepted

## Date

2026-10-06

## Context

M2-T05 needs deliberate approved port sets and host/port/transport evidence. ADR 0002
requires independently scoped numeric contact: name membership cannot authorize DNS
answers. Naabu can expand names/CIDRs/ASNs and enable SYN, discovery, service/Nmap,
passive lookup or ambient configuration. Generic output lacks per-host completion.

## Decision

Pin source-reviewed Naabu 2.3.5. Send only canonical independently scoped numeric IPs
through isolated fixed CONNECT stream execution. Hostname inputs require explicit
operator bindings to independently scoped addresses; bindings assert intended contact
and never prove DNS or grant authority. No resolver orchestration or tool DNS lookup.
Atomic primary/batch/contact scope and shared host/resource checks precede input.

Trusted immutable settings hold typed inclusive integer TCP ranges, at most 128 ports;
default 80/443. At most 64 contacts and 4,096 pairs. Planner controls only candidates.
Fix one connection start per second and one concurrent connect; disable retries via
stream semantics, use explicit 1s dial timeout and existing action/session/capture/
normalized limits. Isolate environment/config/temp, auth/update/cloud and hidden modes.
Use the unchanged runner/policy/budget/registry and generic Host/Service/Observation/
Evidence contracts. Preserve partial parse errors and empty-result uncertainty;
never infer fingerprint/closed-port facts or follow-up permission.

## Alternatives Considered

- Scan names and scope-check output IPs: cannot undo outside contact or contain rebinding.
- Add DNS resolution/pipeline here: expands task scope and still needs pinned contacts.
- Pass full CIDRs or default top ports: implicit expansion defeats finite work bounds.
- Expose planner port text/rate/scan flags: unnecessarily expands trusted parsing/policy.
- SYN/default scan or service detection: outside this bounded CONNECT discovery task.
- Require every contact to appear in output: empty hosts may simply have no open ports;
  Naabu supplies no exhaustive per-host completion status.

## Consequences

Domain-only scope cannot execute; operators need bindings plus address declarations.
Numeric IP targets require no bindings. Conservative fixed rate can yield few facts
before timeout, which remains explicit. Supported version is source/fixture-reviewed,
without live binary/network compatibility claims. No new dependencies/global config/
runner/domain/policy contract changes. Generic state accepts the normalized lineage.

## Security Impact

No automatic DNS/target expansion, arbitrary flags/shell, raw SYN/evasion, application
probes or external fingerprint tool. Centralized exclusions/private gates and current
policy/dedup plus atomic charged resources precede contact. Evidence never authorizes.
Normal TCP retransmissions remain kernel behavior, not a packet-rate guarantee.

## Testing Impact

Offline guarded fakes verify exact argv/numeric input, approved ranges and boundaries,
name/IP/batch/contact/exclusion denials, provenance/generic state ingestion, dedup,
malformed/partial/empty/failure output, availability and budget/cancellation cleanup.
Full repository/network-blocked/build/wheel/CLI/artifact validation remains required.
See the [Naabu contract](../naabu-adapter.md) for source assumptions and limits.

## Follow-up

M2-T06 becomes READY only after closeout; Nmap and later tasks remain unimplemented.

# Separate scope-safe bulk DNS verification

ADR 0010 — DNSX capability, contact and ambiguous evidence

## Status

Accepted

## Date

2026-10-06

## Context

M2-T03 requires bounded bulk DNSX verification after discovery. The existing catalog
has only resolve_dns (already owned by native_dns) and enumerate_subdomains (passive
Subfinder). The immutable registry allows one selected adapter per capability.
DNSX defaults include resolver infrastructure; wildcard/trace modes can generate
additional queries. Its JSON merges DNS response sections and drops owner/type/TTL
information from aggregate address arrays. Those defaults cannot define authority.

## Decision

Add verify_dns as the eleventh finite capability, with dnsx/active_safe and strict
1–64 independently scoped candidates plus one selected A/AAAA/CNAME/MX/NS/TXT type.
Keep native resolution and passive discovery unchanged. Reject an entire mixed batch
before writing input; deterministic canonical names alone enter the absolute-name
list. Scope the operator's numeric IPv4 resolver independently and charge its host.

Review/pin DNSX 1.2.2; isolated local version probe uses the existing process runner.
Fresh child home/config/temp environment prevents ambient YAML, credentials and
proxies; disable cloud auth/update checks. Fixed stream mode, single worker,
one candidate/second, one attempt and one record mode prevent scope expansion.
TCP fallback stays at the same scoped resolver. Disable wildcard probing, trace,
hosts-file, CDN/ASN and brute-force modes. Preserve existing deadline/capture/cleanup.

Parse bounded full RR strings into existing internal DnsRecord and generic domain
observations/evidence, retaining actual owner/TTL/MX/TXT data. Explicitly flag merged
section ambiguity and unchecked/suspected shared-address wildcard status. No new
remote assets/authority. Discard malformed query lines while retaining valid queries;
conflicting duplicates discard the host deterministically. Partial output has counts,
unreported candidates and canonical ErrorInfo; all-malformed/truncated output fails.
No empty output implies a negative DNS fact. Caller owns lifecycle/state ingestion.

## Alternatives Considered

- Replace native resolve_dns with DNSX: breaks distinct direct-resolution behavior.
- Register both under resolve_dns: conflicts with the immutable registry contract.
- Treat DNSX as passive discovery: DNS verification performs active DNS questions.
- Silently remove unauthorized inputs: obscures malformed actions; atomic rejection
  is simpler and prevents any rejected name reaching the tool.
- Wildcard random-name checks: adds non-input questions and ambiguous authority.
- Trust aggregated address arrays/TTL: loses record owners and response sections.
- Fail every malformed line atomically: loses useful valid bulk evidence; explicitly
  partial output preserves limits without fabricating complete success.
- Extend runner stdin or implement subprocess here: temporary approved input lists
  use existing argv/environment runner interfaces without shared runtime changes.

## Consequences

New capability enablement is explicit; existing config/policy/registry logic remains
unchanged. Compatibility is source/fixture-reviewed for one version, not live-tested.
IPv6 resolver configuration and section-specific verified-answer claims are absent.
Empty/failed queries may be suppressed by DNSX; operators must preserve partial
status. Legitimate shared hosting can trigger suspicion. Binary integrity and upstream
recursive server behavior remain operator/infrastructure boundaries. Existing runner
limits cover the direct child, not arbitrary process trees or OS CPU/memory quotas.

## Security Impact

Every queried name and contacted numeric endpoint passes centralized scope policy.
Results never authorize later contact. Planner sees semantics only; adapter owns
executable/argv/config isolation, runner owns shell-free execution and cleanup.
No later capability, shell fallback, credentials, auto-install or scope expansion.

## Testing Impact

Offline source-shaped RR/JSONL fixtures and fake runners assert exact argv/list,
pre-execution mixed/all-rejected denial, scoped resolver, all six types, ambiguity,
partial/malformed/empty/nonzero/missing/timeout/cancellation, limits and provenance.
Full network-blocked, fresh-wheel, lint/type/coverage/build/CLI checks are required.
See [DNSX contract](../dnsx-adapter.md).

## Follow-up

Only M2-T04 becomes READY after successful closeout. No HTTPX or later task starts.
Generic orchestration/audit/lifecycle/persistence remain their existing tasks.

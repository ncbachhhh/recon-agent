# ADR 0019 — Specialized FFUF Host testing on numeric endpoints

Status: Accepted. Date: 2026-10-07. Owning task: M3-T05.

## Context

PLAN assigns safe named FFUF modes without unrestricted requests or duplicate default
Ferox work. Existing discover_content identity and immutable registry permit one
selected adapter. Reviewed FFUF 2.1.0 can isolate default config and disable redirects,
but its request-error retry bypasses rate pacing. Generic FUZZ requests/wordlist files
would expose arbitrary targets, credentials and state-changing inputs.

## Decision

Implement only explicit vhost_names: HEAD to a fixed scoped numeric HTTP(S) endpoint,
internal Host: FUZZ, fixed four-label catalog + independently scoped operator suffix.
No hostname resolution, SNI/body/parameter/path fuzzing, arbitrary flags/headers/files
or AI-controlled wordlists. HEAD avoids response body collection; reported words/lines
are intentionally omitted. Numeric HTTPS uses reviewed FFUF insecure TLS behavior,
with no certificate authenticity claim.

Keep existing discover_content and registry contracts: trusted composition selects
FFUF for specialized sessions, Feroxbuster for default recursive discovery. Duplicate
registration conflicts, strict schemas and real existing semantic history dedup
prevent implicit overlap/repeat dispatch. No M3-T06 identity change is added.

Use one candidate per child, reserve two Execute attempts for the upstream one-time
retry and pace completed groups by 2/R or stricter shared interval. Reuse shared
atomic budgets, aggregate output and action/session deadlines, runner cleanup and
private environment/cwd. Recheck actual numeric contact/suffix before each dispatch.
Retain candidate/Location as evidence; only the actual contact creates an Endpoint.

## Alternatives and consequences

- General FFUF templates, request files, planner wordlists and parameter/body modes:
  rejected for current task because they broaden request semantics/security scope.
- FFUF content paths: excluded to avoid duplicating Feroxbuster's assigned default.
- New capability or multi-adapter registry dispatch: unnecessary; would change the
  existing one-selected-adapter architecture and exceed this task's assigned contract.
- Single four-word child: simpler, but hidden retries bypass ticker pacing. Sequential
  one-word children make the conservative attempt/rate envelope explicit.
- GET/body comparison: supplies richer vhost heuristics but would require body bounds
  and interpretation. HEAD collects only status/header metadata and makes no confirmed
  vhost/vulnerability claim.

Conservative numeric-only/HEAD/small catalog limits trade coverage for containment.
Attempt bursts, same-peer transport repair, trusted local installation and runner OS
limits remain explicit. No additional scanner contact, scope expansion, automatic
fallback or future task implementation results. Exact contract/source/tests:
[FFUF adapter](../ffuf-adapter.md).

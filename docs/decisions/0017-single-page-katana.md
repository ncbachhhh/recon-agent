# Adapter-owned Katana graph with single-page extraction

ADR 0017 — Katana read-only contact containment

## Status

Accepted

## Date

2026-10-07

## Context

M3-T03 requires scope checks before links/redirects, finite crawl limits and no
state-changing forms. Katana 1.8.0 always parses htmx into POST/PUT/PATCH navigation;
turning off automatic form fill does not ensure GET-only recursion. Its CLI scope
controls URL membership, without connecting the independent numeric address gate
required by ADR 0002. Post-response filtering cannot undo outside contact.

## Decision

Support numeric HTTP(S) URL seeds only; reject hostname modes before execution.
Use detected Linux Katana 1.8.0 standard engine with depth zero and positive duration.
Reviewed Enqueue emits depth-one discoveries without visiting them, before page/queue
handling. Disable redirects; extract JSONL/forms/JS as data. Adapter owns finite sorted
same-origin hyperlink/script-resource GET scheduling, fresh URL/address scope validation,
pacing, shared budgets/deadline/capture and normalized generic untrusted evidence.
No form/htmx/JS-derived endpoint submission or arbitrary JavaScript execution.

Add only an optional trusted absolute ProcessSpec working_directory and literal runner
cwd forwarding. Katana unconditionally cleans relative katana_field files; a private cwd
isolates this from caller files without process-global chdir. Prior omitted-cwd behavior
is unchanged. Planner never sees executable/flags/environment/cwd controls.

## Alternatives Considered

- Ordinary recursive Katana: htmx methods and hostname resolution violate this profile.
- Host-only regex or post-filtering: cannot authorize concrete addresses before dialing.
- Proxy/HTTPS interception or custom patched Go binary: adds new infrastructure/trust
  prerequisites and substantially expands this task; no such mode is available here.
- Numeric rewriting of hostname URLs/custom Host: loses HTTPS SNI identity and changes
  endpoint semantics; fail closed instead.
- Python HTML/JS crawler: does not fulfill the requested Katana extraction capability.
- Global chdir or checking only whether katana_field exists: unsafe process-wide behavior
  or race-prone local protection; use subprocess cwd.

## Consequences and security

Operational profile is intentionally narrower than all possible scoped web URLs.
Hostname/vhost crawling requires future reviewed containment, not automatic scope expansion.
No gate or PLAN criterion is weakened: supported crawling is bounded, numeric, independently
scoped and read-only before contact. Reported HTTPS data is not authenticity evidence.
Tool drains excess response bytes; page bounds count logical GETs, not packets/fallback
connections. Existing runner has no OS heap/download/process-tree sandbox. Source/fakes
are compatibility evidence, not live scanner validation. Detailed limits and primary
source links are in the [contract](../katana-adapter.md).

## Testing impact and follow-up

Offline graph/argv/failure/budget/state/dedup fixtures and runner fake/harmless local-child
cwd tests; full/network-blocked/lint/type/coverage/build/fresh-wheel/inert CLI review.
M3-T04 becomes READY only at closeout. No Ferox/FFUF or later capability begins.

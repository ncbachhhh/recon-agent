# Fixed native common-file retrieval with numeric contacts

ADR 0015 — Common-file HTTP and redirect boundary

## Status

Accepted

## Date

2026-10-07

## Context

M3-T01 requires bounded robots/sitemap/security metadata while ADR 0002 requires
independent name/address authorization. HTTPX's subprocess interface intentionally
disables redirects and does not expose this task's bounded text extraction. Generic
HTTP clients usually resolve names/follow redirects or read/decompress whole bodies.
A thread-based stdlib HTTP wrapper cannot promptly cancel blocking socket ownership.

## Decision

Add inspect_common_files with an empty planner schema and a fixed three-path catalog.
Use trusted immutable canonical hostname/numeric contact bindings, independently scoped
and budgeted (including possible redirect contacts). Connect directly to numeric IPs
through asyncio, preserve Host/TLS SNI/certificate verification, and use h11 0.16 framing.
h11 is the minimum added runtime dependency and performs no I/O itself. Native transport
has no DNS/proxy/cookie/auth/retry/redirect machinery. It is injected for offline tests.

Bound response headers/wire/body, action/session/per-request deadlines and paced GETs.
Close/abort sockets synchronously on every exit. Follow at most two freshly scoped hops
only for the same catalog path, no query or HTTPS downgrade. Everything else stays
untrusted redirect evidence. Reject all XML DTD/entity declarations and alternate
encodings before bounded stdlib parsing; record sitemap/index URLs without recursion.
Use existing registry/policy/budget/Result/Observation/Evidence/state contracts.

## Alternatives Considered

- curl/wget or subprocess HTTPX body mode: forbidden shell-client choice or unsuitable
  body/redirect callback contract; preserve existing HTTPX probing unchanged.
- High-level resolving HTTP client: additional dependency surface plus custom pinning
  needed for name/address and TLS identity containment; sans-I/O framing is sufficient.
- Hand-written HTTP framing: chunked/EOF/interim/malformed lengths are subtle; use the
  reviewed h11 event interface with adapter-owned transport bounds instead.
- Blocking stdlib client in a thread: cancellation would leave work/socket ownership
  beyond the action deadline; use native async streams.
- Arbitrary same-host redirect paths: changes fixed metadata retrieval into arbitrary
  downloads; reject before contact even when host scope allows the destination.

## Consequences

Operators must explicitly supply numeric contacts for every possible redirect host.
No DNS address is inferred. Strict media/UTF-8/XML/path profiles may reject legitimate
alternate deployments; evidence records those limitations, with no permissive fallback.
CLI/M2 pipeline/global configuration/state/policy/runner remain unchanged. h11's official
[client event documentation](https://h11.readthedocs.io/en/stable/basic-usage.html) supplies
the Request/Response/Data/EndOfMessage interface; default tests require no network.

## Security Impact

Only fixed GET metadata requests execute. Discovery, directives and remote instruction
text cannot change policy or trigger contact. Initial/redirect names and pinned IPs
pass centralized scope; body/time/rate/wire/output limits and cancellation apply.
No XML external resource resolution or HTTP compression expansion is enabled.

## Testing Impact

Fake transports/native streams exercise allowed/denied contact, three files, framing,
headers/wire/body bounds, hostile XML, instruction text, redirects, provenance, errors,
state/dedup/resources and cancellation. Full offline/network-blocked/build/wheel/CLI
validation is required. No live-network compatibility or stronger OS containment claim.

## Follow-up

M3-T02 becomes READY after successful closeout only. No TLSX/crawler/discovery/planner/
loop/persistence/reporting/real CLI task begins. See [contract](../common-file-inspector.md).

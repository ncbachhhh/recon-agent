# Web URL identity and deduplicated state (M3-T06)

`domain.canonical_web_url` is the single pure HTTP(S) contact URL identity function.
It accepts a string and returns a canonical string or raises a fixed `ValueError`.
`WebAssetIdentity` validates through the same function; model errors use Pydantic's
existing hidden-input policy. Parsing performs no scope check, DNS, network,
subprocess, provider, logging, configuration or filesystem operation.

## Supported grammar and exact equivalence

Inputs are absolute ASCII HTTP(S) URLs of 1–2,048 characters, with no whitespace,
control characters or backslashes. Authority must contain a supported ASCII DNS
name, conventional IPv4 address or bracketed IPv6 address, optionally followed by a
decimal port in 1–65,535. Reject userinfo (including `@`), authority percent escapes,
invalid bracket suffixes, empty ports, unbracketed IPv6, IPvFuture, IPv6 zones,
IPv4-mapped IPv6, Unicode/IDN/punycode names and alternative numeric IPv4 forms.
DNS labels follow the existing scope syntax (letters/digits, interior hyphens,
1–63 characters; at most 253 characters without the terminal root dot).

| Component | Canonical rule |
| --- | --- |
| Scheme | Lowercase; HTTP and HTTPS stay distinct |
| DNS host | Lowercase; remove one terminal DNS root dot, matching existing ScopeValidator host identity |
| IPv4 | Conventional dotted decimal from `ipaddress`; alternative spellings reject |
| IPv6 | Compressed lowercase from `ipaddress`, always bracketed in URL authority |
| Port | Parse decimal (leading zeros equivalent); omit HTTP 80 / HTTPS 443; preserve every other port |
| Empty path | `/`, equivalent to explicit `/` |
| Nonempty path | Preserve exactly: case, slash repetitions, dot segments and trailing slash all matter |
| Query | Preserve exactly: order, duplicate keys, separators, bare keys, empty values, plus signs and escapes |
| Empty query delimiter | Preserve `?`; `/` and `/?` remain distinct |
| Fragment | Validate supported syntax, then omit; fragments are not sent to HTTP servers |
| Percent escapes | Require two hex digits; preserve spelling/case and encoded octets; never decode or re-encode |

Path syntax is RFC-style ASCII unreserved characters, sub-delimiters, `:`, `@`, `/`
and well-formed `%HH`. Query/fragment additionally permit `?`. Unsupported literal
characters must be encoded by the source; identity never repairs them. Encoded
controls remain data, not decoded control characters. Fragment syntax is checked
before dropping it: a malformed escape cannot disappear through normalization.
Preserving `%2f` versus `%2F` is deliberate conservatism for raw request-sensitive
servers/intermediaries. Likewise `%41` versus `A`, `%2F` versus `/`, dot segments,
`+` versus `%20` and duplicate parameter order are never merged. This is a supported
contact identity contract, not a browser navigation algorithm.

DNS root-dot/leading-port-zero aliases follow the repository's established host
identity. No scheme upgrade, path traversal cleanup, query sorting, decoding,
resolution, redirect resolution or URL-to-host/IP conversion occurs.

## Portable identity, methods and request variants

`WebAssetIdentity` holds `version=web-v1`, canonical `url`, exact `method` (GET by
default), and optional explicit `host_header`. Its key is full sorted-key, compact
canonical JSON, not a hash. Methods are HTTP tokens and remain case-sensitive:
GET, get, HEAD and POST are distinct. URL identity alone has no method; contact asset
identity does. Source IDs, scanner name, time, status and evidence content do not
change contact identity.

Current explicit Host variants are FFUF's DNS/IPv4 candidate names, normalized with
the same host syntax; no port, bracketed IPv6, userinfo or SNI variant is supported.
HEAD to a numeric peer with Host `api.example.test` remains distinct from Host
`www.example.test` and from the ordinary URL-derived Host. A reported vhost response
cannot satisfy a regular HEAD/GET contact lookup. Additional future headers/bodies/
request variants require an explicit contract extension before using this projection
as their identity. URL equality alone must never merge such requests.

## State projection and provenance

`Endpoint.web_identity` is an opt-in read-only property. It never rewrites the raw
URL or method and is absent from stored model dumps. `ReconState.web_assets` derives
sorted `WebAssetDiscovery` records over existing endpoints and HTTP/endpoint
observations. `find_web_asset(url, method='GET', host_header=None)` returns a matching
record or None; malformed input or participating discovery data raises ValueError.
These are detached projections, with no stored index, second ledger or mutation API.
All records serialize deterministically and rebuild from existing Python/JSON state.

Each entry retains sorted unique endpoint IDs, observation IDs, evidence IDs and
`contacted_observation_ids`. Conflicting response facts remain separate observations;
identity dedup never discards or chooses between them. Raw Evidence, Observation,
Endpoint, Asset and ActionResult lineage/ownership rules remain unchanged. Asset
values are seed/subject labels and may be hostnames; only concrete endpoint and
observation URLs participate, not an invented URL for every seed.

| Source contract | Seen/contact interpretation |
| --- | --- |
| Endpoint | URL/method seen; endpoint alone never proves contact |
| HTTPX / Feroxbuster | Observation URL/method seen; valid integer status 100–599 reports response/contact |
| Katana | Observation URL/method seen; contact requires both `contacted=true` and a valid status |
| Common-file inspector | requested/final URLs, redirect source URLs and sitemap discoveries seen as GET candidates; final response status and redirect source response statuses report contact |
| FFUF vhost_names | URL/HEAD plus explicit candidate Host variant; valid status reports contact only for that variant |
| Other HTTP/endpoint observations with URL | Seen using explicit method or GET default; never infer contact from status or remote `contacted` alone |

A common-file request that times out without a reported response remains seen but
has no affirmative contact claim. Rejected redirect destinations and FFUF candidates
are not separately marked as contacted URLs. Sitemap URLs are possible GET follow-up
candidates, never successful requests or permission. The generic FFUF Endpoint
retains its observation links, but only variant identities have reported contact.
Malformed participating URLs fail the whole lookup closed; raw evidence remains
available for inspection. No invalid-candidate skipping creates a false negative
that a scheduler might treat as safe new work.

## Existing action admission and future follow-up decisions

ActionCanonicalizer reuses `canonical_web_url` for primary URL targets and every
registered declared secondary URL field of probe_http, inspect_common_files,
crawl_web and discover_content. Original inputs pass existing ScopeValidator first;
canonicalization uses the original already-validated representation to preserve an
empty query delimiter lost by scope's host-focused projection. Registered validated
schema fields/defaults, capability identity, arrays/order, scalar types and all
M1-T08 lifecycle/retry/atomic admission rules remain unchanged. Non-web capabilities
keep M1-T08 target semantics. Hostname intent and explicit URL intent remain distinct.
The URL-normalization extension is reconstructed from raw in-memory action history;
there is no persisted-key migration or persistence subsystem here.

All five adapters can use shared Endpoint/state identity without parser rewrites.
Existing policy/dedup checks deny an equivalent crawl/fuzz action before runner or
transport calls and reservation, including aliases of default ports/empty paths.
Different capabilities or profiles remain distinct actions: HTTPX probing does not
substitute for crawling/content work. There is no new dispatch, scanner, M3 web
workflow, scheduling loop or M4 implementation. Future trusted scheduling can use
`find_web_asset` to distinguish seen versus reported-contact resources, then use the
existing atomic action admission and current policy/budgets before any contact.
Discovery/contact lookup is advisory data, never an execution permission token.

## Scope separation and security

Canonicalization != ScopeValidator. A successfully parsed outside URL stays outside.
The authority of `https://example.test.evil.test/` stays `example.test.evil.test`;
`https://example.test@evil.test/` rejects outright. No hostname substring/prefix match
or userinfo replacement can create an allowed authority. Validating an original
input remains mandatory; identity cannot repair a rejected input into permission.
Existing URL scope is host-level; this task adds no path/port authorization rules.
Every later destination/contact address still needs current independent authorization.
Fragment/default-port identity changes do not expand host membership. Tests compare
original and canonical scope results and guard against DNS/network/execution effects.

See [ADR 0020](decisions/0020-web-contact-identity.md), [state](state-transitions.md),
[action dedup](action-deduplication.md) and [scope](scope-model.md).

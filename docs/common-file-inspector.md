# Common-file inspection contract (M3-T01)

`tools.common_files.CommonFilesAdapter` implements `inspect_common_files`, adapter
`native_common_files`, risk `active_safe`. Explicit available registration, current
ActionPolicyValidator (including real dedup), ScopeValidator and shared
BudgetController precede contact. Default registry/imports/CLI remain inert.
The deterministic M2 pipeline is unchanged; this capability is a standalone library
boundary. Caller supplies CommonFilesContext identity/time, retains the normalized
snapshot and owns action lifecycle and atomic state ingestion.

Common-file inspection = fixed safe metadata retrieval.
Katana = bounded numeric crawling (M3-T03).
Feroxbuster = bounded recursive path discovery (M3-T04).
FFUF = specialized typed vhost_names HEAD discovery (M3-T05).

## Inputs, scope and contacts

CommonFilesInput is strict, frozen and empty. Planner cannot choose paths, arbitrary
URLs, headers, proxy, method, body, retries, files, resolver or extra_args. The primary
ActionRequest target must be an independently authorized HTTP(S) URL. Its canonical
origin supplies exactly `/robots.txt`, `/sitemap.xml`, `/.well-known/security.txt`, in
that order. Existing endpoint path/query is retained as query provenance but never
executed as a path input. Scope remains the existing host-level contract, not a new
path/port ACL. Dedup uses the existing original URL identity, including path/query;
callers should use a canonical origin for repeat common-file requests.

Trusted operator composition supplies 1–64 immutable ContactBindings, one canonical
host and numeric IPv4/IPv6 address per host. A binding is a contact selection, not
DNS evidence or inferred permission. Every configured name/address (including
possible unused redirect contacts) independently passes centralized scope and shares
host-budget charges. Literal URL addresses also require an explicit matching numeric
binding. Missing binding, exclusions, private gates, invalid URL or unauthorized
address rejects before spending/contact. No system DNS, resolver or name-to-address
permission propagation exists. Numeric contacts are rechecked immediately before
every GET, after any rate delay.

NativeHttpTransport uses asyncio numeric-address connections, h11 HTTP/1.1 framing
and stdlib SSL with certificate/hostname verification against the original URL host.
Host/SNI preserve URL authority; numeric contact prevents DNS rebinding. No shell,
curl/wget, proxy/environment credentials, cookies, client authentication, request
body, retry, alternate scheme, remote trust fetch or automatic redirect exists.
The default local TLS trust store is used. h11 (`>=0.16,<0.17`) is the only added
runtime dependency: a typed sans-I/O framing parser, not a networking client.
See [ADR 0015](decisions/0015-fixed-native-common-files.md).

## Redirects

At most two followed hops per file (nine total GETs/action). Each Location resolves
relative to the actual contacted URL, independently passes URL scope and numeric
binding/address validation, then is checked again immediately before contact.
Only the same catalog path, no query/fragment/userinfo and no HTTPS downgrade may
follow. Even an authorized `/admin`, `/security.txt` alternate path or query redirect
is rejected by this deliberately narrow profile. Loops and hop limits stop contact.
Truncated responses do not trigger redirects. A rejected destination remains bounded
untrusted metadata with the original rejection ErrorInfo; it never enters a request.
Allowed redirect following does not modify Scope or grant later action authority.

## Bounds and cleanup

One shared atomic reservation covers this finite native operation; no additional
process executions occur. All selected possible hosts/addresses count once. Attempts,
rates and worst-case aggregate output allowances stay charged on failure/cancellation;
only concurrency releases. Request completion pacing is at least one second, or the
stricter configured capability window/count interval. Actions also obey shared
rolling admission rates/concurrency/session/host/action/output limits. This is a GET
rate limit, not a TCP/TLS packet-rate guarantee.

The whole operation (including pacing) uses the smaller snapshotted configured timeout
and remaining session duration. Each connect/TLS/write/read exchange is capped at ten
seconds and the remaining action/session time. Injected transports have an adapter-owned
timeout too. Native reads are 4,096 bytes; header/interim/trailer parser state is bounded
at 16,384 bytes, at most four informational responses, no protocol upgrade. Wire bytes
per request are capped at body allowance + 65,536 to bound chunk framing overhead.
At most 16,384 body bytes/file are retained, reduced to at most one third of the smaller
configured/shared output allowance. The complete serialized output is independently
bounded by that smaller allowance; overflow returns parse_failed without a payload.
Transport/parser buffers and conversion copies add bounded memory overhead; no OS
CPU/memory quota or live-network compatibility claim is made.

HTTP framing supports Content-Length, chunked and EOF bodies. Excess body is not
fully downloaded: retain an exact bounded prefix, mark truncated and close/abort the
stream. Malformed framing after a valid header retains bounded partial body with
parse_failed. Timeout/connection failures have no response body/status; they never
invent a 200. Socket close and transport abort run synchronously in finally, including
repeated cancellation; no unbounded TLS wait_closed. Python cancellation propagates
and releases the permit. Whole-action timeout/final scope abort returns Failure with
no partial payload, following the existing Result contract.

## Parsing and evidence

Only successful 200 text/plain robots/security files or application/xml/text/xml
sitemaps are parsed; UTF-8/BOM only, no NUL, compression or automatic decompression.
Unsupported media/encoding or malformed content is an explicit partial collection
with exact bounded bytes in base64. Ordinary 404/403/other statuses are observed HTTP
outcomes and do not become infrastructure failures. No full body is claimed from a
prefix. Incomplete bodies are not parsed as complete directives/XML.

Robots preserves ordered User-agent/Allow/Disallow/Sitemap directive/value records,
strips comments, and caps 256 directives/2,048 characters per value. These are metadata,
not an executable robots ACL. Sitemap directives become deduplicated sorted HTTP(S)
URL strings only. No discovered path, sitemap, nested sitemap or outside link is fetched.

Sitemaps support urlset and sitemapindex, with the standard sitemap namespace or no
namespace, direct entries/loc values, at most 256 entries, 2,048 characters/URL, 2,048
nodes and depth 16. Strict UTF-8 text rejects all DTD/entity declarations before stdlib
ElementTree parsing. Alternate XML encodings and nested loc elements reject. No
external entities, DTD/network loading, XInclude expansion or sitemap recursion exists.
Extraction is atomic; malformed/oversized structures produce no partial URL set.
Recorded strings still need future independent syntax/scope/policy/contact checks.

Security preserves bounded decoded text plus selected Contact, Expires, Encryption,
Acknowledgments, Preferred-Languages, Canonical, Policy and Hiring field/value records,
with the same 256/2,048 bounds. These are unverified metadata. No email, external URL
visit, encryption-key download or remote instruction runs.

CommonFilesOutput contains three typed CommonFileFacts, generic web_resource Asset,
HTTP Observations and untrusted Evidence. Facts include requested catalog path/URL,
last contacted authorized URL/address, optional status/type/declared length, retained
byte count, base64 prefix/text, truncation, redirect lineage, directives/URLs and
canonical errors. Declared content length is untrusted and need not equal retained
bytes. Every fact states trust=untrusted and discovery_authorizes_contact=false.
Source/capability, caller UTC time/execution/subject, evidence IDs, memory snapshot
reference/locator and SHA-256 preserve provenance. Remote instruction-like text stays
plain data. No discovered URL creates another Asset/Endpoint/action or authorization.

Request timeout/connection/parser errors use existing tool_timeout/
tool_execution_failed/parse_failed ErrorInfo and preserve other files as partial.
Redirect rejection details live in evidence; the partial collection error is
parse_failed, preserving ActionResult's prohibition on policy failures disguised as
partial execution. A changed current scope before actual contact aborts with the
original Failure. Callers ingest completed/partial output through existing ActionResult
and ReconStateMachine; no state/schema/policy arithmetic extension is required.

## Offline verification and limits

Fixtures under tests/fixtures/common_files use reserved names and instruction-like
plain text. Tests inject HttpTransport or fake asyncio streams into the actual native
transport. They verify zero outside contact, fixed GETs, framing/body/header/wire bounds,
independent URL/IP scope, redirects, XXE-like input, directive/index discovery without
contact, deterministic normalization/provenance, state/dedup, deadlines/resources and
cancellation. Full network/DNS-blocked and installed-wheel checks are required.
No live target, scanner, local HTTP server or Python 3.12 test is implied.
TLSX/M3-T02+, crawling/fuzzing, Groq/planner/loop, persistence/reporting and real CLI
remain outside M3-T01.

# Bounded Katana crawling (M3-T03)

`tools.katana.KatanaAdapter` implements existing `crawl_web`, adapter `katana`, risk
`active_safe`. Explicit successful Linux Katana 1.8.0 detection and available registry
composition precede current action policy, real dedup eligibility and one atomic shared
budget reservation. Default registry, imports and CLI remain inert. Caller supplies
KatanaContext identities/UTC time, owns lifecycle/atomic state ingestion and retains
the returned normalized memory snapshot. M2 orchestration remains unchanged.

HTTPX = probe/fingerprint HTTP; common-file inspector = fixed metadata paths;
Katana = bounded crawler; Ferox/FFUF = future content discovery/fuzzing.

## Supported contacts and read-only profile

Only explicit authorized HTTP(S) URLs with canonical numeric IPv4/IPv6 authorities
are supported. Path/query and finite explicit ports are preserved. Bare names/addresses,
hostname URLs, userinfo, fragments, non-ASCII, whitespace/control characters, backslashes
and comma-separated input reject before reservation/execution. ScopeValidator validates
the primary URL and concrete numeric address independently. No hostname rewriting,
DNS binding inference, arbitrary Host/SNI headers or system DNS activity is needed.
Hostname URLs fail closed because reviewed CLI scope matching cannot constrain DNS
answers to independently authorized addresses. Numeric HTTPS uses Katana's reported
HTTP/TLS behavior, including its insecure certificate-verification profile; this is
not certificate authenticity evidence or a substitute for TLSX.

Each process receives exactly one freshly authorized GET seed and fixed `-d 0`, positive
`-ct`, `-dr`, `-mdp 1`, `-fs fqdn`, an exact escaped seed regex, one worker/input,
one request/second, no retries, ten-second request timeout, 16,384-byte parsing prefix,
JSONL/form/JS extraction and omitted raw/body output. Known files, path climb, headless,
form filling, proxy, headers, auth, secrets validation, cloud/update and arbitrary options
are absent. `-ndef` retains resource discoveries normally filtered by extension.

Reviewed standard-engine Enqueue emits every discovered child at depth one as an
unvisited result **before** queue admission when max depth is zero. It never executes
the child, including an htmx POST/PUT/PATCH back to the seed URL. This boundary, rather
than a post-crawl URL filter, prevents hidden contacts and state-changing submissions.
The positive duration permits zero depth in validateOptions. Redirect following and
Location parsing are disabled; Location remains response evidence, never a scheduled
GET. Refresh/base/doctype/custom/form/htmx references stay data.

The adapter separately owns a breadth-first queue. Only GET `a/href` hyperlinks and
`script/src` resource URLs can enter it, after centralized URL validation, numeric
representation checking and exact same-origin comparison. Scheme, address and port
cannot change even if another origin is independently scoped. JS text/regex endpoints
are observations only. Each next URL and numeric contact recheck after pacing immediately
before the next ProcessRunner call. No discovery changes Scope, creates an ActionRequest,
executes JavaScript or supplies instructions. Endpoint creation itself grants no authority.

## Isolation, bounds and cleanup

Trusted KatanaSettings are frozen strict operator composition, never planner fields:
max_depth defaults to 2 (0–3), max_pages to 8 (1–16, root included), max_discoveries
to 256 (1–256 facts including source lineage). KatanaInput is empty and extra-forbid.
The queue is sorted by depth/URL; visited URLs prevent loops. No broader canonicalization
or future content-discovery capability is implemented.

Adapter-owned ProcessSpec supplies the absolute binary, literal argv, complete private
HOME/config/temp/PATH environment, null flag config and private working_directory.
Katana's unconditional relative `katana_field` cleanup therefore cannot touch the caller's
working directory. The small runner cwd seam passes an absolute literal directory to
create_subprocess_exec without global chdir or shell; omitted cwd preserves prior behavior.
Version detection is bounded to five seconds and has no target; unknown/missing versions
fail closed. No installation/fallback exists. Version text is not binary attestation.

One shared reservation charges the action/contact/rate/two-stream worst-case allowance.
Sequential processes share the smaller configured/session deadline, enforced by asyncio
and runner timeouts. GET completion pacing is at least one second, or the stricter shared
capability window/count interval. Attempts/output stay charged on every failure; only
concurrency releases. Timeout/cancellation retains existing direct-child cleanup; temp
ownership closes on every exit. No retry or lifecycle/state mutation occurs in the adapter.

Per-stream capture and cumulative stdout/stderr are bounded by configured max_output_bytes;
serialized normalized output has the same bound. Parser limits are 512 lines/process,
65,536 bytes/line, bounded objects/text, 32 forms and 64 parameter names/form. Aggregate
fact overflow fails rather than silently accepting unlimited discoveries. The tool reads
only a parsing prefix but its standard engine drains remaining body bytes; total download
bytes, Go heap, packets and descendant processes are not OS-sandboxed. Same-peer TLS/transport
fallback can reconnect under the shared deadline; page/rate limits count logical GET starts,
not every packet or transport repair. No live-binary/network compatibility claim is made.

## Normalization and canonical failures

JSONL projects URL, reported method, source page, path/query presence, HTML/JS/resource
source type, tag/attribute, contacted status, HTTP status/content type/Location and selected
form method/action/enctype/parameter names. Forms always state submitted=false. Remote
instruction-like text stays plain data. Raw bodies/headers/requests do not become domain
models. Generic Asset, Endpoint, HTTP Observation and untrusted Evidence preserve source
`katana`, capability/version, subject/execution/UTC time, references, memory locator and
stable SHA-256 snapshot. No Katana domain entity, Finding or vulnerability inference exists.

Identical records deduplicate; distinct source pages retain independent lineage. Records
and endpoints sort deterministically, regardless of JSONL order. Conflicting records fail
atomically. Malformed subsets preserve valid facts as explicit partial parse_failed;
all-malformed/oversized/truncated output fails. Empty output is partial/unreported_page
with evidence and no fabricated endpoint/liveness fact. Depth/page stopping is explicit
partial collection, never a complete-site claim. Completed means this restricted graph
finished; unvisited form/JS/outside/redirect data is deliberately excluded from that graph.

Missing binary/version uses tool_unavailable; nonzero exit tool_execution_failed with
exit_code; timeout tool_timeout; containment/input rejects through scope/planner contracts;
setup/parser failures use canonical tool/parser errors. Failures have no partial payload
under the existing Result contract. Python cancellation propagates. Caller preserves
completed/partial status in ActionResult and atomically ingests subjects/evidence/facts.

## Compatibility and offline evidence

Source-reviewed Katana **1.8.0**, commit `35267ac5c8ff1db9694a319d0eb466ed97b0969f`;
fastdialer **0.5.23**, commit `7f2e2647063cd76f9aa8f652f744b5a9ed41d90c`.
No real Katana was installed or run. Primary review:

- [CLI flags, relative cleanup and config](https://github.com/projectdiscovery/katana/blob/v1.8.0/cmd/katana/main.go)
- [Depth output before queue; seed/limits](https://github.com/projectdiscovery/katana/blob/v1.8.0/pkg/engine/common/base.go)
- [Positive-duration/zero-depth validation](https://github.com/projectdiscovery/katana/blob/v1.8.0/internal/runner/options.go)
- [Redirect/HTTP profile](https://github.com/projectdiscovery/katana/blob/v1.8.0/pkg/engine/common/http.go)
- [Bounded parsing and form projection](https://github.com/projectdiscovery/katana/blob/v1.8.0/pkg/engine/standard/crawl.go)
- [Always-on htmx method extraction](https://github.com/projectdiscovery/katana/blob/v1.8.0/pkg/engine/parser/parser.go)
- [Option-controlled form/JS/Location parsers](https://github.com/projectdiscovery/katana/blob/v1.8.0/pkg/engine/parser/parser_generic.go)
- [Numeric resolution bypass](https://github.com/projectdiscovery/fastdialer/blob/v0.5.23/fastdialer/dialer.go)

Reserved source-shaped fixtures and fake runners verify exact argv/private cwd, graph
containment, scope-before-call, duplicates/order/provenance, remote data, limits, errors,
budgets, cancellation and existing state/dedup. Default tests need no binary/network.
See [ADR 0017](decisions/0017-single-page-katana.md). Stop after M3-T03.

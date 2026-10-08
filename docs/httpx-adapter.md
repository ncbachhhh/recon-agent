# HTTPX probing contract

M2-T04 implements `tools.httpx.HttpxAdapter`, adapter `httpx`, capability
`probe_http`, risk `active_safe`. The default registry remains empty. Trusted
composition calls `detect`, then explicitly registers an available instance.
Registration grants no authority. Current registry binding, action policy, scope,
dedup eligibility and atomic shared resource reservation precede execution.
Caller supplies asset/execution IDs and UTC collection time through HttpxContext;
caller owns lifecycle recording and state ingestion. No generic dispatcher exists.

HTTPX collects HTTP endpoint metadata. Katana provides bounded numeric crawling (M3-T03);
Feroxbuster provides bounded recursive path discovery (M3-T04); FFUF supplies specialized typed vhost_names HEAD discovery (M3-T05). No directory enumeration, links,
robots, authentication, vulnerability inference or follow-up scanner runs here.

## Inputs and contact containment

Strict extra-forbid HttpxInput accepts only `candidates`: at most 64 strings,
each 1–2,048 characters. Omitted/empty candidates probes ActionRequest.target;
a nonempty list is an atomic batch under the independently validated primary
subject. Every original entry passes centralized scope before canonicalization.
One unauthorized member rejects the whole action before temporary file creation,
runner invocation or resource spending. No rejected target enters execution input.

Hostname/domain and IPv4/IPv6 inputs become explicit `https://host/` URLs.
HTTP/HTTPS URLs preserve path/query and a valid explicit nondefault port; empty
path becomes `/`, redundant default ports are omitted. ASCII URLs only; commas,
backslashes and fragments reject. CIDRs, userinfo, ambiguous encodings and unsupported
target forms reject. Canonical URLs sort/deduplicate before one temporary list.
There is no automatic HTTP fallback or additional scheme/port/path probe.
Scope membership is host-level, as established by ScopeValidator, rather than a
new path/port ACL. Supplying a URL requests just that path/query.

Operator composition supplies an absolute executable, numeric IPv4 resolver and
an immutable tuple of 1–64 canonical numeric HTTP contact addresses (IPv4/IPv6).
Each address and resolver passes ScopeValidator independently and joins host-budget
accounting, including possible unused contacts. A name's authorization or DNS answer
cannot establish address membership. Numeric candidates must also belong to this
execution's finite contact set. All destinations recheck before list creation.

Fixed `-allow` contains only these checked addresses. Reviewed HTTPX passes it to
networkpolicy and fastdialer checks concrete addresses before numeric socket dial;
changed DNS answers outside the set cannot connect. This constrains addresses
without inventing name-to-IP authorization or requiring a Python DNS query.
One custom `udp:IPv4:53` resolver disables system/public resolver and syscall lookup
fallback. Fastdialer's A/AAAA lookups use only the original name and this resolver;
incidental CNAME/address records grant no authority. Hosts-file answers remain
subject to the same concrete-IP gate. Resolver upstream recursion belongs to the
authorized infrastructure boundary, as in the existing DNS adapters. HTTP contact
addresses and resolver authorization are distinct; the resolver is never added to
HTTP `-allow` automatically.

## Redirect strategy

Neither follow-redirects nor follow-host-redirects is enabled. The reviewed HTTP
client returns `http.ErrUseLastResponse` for redirects, including same-host
redirects. No HSTS following, favicon, TLS/CSP discovery, headless browser, extra
probe methods, raw requests or authentication mode is enabled. A fresh complete
child environment and null-device flag config prevent ambient YAML/proxy/secret
settings from enabling these behaviors. Cloud auth/update and CDN checks are off.

Location is tool-reported evidence. Relative locations resolve against the probed
URL and pass ScopeValidator for a `redirect_scope_status` of allowed or rejected;
`redirect_authorized` is always false. Even an allowed name requires fresh policy,
budget and independent concrete-IP checks before any later request. No redirect
creates another Endpoint or automatic action. Out-of-scope destinations may remain
untrusted evidence without contact. `final_url` is the actual probed URL because
redirect following is disabled; it never substitutes Location. Unexpected different
final URLs/chains are malformed output. Parsing after contact is an evidence guard;
pre-contact fixed configuration and the IP dial gate supply containment.

Unknown versions and planner-supplied redirect modes reject. There is no configurable
follow mode whose safety depends on a post-response filter.

## Execution and limits

The adapter owns literal ProcessSpec executable/argv/environment; the M1-T03
ProcessRunner owns shell-free execution, timeout, cancellation, direct-child cleanup
and separate bounded stdout/stderr. Planner input cannot supply flags, argv, binary,
proxy, headers, resolver, files, environment, method or extra_args. No automatic
installation or fallback binary exists. Availability detection is an isolated,
no-target version probe with at most five seconds and bounded capture.

Fixed JSONL/stream flags select GET, one worker, one probe/second, zero configured
HTTP retries, a ten-second HTTP timeout, explicit input scheme and 65,536-byte
response-read/save limits. Action timeout is the smaller configured runner/session
remainder. Attempt/host/rate/worst-case output charges persist on failure; concurrency
releases on every outcome including Python cancellation. Tool rate limits govern
probe starts, not every DNS/TLS packet or upstream transport repair. Fastdialer can
try multiple allowed addresses/TLS compatibility exchanges; gzip repair may repeat
the same GET. These stay at constrained contacts and under the action deadline.
No strict packet-rate or OS CPU/memory/process-tree containment claim is made.

Capture truncation/oversize rejects rather than silently accepting incomplete JSON.
Parser bounds: 256 lines, 65,536 bytes/line, 128 fields/object, 4,096-character text
hints, 64 technology hints of 256 characters, plus configured normalized-output cap.
Technology/title/content metadata sees a bounded body; absent fields stay absent.
Content length retains HTTPX's reported integer (header/body measurement), rather
than asserting a complete download. Raw headers/body and ancillary DNS/CDN/CPE/
WordPress bookkeeping do not enter observations. Server is a tool-reported header
hint; arbitrary response headers are not retained.

## Output and failures

HttpProbeOutput is an internal envelope containing existing generic Asset,
Endpoint, HTTP Observation and untrusted Evidence models, status/counts/errors and
unreported URLs. There is no HttpxResult domain entity. URL authority supplies
scheme/host/port; consistent optional wire metadata is checked. Status, title,
server, content type/length, location and sorted/deduplicated technology hints
remain tool facts. Technologies imply no vulnerability, authorization or scheduling.

Source `httpx`, capability `probe_http`, source_version `1.9.0`, caller identity/time,
evidence references and stable normalized snapshot SHA-256 preserve provenance.
Evidence's `memory:execution_id` reference refers to this returned normalized
snapshot, following the existing adapters; no persistence or raw-output storage.
Endpoints reference their observations and the primary asset; no redirect resource
or invented service record is created.

Records sort by URL; identical duplicates collapse. Conflicting duplicates discard
all lines for that URL, with order-independent counts. Malformed lines retain other
valid results as explicit partial output with canonical parse_failed ErrorInfo.
All-malformed output fails. Empty/missing candidate output is partial with zero
fabricated live/negative facts and explicit unreported candidates. Nonzero exits
retain tool_execution_failed/exit_code; missing binary is tool_unavailable; timeout
is tool_timeout. Runner Failure carries no partial capture, and cancellation
propagates. There are no automatic retries.

## Compatibility evidence

Supported ProjectDiscovery HTTPX **1.9.0** only, reviewed at
`f66e469116d8de3416dcdfa7b8f4083e7e7dc246` on 2026-10-06. This is source review
and sanitized source-shaped fixtures/fakes, with no installed/live HTTPX test.
Binary integrity remains an operator responsibility; version text is not attestation.
The unrelated Python `httpx` package is not this tool or a new dependency.

Primary review sources:

- [HTTPX flags/version/config](https://github.com/projectdiscovery/httpx/blob/v1.9.0/runner/options.go)
- [HTTPX network policy and result projection](https://github.com/projectdiscovery/httpx/blob/v1.9.0/runner/runner.go)
- [JSON result fields](https://github.com/projectdiscovery/httpx/blob/v1.9.0/runner/types.go)
- [HTTP client redirects/resolver/body limits](https://github.com/projectdiscovery/httpx/blob/v1.9.0/common/httpx/httpx.go)
- [Pinned dependency versions](https://github.com/projectdiscovery/httpx/blob/v1.9.0/go.mod)
- [fastdialer 0.5.4 concrete-IP checks](https://github.com/projectdiscovery/fastdialer/blob/v0.5.4/fastdialer/dialer_private.go)
- [fastdialer numeric IP and resolver behavior](https://github.com/projectdiscovery/fastdialer/blob/v0.5.4/fastdialer/dialer.go)
- [networkpolicy 0.1.34 allow membership](https://github.com/projectdiscovery/networkpolicy/blob/v0.1.34/networkpolicy.go)
- [retryabledns 1.0.113 original-name lookups](https://github.com/projectdiscovery/retryabledns/blob/v1.0.113/client.go)
- [wappalyzergo 0.2.71 embedded fingerprints](https://github.com/projectdiscovery/wappalyzergo/blob/v0.2.71/fingerprints_data.go)
- [Embedded auxiliary CPE/WordPress datasets](https://github.com/projectdiscovery/awesome-search-queries/blob/961ef30f7193/embed.go)

JSON mode implicitly runs local technology/CPE/WordPress matching against embedded
datasets; these constructors do not fetch additional URLs. Only technology hints
enter this adapter's observations; auxiliary matches are ignored.

The reviewed HTTPX 1.7.1 declares Allow/Deny flags without applying them in its
network policy constructor; it is intentionally unsupported. New versions require
contact/configuration and fixture review before expanding the pin. See
[ADR 0011](decisions/0011-constrained-httpx-probing.md).

## Offline verification

`tests/fixtures/httpx/probing.jsonl` follows reviewed result field names with reserved
names/documentation IPs. `tests/unit/tools/test_httpx.py` injects fake process output
under network/process guards, verifies exact argv/input/config isolation, rejected
batch no-write/no-call, independently scoped contacts, redirects, metadata,
technology provenance, malformed/partial/empty/duplicate results and canonical
failure/resource/cancellation behavior. Full validation includes the existing
network/DNS-blocked suite, guarded installed-wheel composition, artifacts and CLI.

## Workflow integration (M2-T07)

The [deterministic pipeline](deterministic-discovery.md) now supplies caller lifecycle,
atomic state ingestion and normalized-snapshot retention for this adapter. The optional
trusted `on_started` callback runs inside the single owned budget permit before contact;
Failure/malformed outcome aborts without contact and releases concurrency. Default
adapter use is unchanged. Existing profiles/parsers/scope/resource limits remain intact.
M2 is an integration proof; M6/M7 AI planning/autonomous loops remain future work.

## Shared identity (M3-T06)

Generic output participates in the [shared web identity/state contract](web-identity.md).
Raw evidence and adapter-specific contact/profile checks remain unchanged. Existing
web action dedup now recognizes canonical URL aliases; identity grants no authority.

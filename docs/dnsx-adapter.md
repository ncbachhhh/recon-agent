# Bulk DNSX verification (M2-T03)

The flow is discovery → candidates → independent scope checks → `verify_dns` →
normalized DNS evidence. `resolve_dns` (M2-T01) remains direct native typed resolution;
`enumerate_subdomains` (M2-T02) remains passive Subfinder discovery. DNSX implements
bulk verification of names already supplied by the caller. It does not enumerate.

## Input and trusted composition

`DnsxInput` requires 1–64 candidate strings (at most 254 characters each) and one
`record_type`: A (default), AAAA, CNAME, MX, NS or TXT. No arbitrary flags, resolver,
executable, environment, wordlist, tracing, AXFR, ANY or discovery options exist.
ActionRequest.target is the authorized primary subject; DnsxContext supplies its
asset ID, execution ID and aware collection time. Every candidate must independently
pass the current ScopeValidator, even if discovered by Subfinder. Exact hostname
roots need explicit independent candidate declarations; domain descendants require
allow_subdomains. Exclusions still win. Candidates need dotted DNS names; URLs,
addresses, CIDRs and single-label ASN-like inputs reject before launch.

Mixed authorized/unauthorized batches reject **the whole action**. All-rejected and
empty batches launch nothing; no silent filtering or partial authorization occurs.
Policy checks every entry before canonicalization. Approved names lowercase/remove
the trailing dot, deduplicate and sort lexically. Immediately before writing the
input file, the adapter rechecks all actual candidate names and resolver membership.
Only these names, with absolute trailing dots, enter the temporary UTF-8/ASCII list.
No rejected name can reach the child, including in an otherwise valid batch.

Trusted composition calls `await DnsxAdapter.detect(config, nameserver="192.0.2.53")`
with an operator-selected binary/PATH name and **canonical numeric IPv4 resolver**.
The example documentation address is not contacted by examples/tests. The resolver
must independently belong to the same operational scope; its host budget is charged
alongside the primary subject and every distinct candidate. IPv6 resolver endpoints
are deliberately unsupported by this contract. No system/default resolver, install,
`dig`, shell or fallback adapter exists. Detection performs an isolated local
`-auth false -version -nc -duc` runner probe, at most five seconds, with no target.

Only **DNSX 1.2.2** is source-reviewed/fixture-validated; older/newer/prerelease,
missing, malformed or multiple version reports fail closed. This is not a live
binary/network test or a cryptographic binary integrity claim. Operators own binary
integrity and must detect before declaring real instances AVAILABLE. Explicit
AdapterRegistration/ToolRegistry composition selects `dnsx` for `verify_dns`, with
active_safe risk. Default registry remains empty; imports and CLI remain inert.
Existing `resolve_dns` and `enumerate_subdomains` identities/behavior are unchanged.

## Execution and contact bounds

Internal argv, after policy/registry/dedup/budget checks and atomic reservation:

```text
-auth false -silent -nc -duc -json -stream -t 1 -rl 1 -retry 1
-<selected record type> -r udp:<authorized IPv4>:53 -l <temporary candidates file>
```

The adapter owns the executable and every argument. Execution uses ProcessRunner /
AsyncProcessRunner and ProcessSpec only; no direct subprocess logic or command API.
The same complete isolated child-environment seam introduced in M2-T02 sets fresh
HOME/USERPROFILE/APPDATA/LOCALAPPDATA/XDG_CONFIG_HOME and TMPDIR/TMP/TEMP. Only Windows
SystemRoot may be inherited. Credentials, proxies, DNSX/PDCP config variables and
ambient YAML are absent. The pinned goflags configuration path is inside the fresh
home/config directory. DNSX has no -config flag in this version. Cloud authentication
and update checks are explicitly disabled even for the version probe. Temporary
inputs/config/temp files are removed after runner cleanup on every outcome.

The reviewed path issues one selected original-name question per candidate, with
one attempt, one worker and a tool limit of one candidate/second. DNSX enables TCP
fallback for truncated UDP responses to the **same numeric resolver/port 53**.
Thus at most 64 UDP exchanges plus 64 TCP fallback exchanges per action; -rl bounds
candidate starts, not packets or TCP handshakes. Rolling session action rates are
independent upper bounds. No trace, alias/NS follow-up, wildcard probes, hosts-file,
CDN/ASN lookup, brute force or default resolver set is enabled. Recursive upstream
resolver work is external infrastructure behavior, not target authorization.

Runner deadlines clamp to configured action timeout and remaining session time;
per-stream output bounds, cancellation and direct-child cleanup remain unchanged.
An injected runner must honor the same/smaller capture bound; a larger adapter bound
than budget bound rejects before launch. Budgets charge attempts, distinct primary/
candidate/resolver hosts, concurrency, action rates and two-stream output allowances.
Failure/partial/timeout/cancellation retain charges and release concurrency. Partial
results use the existing FAILED reservation outcome; callers record PARTIAL action
lifecycle separately. No generic dispatch, lifecycle ingestion, audit producer,
persistence or later adapter is added.

## Parsing, ambiguity and normalized evidence

Strict JSONL validates host, resolver, status_code and aware timestamp plus bounded
known metadata. Duplicate JSON keys, unsupported fields, incorrect resolver,
unrequested/out-of-scope hosts, invalid UTF-8/JSON or malformed supported RRs discard
that entire query line. Other valid lines survive. Aggregated a/aaaa/cname/mx/ns/txt,
raw_resp and aggregate ttl are not used as facts. The reviewed `all` RR strings
preserve each RR owner, type, value and TTL, MX preference and lossless TXT chunk hex.
Only the selected type and incidental CNAME RRs normalize. Other types/OPT are ignored.
Missing `all` yields no fabricated address facts. The pinned -omit-raw implementation
copies before clearing all, so the adapter does not depend on that option.

DNSX merges Answer, Ns and Extra. Every query explicitly reports section=unspecified;
observations carry attribution=tool_reported_sections_merged. Records with different
owners stay attributed to those owners, never falsely relabeled as the query name.
No section-specific answer proof is inferred from aggregate arrays or NOERROR.
Source metadata is tool evidence, not a promise of resolver authenticity.

No wildcard probe can generate extra query names. Wildcard status is not_checked;
addresses shared by multiple reported query names get suspected_shared_address.
This conservative signal can also describe legitimate shared hosting or additional
records. It neither proves nor filters wildcard results, invents assets, promotes
scope, nor treats unchecked answers as wildcard-free. Conflicting duplicate host
lines discard that host rather than selecting a result by output order. Exact
normalized duplicates collapse; query/record ordering and hashes are deterministic.

Bounds: 256 wire lines, 65,536 bytes per line, 256 RRs per line, 8,192 characters per
RR and 256 normalized RRs across the action, plus configured capture and serialized
output limits. Oversized/truncated aggregate output fails atomically. A malformed
line alongside valid lines returns partial output with a malformed-line count and
canonical parse_failed ErrorInfo; all-malformed output fails with parse_failed.
Candidates absent from valid output are explicitly unreported, never NXDOMAIN.
Even empty/blank output returns partial Success with zero observations, snapshot
evidence, every candidate unreported and a fixed parse_failed completeness error.
This matters because DNSX can skip failed queries despite exiting zero.

DnsxOutput is a tools-local envelope. It returns candidates, selected mode, resolver,
source_version, completed/partial status, queries, unreported candidates and errors.
Existing primary Asset and generic kind=dns Observations/Evidence preserve caller
subject/time/execution, query names, actual owners, typed RRs and tool/capability
provenance. No discovered address or alias becomes a newly authorized host Asset.
One untrusted Evidence references memory:<execution_id>, locator dns-verification;
SHA-256 covers compact sorted JSON of all output fields except asset/observations/
evidence/errors. The caller retains that normalized snapshot; this is not raw stdout
or persisted storage. No stderr/raw_resp/native diagnostic/config/path enters output.

## Canonical outcomes and follow-up authority

| Condition | Existing outcome |
| --- | --- |
| Complete valid JSONL for all candidates | Success[DnsxOutput], completed |
| Some malformed/unreported queries, including empty output | Success[DnsxOutput], partial with ErrorInfo and explicit limits |
| All nonblank lines malformed or aggregate bound/truncation | Failure parse_failed, no facts |
| Missing executable/unsupported version | Failure tool_unavailable |
| Nonzero exit/local execution setup failure | Failure tool_execution_failed; safe exit_code retained |
| Runner/session deadline | Failure tool_timeout; no partial runner payload |
| Scope/policy/registry/budget denial | Canonical Failure; no child contact |
| Caller cancellation | CancelledError after runner cleanup; temp/permit released |

Callers must propagate output.status/errors into ActionResult and lifecycle; a
Success envelope with partial status is not a completed action. The state owner
already accepts properly correlated partial facts. No automatic retries occur.
Resolved IPs, aliases, record owners and discovered names must independently pass
current scope/action policy and concrete-destination checks before any later contact.
DNS resolution does not grant authorization or change Scope.

Reviewed primary compatibility sources:
[DNSX 1.2.2 flags](https://github.com/projectdiscovery/dnsx/blob/v1.2.2/internal/runner/options.go),
[runner](https://github.com/projectdiscovery/dnsx/blob/v1.2.2/internal/runner/runner.go),
[DNS library](https://github.com/projectdiscovery/dnsx/blob/v1.2.2/libs/dnsx/dnsx.go),
[pinned dependencies](https://github.com/projectdiscovery/dnsx/blob/v1.2.2/go.mod),
[retryabledns 1.0.94 queries/RR metadata](https://github.com/projectdiscovery/retryabledns/blob/v1.0.94/client.go),
[goflags 0.1.65 config](https://github.com/projectdiscovery/goflags/blob/v0.1.65/goflags.go).
See [ADR 0010](decisions/0010-scoped-bulk-dnsx.md) and [tests](testing-strategy.md).

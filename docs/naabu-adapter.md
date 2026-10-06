# Naabu bounded port discovery contract

M2-T05 implements `tools.naabu.NaabuAdapter`, adapter `naabu`, capability
`discover_ports`, risk `active_safe`. Naabu provides fast bounded open-port discovery;
Nmap implements deeper bounded service fingerprinting separately in M2-T06. No service/banner/version
probe, UDP scan, vulnerability inference or automatic follow-up runs here.

Trusted composition calls `detect(ExecutionConfig, settings=NaabuSettings(...))`, then
explicitly registers the returned supported adapter as AVAILABLE in ToolRegistry.
The default registry remains empty. Detection is a bounded isolated no-target version
probe, never an installation. Missing binaries and unknown versions fail closed.
Registration grants no scope authority. Caller supplies NaabuContext asset/execution
IDs and UTC collection time; caller owns action lifecycle, state ingestion and evidence
retention. Existing domain/config/policy/registry/runner contracts remain unchanged.

## Inputs, ports and contacts

Strict extra-forbid NaabuInput accepts only `candidates`, a list of at most 64 strings
of 1–254 characters. Omitted/empty candidates selects ActionRequest.target; a nonempty
list requests an atomic batch under the independently authorized primary subject.
Every original primary/member passes current ActionPolicyValidator/ScopeValidator
before conversion, resource reservation or any input-file write. Mixed batches reject
entirely; no rejected target enters argv, stdin or temporary files. Only hostname,
domain and IP forms are supported; URLs, CIDRs, embedded port specifications, ASN,
flags and ambiguous representations reject. Candidates canonicalize, sort and dedup.

Operator-only NaabuSettings holds 1–16 inclusive integer TCP `port_ranges`, endpoints
1–65,535, ordered start <= end, at most 128 distinct ports after overlap deduplication.
Defaults are just 80 and 443. Each individual range is bounded before expansion.
No full-range/top-ports/tool default is used. Operator settings are snapshotted;
planner fields for ports/profiles/raw_ports/extra_args/command/rate/interface/source IP/
proxy/executable or fingerprinting reject. Priority and reason never affect limits.
This is an internal composition contract, not a new global configuration section or
operational CLI flag.

Hostname requests require explicit operator ContactBinding records with canonical
hostname and 1–64 canonical numeric IPv4/IPv6 contacts. These assert the intended
addresses to assess; they are neither DNS verification nor permission. No Python or
Naabu DNS resolution occurs in this mode. Every selected address independently passes
real ScopeValidator membership/exclusions/private gates and joins existing shared
host-budget accounting. Constructor syntax checks use centralized hostname parsing
only; self-declared syntax scope never authorizes an execution. Names without bindings
and domain-only scopes fail closed. Direct IP candidates use just their canonical IP.
Mapped/scoped IPv6 and ambiguous IP forms reject at centralized execution scope.

Only selected scoped numeric contacts enter Naabu's temporary input list. At most
64 distinct contacts and 4,096 host-port pairs per invocation; exceeding either
rejects before resource spending or input creation. Unused hostname bindings cause no contact; every address in a selected binding is
part of the explicit requested contact set. Names and contacts recheck immediately before
writing input. No resolver, CIDR, hostname, reverse lookup or discovered target enters
Naabu. A returned port/address never adds authorization or changes Scope.

## Trusted execution and limits

Adapter owns absolute executable and literal ProcessSpec tuple argv. The unchanged
AsyncProcessRunner uses create_subprocess_exec with DEVNULL stdin, bounded separate
capture, timeout/cancellation and direct-child cleanup. No shell or direct subprocess
path exists in the adapter. Injected runners must obey the same or smaller stream bound.

Fixed mode is `-json -stream -no-stdin -s c -Pn -iv 4,6 -c 1 -rate 1 -retries 1
-timeout 1s -warm-up-time 0`, plus silent/no-color/update-disabled, null flag config,
auth=false, explicit sorted numeric `-p` and the validated-only list. CONNECT stream
mode uses one concurrent connect and one connection start per second; `-c 1` also
bounds input preprocessing. Stream mode does not run retry rounds, verification,
shuffling or Nmap. No SYN/stealth/evasion, host discovery, passive InternetDB, CDN,
PTR, proxy, dashboard, service discovery/version or executable hook is enabled.
The explicit `1s` avoids upstream flag-help ambiguity: goflags parses bare durations
as seconds although Naabu's help describes milliseconds. No TCP application payload
or fingerprint is sent; ordinary kernel TCP behavior is not a packet-rate guarantee.

Each process gets a fresh complete HOME/config/temp environment (and SystemRoot
when needed), excluding ambient credentials, proxy/config/PDCP variables. Null flag
config and isolated default directories prevent YAML options from enabling secondary
contact. Child local temporary/resume data stays under its disposable HOME/temp paths.
Cleanup occurs after runner cleanup on every outcome.

Current registry binding, policy/risk/schema/scope/dedup eligibility and one atomic
BudgetController reservation precede execution. Primary/member/contact hosts share
host limits; repeated IPs charge once. Session action/rolling rate/concurrency/aggregate
output limits are unchanged. Process timeout clamps to the operator execution timeout
and remaining session seconds; post-return expiry discards facts. Attempts/hosts/rate/
output stay charged on failure/timeout/cancellation; concurrency always releases.
Capture and normalized output both obey configured max_output_bytes. These resource
bounds do not claim OS CPU/memory or descendant containment beyond the existing runner.

## Parsing, normalization and failures

The bounded UTF-8 JSONL parser selects ip/host/port/protocol/tls from reviewed output.
Only canonical selected IPs, explicitly scanned valid integer ports, tcp and false TLS
are accepted; optional host must equal the numeric address. Bookkeeping timestamps/CDN
fields are excluded. Duplicate JSON keys, bad UTF-8/types/values, unrequested hosts/ports
and incomplete records are malformed evidence. Limits: 8,192 lines (including blank
lines), 4,096 bytes per nonblank line and 16 object fields; serialized output has the
configured additional bound. Remote instruction-like unknown text is never executed.

Identical (IP, port) discoveries deduplicate and sort independently of output order.
Valid lines alongside malformed/partial lines return Success with status=partial,
malformed_lines and canonical parse_failed errors; all-malformed/oversized/truncated
output fails. Empty zero-exit output completes with evidence and zero facts, without
claiming closed ports, liveness, exhaustive coverage or a successful connection for
unreported contacts. There is no per-host completion signal in this Naabu format.
Missing binary/timeout/nonzero/setup failures retain canonical shared codes, nonzero
exit context and no invented facts. Runner failure/cancellation has no partial payload;
output is discarded. Caller must preserve partial lifecycle when ingesting results.

Existing Asset, numeric Host, Service(transport=tcp) and service Observations carry
actual open IP/port facts, primary subject and candidate references. Operator binding
references do not prove name resolution. Service protocol/product/version remain absent.
Host/service/observation/evidence IDs preserve generic state lineage. Generic untrusted
Evidence preserves naabu/discover_ports/version, subject/time/execution, memory reference,
locator and SHA-256 of the normalized snapshot (not a raw transcript or process argv).
The output envelope retains selected candidates/bindings/contacts/ports and limitations;
it introduces no Naabu-specific domain entity. Caller retains the returned snapshot.

## Reviewed compatibility and evidence

Supported version: **Naabu 2.3.5**, source/fixture review only. Default offline tests
use fake ProcessRunner outcomes and reserved targets; no Naabu binary or live scan
was executed. Source review includes:

- [options and defaults](https://github.com/projectdiscovery/naabu/blob/v2.3.5/pkg/runner/options.go),
  [CONNECT constant](https://github.com/projectdiscovery/naabu/blob/v2.3.5/pkg/runner/default.go),
  [banner/version](https://github.com/projectdiscovery/naabu/blob/v2.3.5/pkg/runner/banners.go).
- [numeric input preprocessing](https://github.com/projectdiscovery/naabu/blob/v2.3.5/pkg/runner/targets.go):
  stream numeric input converts only to its single-address CIDR and bypasses FQDN/PTR/ASN resolution.
- [stream runner, sized wait group/rate and output](https://github.com/projectdiscovery/naabu/blob/v2.3.5/pkg/runner/runner.go),
  [numeric TCP dial/no TCP payload](https://github.com/projectdiscovery/naabu/blob/v2.3.5/pkg/scan/scan.go),
  [CDN client disabled by default](https://github.com/projectdiscovery/naabu/blob/v2.3.5/pkg/scan/cdn.go),
  [JSONL schema](https://github.com/projectdiscovery/naabu/blob/v2.3.5/pkg/runner/output.go).
- [IPRanger 0.0.53 numeric fallback output](https://github.com/projectdiscovery/ipranger/blob/v0.0.53/ipranger.go),
  [DNSX 1.2.2 client construction without lookup/CDN](https://github.com/projectdiscovery/dnsx/blob/v1.2.2/libs/dnsx/dnsx.go),
  [goflags 0.1.74 duration units](https://github.com/projectdiscovery/goflags/blob/v0.1.74/duration_var.go),
  [main cloud gate](https://github.com/projectdiscovery/naabu/blob/v2.3.5/cmd/naabu/main.go),
  [HOME-owned resume data](https://github.com/projectdiscovery/naabu/blob/v2.3.5/pkg/runner/resume.go).

See [ADR 0012](decisions/0012-numeric-bounded-naabu.md), [scope](scope-model.md),
[execution](execution-model.md), [budgets](execution-budgets.md) and
[testing](testing-strategy.md). Binary replacement/operator assertions remain trusted
composition concerns; version matching alone is not executable integrity verification.

## Workflow integration (M2-T07)

The [deterministic pipeline](deterministic-discovery.md) now supplies caller lifecycle,
atomic state ingestion and normalized-snapshot retention for this adapter. The optional
trusted `on_started` callback runs inside the single owned budget permit before contact;
Failure/malformed outcome aborts without contact and releases concurrency. Default
adapter use is unchanged. Existing profiles/parsers/scope/resource limits remain intact.
M2 is an integration proof; M6/M7 AI planning/autonomous loops remain future work.

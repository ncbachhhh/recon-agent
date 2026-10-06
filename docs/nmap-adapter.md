# Nmap bounded service fingerprinting contract

M2-T06 implements `tools.nmap.NmapAdapter`, adapter `nmap`, capability
`fingerprint_services`, risk `active_safe`. Naabu discovers bounded open ports;
Nmap identifies services on explicitly selected, previously discovered ports.
M2-T07 supplies explicit finite pipeline coordination; no autonomous follow-up exists.

Trusted composition calls `NmapAdapter.detect(ExecutionConfig, settings=...)` and
explicitly registers the returned adapter AVAILABLE in ToolRegistry. Default registry
stays empty. Detection runs only an isolated, bounded `--version` process, with no
network target, installation or fallback. Direct construction remains inert and
cannot execute scans until detection succeeds; AVAILABLE registration alone cannot
bypass this check. Local binaries/data files and composition code are trusted operator
inputs and must remain intact for the adapter lifetime.

## Supported installation and no NSE

Supported version is **Nmap 7.95 compiled with `--without-liblua`**, using its trusted
installation data directory and official 7.95 `nmap-service-probes`/`nmap-services`.
The fixed availability parser requires exactly one matching version line, one
`Compiled with:` line without Lua, and one `Compiled without:` line containing the
exact `liblua` token. Unknown versions, ordinary NSE-enabled builds and ambiguous
feature output fail closed with tool_unavailable.

This requirement is necessary: Nmap's native `-sV` automatically sets scriptversion
and loads NSE when Lua support exists. Omitting `--script` does not disable these
version scripts. The accepted build excludes NSE at compilation; scripts cannot
execute in this profile. Operators provide that build; this adapter never builds or
installs Nmap. See [ADR 0013](decisions/0013-nse-free-bounded-nmap.md).

Compatibility is source/fixture-reviewed only, **not live binary/network tested**.
The official [7.95 source archive](https://nmap.org/dist/nmap-7.95.tar.bz2) was inspected:
`configure.ac` documents no-Lua compilation; `nmap.cc` gates script loading under
NOLUA and emits feature/version lines; `service_scan.cc` connects to each selected
service's original target/port and honors max_parallelism. Official descriptions of
[version scripts](https://nmap.org/book/nse-vscan.html),
[service detection](https://nmap.org/book/man-version-detection.html) and
[XML output](https://nmap.org/book/output-formats-xml-output.html) support the contract.
No upstream database or scanner binary is vendored. Supporting another version/build
requires a new source/fixture review and corresponding tests.

## Inputs and authorization

Strict extra-forbid `NmapInput` accepts only required `ports`: 1–128 integer TCP
ports, each 1–65,535. No ports/default/empty selection fails closed. Booleans, floats,
strings, ranges, raw flags and additional planner fields reject. Duplicate ports
sort/deduplicate in the registered schema, so port ordering/repetition cannot evade
existing semantic action deduplication; every original element is structurally validated.
Planner cannot supply scripts, timing, source spoofing, decoys, interfaces, executable,
output paths, data paths, bindings or command fragments.

Operator-only immutable `NmapSettings` requires an absolute trusted `data_directory`
and up to 64 `DiscoveredPortSelection` snapshots (empty default grants no work).
Each selection has one canonical numeric `address`, optional canonical `hostname`,
1–128 prior-discovered TCP ports, and 1–128 nonempty discovery `evidence_ids`.
Subjects must be unique. Trusted composition selects/approves these prior facts;
planner claims and arbitrary remote records cannot populate this operator contract.
Evidence references preserve the discovery basis but do not independently authenticate
facts or grant permission. M2-T07 now owns state-to-adapter workflow composition.

Each action selects exactly one existing subject and a nonempty subset of its approved
ports. A named selection is used only for its hostname; a numeric subject requires its
own numeric selection. No default port scan, broad expansion, batch, CIDR, ASN or UDP
mode exists. Current registry binding, ActionPolicyValidator/schema/risk/dedup and
primary scope validate before execution. Hostname requests require the explicit
operator numeric contact in the selected snapshot. That address passes ScopeValidator
independently, including exclusions/private gates, and joins shared host budgets.
No Python/Nmap DNS resolution or inferred name-to-address authorization occurs.
Both subject and contact recheck immediately before dispatch; only the numeric contact
and explicit selected ports reach Nmap. Metadata never adds targets or permission.

## Exact trusted profile and resource ownership

Fixed argv, followed by adapter-owned data paths and the numeric contact:

```text
--unprivileged -sT -sV --version-intensity 2
-Pn -n --disable-arp-ping
--max-parallelism 1 --scan-delay 1s --max-rate 1 --max-retries 0
-oX - -p <sorted comma-separated selected integers>
--datadir <trusted directory>
--versiondb <trusted directory>/nmap-service-probes
--servicedb <trusted directory>/nmap-services
[-6 for IPv6] <validated numeric contact>
```

`-Pn` deliberately skips host discovery: the purpose is fingerprinting already selected
services, and discovery would add probes outside the port-selection contract.
`--unprivileged -sT` forces ordinary TCP CONNECT; `-n` prevents forward/PTR DNS;
ARP discovery is disabled. No `-A`, `-O`, `-sC`, NSE/script flags, traceroute, `-p-`,
`--allports`, UDP, SYN/stealth/evasion or automatic target expansion is present.
Native service detection can negotiate TLS on the same selected socket. Intensity 2
reduces general probes, but port-specific probes can still run regardless of rarity.
Native database exclusions (notably printer ports 9100–9107) remain respected.

The initial connect scan is limited to one start/second, one outstanding probe and no
Nmap retry round. Native version detection honors concurrency=1; its reconnects/probe
writes and normal kernel retransmissions are not governed by the initial scan's
packet-rate flags. The fixed profile is not a guarantee of one packet or application
request per second across all phases. Whole action/session deadlines and bounded port
counts constrain work; no rate claim beyond source-reviewed behavior is made.

Adapter owns absolute executable and literal ProcessSpec tuple argv; unchanged
AsyncProcessRunner owns shell-free launch, DEVNULL stdin, separate bounded output,
timeout/cancellation and direct-child cleanup. Each child has fresh disposable
HOME/config/temp paths in a complete environment, excluding ambient NMAPDIR,
NMAP_PRIVILEGED, credentials and proxies (SystemRoot is retained when needed).
Explicit databases exclude ambient user database selection. Injected runners must
honor the same or smaller capture/time/cancellation bounds. No direct subprocess path.

One atomic shared BudgetController reservation charges primary/contact host actions,
capability rate, action/concurrency and worst-case two-stream output. Deadline clamps
to execution config and remaining session time; post-return expiry discards facts.
Attempts stay charged on every failure/cancellation; concurrency and temp directories
release. Capture and serialized normalization obey configured max_output_bytes;
XML additionally caps at 1 MiB. Existing OS CPU/memory and direct-child/descendant
limitations remain as documented in [execution model](execution-model.md).

## Safe parsing, facts and canonical errors

Strict UTF-8 XML only. The exact harmless `<!DOCTYPE nmaprun>` is accepted; external
DTDs, internal subsets, entity declarations, CDATA and alternate encodings reject
before standard-library ElementTree parsing. The parser performs no external resource
resolution or execution. Predefined XML escapes decode as data. Limits: 8,192 elements,
depth 12, 32 attributes/element, 4,096 characters/attribute/text, 16 CPE entries/service.
Source envelope/version and successful finished marker must match. NSE/OS/traceroute
output rejects. Only the selected IP, requested ports and TCP transport are accepted.

Identical port records sort/deduplicate deterministically; conflicting duplicates,
malformed/truncated XML, unexpected hosts/ports/protocols, invalid states/confidence
or ambiguous service/state records fail atomically with parse_failed. No speculative
partial facts survive malformed XML. Valid XML with missing requested records returns
Success/status=partial, explicit unreported_ports and canonical parse_failed errors.
Blank zero-exit output/no-host/no-port XML likewise yields partial evidence and no
facts. Compressed extraports summaries do not establish individual states; unreported
ports remain explicit. Missing optional metadata stays absent and unknown names remain
observed data. Missing binary, timeout, nonzero exit (with exit_code), setup and capture
failures retain shared canonical tool_unavailable/tool_timeout/tool_execution_failed/
parse_failed contracts. Runner failure/cancellation has no fabricated partial payload.

Existing generic Asset/numeric Host/Service and service Observation/Evidence preserve
subject/contact/port/tcp/state/name/product/version/extra_info/service_fingerprint/tunnel/method/confidence/
CPE hints, source nmap/fingerprint_services/7.95 and prior-discovery references.
Only explicitly open ports become Services; other reported states remain Observations.
Service protocol carries Nmap's service name; optional metadata remains absent.
No OS result, vulnerability, authentication test or finding is inferred from versions,
CPEs or banners. Host binding is an operator reference, not proof of DNS resolution.

Caller supplies NmapContext asset/execution IDs and UTC collection time, owns lifecycle,
state ingestion and evidence retention. IDs link each Service through Observation to
untrusted Evidence with origin/time/execution, memory reference/locator and SHA-256 of
the stable normalized fact snapshot (not raw XML or argv). Discovery IDs are metadata;
new observations cite their own Nmap evidence, preserving generic state referential
validation. Unselected bookkeeping is omitted; bounded servicefp banner fingerprints and supported
version/banner metadata stays verbatim data. Caller must preserve partial status.

## Workflow integration (M2-T07)

The [deterministic pipeline](deterministic-discovery.md) now supplies caller lifecycle,
atomic state ingestion and normalized-snapshot retention for this adapter. The optional
trusted `on_started` callback runs inside the single owned budget permit before contact;
Failure/malformed outcome aborts without contact and releases concurrency. Default
adapter use is unchanged. Existing profiles/parsers/scope/resource limits remain intact.
M2 is an integration proof; M6/M7 AI planning/autonomous loops remain future work.

`with_selections` creates a detached snapshot for the same trusted installation,
runner, effective timeout/capture limits and data directory, retaining its detected
no-Lua gate. It performs no probe and cannot enable an undetected adapter. Workflow
selections use recorded completed/partial Naabu open-port observations and evidence;
registry/policy/budgets and independent numeric scope still gate every execution.

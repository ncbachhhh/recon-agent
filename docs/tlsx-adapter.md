# TLSX inspection contract (M3-T02)

`tools.tlsx.TlsxAdapter` implements `inspect_tls`, adapter `tlsx`, risk
`active_safe`, through the existing ToolAdapter/ToolRegistry/ActionPolicyValidator/
BudgetController/AsyncProcessRunner boundaries. Default registry, imports and CLI
remain inert. Direct construction does not enable execution: explicit successful
`detect` is required before AVAILABLE registration. Caller supplies TlsxContext
identity/aware UTC time, retains the normalized snapshot, owns action lifecycle and
atomic state ingestion. The six-stage deterministic M2 workflow is unchanged.

TLSX = bounded TLS/certificate metadata inspection.
Certificate discoveries = observations only; discovery != authorization.
Common-file inspection = fixed safe metadata retrieval.
Katana = future crawling. Ferox/FFUF = future content discovery.

## Typed targets and authorization

TlsxInput is strict, extra-forbidden and frozen: candidates is a list of at most 64
strings (empty selects the primary target); port is an optional integer 1–65535.
Supported forms are canonical authorized DNS names, IPv4/IPv6, and HTTPS authority
URLs with no path except `/`, query or fragment. Bare names/IPs use port or 443;
HTTPS uses its effective port and any explicit parameter must match. Host:port strings,
HTTP URLs, CIDR/ranges and ambiguous representations fail closed. The primary target
is checked even for a batch. The existing scope model is host-level, not a port ACL.

Trusted operator TlsxSettings contains at most 64 canonical name bindings, each with
1–64 canonical numeric addresses, and 1–64 unique allowed ports (default `(443,)`).
Every selected port must be in that finite operator set. Numeric targets select their
own address; names require explicit bindings. No DNS-derived or ambient resolver
binding is inferred. Names, original batch members and each concrete address pass
ScopeValidator independently, including exclusions/private gates. All members are
validated before reservation/files/execution; one rejection rejects the entire batch.
At most 64 distinct (host,address,port) contacts survive sorted deduplication.

All candidate authorities and selected addresses are revalidated before any input
file, and again immediately before each process. Rejected targets never enter TLSX
argv/input files. One shared reservation charges original names and concrete contacts
once, including every batch member. Current registered identity, real policy/dedup,
shared controller and capture-limit compatibility are mandatory.

Planner cannot supply executable, flags, SNI, resolver, proxy, interface, config,
input/output/CA files, cipher lists, rate/concurrency/timeouts, CT logs or extra_args.
SNI is derived only from a validated original hostname. Certificate CN/SANs never
become input, bindings or actionable assets, even when their names happen to be in
scope. Subsequent actions require independent scope/policy/contact validation.

## Trusted execution and source compatibility

Reviewed profile: **Linux, TLSX v1.4.0**, source commit
`ffe1cfef11fc71fd7b73e41c603c18bebfb28258`. Other versions/platforms fail closed.
Compatibility is source review plus source-shaped reserved fixtures/fake runners;
no TLSX installation, live binary handshake or live-network compatibility test.
The version-only probe has no target and returns before runner/network initialization.
No auto-install, runtime Python dependency or packaging change is needed.

Each distinct authorized SNI has one sequential process; numeric-only contacts share
one SNI-free process. This prevents TLSX's global SNI list from creating a target/SNI
cross product. Adapter-owned temporary files hold numeric `IP:port` entries (IPv6 is
bracketed) and exactly one canonical hostname for `-sni` when needed. Using a trusted
SNI file avoids goflags' automatic filename interpretation of a hostname. All files
are private temporary artifacts removed on success/error/cancellation; no persistence.

Fixed argv, following `-config <os.devnull>`:

```text
-silent -nc -duc -json -sm ctls -c 1 -retry 1 -timeout 5 -delay 1s -tps
-san -cn -so -tv -cipher -se -hash sha256
-l <adapter temporary numeric input> [-sni <adapter temporary SNI file>]
```

The complete child environment contains only temporary HOME/USERPROFILE/APPDATA/
LOCALAPPDATA/XDG_CONFIG_HOME/TMPDIR/TMP/TEMP/PATH (and SystemRoot if present).
PATH points at the private directory, preventing TLSX package initialization from
looking up/running ambient OpenSSL. No parent credentials, proxies, DEBUG, PDCP or
scanner-config variables propagate. Null config and empty homes exclude ambient
configuration. Update/cloud/dashboard/CT-streaming/health-check modes are disabled.
DEVNULL stdin and explicit nonempty `-l` prevent interactive or default CT input.
The runner uses an absolute executable and literal argv, never a shell.

Revocation/HardFail, verification, chain/PEM, JARM, version/cipher enumeration,
PTR/random SNI, scan-all-IPs, resolvers and alternate TLSX engines are not enabled.
TLSX 1.4.0 makes CRL/OCSP verification opt-in; leaving it disabled prevents
certificate-derived resource contact. Native ctls inspects unverified certificates;
it does not assert certificate trust or infer vulnerabilities. Local certificate
classification flags are not normalized as security Findings.

Source review includes fastdialer v0.5.18
(`eff51d62312508fb146a5314e52dd2fdc01091b2`). Numeric GetDNSData returns the supplied
address before resolver/hosts-file lookup. On a TCP dial failure its dialIPS helper
can make one further TCP/TLS fallback attempt to the **same numeric address/port**,
even with ctls selected. Thus `-retry 1` means one TLSX logical probe, up to two
underlying dial attempts, not a single packet/connection guarantee. There is no
address fallback, DNS query, SAN follow-up, revocation or outside contact in this
profile. The fixed one-second per-input delay bounds logical probe starts; it is
not a native packet-rate or individual fallback-connection rate guarantee.

Primary review sources: pinned [CLI flags/config/input selection](https://github.com/projectdiscovery/tlsx/blob/ffe1cfef11fc71fd7b73e41c603c18bebfb28258/cmd/tlsx/main.go),
[runner/numeric input/SNI/version behavior](https://github.com/projectdiscovery/tlsx/blob/ffe1cfef11fc71fd7b73e41c603c18bebfb28258/internal/runner/runner.go),
[native TLS engine](https://github.com/projectdiscovery/tlsx/blob/ffe1cfef11fc71fd7b73e41c603c18bebfb28258/pkg/tlsx/tls/tls.go),
[certificate/connection projection](https://github.com/projectdiscovery/tlsx/blob/ffe1cfef11fc71fd7b73e41c603c18bebfb28258/pkg/tlsx/clients/utils.go),
[revocation opt-in](https://github.com/projectdiscovery/tlsx/blob/ffe1cfef11fc71fd7b73e41c603c18bebfb28258/pkg/tlsx/clients/clients.go),
[OpenSSL initialization](https://github.com/projectdiscovery/tlsx/blob/ffe1cfef11fc71fd7b73e41c603c18bebfb28258/pkg/tlsx/openssl/common.go),
[goflags file-option parsing](https://github.com/projectdiscovery/goflags/blob/c2b50c5141a365283151dc487b288fc223e62b8c/slice_common.go),
[fastdialer numeric resolution](https://github.com/projectdiscovery/fastdialer/blob/eff51d62312508fb146a5314e52dd2fdc01091b2/fastdialer/dialer.go) and
[dial/fallback](https://github.com/projectdiscovery/fastdialer/blob/eff51d62312508fb146a5314e52dd2fdc01091b2/fastdialer/dialer_private.go).

## Bounds, outcomes and provenance

Existing runner owns cancellation, direct-child termination/reaping and separate raw
stdout/stderr capture limits. No runner behavior is duplicated. One whole-action
monotonic deadline covers all processes/setup/parsing, capped by the snapshotted
configured timeout and remaining session duration; every process gets the remaining
allowance, with TLSX's inner five-second connect/handshake timeout. Shared action/
capability rate/host/concurrency/session/output reservations apply. Attempt/output
charges remain on all exits; concurrency releases. Python cancellation propagates.

Captured stdout and stderr are checked per process and cumulatively across groups;
exceeding either configured stream allowance fails without a payload. The runner's
per-process capture bound also caps the transient last capture before the cumulative
check. Normalized serialized output has the same independent byte limit. At most
256 JSONL lines/process, 65,536 bytes/line, 128 keys/object, 4,096 characters/text,
128 SANs, 64 organization strings, and three bounded fingerprint entries. No native
TLSX heap/CPU/process-tree sandbox or native packet quota is claimed; certificates
are parsed inside the external process under its deadline/capture bounds.

Selected JSON fields are structurally strict. Duplicate keys, non-finite constants,
invalid UTF-8/types, unrequested host/address/port/SNI/engine, conflicting duplicate
records and oversized structures are malformed. Successful output must report the
requested numeric peer and ctls. Equal records collapse; conflicting contacts are
entirely discarded independent of input order. Unknown bounded bookkeeping (including
tool wall-clock timestamp) is ignored. All-malformed output fails `parse_failed`.
Valid subsets plus malformed lines retain partial evidence; empty output explicitly
records unreported contacts instead of inventing a successful handshake.

Each reported contact becomes generic `Observation(kind="tls")`: original host,
contact address, port, probe status, TLS version/cipher/key exchange, subject/issuer
DN/CN/organizations, multiple raw DNS SANs, serial, fingerprint hashes, validity
strings and optional tool expiration/client-cert-required metadata. TLSX's reviewed
projection emits DNS SANs, not x509 IPAddress SANs; absent fields remain absent, not
invented. CN/SAN and organization text are bounded untrusted data. Dates must be aware
RFC3339; missing/invalid/reversed validity preserves available metadata and explicit
partial limitations. Valid dates derive expired/not-yet-valid at the caller's collection
time. Omitted `expired:false` is not invented; expiration never creates a Finding.

Handshake failures are observed partial outcomes with bounded plain error text and
canonical `tool_execution_failed` metadata. Missing binary/unsupported detection uses
`tool_unavailable`; runner timeout/nonzero and parser/capture/setup errors retain
existing canonical codes. A whole-action infrastructure, deadline or scope failure
returns Failure without partial payload, including any earlier completed group.

TlsInspectionOutput contains the query/candidates/contact list, completed/partial
status, malformed/unreported limitations, shared ErrorInfo, one caller-owned generic
host Asset, TLS Observations and untrusted Evidence. It adds no TLSX domain entity,
certificate-derived Asset/Endpoint/Host/Service, or Finding. Source/capability/version,
caller UTC/asset/execution, evidence IDs, memory reference/locator and normalized-fact
SHA-256 preserve provenance. The caller retains the snapshot; a memory reference
alone does not persist source bytes. Real state lifecycle/dedup tests use unchanged
contracts. No automatic follow-up, crawling, fuzzing, Groq/planner/loop, persistence,
reporting, real CLI or M3-T03 implementation. See [ADR 0016](decisions/0016-numeric-tlsx-inspection.md).

# Numeric TLSX inspection with isolated SNI

ADR 0016 — TLS certificate collection boundary

## Status

Accepted

## Date

2026-10-07

## Context

M3-T02 requires TLSX metadata; ADR 0002 separately authorizes each concrete address.
TLSX defaults to many workers, retries, auto TLS engines, update checks and implicit
CT-log streaming without input. SNI flags can interpret filenames and create a global
cross product. Older TLSX revocation behavior may contact certificate CRL/OCSP URLs.
Even native-mode startup looks up OpenSSL. Post-result filtering cannot contain contact.

## Decision

Support detected Linux TLSX 1.4.0 only, source-reviewed with fastdialer 0.5.18.
Trusted operator bindings select independently scoped numeric contacts and finite
ports. Validate the complete batch before any files/contact. Isolate child PATH/home/
config/environment, use explicit numeric input and one trusted SNI file per original
name, native ctls, one logical attempt, single worker, five-second handshake limit,
one-second logical probe delay, JSON/probe-status and no revocation/cloud/updates.
Execute sequential SNI groups under one shared deadline/reservation through the
existing runner. Default construction/imports/CLI do not run/detect TLSX.

Bounded deterministic parser projects into generic TLS Observations/untrusted Evidence;
CN/SAN strings never create actionable assets. Preserve invalid/incomplete/expired
metadata with limitations; no vulnerability inference. Discoveries require independent
future scope/policy/binding checks. No new runtime dependency or core/domain change.

## Alternatives Considered

- Hostnames directly in TLSX: resolver/rebinding contact cannot satisfy independent
  address scope; use numeric input with original validated hostname as SNI.
- One multi-host/global-SNI process: TLSX scans a cross product, so group per SNI.
- ctls flag alone: OpenSSL initialization still occurs; isolate PATH too.
- Revocation/enumeration/auto engines: additional remote contacts/probes exceed bounded
  certificate inspection; keep them disabled and pin the reviewed source version.
- Creating SAN/CN assets after scope validation: unnecessary execution temptation;
  this task retains names solely as facts and does not create any derived asset.
- Native Python TLS client: contrary to this task's TLSX objective; reuse trusted runner.

## Consequences and limits

Explicit name/address/port composition is required; no inferred DNS contacts.
Other versions/platforms fail closed. Availability strings identify supported versions,
not binary attestation; the operator remains responsible for the trusted executable.
Source review/fake fixtures are not a live compatibility claim. Dialer TCP-failure
fallback can attempt the same numeric peer once more; fixed pacing is per logical
probe rather than per packet/fallback connection. External process heap/process-tree
containment is not supplied by the runner. These limits and pinned primary sources
are detailed in the [contract](../tlsx-adapter.md).

## Security and testing impact

Atomic input/contact rejection, original SNI, isolated config/PATH, fixed argv, budgets/
deadlines/output caps and cleanup apply. Remote certificate text grants no authority.
Offline guarded fake-runner tests cover these boundaries, metadata/provenance/state/
dedup, partial/malformed/empty/handshake failures and availability/cancellation.
Full network/DNS-blocked/lint/types/coverage/build/fresh-wheel/inert CLI review required.
M3-T03 becomes READY only at closeout; no crawling or later capability is implemented.

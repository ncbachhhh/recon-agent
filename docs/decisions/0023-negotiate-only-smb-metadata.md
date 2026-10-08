# ADR 0023 — Native SMB2 negotiation metadata only

Status: Accepted. Date: 2026-10-08. Owning task: M4-T03.

## Context and decision

PLAN assigns review of permitted SMB negotiation/share visibility to M4-T03.
It allows safe non-destructive metadata but forbids credentials, remote changes,
file retrieval/execution and attack fallbacks. No SMB collector was previously chosen.
M4-T01 supplies exact normalized relevance and inspect_protocol semantics; ADR 0003
still selects only one explicitly registered adapter per capability.

Approve one native smb2_negotiate_v1 profile: one scoped numeric Direct TCP contact,
one fixed sessionless SMB2 NEGOTIATE offering 2.0.2/2.1/3.0/3.0.2, one bounded response,
then abort/close. No session setup or authentication, even anonymous/guest; no shares,
names/domain/workgroup queries, RPC, files, commands or generic SMB client API.
No SMB1/3.1.1/NetBIOS/transform/fallback profile. Reject port 139/netbios-ssn before
contact. Native transport writes only this immutable operation; planner cannot pick
operations, dialects, flags, addresses or credentials.

Reapply the SSH adapter's proven explicit immutable Service binding and policy/scope/
dedup/shared-budget pattern without refactoring earlier source. Independent subject
and numeric address checks, registry/scope recheck after start, outer/native deadline,
finite framing/output and synchronous socket/permit cleanup apply. Preserve original
Service and common generic untrusted Observation/Evidence with caller IDs/time,
exact response and canonical digest. No dependencies, default registrations/router,
workflow/provider/CLI or new domain/state/policy behavior.

## Alternatives and consequences

General SMB libraries/clients expose session/authentication, shares and file writes;
external scripts may perform implicit login or more operations. Neither is needed
for approved negotiation metadata. Anonymous shares/name metadata require additional
session/RPC semantics and authorization review; deliberately not approved here.
SMB1 and 3.1.1 negotiation would add distinct framing/contexts and fallback; excluded
from this finite profile rather than claiming a complete support inventory.

Only selected dialect, signing advertisement, GUID, capability/size/time fields and
opaque server offer are collected. No auth verification or vulnerability findings.
Denied/unsupported metadata yields canonical limitations, never escalation. SMB-only
servers or 3.1.1-only policies may reject; no live interoperability guarantee. A
successful response does not establish exhaustive dialect support or share access.
One selected adapter means SMB and SSH are explicit composition alternatives until
future reviewed routing, not simultaneous conflicting registrations.

## Security and validation

Primary MS-SMB2 transport/header/request/response/error and SMB2-only negotiation
sources are linked in [SMB contract](../smb-adapter.md). Independent synthetic hex
fixtures and fake streams inspect exact sole outbound command 0/session 0, forbid
second packets/auth/file dispatch and retain hostile offers as untrusted data. Real
policy/scope/dedup/budget and state-lineage tests cover denial, deadlines/cancellation,
bounds and canonical failures. Required full/offline/coverage/build/wheel/CLI checks
precede DONE. No live target, scanner or SMB library is used. M4-T04+ remain future work.

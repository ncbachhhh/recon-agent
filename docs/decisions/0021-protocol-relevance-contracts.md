# ADR 0021 — Protocol relevance separated from operational availability

Status: Accepted. Date: 2026-10-08. Owning task: M4-T01.

## Context and decision

PLAN and CapabilityId already define inspect_protocol; registry cardinality is one
trusted adapter per capability. M4-T01 needs family relevance and typed contracts
before any actual protocol adapter exists. The user explicitly limits this task to
selection/framework, overriding initial PLAN scoped-dispatch/fake-module wording.

Keep inspect_protocol with finite semantic family/port/tcp parameters. Provide a
separate immutable relevance catalog sharing CapabilityDescriptor and trusted strict
schema classes with AdapterDefinition. Do not construct/register pretend operational
adapters or change ToolRegistry/policy/budget/state behavior. Future composition owns
real supported profiles and their execution; known contracts carry no availability.

Require exact recognized ASCII case-insensitive normalized Service.protocol on TCP.
Ports cannot rescue absent/unknown identity. Exact recognized product hints only veto
conflicts (including different database identities); never classify arbitrary banners.
Unknown/unreviewed/ambiguous names and malformed records return no candidate.
Generic metadata output validates existing evidence attribution without collection.

## Alternatives and consequences

Five new capability identities would diverge from PLAN and introduce new policy names
before adapters exist. Operational fake registrations would misrepresent availability.
Port-only/product-substring heuristics would guess service identity. Automatic dispatch
would exceed the user's task boundary. All are deferred or rejected here.

One capability preserves existing registry semantics. Future protocol composition must
validate finite family/profile relevance and supply the reviewed adapter without
registering conflicting ownership. No particular exchange/library/router is chosen.
Unsupported or unsafe database handshakes remain unavailable under M4-T06 review.

## Security and validation

Relevance is not authorization. No auth/credential/exploit path, network/process/Groq,
scope/budget/state change, dynamic loading or execution. Offline normalized Service
cases, hostile/composite/unknown/conflicting metadata, schema/provenance fixtures,
registry availability and real scope/schema/budget/history denials verify the boundary.
Full baseline/network-blocked/wheel checks are required. Only M4-T02 becomes READY.
Normative semantics: [protocol contracts](../protocol-capabilities.md).

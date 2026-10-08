# ADR 0022 — Receive-only native SSH identification

Status: Accepted. Date: 2026-10-08. Owning task: M4-T02.

## Context and decision

M4-T02 permits bounded non-authentication banner/handshake/protocol metadata but
forbids login, credential/command clients and unsafe expansion. M4-T01 decided
inspect_protocol, typed family/port/tcp contracts, exact Service relevance and one
selected adapter per capability; it did not choose a collector/library.

Implement one native receive-only server_identification_v1 profile. Connect once to
a trusted observed SSH service's independently authorized numeric contact, read its
bounded identification/preamble and close/abort with zero application bytes sent.
Do not implement a full client handshake, KEX, algorithm negotiation, host keys,
authentication, packet writers, session/command/SFTP/SCP APIs or retry fallbacks.
Use the established native asyncio stream pattern with numeric-only family/flags,
injected transport, outer/native deadlines and synchronous cleanup.

Specialize common input to family=ssh; planner cannot pick addresses/credentials/
wire options. Immutable operator Service/host/address bindings and current registry/
policy/scope/dedup/shared atomic budgets constrain every contact. Extend common
metadata output with explicit profile/outcome/limitations; preserve original Service
and untrusted generic Observation/Evidence. Unsupported numeric protocol versions
retain partial identification only; malformed/timeout/connection errors use existing
canonical failures. No new dependency, generic dispatcher or workflow startup.

## Alternatives and consequences

A general SSH library may expose credentials, key loading and session/authentication
fallbacks unrelated to metadata. External clients/keyscan require binary availability
and protocol/profile source review. Implementing binary KEX/host-key collection would
expand state, parsing and cryptography beyond the minimum specified metadata profile.
Receive-only identification establishes a smaller auditable boundary and no send path.

This profile cannot collect algorithms/keys, verify server identity or guarantee a
banner from servers waiting on client identification. Those limitations are explicit;
no negotiation/authentication/expanded fallback follows. Binding facts are trusted
caller selections, not permission or proof of DNS. Existing one-adapter cardinality
and all earlier production boundaries stay unchanged. M4-T03+ remain future work.

## Security and validation

RFC 4253 identification syntax/source review, normalized-service/provenance fixtures,
real registry/policy/scope/dedup/budget denials and native fake-stream tests with every
write/drain forbidden. Unread KEX/userauth bytes, exact bounds, timeout/refused/EOF/
partial/cancellation and cleanup verify the zero-client-message boundary. Full,
network-blocked, coverage/build/wheel/CLI/artifact checks are required. No live target
or SSH binary/library runs. Full profile/source references: [SSH contract](../ssh-adapter.md).

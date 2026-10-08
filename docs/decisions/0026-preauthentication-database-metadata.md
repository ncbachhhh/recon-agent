# ADR 0026 — Finite pre-authentication database metadata profiles

Status: Accepted. Date: 2026-10-08. Owning task: M4-T06.

## Context and decision

PLAN delegates the initial safe database set and explicit permitted exchanges to
M4-T06. M4-T01 already assigns mysql/mariadb, postgresql/postgres, redis, mongodb
and ms-sql-s relevance. Queries, authentication and arbitrary driver access are
out of scope. Existing adapters establish prior Service/numeric-contact bindings,
current scope/policy/dedup/shared budgets and one selected inspect_protocol adapter.

Approve one native_database adapter with separate fixed internal handlers:
receive-only MySQL/MariaDB sequence-zero V10 metadata; PostgreSQL's immutable
SSLRequest, one-byte S/N signal, then close. No PostgreSQL startup/TLS/user/database
or auth negotiation; unavailable version is explicit partial metadata. MySQL sends
zero bytes and parses only fixed greeting metadata; auth/vendor tails remain opaque.
Redis/MongoDB/SQL Server have no approved profile and reject before contact/spending.
No new family, default registration/router, driver/dependency or earlier source change.

Reuse established strict inputs with a required canonical database_type checked
against Service aliases/product conflicts. Independent current subject/address scope,
atomic budgets, native/outer/session deadlines, finite capture/serialized output and
synchronous abort/permit cleanup gate a single contact. Original Service/generic
untrusted Observation/Evidence retain caller source/time/execution/hash and limits.

## Alternatives and consequences

A generic DB client exposes login, queries/data and implicit startup. PostgreSQL
StartupMessage requires a username and may create an authenticated session even
without a password; it is forbidden. TLS negotiation adds unrelated work. Redis INFO
and MongoDB hello/buildInfo are commands; even unauthenticated deployments do not
justify a query/command path under this task. SQL Server adds distinct framing and
negotiation unnecessary for the initial minimal set. All are excluded.

Receive-only MySQL provides useful version metadata without login. PostgreSQL's
SSLRequest gives only a reported support signal, so version/protocol-version fields
remain null and the result is partial. No vulnerability or verified product identity
is inferred. Unsupported/error/auth-required behavior never escalates or retries.
A complete fixed MySQL prefix does not validate opaque authentication tails or a
complete client handshake. These limits are explicit rather than relaxed criteria.

## Security and validation

Primary wire-format sources, exact approved packets and no-auth/no-query/data/
mutation exclusions are linked in [database contract](../database-adapter.md).
Independent offline hex fixtures/fake streams inspect every application byte;
no MySQL write and exactly one immutable PostgreSQL SSLRequest. Real policy/scope/
budget/dedup/state tests cover rejection without contact/spending, provenance,
partial/unavailable/malformed/auth-boundary/refused/timeouts/bounds/cancellation.
Full/network-DNS-blocked/coverage/build/fresh-wheel/inert CLI/artifact checks are
required before DONE. No live client/server/scanner/Groq or M4-T07 work.

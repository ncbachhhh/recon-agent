# Database service metadata adapter (M4-T06)

`tools.database.DatabaseAdapter` / `native_database` implements existing
inspect_protocol/family=database, active_safe. One coherent capability uses separate
internal MySQL and PostgreSQL handlers. Explicit AVAILABLE registration asserts
implementation availability, never target authorization, reachability or database
access. Imports/default registry/workflow/CLI stay inert; no database driver exists.

## Approved set and exact exchanges

PLAN delegates the initial safe set to M4-T06. The existing M4-T01 relevance catalog
assigns MySQL/MariaDB, PostgreSQL, Redis, MongoDB and ms-sql-s. This task enables only
two narrowly defined profiles; relevance alone does not promise collection.

| Database type / observed aliases | Profile / application exchange | Normalized metadata |
| --- | --- | --- |
| mysql / mysql, mariadb | mysql_greeting_v1: receive one sequence-zero packet; send **zero bytes** | V10 reported server-version string, connection ID, capability flags, character set/status flags when fixed extension exists, SSL capability bit, narrow product hint |
| postgresql / postgresql, postgres | postgresql_ssl_support_v1: send exactly hex `0000000804d2162f`; read exactly one byte; close | S/N reported willingness for SSL; version and protocol version unavailable; always partial |
| redis, mongodb, ms-sql-s | No approved profile; tool_unavailable before reservation/contact | None |
| Unknown/ambiguous/unassigned types | Strict input/relevance rejection before contact | None |

MySQL packet length is a three-byte little-endian payload length followed by sequence
ID. V10 sends the initial server version and fixed connection/capability fields before
any client response. See primary [packet framing](https://dev.mysql.com/doc/dev/mysql-server/latest/page_protocol_basic_packets.html),
[V10 layout](https://dev.mysql.com/doc/dev/mysql-server/latest/page_protocol_connection_phase_packets_protocol_handshake_v10.html)
and [MariaDB greeting layout](https://mariadb.com/docs/server/reference/clientserver-protocol/1-connecting/connection).
No HandshakeResponse, SSLRequest, authentication response, COM_QUERY, COM_INIT_DB,
COM_FIELD_LIST, COM_PING, COM_QUIT or any other client packet is sent to MySQL.

PostgreSQL's [SSLRequest format](https://www.postgresql.org/docs/18/protocol-message-formats.html#PROTOCOL-MESSAGE-FORMATS-SSLREQUEST)
is Int32 length=8 and Int32 code=80877103. Its [message flow](https://www.postgresql.org/docs/18/protocol-flow.html#PROTOCOL-FLOW-SSL)
permits closing after the S/N response. This adapter always closes there: no TLS/GSS
handshake, StartupMessage, user/database parameter, password/SASL response,
CancelRequest, Query, Parse/Bind/Execute, replication, Terminate or fallback. S/N
is only a protocol-compatible signal, not a verified PostgreSQL identity or version.
The request code is never labeled a negotiated protocol version. PostgreSQL version
metadata is explicitly unavailable under this unauthenticated profile.

Redis INFO/PING/AUTH/HELLO/CONFIG/KEYS/GET/SET/EVAL and all other RESP requests,
MongoDB hello/isMaster/buildInfo/auth/list/find/document operations and SQL Server
PRELOGIN/LOGIN7/batch/query operations are deliberately unimplemented. No contact,
partial synthetic evidence or inferred version is generated for these catalog types.
Neither a harmless-sounding command nor server-advertised text expands the allowlist.

## Typed input and contact authority

DatabaseInput extends ProtocolMetadataInput with required canonical database_type:
mysql/postgresql/redis/mongodb/ms-sql-s, family=database, strict integer port 1–65535,
transport=tcp. Alias names come from the observed Service; input types are canonical.
Extra fields reject: credentials, usernames/passwords, connection strings/URIs, user/
database names, queries/commands, schema/table/collection names, flags/raw options,
TLS/proxy settings or arbitrary contact addresses. ActionRequest.target is an
explicit authorized host/IP; query_target in output names that subject, not a DB query.

Trusted composition supplies 1–64 immutable prior Service/subject/numeric-address
bindings. Existing exact ASCII Service relevance, TCP and product-conflict vetoes
apply; request type and port must match the selected observed Service and asset.
Numeric subjects equal the contact address. Discovery/DNS/banner names confer no
permission. Independent subject and concrete IPv4/IPv6 ScopeValidator checks, current
registry/policy/risk/schema/dedup and atomic shared budgets gate contact. Registry/
subject/address recheck after trusted start notification, immediately before opening
the numeric connection. No DNS/proxy/redirect/name follow-up/address switching.

Database/SSH/SMB/FTP/SMTP are explicit composition alternatives under ADR 0003:
one selected adapter per inspect_protocol registry, no generic router/default
registration or conflicting registrations. Only the database adapter selects its
finite internal wire handlers; remote or planner values cannot name/import a driver.
Earlier production source/framework/domain/policy/runner/state/dependencies/CLI remain
unchanged. No M4-T07 selection matrix or later subsystem is implemented.

## Framing and completeness

Capture ≤min(4096, execution/shared per-action output allowance); serialized normalized
output must also fit the allowance. MySQL reads four header bytes, checks sequence=0
and payload size before body allocation/read, then stops at exactly one packet.
UTF-8 version is 1–255 bytes, NUL-terminated, with no ASCII controls. V10 requires the
fixed connection/scramble/filler/low-capability prefix; filler must be zero. A greeting
ending exactly after that prefix is partial (incomplete_greeting). A truncated fixed
extension fails. A full fixed extension exposes charset/status/high flags; its
reserved/vendor/authentication tail is opaque raw evidence, never decoded as an
operation or a complete authentication offer. Completed means these fixed metadata
fields were collected, not a validated/full handshake or exhaustive feature inventory.
No auth mechanism, salt interpretation, authenticated identity or vulnerability is
inferred. V9 records only protocol=9 with unsupported_handshake/partial; no fallback.

Product hints use the entire bounded version grammar: explicit MariaDB spelling or
numeric MySQL-compatible form; instruction-like versions remain exact data without
hints. MySQL-compatible does not prove Oracle MySQL. Original discovered Service
product/version remain unchanged. SSL bits and PostgreSQL S/N are advertisements,
not TLS testing. PostgreSQL reads only one byte, aborts unread bytes, and rejects
extra bytes from injected capture; ErrorResponse/auth-like signals yield a fixed
failure without reading/displaying remote error text or attempting startup.

One connection/action; PostgreSQL at most one eight-byte write; MySQL none. Native/
outer whole-action deadline = min(configured timeout, remaining session time), no
per-read reset. Shared action/host/rate/concurrency/output/session limits apply;
subject and distinct numeric contact both charge host budgets. Rate counts admitted
connections, not packets. Asyncio/OS may buffer unread bytes; retained capture is
bounded, and synchronous close/abort discards remaining data. No cleanup await can
interrupt socket/permit release. Python cancellation propagates after cleanup.
Offline validation does not establish live interoperability or Python 3.12 execution.

## Provenance and canonical outcomes

DatabaseOutput extends ProtocolMetadataOutput with original Service, subject/contact,
canonical type/profile, completed/partial and at most one ErrorInfo. Generic metadata
Observation/untrusted Evidence retain asset/host/service/port, source=native_database,
capability=inspect_protocol, caller UTC/execution, memory reference/locator and SHA-256
normalized snapshot digest. Exact raw response is base64, including opaque pre-auth
server offer; it is data, never instructions. Authentication/query/data/mutation/TLS
flags are false. No credentials, schema/table/user/document/row inventory or Finding.
Caller owns ActionResult/state lifecycle; partial uses output.errors[0].

| Condition | Canonical outcome |
| --- | --- |
| Scope/policy/schema/type/observed service/dedup/budget denial | Existing Failure, no contact; unsupported catalog profile = tool_unavailable, no spending |
| Refusal/unreachable/empty read/initial MySQL ERR (including access required) | tool_execution_failed, fixed diagnostic, no retry/auth fallback |
| Native/action/session timeout | tool_timeout, no payload |
| Malformed/truncated/oversized framing/version/SSL signal or normalized output | parse_failed, no observations |
| MySQL V9 or short fixed V10 prefix | Success[DatabaseOutput], partial + parse_failed limitation |
| PostgreSQL S/N | Success[DatabaseOutput], partial + parse_failed/version_unavailable; signal preserved |
| Full MySQL V10 fixed metadata | completed; opaque tail remains unparsed |

Tests use independent synthetic hex fixtures and fake transports/streams. Exact
outbound vectors, unread next messages, no authenticated/data/mutation API and strict
parameter denials prove the security boundary. Actual policy/scope/resources/state/
dedup tests cover before-contact denials, provenance, deadlines/cancellation/cleanup
and partial ingestion. See [ADR 0026](decisions/0026-preauthentication-database-metadata.md).

# ADR 0020 — Conservative shared web contact identity

Status: Accepted. Date: 2026-10-08. Owning task: M3-T06.

## Context

HTTPX, common-file inspection, Katana, Feroxbuster and FFUF emit generic facts with
independent IDs/provenance and varying URL spellings. M1-T08 originally preserved
scope-normalized resource text, including fragments and explicit default ports.
Follow-up decisions need one shared identity while preserving scope, raw evidence,
method/query distinctions and FFUF's explicit Host variants.

## Decision

Place pure HTTP(S) URL canonicalization and portable web-v1 contact identity in
domain. Collapse scheme/host case, established DNS root-dot aliases, numeric host
spellings, decimal/default ports, empty path and validated fragments. Preserve path
bytes, query bytes/order/duplicates, explicit empty query and percent escape spelling.
Reject unsupported/malformed/ambiguous authorities rather than repairing them.
Methods remain case-sensitive; explicit FFUF Host variants remain distinct contacts.

Expose derived read-only Endpoint identity and ReconState discovery/contact lookup,
with sorted complete provenance references and no second cache/ledger. Preserve all
raw subject/fact/evidence records and conflicting observations. Report contact only
from existing known-adapter response contracts; endpoint existence/discovery alone
cannot manufacture contact. Invalid participating URLs fail the complete lookup.

Reuse URL identity for existing web capability primary/declared secondary URL action
fields only after original scope/schema validation. Preserve every other M1-T08
capability/parameter/lifecycle/retry/admission rule and non-web target semantics.
No adapter dispatcher, new scanner or scheduling loop is introduced.

## Alternatives and consequences

- Sorting/removing query parameters, decoding escapes or resolving dot segments:
  rejected because raw request semantics can differ.
- Normalizing only inside each parser: diverging identities and future scheduling
  decisions; central domain identity works with all existing generic outputs.
- Physically deleting/merging state records: loses source facts or forces lineage
  remapping; derived equivalence preserves history and ownership.
- URL-only contact proof: loses method and explicit Host semantics; FFUF responses
  cannot prove ordinary GET/HEAD contact to the numeric URL.
- Treating successful parsing as scope approval: violates independent authorization;
  original input checks remain mandatory.

Conservative equivalence can retain apparently redundant escaped URLs, empty queries
and distinct capability work. This favors correctness over fewer requests. The
in-memory raw history can rebuild new web URL action identity; persisted migration
is outside scope because persistence is unimplemented. Full normative contract:
[web identity](../web-identity.md).

## Security and tests

No I/O, DNS, process/provider runtime, scope expansion or evidence mutation.
Offline table/adversarial/serialization/projection tests, five-adapter normalization
and before-dispatch repeat denials, full/network-blocked/build/fresh-wheel checks.
M3 closes; only M4-T01 becomes READY, without starting protocol work.

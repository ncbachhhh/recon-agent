# Synthetic policy review records

reviews.json contains two inert typed manifest fixtures, not Nuclei templates.
IDs, all-zero revision, 0.0.0 package version and hashes of synthetic descriptions
are deliberately fictional. They do not refer to any reviewed upstream template
and must never be installed, executed or used as production operator approvals.

Behavior records exercise the repository's one root HEAD/status-and-headers envelope.
The policy review date/version is explicit; every identity/behavior field is pinned.
No template source, YAML, payload, credentials or package is downloaded or included.
The real default NucleiProfileCatalog has zero concrete template reviews.

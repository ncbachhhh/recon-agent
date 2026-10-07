# Feroxbuster discovery fixture

`discovery.jsonl` is sanitized source-shaped Feroxbuster 2.13.1 response serialization
from `src/response.rs`, with documentation numeric address and reserved external name.
It is authored offline; no real scanner/target was used. Root and four approved words
cover 200/204/301/403, Location and generic length/method/source/header fields.
Tests generate nested 404/error/duplicate/malformed/budget cases with fake runners.
Upstream commit: aa8e1335801e91d98ce0d4fd148c2159a667a83b.

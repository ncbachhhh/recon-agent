"""Operator declarations, without parsing, matching or authorization policy."""

from typing import Literal

from recon_agent.domain._base import NonEmptyText, Record


class Target(Record):
    """A declared starting subject. Presence never confers authorization."""

    id: NonEmptyText
    kind: Literal["domain", "hostname", "ip", "cidr", "url"]
    value: NonEmptyText


class Scope(Record):
    """Declared roots/exclusions/options; the M1 validator defines their policy."""

    id: NonEmptyText
    roots: tuple[Target, ...] = ()
    exclusions: tuple[Target, ...] = ()
    allow_subdomains: bool = False
    allow_private_ips: bool = False
    authorization_context: NonEmptyText | None = None

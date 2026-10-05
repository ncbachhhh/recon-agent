"""Scanner-independent subjects and network metadata; no discovery or inference."""

from typing import Annotated, Literal

from pydantic import StringConstraints

from recon_agent.domain._base import NonEmptyText, Port, Record


class Asset(Record):
    """The discovered thing; supporting facts belong in observations/evidence."""

    id: NonEmptyText
    kind: Literal["host", "web_resource"]
    value: NonEmptyText
    observation_ids: tuple[NonEmptyText, ...] = ()


class Host(Record):
    """Host identity and reported resolution data; no DNS lookup or scope grant."""

    id: NonEmptyText
    asset_id: NonEmptyText
    value: NonEmptyText
    addresses: tuple[NonEmptyText, ...] = ()
    observation_ids: tuple[NonEmptyText, ...] = ()


class Service(Record):
    """Observed service metadata is evidence, not a vulnerability conclusion."""

    id: NonEmptyText
    asset_id: NonEmptyText
    host_id: NonEmptyText
    port: Port
    transport: Literal["tcp", "udp"]
    protocol: NonEmptyText | None = None
    product: NonEmptyText | None = None
    version: NonEmptyText | None = None
    observation_ids: tuple[NonEmptyText, ...] = ()


class Endpoint(Record):
    """Preserved URL/method data; construction does not canonicalize or fetch."""

    id: NonEmptyText
    asset_id: NonEmptyText
    url: NonEmptyText
    method: Annotated[
        str, StringConstraints(pattern=r"^[!#$%&'*+.^_`|~0-9A-Za-z-]+$")
    ] = "GET"
    service_id: NonEmptyText | None = None
    observation_ids: tuple[NonEmptyText, ...] = ()

"""Pure derived web discovery index over existing evidence, without a ledger."""

from recon_agent.domain.assets import Endpoint
from recon_agent.domain.observations import Observation
from recon_agent.domain.web import WebAssetDiscovery, WebAssetIdentity


def web_discoveries(
    endpoints: tuple[Endpoint, ...], observations: tuple[Observation, ...]
) -> tuple[WebAssetDiscovery, ...]:
    """Collapse identities only, preserving every source record and reference.

    Invalid candidate URL/method data fails the whole lookup closed. Only known
    adapter response fields establish reported contact. Raw records remain intact.
    """
    identities: dict[str, WebAssetIdentity] = {}
    refs: dict[str, dict[str, set[str]]] = {}
    by_id = {item.id: item for item in observations}

    def add(
        url: object,
        method: object = "GET",
        *,
        endpoint: Endpoint | None = None,
        observation: Observation | None = None,
        contacted: bool = False,
        host_header: object = None,
    ) -> None:
        if not isinstance(url, str) or not isinstance(method, str):
            raise ValueError("Malformed web discovery")
        if host_header is not None and not isinstance(host_header, str):
            raise ValueError("Malformed Host variant")
        identity = WebAssetIdentity(url=url, method=method, host_header=host_header)
        key = identity.key
        identities[key] = identity
        bucket = refs.setdefault(
            key,
            {
                name: set()
                for name in (
                    "endpoint_ids",
                    "observation_ids",
                    "evidence_ids",
                    "contacted_observation_ids",
                )
            },
        )
        if endpoint is not None:
            bucket["endpoint_ids"].add(endpoint.id)
            bucket["observation_ids"].update(endpoint.observation_ids)
            for ref in endpoint.observation_ids:
                bucket["evidence_ids"].update(by_id[ref].evidence_ids)
        if observation is not None:
            bucket["observation_ids"].add(observation.id)
            bucket["evidence_ids"].update(observation.evidence_ids)
            if contacted:
                bucket["contacted_observation_ids"].add(observation.id)

    for endpoint in endpoints:
        add(endpoint.url, endpoint.method, endpoint=endpoint)
    for observation in observations:
        if observation.kind not in ("http", "endpoint"):
            continue
        data = observation.data
        status = data.get("status_code")
        response = type(status) is int and 100 <= status <= 599
        if observation.source == "native_common_files":
            add(data.get("requested_url"), observation=observation)
            add(data.get("final_url"), observation=observation, contacted=response)
            redirects = data.get("redirects", [])
            discovered = data.get("discovered_urls", [])
            if not isinstance(redirects, list) or not isinstance(discovered, list):
                raise ValueError("Malformed common-file discovery")
            for redirect in redirects:
                if not isinstance(redirect, dict):
                    raise ValueError("Malformed common-file redirect")
                code = redirect.get("status_code")
                add(
                    redirect.get("url"),
                    observation=observation,
                    contacted=type(code) is int and 100 <= code <= 599,
                )
            for url in discovered:
                add(url, observation=observation)
        elif "url" in data:
            contacted = response and (
                observation.source in ("httpx", "feroxbuster", "ffuf")
                or observation.source == "katana"
                and data.get("contacted") is True
            )
            variant = None
            if observation.source == "ffuf":
                if (
                    data.get("profile") != "vhost_names"
                    or "candidate_value" not in data
                ):
                    raise ValueError("Unsupported FFUF request identity")
                variant = data["candidate_value"]
            add(
                data["url"],
                data.get("method", "GET"),
                observation=observation,
                contacted=contacted,
                host_header=variant,
            )
    return tuple(
        WebAssetDiscovery(
            identity=identities[key],
            **{name: tuple(sorted(values)) for name, values in refs[key].items()},
        )
        for key in sorted(identities)
    )

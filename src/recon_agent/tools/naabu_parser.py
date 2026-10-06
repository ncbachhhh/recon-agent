"""Bounded untrusted JSONL to generic open TCP facts, without service inference."""

import json
from hashlib import sha256
from ipaddress import ip_address
from typing import Literal

from recon_agent.core.errors import ParserError
from recon_agent.domain import Asset, Evidence, Host, Observation, Service
from recon_agent.tools.naabu_models import (
    ContactBinding,
    NaabuContext,
    NaabuLine,
    PortDiscoveryOutput,
)


def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def parse(
    raw: bytes, addresses: tuple[str, ...], ports: tuple[int, ...]
) -> tuple[tuple[tuple[str, int], ...], int]:
    lines = raw.splitlines()
    if len(lines) > 8192:
        raise ValueError("line count bound")
    facts: set[tuple[str, int]] = set()
    malformed = 0
    for line in lines:
        if not line.strip():
            continue
        try:
            if len(line) > 4096:
                raise ValueError("line size bound")
            obj = json.loads(line.decode("utf-8"), object_pairs_hook=_unique)
            if not isinstance(obj, dict) or len(obj) > 16:
                raise ValueError("object bound")
            record = NaabuLine.model_validate(
                {k: v for k, v in obj.items() if k in NaabuLine.model_fields}
            )
            address = str(ip_address(record.ip))
            if (
                address != record.ip
                or address not in addresses
                or record.port not in ports
                or record.host not in (None, address)
            ):
                raise ValueError("unrequested discovery")
            facts.add((address, record.port))
        except (ValueError, TypeError, AttributeError, RecursionError):
            malformed += 1
    if malformed and not facts:
        raise ValueError("no valid port records")
    return tuple(sorted(facts)), malformed


def normalize(
    facts: tuple[tuple[str, int], ...],
    malformed: int,
    candidates: tuple[str, ...],
    bindings: tuple[ContactBinding, ...],
    addresses: tuple[str, ...],
    ports: tuple[int, ...],
    root: str,
    context: NaabuContext,
) -> PortDiscoveryOutput:
    status: Literal["partial", "completed"] = "partial" if malformed else "completed"
    snapshot = json.dumps(
        dict(
            query_target=root,
            candidates=candidates,
            bindings=[b.model_dump(mode="json") for b in bindings],
            contact_addresses=addresses,
            ports=ports,
            source_version="2.3.5",
            facts=facts,
            malformed_lines=malformed,
            status=status,
        ),
        sort_keys=True,
        separators=(",", ":"),
    )
    evidence_id = f"{context.execution_id}:naabu:evidence"
    observations = tuple(
        Observation(
            id=f"{context.execution_id}:naabu:observation:{index}",
            kind="service",
            asset_id=context.asset_id,
            source="naabu",
            data={
                "host": address,
                "port": port,
                "transport": "tcp",
                "state": "open",
                "capability": "discover_ports",
                "source_version": "2.3.5",
                "candidate_references": [
                    b.hostname for b in bindings if address in b.addresses
                ],
            },
            observed_at=context.collected_at,
            execution_id=context.execution_id,
            evidence_ids=(evidence_id,),
        )
        for index, (address, port) in enumerate(facts)
    )
    host_ids = {
        address: f"{context.execution_id}:naabu:host:{index}"
        for index, address in enumerate(sorted({a for a, _ in facts}))
    }
    hosts = tuple(
        Host(
            id=host_id,
            asset_id=context.asset_id,
            value=address,
            addresses=(address,),
            observation_ids=tuple(
                observations[i].id for i, (a, _) in enumerate(facts) if a == address
            ),
        )
        for address, host_id in host_ids.items()
    )
    services = tuple(
        Service(
            id=f"{context.execution_id}:naabu:service:{index}",
            asset_id=context.asset_id,
            host_id=host_ids[address],
            port=port,
            transport="tcp",
            observation_ids=(observations[index].id,),
        )
        for index, (address, port) in enumerate(facts)
    )
    return PortDiscoveryOutput(
        query_target=root,
        candidates=candidates,
        bindings=bindings,
        contact_addresses=addresses,
        ports=ports,
        status=status,
        malformed_lines=malformed,
        errors=(ParserError("Partial Naabu output; malformed lines").to_error_info(),)
        if malformed
        else (),
        asset=Asset(
            id=context.asset_id,
            kind="host",
            value=root,
            observation_ids=tuple(o.id for o in observations),
        ),
        hosts=hosts,
        services=services,
        observations=observations,
        evidence=(
            Evidence(
                id=evidence_id,
                source="naabu",
                capability="discover_ports",
                origin=root,
                artifact_reference=f"memory:{context.execution_id}",
                locator="open-tcp-ports",
                collected_at=context.collected_at,
                execution_id=context.execution_id,
                sha256=sha256(snapshot.encode()).hexdigest(),
            ),
        ),
    )

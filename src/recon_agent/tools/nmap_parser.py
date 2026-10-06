"""Bounded local XML parsing; remote metadata is data and grants no authority."""

import json
import re
from hashlib import sha256
from xml.etree import ElementTree as ET

from recon_agent.core.errors import ParserError
from recon_agent.domain import Asset, Evidence, Host, Observation, Service
from recon_agent.tools.nmap_models import (
    NmapContext,
    NmapPort,
    ServiceFingerprintOutput,
)


def parse(
    raw: bytes, address: str, ports: tuple[int, ...]
) -> tuple[tuple[NmapPort, ...], tuple[int, ...]]:
    # Nmap emits this harmless declaration. No internal subset, entity, external
    # DTD, alternate encoding or external-resource lookup is accepted.
    if len(raw) > 1_048_576:
        raise ValueError("XML byte bound")
    text = raw.decode("utf-8")
    if not text.strip():
        return (), ports
    text = text.replace("<!DOCTYPE nmaprun>", "")
    if "<!" in text.replace("<!--", "") or re.search(
        r"<\?xml[^?]*encoding\s*=\s*['\"](?!UTF-8['\"]|utf-8['\"])", text
    ):
        raise ValueError("unsupported XML declaration")
    try:
        root = ET.fromstring(text)
    except ET.ParseError as cause:
        raise ValueError("malformed XML") from cause
    pending = [(root, 0)]
    count = 0
    while pending:
        node, depth = pending.pop()
        count += 1
        if (
            count > 8192
            or depth > 12
            or len(node.attrib) > 32
            or any(len(v) > 4096 for v in node.attrib.values())
            or len(node.text or "") > 4096
        ):
            raise ValueError("XML structure bound")
        if node.tag in (
            "script",
            "hostscript",
            "prescript",
            "postscript",
            "os",
            "trace",
        ):
            raise ValueError("unexpected scan mode output")
        pending.extend((child, depth + 1) for child in node)
    if (
        root.tag != "nmaprun"
        or root.get("scanner") != "nmap"
        or root.get("version") != "7.95"
    ):
        raise ValueError("unsupported XML envelope")
    finished = root.findall("runstats/finished")
    if len(finished) != 1 or finished[0].get("exit") != "success":
        raise ValueError("incomplete Nmap run")
    hosts = root.findall("host")
    if len(hosts) > 1:
        raise ValueError("unrequested hosts")
    facts: dict[int, NmapPort] = {}
    for host in hosts:
        addresses = [
            a for a in host.findall("address") if a.get("addrtype") in ("ipv4", "ipv6")
        ]
        if len(addresses) != 1 or addresses[0].get("addr") != address:
            raise ValueError("unrequested address")
        for node in host.findall("ports/port"):
            port_text = node.get("portid", "")
            if not port_text.isascii() or not port_text.isdecimal():
                raise ValueError("invalid port")
            port = int(port_text)
            if node.get("protocol") != "tcp" or port not in ports:
                raise ValueError("unrequested port or transport")
            states = node.findall("state")
            services = node.findall("service")
            if len(states) != 1 or len(services) > 1:
                raise ValueError("ambiguous port metadata")
            values: dict[str, object] = dict(port=port, state=states[0].get("state"))
            if services:
                service = services[0]
                for key, name in (
                    ("name", "name"),
                    ("product", "product"),
                    ("version", "version"),
                    ("extrainfo", "extra_info"),
                    ("servicefp", "service_fingerprint"),
                    ("tunnel", "tunnel"),
                    ("method", "method"),
                ):
                    value = service.get(key)
                    if value is not None and value.strip():
                        values[name] = value
                confidence = service.get("conf")
                if confidence is not None:
                    if not confidence.isascii() or not confidence.isdecimal():
                        raise ValueError("invalid confidence")
                    values["confidence"] = int(confidence)
                if len(service.findall("cpe")) > 16:
                    raise ValueError("CPE count bound")
                values["cpes"] = tuple(
                    sorted(
                        {
                            c.text
                            for c in service.findall("cpe")
                            if c.text and c.text.strip()
                        }
                    )
                )
            fact = NmapPort.model_validate(values)
            if port in facts and facts[port] != fact:
                raise ValueError("conflicting port records")
            facts[port] = fact
    return tuple(facts[p] for p in sorted(facts)), tuple(
        p for p in ports if p not in facts
    )


def normalize(
    facts: tuple[NmapPort, ...],
    unreported: tuple[int, ...],
    address: str,
    ports: tuple[int, ...],
    root: str,
    context: NmapContext,
    discovery_ids: tuple[str, ...],
) -> ServiceFingerprintOutput:
    evidence_id = f"{context.execution_id}:nmap:evidence"
    host_id = f"{context.execution_id}:nmap:host"
    snapshot = json.dumps(
        dict(
            query_target=root,
            contact_address=address,
            ports=ports,
            facts=[f.model_dump(mode="json") for f in facts],
            unreported_ports=unreported,
            discovery_evidence_ids=discovery_ids,
            source_version="7.95",
        ),
        sort_keys=True,
        separators=(",", ":"),
    )
    observations = tuple(
        Observation(
            id=f"{context.execution_id}:nmap:observation:{i}",
            kind="service",
            asset_id=context.asset_id,
            source="nmap",
            data={
                "host": address,
                "transport": "tcp",
                "capability": "fingerprint_services",
                "source_version": "7.95",
                "query_target": root,
                "discovery_evidence_ids": list(discovery_ids),
                **fact.model_dump(mode="json", exclude_none=True),
            },
            observed_at=context.collected_at,
            execution_id=context.execution_id,
            evidence_ids=(evidence_id,),
        )
        for i, fact in enumerate(facts)
    )
    services = tuple(
        Service(
            id=f"{context.execution_id}:nmap:service:{i}",
            asset_id=context.asset_id,
            host_id=host_id,
            port=fact.port,
            transport="tcp",
            protocol=fact.name,
            product=fact.product,
            version=fact.version,
            observation_ids=(observations[i].id,),
        )
        for i, fact in enumerate(facts)
        if fact.state == "open"
    )
    return ServiceFingerprintOutput(
        query_target=root,
        contact_address=address,
        ports=ports,
        discovery_evidence_ids=discovery_ids,
        status="partial" if unreported else "completed",
        unreported_ports=unreported,
        errors=(
            ParserError("Nmap did not report every requested port").to_error_info(),
        )
        if unreported
        else (),
        asset=Asset(
            id=context.asset_id,
            kind="host",
            value=root,
            observation_ids=tuple(o.id for o in observations),
        ),
        hosts=(
            Host(
                id=host_id,
                asset_id=context.asset_id,
                value=address,
                addresses=(address,),
                observation_ids=tuple(o.id for o in observations),
            ),
        )
        if facts
        else (),
        services=services,
        observations=observations,
        evidence=(
            Evidence(
                id=evidence_id,
                source="nmap",
                capability="fingerprint_services",
                origin=root,
                artifact_reference=f"memory:{context.execution_id}",
                locator="tcp-service-fingerprints",
                collected_at=context.collected_at,
                execution_id=context.execution_id,
                sha256=sha256(snapshot.encode()).hexdigest(),
            ),
        ),
    )

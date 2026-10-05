"""Operational resolve_dns adapter: current policy, scope, resources, then facts."""

import asyncio
from dataclasses import dataclass, field
from hashlib import sha256
from ipaddress import ip_address

import dns.exception
import dns.flags
import dns.message
import dns.name
import dns.query
import dns.rcode
import dns.rdataclass
import dns.rdatatype
from dns.rdtypes.ANY.CNAME import CNAME
from dns.rdtypes.ANY.MX import MX
from dns.rdtypes.ANY.NS import NS
from dns.rdtypes.ANY.TXT import TXT
from dns.rdtypes.IN.A import A
from dns.rdtypes.IN.AAAA import AAAA
from pydantic import JsonValue

from recon_agent.core.config.models import ExecutionConfig
from recon_agent.core.errors import (
    ConfigurationError,
    ParserError,
    PlannerValidationError,
    ToolExecutionError,
    ToolTimeoutError,
)
from recon_agent.core.results import Failure, OperationResult, Success
from recon_agent.domain import ActionRequest, Asset, Evidence, Observation, Target
from recon_agent.domain.budgets import ReservationOutcome
from recon_agent.domain.capabilities import (
    CapabilityDescriptor,
    CapabilityId,
    RiskClass,
)
from recon_agent.policy.actions import ActionPolicyValidator
from recon_agent.policy.budgets import BudgetController
from recon_agent.tools.base import AdapterDefinition, ToolAdapter
from recon_agent.tools.dns_models import (
    DnsContext,
    DnsInput,
    DnsOutput,
    DnsQueryResult,
    DnsRecord,
    DnsRecordType,
)
from recon_agent.tools.native_dns import DnsResolver, NativeDnsResolver


def _invalid(message: str) -> Failure:
    return Failure(error=PlannerValidationError(message).to_error_info())


def _name(value: dns.name.Name) -> str:
    # Canonical presentation preserves arbitrary DNS names as remote evidence;
    # it does not promote them to ScopeValidator-compatible executable targets.
    return value.canonicalize().to_text(omit_final_dot=True) or "."


def _records(
    query: dns.message.Message,
    response: dns.message.Message,
    target: str,
    record_type: DnsRecordType,
) -> DnsQueryResult:
    if (
        not isinstance(response, dns.message.Message)
        or not query.is_response(response)
        or response.flags & dns.flags.TC
        or response.opcode() != query.opcode()
    ):
        raise ValueError("invalid response envelope")
    rcode = response.rcode()
    if rcode not in (dns.rcode.NOERROR, dns.rcode.NXDOMAIN):
        raise ToolExecutionError("DNS resolver returned an unsuccessful response")
    records: dict[str, DnsRecord] = {}
    count = 0
    for rrset in response.answer:
        if rrset.rdclass != dns.rdataclass.IN or rrset.rdtype not in (
            dns.rdatatype.from_text(record_type),
            dns.rdatatype.CNAME,
        ):
            raise ValueError("unexpected answer type")
        if rcode == dns.rcode.NXDOMAIN and rrset.rdtype != dns.rdatatype.CNAME:
            raise ValueError("NXDOMAIN with contradictory answers")
        for item in rrset:
            count += 1
            if count > 256:
                raise ValueError("DNS record bound exceeded")
            preference = None
            chunks: tuple[str, ...] = ()
            if isinstance(item, (A, AAAA)):
                value = str(ip_address(item.address))
            elif isinstance(item, (CNAME, NS)):
                value = _name(item.target)
            elif isinstance(item, MX):
                value = _name(item.exchange)
                preference = item.preference
            elif isinstance(item, TXT):
                chunks = tuple(chunk.hex() for chunk in item.strings)
                # JSON-escaped DNS presentation is data only; chunks preserve bytes.
                value = item.to_text()
            else:
                raise ValueError("unsupported record")
            record = DnsRecord(
                owner=_name(rrset.name),
                record_type="CNAME"
                if item.rdtype == dns.rdatatype.CNAME
                else record_type,
                value=value,
                ttl=rrset.ttl,
                preference=preference,
                txt_chunks_hex=chunks,
            )
            records[record.model_dump_json()] = record
    return DnsQueryResult(
        query_target=target,
        record_type=record_type,
        outcome=(
            "nxdomain"
            if rcode == dns.rcode.NXDOMAIN
            else "answer"
            if records
            else "no_answer"
        ),
        records=tuple(records[key] for key in sorted(records)),
    )


def _normalize(
    queries: tuple[DnsQueryResult, ...], context: DnsContext, nameserver: str
) -> DnsOutput:
    observations: list[Observation] = []
    evidence: list[Evidence] = []
    for index, query in enumerate(queries):
        evidence_id = f"{context.execution_id}:dns:evidence:{index}"
        evidence.append(
            Evidence(
                id=evidence_id,
                source="native_dns",
                capability="resolve_dns",
                origin=query.query_target,
                artifact_reference=f"memory:{context.execution_id}",
                locator=f"queries/{index}",
                collected_at=context.collected_at,
                execution_id=context.execution_id,
                sha256=sha256(query.model_dump_json().encode()).hexdigest(),
            )
        )
        # A status observation also preserves negative answers with provenance.
        for record_index, record in enumerate(query.records or (None,)):
            data: dict[str, JsonValue] = {
                "query_target": query.query_target,
                "query_type": query.record_type,
                "outcome": query.outcome,
            }
            if record is not None:
                data.update(record.model_dump(mode="json"))
            observations.append(
                Observation(
                    id=f"{context.execution_id}:dns:observation:{index}:{record_index}",
                    kind="dns",
                    asset_id=context.asset_id,
                    source="native_dns",
                    data=data,
                    observed_at=context.collected_at,
                    evidence_ids=(evidence_id,),
                    execution_id=context.execution_id,
                )
            )
    return DnsOutput(
        resolver_address=nameserver,
        queries=queries,
        asset=Asset(
            id=context.asset_id,
            kind="host",
            value=queries[0].query_target,
            observation_ids=tuple(item.id for item in observations),
        ),
        observations=tuple(observations),
        evidence=tuple(evidence),
    )


@dataclass(frozen=True, slots=True)
class DnsAdapter(ToolAdapter):
    """Explicit trusted composition; no default registry or runtime startup.

    Caller obtains this adapter through ToolRegistry.resolve. execute rechecks that
    binding and current action policy, never accepts an ApprovedAction as authority.
    Resolver endpoint is operator-supplied numeric infrastructure and independently
    scope checked. Fake resolver injection is trusted code, never a planner field.
    """

    nameserver: str
    config: ExecutionConfig = field(repr=False)
    resolver: DnsResolver = field(default_factory=NativeDnsResolver, repr=False)
    _timeout: float = field(init=False, repr=False)
    _output_limit: int = field(init=False, repr=False)

    def __post_init__(self) -> None:
        try:
            endpoint = ip_address(self.nameserver)
            if "%" in self.nameserver or getattr(endpoint, "ipv4_mapped", None):
                raise ValueError("unsupported endpoint")
            snapshot = ExecutionConfig.model_validate(self.config.model_dump())
        except (ValueError, TypeError, AttributeError) as cause:
            raise ConfigurationError("Invalid trusted DNS adapter settings") from cause
        object.__setattr__(self, "nameserver", str(endpoint))
        object.__setattr__(self, "_timeout", snapshot.default_timeout_seconds)
        object.__setattr__(self, "_output_limit", snapshot.max_output_bytes)

    @property
    def definition(self) -> AdapterDefinition:
        return AdapterDefinition(
            adapter_id="native_dns",
            descriptor=CapabilityDescriptor(
                capability=CapabilityId.RESOLVE_DNS,
                description="Resolve authorized DNS names into bounded DNS evidence",
                risk_class=RiskClass.ACTIVE_SAFE,
            ),
            input_schema=DnsInput,
            output_schema=DnsOutput,
            parameter_target_fields=(),
        )

    async def execute(
        self,
        request: ActionRequest,
        *,
        policy: ActionPolicyValidator,
        budgets: BudgetController,
        context: DnsContext,
    ) -> OperationResult[DnsOutput]:
        try:
            request = ActionRequest.model_validate(request)
            context = DnsContext.model_validate(context)
        except (ValueError, TypeError):
            return _invalid("Malformed DNS request or context")
        if (
            request.capability != CapabilityId.RESOLVE_DNS
            or policy.budget_eligibility is not budgets
            or request.asset_id not in (None, context.asset_id)
        ):
            return _invalid("DNS execution composition does not match request")
        selected = policy.registry.resolve(request.capability)
        if isinstance(selected, Failure):
            return selected
        if selected.value is not self:
            return _invalid("DNS adapter is not the registered capability binding")
        approved = policy.validate(request)
        if isinstance(approved, Failure):
            return approved
        target = approved.value.scope_match.canonical_target
        if target.kind not in ("domain", "hostname"):
            return _invalid("DNS resolution requires a hostname target")
        # Resolver infrastructure needs explicit IP/CIDR scope too; no system DNS.
        endpoint = policy.scope_validator.validate(
            Target(id="dns-resolver", kind="ip", value=self.nameserver)
        )
        if isinstance(endpoint, Failure):
            return endpoint
        parameters = DnsInput.model_validate(approved.value.parameters)
        reserved = budgets.reserve(
            approved.value.model_copy(
                update={"parameter_scope_matches": (endpoint.value,)}
            )
        )
        if isinstance(reserved, Failure):
            return reserved
        with reserved.value as permit:
            timeout = min(self._timeout, budgets.state.remaining_seconds)
            if timeout <= 0:
                permit.release(ReservationOutcome.TIMEOUT)
                return Failure(
                    error=ToolTimeoutError(
                        "DNS execution deadline reached"
                    ).to_error_info()
                )
            try:
                async with asyncio.timeout(timeout):
                    queries: list[DnsQueryResult] = []
                    for record_type in parameters.record_types:
                        # Check each actual query afresh; no discovered name is queried.
                        scoped = policy.scope_validator.validate(target)
                        if isinstance(scoped, Failure):
                            permit.release(ReservationOutcome.ABORTED)
                            return scoped
                        resolver_scope = policy.scope_validator.validate(
                            Target(id="dns-resolver", kind="ip", value=self.nameserver)
                        )
                        if isinstance(resolver_scope, Failure):
                            permit.release(ReservationOutcome.ABORTED)
                            return resolver_scope
                        remaining = min(timeout, budgets.state.remaining_seconds)
                        if remaining <= 0:
                            raise TimeoutError
                        query = dns.message.make_query(
                            target.value + ".", record_type, use_edns=0, payload=1232
                        )
                        response = await self.resolver.exchange(
                            query, self.nameserver, remaining
                        )
                        if budgets.state.remaining_seconds <= 0:
                            raise TimeoutError
                        queries.append(
                            _records(query, response, target.value, record_type)
                        )
                        if sum(len(item.records) for item in queries) > 256:
                            raise ValueError("DNS action record bound exceeded")
                    output = _normalize(tuple(queries), context, self.nameserver)
                    if len(output.model_dump_json().encode()) > min(
                        self._output_limit, budgets.limits.max_output_bytes
                    ):
                        raise ValueError("DNS normalized output bound exceeded")
                    permit.release(ReservationOutcome.COMPLETED)
                    return Success[DnsOutput](value=output)
            except (TimeoutError, dns.exception.Timeout):
                permit.release(ReservationOutcome.TIMEOUT)
                return Failure(
                    error=ToolTimeoutError(
                        "DNS execution deadline reached"
                    ).to_error_info()
                )
            except ToolExecutionError as error:
                permit.release(ReservationOutcome.FAILED)
                return Failure(error=error.to_error_info())
            except (OSError, dns.query.UnexpectedSource):
                permit.release(ReservationOutcome.FAILED)
                return Failure(
                    error=ToolExecutionError(
                        "DNS resolver exchange failed"
                    ).to_error_info()
                )
            except (ValueError, TypeError, AttributeError, dns.exception.DNSException):
                permit.release(ReservationOutcome.FAILED)
                return Failure(
                    error=ParserError(
                        "Malformed or oversized DNS response"
                    ).to_error_info()
                )

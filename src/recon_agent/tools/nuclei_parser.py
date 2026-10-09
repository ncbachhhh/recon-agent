"""Bounded offline ResultEvent ingestion; no contact, paths or commands are used."""

import base64
import json
from hashlib import sha256
from typing import Literal
from urllib.parse import urlsplit

from recon_agent.core.errors import ErrorContext, ParserError, ToolExecutionError
from recon_agent.core.results import Failure, OperationResult, Success
from recon_agent.domain import Evidence, Observation
from recon_agent.execution import ProcessExecution
from recon_agent.policy.scope import ScopeValidator
from recon_agent.tools.nuclei_models import (
    NucleiCandidate,
    NucleiContext,
    NucleiEvent,
    NucleiInfo,
    NucleiOutput,
)

MAX_BYTES = 1_048_576
MAX_LINES = 256
MAX_LINE_BYTES = 65_536


def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _constant(value: str) -> None:
    raise ValueError("non-finite JSON")


def ingest(
    result: OperationResult[ProcessExecution],
    *,
    context: NucleiContext,
    scope: ScopeValidator,
    output_limit: int = MAX_BYTES,
) -> OperationResult[NucleiOutput]:
    """Interpret captured bytes only. No scan approval or Finding creation.

    No data accompanies runner Failure (including timeout); preserve that failure.
    Valid records from bounded nonzero/truncated captures remain explicitly partial.
    Invalid records remain in stream evidence but never become candidates.
    """
    if isinstance(result, Failure):
        return Failure.model_validate(result)
    try:
        context = NucleiContext.model_validate(context)
        process = ProcessExecution.model_validate(result.value)
        if type(output_limit) is not int or output_limit < 1:
            raise ValueError("invalid bound")
        limit = min(output_limit, MAX_BYTES)
        if len(process.stdout) > limit or len(process.stderr) > limit:
            raise ValueError("stream bound")
        lines = process.stdout.splitlines()
        if len(lines) > MAX_LINES:
            raise ValueError("line count bound")
    except (ValueError, TypeError, AttributeError):
        return Failure(
            error=ParserError("Invalid or oversized Nuclei capture").to_error_info()
        )
    checked = scope.validate_value(context.query_target)
    if isinstance(checked, Failure):
        return checked

    def host(value: str) -> str:
        if "://" in value:
            return urlsplit(value).hostname or value
        return value

    query_host = host(checked.value.canonical_target.value)

    stdout_id = f"{context.execution_id}:nuclei:stdout"
    evidence = tuple(
        Evidence(
            id=f"{context.execution_id}:nuclei:{stream}",
            source="nuclei",
            capability="scan_templates",
            origin=context.query_target,
            artifact_reference=f"memory:{context.execution_id}:nuclei:{stream}",
            locator=f"{stream}_base64; untrusted retained scanner output",
            sha256=sha256(raw).hexdigest(),
            collected_at=context.collected_at,
            execution_id=context.execution_id,
            truncated=truncated,
        )
        for stream, raw, truncated in (
            ("stdout", process.stdout, process.stdout_truncated),
            ("stderr", process.stderr, process.stderr_truncated),
        )
    )
    candidates: list[NucleiCandidate] = []
    observations: list[Observation] = []
    malformed = 0
    for number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            # A truncated terminal line may be syntactically complete by accident.
            if (
                process.stdout_truncated
                and number == len(lines)
                and not process.stdout.endswith(b"\n")
            ):
                raise ValueError("incomplete terminal record")
            if len(line) > MAX_LINE_BYTES:
                raise ValueError("record bound")
            obj = json.loads(
                line.decode("utf-8"),
                object_pairs_hook=_unique,
                parse_constant=_constant,
            )
            if not isinstance(obj, dict) or len(obj) > 128:
                raise ValueError("object bound")
            if obj.get("matcher-status") is not True or obj.get("error", "") != "":
                raise ValueError("unsuccessful or ambiguous match")
            info = obj.get("info")
            if not isinstance(info, dict) or len(info) > 64:
                raise ValueError("info bound")
            selected = {
                field.alias or name: obj[field.alias or name]
                for name, field in NucleiEvent.model_fields.items()
                if (field.alias or name) in obj
            }
            selected["info"] = {
                k: v for k, v in info.items() if k in NucleiInfo.model_fields
            }
            event = NucleiEvent.model_validate(selected)
            # Reported locations and addresses get independent centralized checks.
            # Scope membership is not proof that a process was authorized to contact.
            for value in (event.host, event.matched_at, event.url):
                if value is not None:
                    match = scope.validate_value(value)
                    if isinstance(match, Failure):
                        raise ValueError("unsupported or out-of-scope reported target")
                    if host(match.value.canonical_target.value) != query_host:
                        raise ValueError("reported subject mismatch")
            if event.ip is not None:
                address = scope.validate_value(event.ip)
                if (
                    isinstance(address, Failure)
                    or address.value.canonical_target.kind != "ip"
                ):
                    raise ValueError("unsupported or out-of-scope reported address")
            candidate = NucleiCandidate(
                execution_id=context.execution_id,
                observation_id=f"{context.execution_id}:nuclei:observation:{number}",
                evidence_ids=(stdout_id,),
                source_line=number,
                record_sha256=sha256(line).hexdigest(),
                reported=event,
            )
            observations.append(
                Observation(
                    id=candidate.observation_id,
                    kind="metadata",
                    asset_id=context.asset_id,
                    source="nuclei",
                    data=candidate.model_dump(mode="json"),
                    observed_at=context.collected_at,
                    execution_id=context.execution_id,
                    evidence_ids=candidate.evidence_ids,
                )
            )
            candidates.append(candidate)
        except (ValueError, TypeError, AttributeError, RecursionError):
            malformed += 1

    errors = []
    if process.return_code != 0:
        errors.append(
            ToolExecutionError(
                "Nuclei capture reports non-zero exit",
                context=ErrorContext(tool="nuclei", exit_code=process.return_code),
            ).to_error_info()
        )
    if malformed or process.stdout_truncated or process.stderr_truncated:
        errors.append(
            ParserError("Incomplete or invalid Nuclei captured output").to_error_info()
        )
    status: Literal["completed", "partial", "failed"] = (
        "completed" if not errors else ("partial" if candidates else "failed")
    )
    return Success[NucleiOutput](
        value=NucleiOutput(
            query_target=context.query_target,
            scanner_version=context.scanner_version,
            status=status,
            malformed_lines=malformed,
            errors=tuple(errors),
            candidates=tuple(candidates),
            observations=tuple(observations),
            evidence=evidence,
            stdout_base64=base64.b64encode(process.stdout).decode("ascii"),
            stderr_base64=base64.b64encode(process.stderr).decode("ascii"),
        )
    )

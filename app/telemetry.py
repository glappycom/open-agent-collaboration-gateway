from __future__ import annotations

from .config import settings
from .db import log_telemetry
from .providers import CallResult
from .schemas import Provider


def estimate_cost_usd(provider: Provider, result: CallResult) -> float | None:
    if result.input_tokens is None and result.output_tokens is None:
        return None

    if provider == Provider.openai:
        input_rate = settings.openai_input_cost_per_million
        output_rate = settings.openai_output_cost_per_million
    else:
        input_rate = settings.xai_input_cost_per_million
        output_rate = settings.xai_output_cost_per_million

    if input_rate <= 0 and output_rate <= 0:
        return None

    input_cost = ((result.input_tokens or 0) / 1_000_000) * input_rate
    output_cost = ((result.output_tokens or 0) / 1_000_000) * output_rate
    return round(input_cost + output_cost, 10)


def result_metadata(provider: Provider, result: CallResult) -> dict:
    return {
        "input_tokens": result.input_tokens,
        "output_tokens": result.output_tokens,
        "total_tokens": result.total_tokens,
        "retry_count": max(0, result.attempts - 1),
        "estimated_cost_usd": estimate_cost_usd(provider, result),
    }


def record_provider_result(
    *,
    trace_id: str,
    conversation_id: str,
    provider: Provider,
    result: CallResult,
    turn: int | None = None,
    kind: str = "provider_response",
) -> dict:
    metadata = result_metadata(provider, result)
    log_telemetry(
        trace_id=trace_id,
        conversation_id=conversation_id,
        event_type=kind,
        provider=provider.value,
        model=result.model,
        latency_ms=result.latency_ms,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        total_tokens=result.total_tokens,
        retry_count=metadata["retry_count"],
        estimated_cost_usd=metadata["estimated_cost_usd"],
        metadata={"turn": turn} if turn is not None else {},
    )
    return metadata


def record_trace_event(
    *,
    trace_id: str,
    conversation_id: str,
    event_type: str,
    metadata: dict | None = None,
) -> None:
    log_telemetry(
        trace_id=trace_id,
        conversation_id=conversation_id,
        event_type=event_type,
        metadata=metadata or {},
    )

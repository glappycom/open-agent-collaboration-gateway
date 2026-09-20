import uuid
from datetime import datetime, timedelta, timezone

from .config import settings
from .controls import HostControlError, controlled_call, redact_text
from .db import load_messages, log_message
from .protocol import MessageKind, BrokerEnvelope, new_envelope
from .schemas import Provider, RiskLevel, CollaborateRequest, MessageOut, GatewayResponse

RISK_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}


def _approval_required(risk: RiskLevel, approved: bool) -> bool:
    threshold = RISK_ORDER.get(settings.approval_risk_level.lower(), 2)
    return RISK_ORDER[risk.value] >= threshold and not approved


def _validate_text(label: str, value: str | None) -> None:
    if value and len(value) > settings.max_prompt_chars:
        raise ValueError(
            f"{label} exceeds MAX_PROMPT_CHARS ({settings.max_prompt_chars}). "
            "Use a retrieval/memory layer rather than sending unbounded context."
        )


def _history_text(conversation_id: str) -> str:
    rows = load_messages(conversation_id, limit=30)
    if not rows:
        return ""
    rendered = "\n".join(f"[{r['provider']}/{r['role']}] {r['content']}" for r in rows)
    return rendered[-settings.max_context_chars:]


def _deadline() -> datetime:
    return datetime.now(timezone.utc) + timedelta(seconds=settings.provider_timeout_seconds)


def _log_envelope(conversation_id: str, provider: str, role: str, envelope: BrokerEnvelope) -> None:
    safe_content = redact_text(envelope.content)
    safe_envelope = envelope.model_copy(update={"content": safe_content})
    log_message(
        conversation_id,
        provider,
        role,
        safe_content,
        {"broker_envelope": safe_envelope.model_dump(mode="json")},
    )


def _message_out(provider: Provider, turn: int, envelope: BrokerEnvelope) -> MessageOut:
    return MessageOut(
        provider=provider,
        content=envelope.content,
        turn=turn,
        model=envelope.model,
        latency_ms=envelope.latency_ms,
        schema_version=envelope.schema_version,
        trace_id=envelope.trace_id,
        message_id=envelope.message_id,
        sender=envelope.sender,
        recipient=envelope.recipient,
        sequence=envelope.sequence,
    )


def _enforce_collaboration_call_quota(turns: int) -> None:
    required_calls = turns + 1  # one provider call per turn plus final synthesis
    if required_calls > settings.max_provider_calls_per_request:
        raise HostControlError(
            f"collaboration requires {required_calls} provider calls but host quota allows "
            f"{settings.max_provider_calls_per_request}"
        )


def ask(
    provider: Provider,
    prompt: str,
    conversation_id: str | None,
    system_context: str | None,
    risk_level: RiskLevel,
    approved: bool,
) -> GatewayResponse:
    _validate_text("prompt", prompt)
    _validate_text("system_context", system_context)
    cid = conversation_id or str(uuid.uuid4())
    trace_id = str(uuid.uuid4())

    if _approval_required(risk_level, approved):
        return GatewayResponse(
            conversation_id=cid,
            trace_id=trace_id,
            status="approval_required",
            messages=[],
            approval_reason=f"Risk level '{risk_level.value}' requires explicit approval before an external model call.",
        )

    history = _history_text(cid)
    context = "\n\n".join(x for x in [system_context, history] if x)

    request_envelope = new_envelope(
        trace_id=trace_id,
        sender="host",
        recipient=provider.value,
        kind=MessageKind.request,
        sequence=1,
        content=prompt,
        deadline_at=_deadline(),
        metadata={"risk_level": risk_level.value},
    )
    _log_envelope(cid, provider.value, "broker_request", request_envelope)

    result = controlled_call(provider, prompt, context or None)

    response_envelope = new_envelope(
        trace_id=trace_id,
        sender=provider.value,
        recipient="host",
        kind=MessageKind.final_synthesis,
        sequence=2,
        content=result.text,
        model=result.model,
        latency_ms=result.latency_ms,
    )
    _log_envelope(cid, provider.value, "broker_response", response_envelope)

    return GatewayResponse(
        conversation_id=cid,
        trace_id=trace_id,
        status="completed",
        messages=[_message_out(provider, 1, response_envelope)],
        final=result.text,
        final_model=result.model,
        final_latency_ms=result.latency_ms,
        final_message_id=response_envelope.message_id,
        final_schema_version=response_envelope.schema_version,
    )


def collaborate(req: CollaborateRequest) -> GatewayResponse:
    _validate_text("task", req.task)
    _validate_text("shared_context", req.shared_context)
    cid = req.conversation_id or str(uuid.uuid4())
    trace_id = str(uuid.uuid4())

    if _approval_required(req.risk_level, req.approved):
        return GatewayResponse(
            conversation_id=cid,
            trace_id=trace_id,
            status="approval_required",
            messages=[],
            approval_reason=f"Risk level '{req.risk_level.value}' requires explicit approval before collaboration begins.",
        )

    turns = min(req.turns, settings.max_turns)
    _enforce_collaboration_call_quota(turns)

    current = req.starter
    transcript: list[MessageOut] = []
    shared = req.shared_context or ""
    sequence = 1

    mode_instruction = {
        "solve": "Work toward the best actionable solution. Challenge weak assumptions and add missing details.",
        "critique": "Critique the other model's work constructively. Identify errors, risks, and concrete improvements.",
        "architecture": "Act as a senior architecture reviewer. Prioritize modularity, security, observability, cost, and operability.",
    }[req.mode]

    last_output = ""
    for i in range(1, turns + 1):
        other = Provider.grok if current == Provider.openai else Provider.openai
        if i == 1:
            prompt = (
                f"COLLABORATION TASK:\n{req.task}\n\n"
                f"MODE:\n{mode_instruction}\n\n"
                "Produce your contribution for the other AI collaborator. Be concise but substantive."
            )
        else:
            prompt = (
                f"COLLABORATION TASK:\n{req.task}\n\n"
                f"MODE:\n{mode_instruction}\n\n"
                f"THE OTHER MODEL'S MOST RECENT CONTRIBUTION:\n{last_output}\n\n"
                "Respond to it, improve the solution, resolve disagreements with evidence/reasoning, and move toward a final recommendation."
            )

        history = _history_text(cid)
        system_context = (
            "You are participating in a bounded AI-to-AI collaboration gateway. "
            "All peer communication is mediated by the OACG host. "
            "Do not attempt to establish direct model-to-model channels or contact external systems unless explicitly provided as tools. "
            "Never reveal secrets. Do not create recursive delegation. "
            f"You are {current.value}; your counterpart is {other.value}.\n\n"
            f"SHARED CONTEXT:\n{shared}\n\n"
            f"PRIOR TRANSCRIPT:\n{history}"
        )[-settings.max_context_chars:]

        request_envelope = new_envelope(
            trace_id=trace_id,
            sender="host",
            recipient=current.value,
            kind=MessageKind.request,
            sequence=sequence,
            content=prompt,
            deadline_at=_deadline(),
            metadata={"turn": i, "mode": req.mode},
        )
        sequence += 1
        _log_envelope(cid, current.value, "broker_request", request_envelope)

        result = controlled_call(current, prompt, system_context)
        last_output = redact_text(result.text)

        response_envelope = new_envelope(
            trace_id=trace_id,
            sender=current.value,
            recipient="host",
            kind=MessageKind.contribution,
            sequence=sequence,
            content=result.text,
            model=result.model,
            latency_ms=result.latency_ms,
            metadata={"turn": i, "mode": req.mode},
        )
        sequence += 1
        _log_envelope(cid, current.value, "broker_response", response_envelope)

        transcript.append(_message_out(current, i, response_envelope))
        current = other

    final_provider = Provider.openai
    final_prompt = (
        "Synthesize the following bounded AI collaboration into one executive-quality answer.\n\n"
        f"TASK:\n{req.task}\n\n"
        "TRANSCRIPT:\n"
        + "\n\n".join(
            f"TURN {m.turn} - {m.provider.value.upper()}:\n{redact_text(m.content)}" for m in transcript
        )
        + "\n\nReturn: (1) agreed recommendation, (2) unresolved disagreements/uncertainties, "
        " (3) immediate next actions. Do not invent consensus."
    )
    final_context = (req.shared_context or "")[-settings.max_context_chars:]

    final_request = new_envelope(
        trace_id=trace_id,
        sender="host",
        recipient=final_provider.value,
        kind=MessageKind.request,
        sequence=sequence,
        content=final_prompt,
        deadline_at=_deadline(),
        metadata={"kind": "final_synthesis_request"},
    )
    sequence += 1
    _log_envelope(cid, final_provider.value, "broker_request", final_request)

    final_result = controlled_call(final_provider, final_prompt, final_context or None)

    final_envelope = new_envelope(
        trace_id=trace_id,
        sender=final_provider.value,
        recipient="host",
        kind=MessageKind.final_synthesis,
        sequence=sequence,
        content=final_result.text,
        model=final_result.model,
        latency_ms=final_result.latency_ms,
    )
    _log_envelope(cid, final_provider.value, "broker_response", final_envelope)

    return GatewayResponse(
        conversation_id=cid,
        trace_id=trace_id,
        status="completed",
        messages=transcript,
        final=final_result.text,
        final_model=final_result.model,
        final_latency_ms=final_result.latency_ms,
        final_message_id=final_envelope.message_id,
        final_schema_version=final_envelope.schema_version,
    )

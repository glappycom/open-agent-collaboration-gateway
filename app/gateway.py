import uuid

from .config import settings
from .db import load_messages, log_message
from .providers import call_model
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
    if _approval_required(risk_level, approved):
        return GatewayResponse(
            conversation_id=cid,
            status="approval_required",
            messages=[],
            approval_reason=f"Risk level '{risk_level.value}' requires explicit approval before an external model call.",
        )

    history = _history_text(cid)
    context = "\n\n".join(x for x in [system_context, history] if x)
    log_message(cid, provider.value, "user", prompt, {"risk_level": risk_level.value})
    result = call_model(provider, prompt, context or None)
    log_message(
        cid,
        provider.value,
        "assistant",
        result.text,
        {"model": result.model, "latency_ms": result.latency_ms},
    )
    return GatewayResponse(
        conversation_id=cid,
        status="completed",
        messages=[
            MessageOut(
                provider=provider,
                content=result.text,
                turn=1,
                model=result.model,
                latency_ms=result.latency_ms,
            )
        ],
        final=result.text,
        final_model=result.model,
        final_latency_ms=result.latency_ms,
    )


def collaborate(req: CollaborateRequest) -> GatewayResponse:
    _validate_text("task", req.task)
    _validate_text("shared_context", req.shared_context)
    cid = req.conversation_id or str(uuid.uuid4())
    if _approval_required(req.risk_level, req.approved):
        return GatewayResponse(
            conversation_id=cid,
            status="approval_required",
            messages=[],
            approval_reason=f"Risk level '{req.risk_level.value}' requires explicit approval before collaboration begins.",
        )

    turns = min(req.turns, settings.max_turns)
    current = req.starter
    transcript: list[MessageOut] = []
    shared = req.shared_context or ""

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
            "Do not attempt to contact external systems unless explicitly provided as tools. "
            "Never reveal secrets. Do not create recursive delegation. "
            f"You are {current.value}; your counterpart is {other.value}.\n\n"
            f"SHARED CONTEXT:\n{shared}\n\n"
            f"PRIOR TRANSCRIPT:\n{history}"
        )[-settings.max_context_chars:]

        log_message(cid, current.value, "user", prompt, {"turn": i, "mode": req.mode})
        result = call_model(current, prompt, system_context)
        last_output = result.text
        log_message(
            cid,
            current.value,
            "assistant",
            result.text,
            {"turn": i, "model": result.model, "latency_ms": result.latency_ms},
        )
        transcript.append(
            MessageOut(
                provider=current,
                content=result.text,
                turn=i,
                model=result.model,
                latency_ms=result.latency_ms,
            )
        )
        current = other

    final_provider = Provider.openai
    final_prompt = (
        "Synthesize the following bounded AI collaboration into one executive-quality answer.\n\n"
        f"TASK:\n{req.task}\n\n"
        "TRANSCRIPT:\n"
        + "\n\n".join(
            f"TURN {m.turn} - {m.provider.value.upper()}:\n{m.content}" for m in transcript
        )
        + "\n\nReturn: (1) agreed recommendation, (2) unresolved disagreements/uncertainties, "
        " (3) immediate next actions. Do not invent consensus."
    )
    final_context = (req.shared_context or "")[-settings.max_context_chars:]
    final_result = call_model(final_provider, final_prompt, final_context or None)
    log_message(
        cid,
        final_provider.value,
        "assistant",
        final_result.text,
        {"kind": "final_synthesis", "model": final_result.model, "latency_ms": final_result.latency_ms},
    )

    return GatewayResponse(
        conversation_id=cid,
        status="completed",
        messages=transcript,
        final=final_result.text,
        final_model=final_result.model,
        final_latency_ms=final_result.latency_ms,
    )

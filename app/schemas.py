from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class Provider(str, Enum):
    openai = "openai"
    grok = "grok"


class RiskLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class AskRequest(BaseModel):
    prompt: str = Field(min_length=1)
    provider: Provider
    conversation_id: str | None = None
    system_context: str | None = None
    risk_level: RiskLevel = RiskLevel.low
    approved: bool = False
    idempotency_key: str | None = Field(
        default=None,
        min_length=8,
        max_length=128,
        pattern=r"^[A-Za-z0-9._:-]+$",
    )


class CollaborateRequest(BaseModel):
    task: str = Field(min_length=1)
    starter: Provider = Provider.openai
    turns: int = Field(default=4, ge=1, le=12)
    conversation_id: str | None = None
    shared_context: str | None = None
    risk_level: RiskLevel = RiskLevel.low
    approved: bool = False
    mode: Literal["solve", "critique", "architecture"] = "solve"
    idempotency_key: str | None = Field(
        default=None,
        min_length=8,
        max_length=128,
        pattern=r"^[A-Za-z0-9._:-]+$",
    )


class MessageOut(BaseModel):
    provider: Provider
    content: str
    turn: int
    model: str | None = None
    latency_ms: int | None = None
    schema_version: str
    trace_id: str
    message_id: str
    sender: str
    recipient: str
    sequence: int
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    retry_count: int = 0
    estimated_cost_usd: float | None = None


class GatewayResponse(BaseModel):
    conversation_id: str
    trace_id: str
    status: Literal["completed", "approval_required"]
    messages: list[MessageOut]
    final: str | None = None
    final_model: str | None = None
    final_latency_ms: int | None = None
    final_message_id: str | None = None
    final_schema_version: str | None = None
    final_input_tokens: int | None = None
    final_output_tokens: int | None = None
    final_total_tokens: int | None = None
    final_retry_count: int = 0
    final_estimated_cost_usd: float | None = None
    approval_reason: str | None = None

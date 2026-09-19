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


class CollaborateRequest(BaseModel):
    task: str = Field(min_length=1)
    starter: Provider = Provider.openai
    turns: int = Field(default=4, ge=1, le=12)
    conversation_id: str | None = None
    shared_context: str | None = None
    risk_level: RiskLevel = RiskLevel.low
    approved: bool = False
    mode: Literal["solve", "critique", "architecture"] = "solve"


class MessageOut(BaseModel):
    provider: Provider
    content: str
    turn: int
    model: str | None = None
    latency_ms: int | None = None


class GatewayResponse(BaseModel):
    conversation_id: str
    status: Literal["completed", "approval_required"]
    messages: list[MessageOut]
    final: str | None = None
    final_model: str | None = None
    final_latency_ms: int | None = None
    approval_reason: str | None = None

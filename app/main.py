from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from .config import settings
from .db import init_db, load_messages
from .gateway import ask, collaborate
from .providers import ProviderError, provider_configs
from .schemas import AskRequest, CollaborateRequest, GatewayResponse


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "A small, provider-aware gateway for bounded collaboration between heterogeneous AI systems. "
        "v0.1 ships with OpenAI and xAI/Grok adapters."
    ),
    lifespan=lifespan,
)


@app.get("/health")
def health():
    return {"status": "ok", "version": settings.app_version}


@app.get("/providers")
def providers():
    return {
        "providers": [
            {
                "name": p.name.value,
                "model": p.model,
                "configured": p.configured,
            }
            for p in provider_configs()
        ]
    }


@app.post("/ask", response_model=GatewayResponse)
def ask_endpoint(req: AskRequest):
    try:
        return ask(
            req.provider,
            req.prompt,
            req.conversation_id,
            req.system_context,
            req.risk_level,
            req.approved,
        )
    except ValueError as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/collaborate", response_model=GatewayResponse)
def collaborate_endpoint(req: CollaborateRequest):
    try:
        return collaborate(req)
    except ValueError as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/conversations/{conversation_id}")
def conversation(conversation_id: str):
    return {"conversation_id": conversation_id, "messages": load_messages(conversation_id, limit=200)}

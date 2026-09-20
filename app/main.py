import hashlib
import json
import secrets
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse

from .config import settings
from .controls import (
    CircuitOpenError,
    HostControlError,
    RequestCancelledError,
    cancellation_registry,
    request_rate_limiter,
)
from .db import (
    get_idempotency_record,
    init_db,
    load_messages,
    load_trace_telemetry,
    store_idempotency_record,
    telemetry_summary,
)
from .gateway import ask, collaborate
from .providers import ProviderError, provider_configs
from .schemas import AskRequest, CollaborateRequest, GatewayResponse


STATIC_DIR = Path(__file__).resolve().parent / "static"
WEB_CONSOLE = STATIC_DIR / "index.html"


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "A small, provider-aware gateway for bounded collaboration between heterogeneous AI systems. "
        "v0.3 hardening adds a versioned broker contract and host-enforced controls."
    ),
    lifespan=lifespan,
)


def _extract_access_token(authorization: str | None, x_oacg_token: str | None) -> str:
    if x_oacg_token:
        return x_oacg_token
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    return ""


def require_request_access(
    request: Request,
    authorization: str | None = Header(default=None),
    x_oacg_token: str | None = Header(default=None, alias="X-OACG-Token"),
) -> None:
    configured = settings.oacg_access_token
    if configured:
        supplied = _extract_access_token(authorization, x_oacg_token)
        if not supplied or not secrets.compare_digest(supplied, configured):
            raise HTTPException(status_code=401, detail="valid OACG access token required")

    client_key = request.client.host if request.client else "unknown"
    if not request_rate_limiter.allow(client_key, settings.max_requests_per_minute):
        raise HTTPException(status_code=429, detail="OACG request rate limit exceeded")


def _request_hash(req: AskRequest | CollaborateRequest) -> str:
    payload = req.model_dump(mode="json", exclude={"idempotency_key"})
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _cached_response(req: AskRequest | CollaborateRequest) -> tuple[str | None, GatewayResponse | None]:
    if not req.idempotency_key:
        return None, None

    request_hash = _request_hash(req)
    record = get_idempotency_record(req.idempotency_key, settings.idempotency_ttl_seconds)
    if record is None:
        return request_hash, None

    if record["request_hash"] != request_hash:
        raise HTTPException(
            status_code=409,
            detail="idempotency key was already used for a different request",
        )

    return request_hash, GatewayResponse.model_validate_json(record["response_json"])


def _store_response(req: AskRequest | CollaborateRequest, request_hash: str | None, response: GatewayResponse) -> None:
    if req.idempotency_key and request_hash:
        store_idempotency_record(
            req.idempotency_key,
            request_hash,
            response.model_dump_json(),
        )


@app.get("/", include_in_schema=False)
def web_console():
    return FileResponse(WEB_CONSOLE)


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
def ask_endpoint(req: AskRequest, _: None = Depends(require_request_access)):
    request_hash, cached = _cached_response(req)
    if cached is not None:
        return cached

    try:
        response = ask(
            req.provider,
            req.prompt,
            req.conversation_id,
            req.system_context,
            req.risk_level,
            req.approved,
            req.fallback_provider,
        )
        _store_response(req, request_hash, response)
        return response
    except ValueError as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc
    except CircuitOpenError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except RequestCancelledError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except HostControlError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/collaborate", response_model=GatewayResponse)
def collaborate_endpoint(req: CollaborateRequest, _: None = Depends(require_request_access)):
    request_hash, cached = _cached_response(req)
    if cached is not None:
        return cached

    try:
        response = collaborate(req)
        _store_response(req, request_hash, response)
        return response
    except ValueError as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc
    except CircuitOpenError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except RequestCancelledError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except HostControlError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/metrics")
def metrics(_: None = Depends(require_request_access)):
    return telemetry_summary()


@app.get("/traces/{trace_id}")
def trace_telemetry(trace_id: str, _: None = Depends(require_request_access)):
    return {"trace_id": trace_id, "events": load_trace_telemetry(trace_id)}


@app.post("/conversations/{conversation_id}/cancel")
def cancel_conversation(conversation_id: str, _: None = Depends(require_request_access)):
    cancellation_registry.cancel(conversation_id)
    return {"conversation_id": conversation_id, "status": "cancel_requested"}


@app.get("/conversations/{conversation_id}")
def conversation(conversation_id: str, _: None = Depends(require_request_access)):
    return {"conversation_id": conversation_id, "messages": load_messages(conversation_id, limit=200)}

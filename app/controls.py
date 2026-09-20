from __future__ import annotations

import re
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, replace

from .config import settings
from .providers import CallResult, ProviderError, call_model
from .schemas import Provider


class HostControlError(RuntimeError):
    pass


class CircuitOpenError(HostControlError):
    pass


class RequestCancelledError(HostControlError):
    pass


@dataclass
class _BreakerState:
    failures: int = 0
    opened_at: float | None = None


_BREAKERS: dict[Provider, _BreakerState] = defaultdict(_BreakerState)
_BREAKER_LOCK = threading.Lock()


_SECRET_PATTERNS = [
    re.compile(r"\bsk-[A-Za-z0-9_-]{10,}\b"),
    re.compile(r"\bxai-[A-Za-z0-9_-]{10,}\b", re.IGNORECASE),
    re.compile(r"(?i)(OPENAI_API_KEY\s*=\s*)\S+"),
    re.compile(r"(?i)(XAI_API_KEY\s*=\s*)\S+"),
]


def redact_text(value: str) -> str:
    redacted = value
    for pattern in _SECRET_PATTERNS:
        if pattern.pattern.startswith("(?i)("):
            redacted = pattern.sub(r"\1[REDACTED]", redacted)
        else:
            redacted = pattern.sub("[REDACTED]", redacted)
    return redacted


def _breaker_allows(provider: Provider) -> bool:
    now = time.monotonic()
    with _BREAKER_LOCK:
        state = _BREAKERS[provider]
        if state.opened_at is None:
            return True
        if now - state.opened_at >= settings.circuit_breaker_reset_seconds:
            state.failures = 0
            state.opened_at = None
            return True
        return False


def _record_success(provider: Provider) -> None:
    with _BREAKER_LOCK:
        _BREAKERS[provider] = _BreakerState()


def _record_failure(provider: Provider) -> None:
    with _BREAKER_LOCK:
        state = _BREAKERS[provider]
        state.failures += 1
        if state.failures >= settings.circuit_breaker_failures:
            state.opened_at = time.monotonic()


def reset_circuit_breakers() -> None:
    with _BREAKER_LOCK:
        _BREAKERS.clear()


def controlled_call(provider: Provider, prompt: str, system_context: str | None = None) -> CallResult:
    if not _breaker_allows(provider):
        raise CircuitOpenError(
            f"{provider.value} circuit is open after repeated failures; "
            "the host will not call the provider until the reset window expires"
        )

    attempts = max(1, settings.provider_max_retries + 1)
    last_error: ProviderError | None = None

    for attempt in range(attempts):
        try:
            result = call_model(provider, prompt, system_context)
            _record_success(provider)
            return replace(result, attempts=attempt + 1)
        except ProviderError as exc:
            last_error = exc
            _record_failure(provider)
            if attempt >= attempts - 1:
                break
            delay = settings.provider_retry_backoff_seconds * (2**attempt)
            if delay > 0:
                time.sleep(delay)

    assert last_error is not None
    raise last_error


class SlidingWindowRateLimiter:
    def __init__(self) -> None:
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key: str, limit: int, window_seconds: float = 60.0) -> bool:
        if limit <= 0:
            return True
        now = time.monotonic()
        cutoff = now - window_seconds
        with self._lock:
            events = self._events[key]
            while events and events[0] < cutoff:
                events.popleft()
            if len(events) >= limit:
                return False
            events.append(now)
            return True

    def reset(self) -> None:
        with self._lock:
            self._events.clear()


class CancellationRegistry:
    def __init__(self) -> None:
        self._cancelled: set[str] = set()
        self._lock = threading.Lock()

    def cancel(self, conversation_id: str) -> None:
        with self._lock:
            self._cancelled.add(conversation_id)

    def is_cancelled(self, conversation_id: str) -> bool:
        with self._lock:
            return conversation_id in self._cancelled

    def require_active(self, conversation_id: str) -> None:
        if self.is_cancelled(conversation_id):
            raise RequestCancelledError(
                f"conversation '{conversation_id}' was cancelled by the OACG host"
            )

    def reset(self) -> None:
        with self._lock:
            self._cancelled.clear()


request_rate_limiter = SlidingWindowRateLimiter()
cancellation_registry = CancellationRegistry()

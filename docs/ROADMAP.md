# Roadmap

## v0.1 — bounded collaboration
- OpenAI + Grok
- audit transcript
- turn limits
- approval gate
- Docker + CI

## v0.2 — browser console
- browser UI at `/`
- Collaborate and Ask-one-model modes
- rendered turn-by-turn transcript
- model and latency metadata
- provider readiness display
- approval control in the UI

## v0.3 — Broker Hardening
- versioned broker message contract
- host-side authentication, authorization, redaction, quotas, and deadlines
- strict provider-adapter validation with fail-closed behavior
- collaboration observability and cost telemetry
- retries, deduplication, idempotency, replay protection, and circuit breakers
- adversarial collaboration test suite
- explicit terminal states and safe fallback behavior

Tracking issue: #29

## v0.4 — provider ecosystem + shared context
- formal provider adapter interface
- Claude adapter
- provider capabilities registry
- pluggable memory and retrieval
- project-scoped context
- redaction and retention controls

## v0.5 — evaluation and economics
- token and dollar accounting
- latency tracing
- A/B collaboration evals
- single-model vs multi-model comparisons

## v0.6 — Decision Plane integration
- deterministic routing policies
- specialized decision model adapter
- confidence thresholds
- escalation to collaborative reasoning or human review

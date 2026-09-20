# OACG Observability

OACG records operational metadata at the broker/host layer. The metrics layer does **not** require models to reveal private reasoning and does not store prompt or response content.

## Per-provider event metadata

When available:

- trace ID
- conversation ID
- provider
- model
- latency
- input tokens
- output tokens
- total tokens
- retry count
- estimated cost
- event timestamp
- turn number

## Trace events

The host also records non-content events such as:

- `approval_required`
- `provider_response`
- `final_synthesis`
- `request_completed`
- `collaboration_completed`

Future terminal-state work will add explicit failure/fallback terminal reasons.

## Endpoints

Protected endpoints:

```http
GET /metrics
GET /traces/{trace_id}
```

`/metrics` returns aggregate operational totals.

`/traces/{trace_id}` returns structured event metadata for one execution trace.

## Cost estimates

OACG intentionally does not hard-code provider prices because prices change.

Configure optional rates in USD per one million tokens:

- `OPENAI_INPUT_COST_PER_MILLION`
- `OPENAI_OUTPUT_COST_PER_MILLION`
- `XAI_INPUT_COST_PER_MILLION`
- `XAI_OUTPUT_COST_PER_MILLION`

When rates are zero or token usage is unavailable, estimated cost remains unavailable rather than being fabricated.

## Privacy boundary

Telemetry does not store model output, prompts, hidden reasoning, API keys, or system prompts. Content remains in the separate broker transcript/audit path, where redaction controls apply.

Production deployments should integrate these events with their existing observability stack and retention policy rather than treating the reference SQLite metrics store as a production telemetry backend.

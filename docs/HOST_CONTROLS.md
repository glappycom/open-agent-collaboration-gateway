# OACG Host Controls

OACG v0.3 treats the host as the policy and transport boundary. Models can propose content, but they do not own authentication, routing, retry policy, quotas, deadlines, cancellation, idempotency, or circuit-breaking behavior.

## Authentication

Set `OACG_ACCESS_TOKEN` to require a token on protected endpoints.

Accepted forms:

```http
Authorization: Bearer <token>
```

or:

```http
X-OACG-Token: <token>
```

Leaving `OACG_ACCESS_TOKEN` empty preserves local-development behavior.

## Rate limiting

`MAX_REQUESTS_PER_MINUTE` applies a host-side sliding-window limit per client address.

This in-memory limiter is appropriate for the reference implementation. Multi-instance deployments should replace it with shared infrastructure such as Redis or an API gateway.

## Provider-call quota

`MAX_PROVIDER_CALLS_PER_REQUEST` caps the number of logical model calls in one collaboration. A standard collaboration consumes one provider call per turn plus one final-synthesis call.

The host rejects a collaboration before execution if its required call count exceeds the configured quota.

## Timeouts and deadlines

`PROVIDER_TIMEOUT_SECONDS` is enforced at the provider client and is also written into request-envelope deadlines.

Models do not decide their own timeout.

## Retry policy

The OACG host owns retries:

- `PROVIDER_MAX_RETRIES`
- `PROVIDER_RETRY_BACKOFF_SECONDS`

The provider SDK is configured with internal retries disabled so retry behavior remains explicit and auditable at the host layer.

## Circuit breaker

Repeated provider failures open a host-side circuit breaker:

- `CIRCUIT_BREAKER_FAILURES`
- `CIRCUIT_BREAKER_RESET_SECONDS`

When open, OACG refuses additional calls to the affected provider until the reset window expires.

## Idempotency and deduplication

`/ask` and `/collaborate` accept an optional `idempotency_key`.

The host stores the request hash and response for `IDEMPOTENCY_TTL_SECONDS`.

- Reusing the same key with the same request returns the stored response.
- Reusing the same key with a different request fails with HTTP 409.

This prevents accidental duplicate execution while preserving deterministic replay semantics.

## Cancellation

Protected endpoint:

```http
POST /conversations/{conversation_id}/cancel
```

The host records the cancellation request and checks it before each subsequent collaboration hop and before final synthesis.

Cancellation cannot forcibly interrupt a provider HTTP request already in flight; that request is bounded by the provider timeout. The collaboration will stop at the next host-controlled hop boundary.

## Redaction

Broker logs redact common OpenAI/xAI API-key patterns and environment-variable forms before persistence.

Redaction is a defense-in-depth control, not a substitute for proper secret handling. Secrets should never be included in prompts or shared context.

## Production note

The current authentication, rate limiting, cancellation registry, and circuit breaker are process-local reference implementations. Production deployments should move shared state into durable/distributed infrastructure and should place OACG behind TLS, managed secrets, and an external identity/access layer.

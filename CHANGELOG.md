# Changelog

## 0.3.0 — 2026-09-19

Broker hardening release.

- Added versioned broker envelope with host-generated trace IDs, message IDs, nonces, sequence numbers, deadlines, sender/recipient and message kinds
- Added optional access-token authentication and per-client rate limiting
- Added host-owned provider-call quotas, retries/backoff, timeouts, cancellation and circuit breaking
- Added idempotency keys and duplicate-request protection
- Added broker-log redaction
- Formalized provider adapter contract with strict response validation and typed provider errors
- Added provider token-usage normalization and configurable output-size limits
- Added broker telemetry, trace inspection and aggregate metrics endpoints
- Added optional cost estimation without hard-coding provider prices
- Added adversarial/failure-path CI regression tests
- Added explicit terminal states and bounded single-provider fallback
- Added partial-result behavior when final synthesis cannot complete
- Enforced mediated-only transport at the broker protocol layer; provider-to-provider envelopes fail closed
- Added security/architecture documentation for broker contract, host controls, provider adapters, observability, threat testing, terminal states and transport policy
- Added Zenodo DOI citation for the initial public release

## 0.2.0 — 2026-09-19

Browser console release.

- Added responsive browser UI at `/`
- Added Collaborate and Ask-one-model workflows
- Added provider readiness display
- Added rendered turn-by-turn transcript
- Added model and latency display in the console
- Added conversation ID and copy-final-answer controls
- Added explicit approval control for higher-risk requests
- Added browser-console API test
- Updated application/package version to 0.2.0

## 0.1.0 — 2026-09-19

Initial public release.

- OpenAI and xAI/Grok provider adapters
- `/ask`, `/collaborate`, `/providers`, `/health`, and conversation transcript endpoints
- Bounded alternating collaboration loop
- Final synthesis preserving unresolved disagreement
- SQLite audit trail
- Risk-level approval gate
- Prompt/context bounds
- Provider model and latency metadata
- Provider-side response storage disabled by default
- Docker packaging
- CI tests
- Community, citation, and security files

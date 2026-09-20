# Adversarial and Failure-Path Testing

OACG treats hostile or malformed model output as a normal engineering condition, not an exceptional research scenario. The v0.3 CI suite permanently exercises the broker against bounded failure modes.

## Covered threat families

| Threat / failure | Control | Regression coverage |
| --- | --- | --- |
| Peer text attempts to override host policy | Peer output is explicitly framed as untrusted data and separated from host instructions | `tests/test_adversarial.py` |
| Malformed broker envelope | Strict Pydantic envelope validation, unknown fields forbidden | `tests/test_protocol.py` |
| Unsupported schema version | Fail closed | `tests/test_protocol.py` |
| Duplicate/replayed application request | Idempotency key + request hash | `tests/test_api.py` |
| Idempotency-key reuse with different payload | HTTP 409 conflict | `tests/test_api.py` |
| Provider unavailable / repeated failure | Bounded retries + circuit breaker | `tests/test_controls.py`, `tests/test_adversarial.py` |
| Contradiction/debate loop | Server-side turn cap + final bounded synthesis | `tests/test_adversarial.py` |
| Oversized prompt/context | Host prompt-size limits | `tests/test_gateway.py` |
| Provider-call budget exhaustion | Host call quota | `tests/test_gateway.py` |
| Provider output attempts to claim transport metadata | Host generates routing/IDs independently of model text | `tests/test_adversarial.py` |
| Empty/missing/oversized provider output | Strict adapter validation | `tests/test_providers.py` |
| Credential echoed by provider | Adapter fails closed; logs also redact common key patterns | `tests/test_providers.py`, `tests/test_controls.py` |
| Cancellation between hops | Host cancellation registry | `tests/test_controls.py`, `tests/test_api.py` |

## Testing principle

No adversarial regression test requires production provider credentials. Provider behavior is simulated at the adapter/control boundary so the suite remains deterministic and safe to run in CI.

## Remaining work

The explicit terminal-state/fallback issue adds machine-readable terminal reasons for failure paths. The mediated-only transport issue adds route validation at the protocol boundary. Those controls extend this suite rather than replacing it.

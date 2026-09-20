# Provider Adapter Contract

OACG provider adapters are intentionally narrow. An adapter may communicate with one configured model provider and return a normalized result to the OACG host. It does not route to peer models, choose collaboration policy, or control retries.

## Interface

A provider adapter exposes:

- `provider`
- `model`
- `base_url`
- `configured`
- `invoke(prompt, system_context)`

The host selects an adapter through `get_adapter(provider)`.

## Fail-closed response handling

Before provider output re-enters collaboration state, the adapter validates that:

- textual output exists,
- output is non-empty after trimming,
- output is within `MAX_PROVIDER_OUTPUT_CHARS`,
- the exact configured provider credential is not present in the response,
- normalized metadata is structurally valid.

Malformed responses raise `ProviderResponseError`.

Provider configuration failures raise `ProviderConfigurationError`.

Transport/provider failures raise `ProviderError`.

## Retry ownership

Provider SDK retries are disabled (`max_retries=0`). Retry/backoff and circuit-breaking policy belong to the OACG host-control layer.

## Usage metadata

Adapters normalize provider usage metadata when available:

- input tokens
- output tokens
- total tokens

The absence of usage metadata is valid; fabricated values are never substituted.

## Security boundary

Model output is untrusted data. Provider response text cannot set broker routing, message IDs, trace IDs, schema versions, nonces, deadlines, or authorization policy.

Future adapters (Claude, Gemini, local models, specialized decision models) should implement the same narrow contract rather than introducing provider-specific collaboration semantics.

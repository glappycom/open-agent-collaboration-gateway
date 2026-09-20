# Terminal States and Bounded Fallback

OACG v0.3 makes workflow termination explicit. Every completed or interrupted execution returns a machine-readable `terminal_state` and a human-readable `terminal_reason` when applicable.

## Terminal states

| State | Meaning |
| --- | --- |
| `completed` | The requested workflow completed within host policy and budgets. |
| `partial` | Useful bounded work exists, but final synthesis could not be completed. |
| `budget_exhausted` | The host rejected or stopped work because configured call budget was insufficient. |
| `policy_blocked` | Human approval or another host policy prevented execution. |
| `provider_unavailable` | A required provider remained unavailable after bounded retry/fallback policy. |
| `timed_out` | A provider operation timed out. |
| `cancelled` | The host received a cancellation for the conversation. |
| `failed` | A non-classified failure terminated execution. |

The legacy-friendly `status` field remains present:

- `completed`
- `approval_required`
- `partial`
- `failed`

`terminal_state` is the more precise machine-readable reason.

## Bounded fallback

Requests may specify an optional `fallback_provider`.

Fallback rules:

1. The primary provider is attempted under the host retry/circuit-breaker policy.
2. A fallback is considered only for provider/circuit failures.
3. Fallback never bypasses cancellation, approval, or host budgets.
4. The number of fallback provider calls is capped by `MAX_FALLBACK_CALLS_PER_REQUEST` (default: 1).
5. A fallback provider cannot recursively create another fallback chain.
6. The response records which fallback provider was used.

## Partial results

If collaboration turns succeeded but the final synthesis provider is unavailable, OACG returns:

- the completed transcript,
- the most recent useful contribution as `final`,
- `status: partial`,
- `terminal_state: partial`,
- a reason identifying why final synthesis was unavailable.

This is preferable to discarding useful work or retrying indefinitely.

## Telemetry

Terminal events are written to the trace stream with:

- terminal state,
- public status,
- reason,
- fallback provider where applicable.

The terminal event contains operational metadata only; it does not require private chain-of-thought.

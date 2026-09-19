# Changelog

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

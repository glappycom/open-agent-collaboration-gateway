# Open Agent Collaboration Gateway (OACG)

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22850844.svg)](https://doi.org/10.5281/zenodo.22850844)

**An open-source gateway for bounded, auditable collaboration between heterogeneous AI systems.**

OACG v0.3 lets OpenAI and xAI/Grok collaborate through a host-mediated control plane with a browser console, explicit budgets, audit traces, terminal states, bounded fallback, and protocol-level prevention of direct provider-to-provider transport.

> The goal is not to make AI systems talk more. The goal is to let independent systems collaborate when collaboration creates measurable value—while preserving budgets, observability, security, and human authority.

## Architecture

```text
Browser / API client
        |
        v
+--------------------------------+
| OACG Host                      |
|--------------------------------|
| web console                    |
| auth / approval / quotas       |
| versioned broker contract      |
| bounded turn controller        |
| retries / timeout / breaker    |
| telemetry / audit              |
| terminal states / fallback     |
+---------------+----------------+
                |
        +-------+-------+
        |               |
        v               v
     OpenAI          xAI/Grok

Provider -> Provider direct transport: prohibited
```

## v0.3 capabilities

- Browser collaboration console at `/`
- `POST /ask` and `POST /collaborate`
- Versioned host-owned broker envelopes
- Stable trace/message identifiers and audit metadata
- Optional access-token authentication
- Human approval gate for configurable risk levels
- Rate limiting and provider-call quotas
- Host-owned retries, exponential backoff, timeouts and circuit breaking
- Idempotency keys and duplicate-request protection
- Strict provider adapter response validation
- Prompt/context/output bounds
- Secret-pattern redaction in broker logs
- Token, latency, retry and optional cost telemetry
- `GET /metrics` and `GET /traces/{trace_id}`
- Explicit terminal states: completed, partial, budget exhausted, policy blocked, provider unavailable, timed out, cancelled, failed
- Optional bounded fallback provider
- Host-mediated transport enforcement: provider-to-provider broker envelopes fail closed
- Docker packaging and GitHub Actions CI

## Quick start

```bash
git clone https://github.com/glappycom/open-agent-collaboration-gateway.git
cd open-agent-collaboration-gateway
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Add provider keys to `.env`:

```env
OPENAI_API_KEY=...
XAI_API_KEY=...
```

Never commit `.env`.

Run:

```bash
uvicorn app.main:app --reload --port 8080
```

Open:

- Browser console: `http://localhost:8080/`
- API docs: `http://localhost:8080/docs`

Or:

```bash
docker compose up --build
```

## Example collaboration

```bash
curl -X POST http://localhost:8080/collaborate \
  -H "Content-Type: application/json" \
  -d '{
    "task":"Review a provider-independent AI decision plane.",
    "starter":"openai",
    "fallback_provider":"grok",
    "turns":4,
    "mode":"architecture",
    "shared_context":"Minimize lock-in, inference cost, and latency.",
    "risk_level":"low"
  }'
```

OACG mediates each hop through the host, preserves the bounded transcript, and returns a final synthesis or an explicit bounded terminal outcome.

## Security model

OACG v0.3 adds meaningful broker hardening, but it remains a **reference implementation**, not a turnkey internet-facing production control plane.

The reference authentication, rate limiter, circuit breaker, cancellation registry, SQLite stores, and telemetry backend are process-local. Production deployments should use TLS, managed secrets, external identity/RBAC, distributed state, durable production storage, retention policy, and signed human approvals.

See:

- [Broker contract](docs/BROKER_CONTRACT.md)
- [Host controls](docs/HOST_CONTROLS.md)
- [Provider adapters](docs/PROVIDER_ADAPTERS.md)
- [Observability](docs/OBSERVABILITY.md)
- [Threat testing](docs/THREAT_TESTING.md)
- [Terminal states](docs/TERMINAL_STATES.md)
- [Transport policy](docs/TRANSPORT_POLICY.md)
- [Security policy](SECURITY.md)

## Tests

```bash
pytest -q
```

The default suite does not require live provider credentials and includes protocol, control-plane, adapter, telemetry, terminal-state, and adversarial regression tests.

## Research track: Decision Plane

The repository also contains the initial experimental protocol for a related research question:

> Can a hierarchical AI Decision Plane reduce the cost and latency of agentic workflows without materially degrading decision quality or workflow completion?

See [`research/DECISION_PLANE_EXPERIMENT.md`](research/DECISION_PLANE_EXPERIMENT.md).

## Roadmap

See [`docs/ROADMAP.md`](docs/ROADMAP.md).

Major next priorities:

- Claude provider adapter
- Pluggable shared memory/retrieval
- Single-model vs multi-model evaluation harness
- Decision Plane benchmark pilot
- Production-grade distributed control state

## Contributing

Contributions are welcome. Start with [CONTRIBUTING.md](CONTRIBUTING.md).

## Citation

The initial public software release is archived on Zenodo:

**DOI: 10.5281/zenodo.22850844**

A `CITATION.cff` file is included for research-software citation. Future GitHub releases are configured for automatic Zenodo preservation.

## License

Apache License 2.0. See [LICENSE](LICENSE).

## Maintainer

OACG was initiated by **Russell Avre / Glappy Inc.** as an open experiment in interoperable AI collaboration.

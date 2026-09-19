# Open Agent Collaboration Gateway (OACG)

**A small open-source gateway for bounded, auditable collaboration between heterogeneous AI systems.**

OACG v0.2 lets OpenAI and xAI/Grok work on the same task through a controlled collaboration loop and now includes a lightweight browser console so users can run collaborations without sending JSON manually.

> The goal is not to make AI systems talk more. The goal is to let independent systems collaborate when collaboration creates measurable value—while preserving budgets, auditability, and human authority.

## Why OACG?

Most AI integrations focus on **routing**: choose one model and send it a request.

OACG explores **collaboration**: allow more than one model to propose, critique, revise, and synthesize work under explicit limits.

```text
Browser / API client
        |
        v
+---------------------------+
| OACG                      |
|---------------------------|
| web console               |
| policy + approval gate    |
| bounded turn controller   |
| shared transcript         |
| audit log                 |
| provider adapters         |
+------------+--------------+
             |
      +------+------+
      |             |
      v             v
   OpenAI         xAI/Grok
```

## v0.2 capabilities

- Browser collaboration console at `/`.
- `POST /ask` — call one configured provider.
- `POST /collaborate` — run a bounded alternating OpenAI ↔ Grok workflow.
- `GET /providers` — inspect configured adapters and model names without exposing keys.
- `GET /conversations/{id}` — retrieve the local audit transcript.
- Low/medium/high/critical risk classification.
- Approval gate for configurable risk levels.
- Server-side collaboration turn cap.
- Prompt/context bounds.
- SQLite transcript and metadata log.
- Per-call model and latency metadata.
- Provider-side response storage disabled by default where supported.
- Docker packaging and CI tests.

## Quick start

### 1. Clone and configure

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

### 2. Run

```bash
uvicorn app.main:app --reload --port 8080
```

Open the browser console:

```text
http://localhost:8080/
```

Interactive API documentation remains available at:

```text
http://localhost:8080/docs
```

Or run with Docker:

```bash
docker compose up --build
```

## Using the web console

The web console supports two workflows:

### Collaborate

Enter a task, optional shared context, starter model, turn limit, collaboration mode, and risk level. OACG coordinates the bounded OpenAI ↔ Grok exchange and renders each turn plus the final synthesis.

### Ask one model

Switch to **Ask one model** when you want to call OpenAI or Grok directly without collaboration.

The console also shows provider configuration status, conversation ID, model metadata, latency, approval-gate messages, and a copyable final answer.

## Example: ask one provider

```bash
curl -X POST http://localhost:8080/ask \
  -H "Content-Type: application/json" \
  -d '{
    "provider":"grok",
    "prompt":"Review this API architecture for failure modes.",
    "risk_level":"low"
  }'
```

## Example: bounded collaboration

```bash
curl -X POST http://localhost:8080/collaborate \
  -H "Content-Type: application/json" \
  -d '{
    "task":"Design a provider-independent AI decision plane.",
    "starter":"openai",
    "turns":4,
    "mode":"architecture",
    "shared_context":"Minimize provider lock-in, inference cost, and latency.",
    "risk_level":"low"
  }'
```

OACG alternates providers for the bounded number of turns and asks OpenAI to produce a final synthesis that explicitly preserves unresolved disagreement.

## Approval gate

By default, high- and critical-risk requests do not start until approval is explicitly supplied.

```json
{
  "status": "approval_required"
}
```

The current `approved: true` mechanism is intentionally a prototype control. Production deployments should replace it with authenticated users, authorization policy, and signed approval records.

## Provider defaults

The sample configuration currently uses:

- OpenAI: `gpt-5.6-luna`
- xAI: `grok-4.6`

Both are configurable through environment variables. OACG should not hard-code long-term application logic to a specific model ID.

## Tests

```bash
pytest -q
```

The default test suite does **not** make live provider calls.

## Design principles

1. Provider independence over provider lock-in.
2. Bounded collaboration over recursive agent loops.
3. Human accountability for consequential actions.
4. Observable cost, latency, and decisions.
5. Deterministic software when deterministic software is sufficient.
6. Explicit tool permissions and minimal privilege.
7. Benchmark collaboration against strong single-model baselines.

## Security status

OACG is a public **reference implementation**, not an internet-facing production control plane. See [SECURITY.md](SECURITY.md) for deployment guidance.

Before production use, add at minimum authentication, role-based authorization, managed secrets, production storage, rate limits, circuit breakers, data-retention/redaction policies, stronger prompt-injection controls, and signed human approvals.

## Research track: Decision Plane

The repository also contains the initial experimental protocol for a related research question:

> Can a hierarchical AI Decision Plane reduce the cost and latency of agentic workflows without materially degrading decision quality or workflow completion?

See [`research/DECISION_PLANE_EXPERIMENT.md`](research/DECISION_PLANE_EXPERIMENT.md).

## Roadmap

See [`docs/ROADMAP.md`](docs/ROADMAP.md).

Near-term priorities include:

- Formal provider-adapter interface.
- Claude support.
- Pluggable shared memory/retrieval.
- Token and dollar accounting.
- Authenticated projects/tenants.
- Evaluation harness comparing multi-model collaboration with single-model baselines.
- Decision Plane integration.

## Contributing

Contributions are welcome. Start with [CONTRIBUTING.md](CONTRIBUTING.md). Provider adapters, evaluation harnesses, governance mechanisms, observability, and collaboration protocols are especially useful.

## Citation

A `CITATION.cff` file is included so releases can be cited as research software. GitHub releases are archived through Zenodo for persistent citation.

## License

Apache License 2.0. See [LICENSE](LICENSE).

## Maintainer

OACG was initiated by **Glappy Inc.** as an open experiment in interoperable AI collaboration.

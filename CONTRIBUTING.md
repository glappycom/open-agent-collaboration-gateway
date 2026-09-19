# Contributing to OACG

Thank you for helping make heterogeneous AI systems collaborate more safely and usefully.

## Good first contributions

- Provider adapters
- Evaluation harnesses
- Cost and latency instrumentation
- Collaboration protocols
- Memory/retrieval interfaces
- Approval and governance mechanisms
- Documentation and examples

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
uvicorn app.main:app --reload --port 8080
```

## Design principles

1. Provider independence over provider lock-in.
2. Bounded collaboration over unrestricted recursive loops.
3. Human accountability for consequential actions.
4. Observable costs, latency, and decisions.
5. Deterministic software when deterministic software is sufficient.
6. Minimal privilege and explicit tool access.
7. No secrets in prompts, source code, tests, or issues.

For substantial changes, open an issue describing the problem before writing a large patch.

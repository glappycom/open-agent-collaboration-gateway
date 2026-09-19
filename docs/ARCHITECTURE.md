# Architecture

OACG is intentionally a gateway, not an autonomous society of agents.

```text
Client / application
        |
        v
+---------------------------+
| OACG                      |
|---------------------------|
| request policy            |
| risk / approval gate      |
| bounded turn controller   |
| transcript + audit        |
| provider adapters         |
+------------+--------------+
             |
      +------+------+
      |             |
      v             v
   OpenAI         xAI/Grok
```

## Why bounded collaboration?

Unrestricted model-to-model conversation creates four immediate problems: runaway cost, circular reasoning, hard-to-audit decisions, and ambiguous accountability. OACG therefore treats collaboration as a finite workflow with a defined starter, mode, turn budget, and final synthesis step.

## Provider layer

v0.1 includes OpenAI and xAI/Grok. The provider boundary is intentionally small so future adapters such as Claude, Gemini, local models, or specialized decision models can be added without changing collaboration semantics.

## What OACG is not

- It is not a general-purpose workflow engine.
- It is not a replacement for MCP.
- It is not a model router alone.
- It does not grant models unrestricted tools.
- It does not claim that multiple models are always better than one.

## Next architecture milestones

1. Provider adapter protocol/package split.
2. Claude adapter.
3. Authenticated tenants/projects.
4. Postgres storage.
5. Cost/token telemetry.
6. Pluggable memory/retrieval.
7. Evaluation harness.
8. Decision Plane integration.

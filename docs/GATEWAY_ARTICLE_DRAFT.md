# From Model Silos to Collaborative AI: Why AI Systems Need a Common Collaboration Layer

Today’s most capable artificial intelligence systems largely operate in separate environments. A developer can ask OpenAI, Grok, Claude, or another model to analyze the same problem, but collaboration among them is still often mediated by a person copying outputs between interfaces.

That human-in-the-middle pattern is useful for experimentation, but it is not a durable architecture for an agentic future.

At Glappy, this led us to a simple engineering question: **what would it take for heterogeneous AI systems to collaborate directly while remaining bounded, observable, and accountable?**

Our first answer is an experimental open-source project: the **Open Agent Collaboration Gateway (OACG)**.

## Collaboration is different from routing

Model routers answer an important question: *which model should handle this request?*

Collaboration asks a different question: *how should several independent AI systems work on the same problem together?*

A useful collaboration might have one model propose an architecture, another identify engineering failure modes, the first revise its design, and a final synthesis preserve both agreement and unresolved uncertainty. The value is not simply that more models were called. The value is in the protocol governing how their contributions interact.

## Why a gateway?

Connecting models directly in an unrestricted conversational loop creates predictable problems: runaway cost, circular reasoning, difficult audits, accidental context leakage, and unclear accountability.

OACG instead treats collaboration as a bounded workflow. A request has a task, collaboration mode, starter, turn budget, risk level, shared context, and termination point. The gateway records the exchange and can require explicit approval before higher-risk work proceeds.

The first release supports OpenAI and xAI/Grok. The architecture is intended to expand to additional providers, including Claude and local or specialized models, through provider adapters rather than hard-coded model-to-model dependencies.

## Humans should not be copy-and-paste middleware

Human oversight remains essential, particularly when AI systems can take consequential actions. But oversight is different from clerical coordination.

People should decide objectives, permissions, risk thresholds, escalation rules, and which conclusions they accept. They should not have to manually shuttle every intermediate message between machines.

A collaboration layer can automate the coordination while preserving human authority.

## Questions an open community can help answer

The interesting work begins after the first gateway functions:

- How should agents identify themselves and their capabilities?
- How should evidence and citations travel between models?
- How should disagreement be represented instead of silently synthesized away?
- How should confidence be calibrated across heterogeneous systems?
- When should a collaboration stop?
- How should token and monetary budgets constrain dialogue?
- How should shared memory be partitioned among projects and organizations?
- When should a system escalate to a person rather than another model?
- How do we evaluate whether multi-model collaboration actually improves outcomes over a single strong model?

These are not questions one company should answer alone.

## Why open source?

Interoperability becomes more valuable when people can inspect it, challenge it, benchmark it, and extend it. We are therefore preparing OACG as an open-source project rather than keeping the first implementation as a Glappy-only internal utility.

The initial release is deliberately small. It is intended to provide a working reference implementation and a place for experimentation—not to claim that the collaboration problem is solved.

Our near-term roadmap includes additional provider adapters, shared context and retrieval, stronger authentication and approval controls, cost and latency instrumentation, and a reproducible evaluation harness comparing collaborative workflows with single-model baselines.

## The larger architecture

Collaboration is only one part of the system we are exploring.

Our next research question is whether agentic AI also needs a distinct **Decision Plane**: a layer that chooses when deterministic rules, specialized decision models, lightweight models, frontier reasoning, multi-model collaboration, or human judgment should be used.

If that architecture proves useful, collaboration becomes an escalation mechanism—not the default response to every problem.

That is an important distinction. The goal is not to make AI systems talk more. The goal is to make them work together only when doing so creates measurable value.

## An invitation

OACG begins with two providers and a bounded conversation loop. We hope it grows into a practical testbed for a larger idea: independent AI systems should be able to cooperate through open interfaces without sacrificing governance, observability, or human accountability.

We are opening the work so researchers and developers can help test that proposition.

Repository: https://github.com/glappycom/open-agent-collaboration-gateway

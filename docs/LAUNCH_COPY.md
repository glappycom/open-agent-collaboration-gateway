# OACG Launch Copy

## One-line announcement

We are open-sourcing OACG, an experimental gateway that lets independent AI systems such as OpenAI and Grok collaborate through bounded, auditable workflows rather than human copy-and-paste coordination.

## Short project description

OACG explores an emerging problem in agentic AI: not simply which model should answer, but how heterogeneous AI systems should collaborate. The project provides a small provider-independent gateway with bounded turns, shared transcripts, approval gates, and an extensible path toward Claude and other providers.

## Contributor invitation

We are especially interested in contributions around provider adapters, multi-model evaluation, cost and latency instrumentation, shared memory, collaboration protocols, security, and human-approval mechanisms. A major research question is whether multi-model collaboration measurably improves outcomes over a strong single-model baseline—and when it does not.

## LinkedIn launch draft

Most AI systems can reason about the same problem. Very few can reason *with each other*.

Today, humans are often the middleware: ask one model, copy its answer to another, ask for a critique, paste the result back, and repeat.

We have been experimenting with a different approach at Glappy: a small collaboration gateway that allows heterogeneous AI systems to exchange work through a bounded, auditable workflow.

We call it the Open Agent Collaboration Gateway (OACG).

The first version connects OpenAI and Grok. It limits turns, maintains an audit transcript, supports approval gates, and is intentionally designed so additional providers such as Claude can be added without hard-coding the architecture around one model company.

This is not an attempt to make AI systems talk endlessly. The research question is more useful: **when does collaboration between independent models produce a better result than using one strong model—and how do we control cost, security, disagreement, and human accountability when it does?**

We are preparing the project as open source because these interoperability questions should be tested in the open.

If you work on agents, orchestration, model evaluation, AI governance, or provider interoperability, we would welcome your perspective and contributions.

Repository: https://github.com/glappycom/open-agent-collaboration-gateway

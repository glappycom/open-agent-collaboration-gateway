# Decision Plane Experiment Protocol — Draft 0.1

## Research question

Can a hierarchical AI Decision Plane reduce the cost and latency of agentic workflows without materially degrading decision quality or workflow completion?

## Hypothesis

High-frequency operational decisions such as routing, classification, retry/stop, tool selection, and escalation often do not require a frontier reasoning model. A tiered Decision Plane can select the least expensive mechanism that satisfies confidence and risk requirements.

## Compared decision mechanisms

1. Deterministic rules
2. Lightweight/local classifier
3. Specialized decision model (Jev or equivalent, subject to API availability and terms)
4. Low-cost language model
5. Frontier reasoning model

## Initial task families

- Agent routing
- Continue / stop
- Retry / escalate
- Tool selection
- Evidence sufficiency
- Human-review escalation

## African infrastructure scenarios

Evaluate the same decision workload under simulated constraints relevant to heterogeneous deployments:

- high and variable network latency
- constrained bandwidth
- intermittent cloud reachability
- strict per-decision cost ceilings
- local-first / data-residency requirements
- edge or low-compute environments

These scenarios are experimental constraints, not claims that all African deployments share the same conditions.

## Dataset target

Phase A: 1,000 labeled decisions for pipeline validation.
Phase B: 5,000–20,000 decisions across at least four workflow families.

Each record should include:

- decision_id
- task_family
- sanitized context
- allowed choices
- reference decision / adjudication
- risk level
- provider/mechanism
- selected decision
- confidence where available
- latency_ms
- estimated input/output tokens where applicable
- estimated cost_usd
- correct / incorrect / abstain
- human escalation
- downstream workflow success

## Primary metrics

- Decision accuracy
- Selective accuracy at confidence threshold
- Abstention rate
- False-positive / false-negative rate where applicable
- Median and P95 latency
- Cost per 1,000 decisions
- Frontier-model calls avoided
- Human-escalation rate
- End-to-end workflow success

## Experimental controls

- Freeze test cases before comparative evaluation.
- Do not tune on the held-out test split.
- Use identical allowed-choice sets across mechanisms where possible.
- Record model/API version and test date.
- Separate vendor-reported benchmarks from reproduced results.
- Run enough repetitions to characterize API latency variance.
- Treat deterministic rules as a serious baseline, not a straw man.

## Governance

Consequential real-world decisions are out of scope for the initial benchmark. Use synthetic, public, or properly de-identified workflow data. Human adjudicators remain the reference for disputed labels.

## Minimum evidence required before paper submission

- Reproducible benchmark harness
- Documented dataset construction
- At least one held-out evaluation set
- Results with confidence intervals or appropriate uncertainty reporting
- Cost and latency methodology
- Failure-case analysis
- Clear limitations section

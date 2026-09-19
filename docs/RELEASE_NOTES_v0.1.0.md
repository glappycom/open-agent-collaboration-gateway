# OACG v0.1.0 Release Notes

OACG v0.1.0 is the first public release candidate of the Open Agent Collaboration Gateway.

## Purpose

Provide a small reference implementation for bounded, auditable collaboration between heterogeneous AI providers.

## Included

- OpenAI and xAI/Grok adapters
- single-provider `/ask` requests
- bounded `/collaborate` workflows
- final synthesis with unresolved disagreement preserved
- risk/approval gate
- local transcript/audit storage
- model and latency metadata
- prompt/context limits
- provider response storage disabled by default where supported
- Docker packaging
- GitHub Actions CI
- five automated tests
- Apache-2.0 licensing and community/security files
- citation metadata for future Zenodo archival
- Decision Plane research protocol

## Known limitations

This release candidate is not a production control plane. It lacks authenticated users/tenants, production-grade authorization, signed approvals, centralized telemetry, cost accounting, rate limiting, circuit breakers, and production storage.

The default collaboration protocol alternates providers. Future releases should support richer collaboration policies and evaluate when multi-model collaboration outperforms a single strong model.

# Security Policy

OACG coordinates calls across external AI providers and may process sensitive prompts. Treat deployment as security-sensitive infrastructure.

## Reporting vulnerabilities

Please do not open a public issue for a suspected vulnerability. Report security issues privately to the maintainers through the repository's private vulnerability reporting feature once enabled.

## Deployment guidance

- Never commit provider API keys.
- Use managed secrets in production.
- Put OACG behind authentication and TLS.
- Replace the prototype approval flag with authenticated, signed approvals.
- Apply rate limits, quotas, and provider circuit breakers.
- Redact secrets and sensitive data from logs.
- Use explicit allowlists before enabling external tools or write actions.
- Define retention policies for transcripts.

The default v0.1 configuration sets provider-side response storage to false where the provider API supports that setting. Review each provider's current data-handling terms before production use.

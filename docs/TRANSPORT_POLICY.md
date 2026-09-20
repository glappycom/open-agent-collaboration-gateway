# Mediated-Only Transport Policy

OACG uses a **brokered transport model**. Independent model providers do not communicate directly with one another. Every collaboration hop returns to the OACG host before another provider can receive a new request.

```text
Provider A
    |
    v
 OACG Host
    |
    v
Provider B
```

The following route is intentionally invalid:

```text
Provider A  ----X---->  Provider B
```

## Protocol enforcement

The broker envelope validates route direction by message kind.

### Request

Valid:

```text
host -> provider
```

Invalid:

```text
provider -> provider
provider -> host
host -> host
```

### Contribution / final synthesis

Valid:

```text
provider -> host
```

Invalid:

```text
provider -> provider
host -> provider
host -> host
```

An invalid route fails envelope validation before transport/audit state is accepted.

## Why the host remains in the path

The host is the single boundary for:

- routing
- authentication and authorization
- policy
- redaction
- quotas and budgets
- retries and circuit breaking
- idempotency
- cancellation
- observability
- terminal-state handling
- human approval

A direct peer channel would bypass those controls.

## Provider adapters

Adapters expose a narrow `invoke` interface to one configured provider. They do not receive:

- peer credentials,
- peer adapter objects,
- arbitrary network destinations from model output,
- transport-routing authority.

Provider endpoints are application configuration/code, not model-generated payload fields.

## External tools

Future external tool/network access must be a separate, explicitly permissioned capability. Tool access is not implied by participation in an OACG collaboration.

## Extension rule

Adding Claude, Gemini, local models, or other providers does not change the transport rule:

**provider responses return to host; host creates the next provider request.**

# OACG Broker Contract v1.0

OACG treats every model interaction as a **host-mediated broker hop**. Models do not establish direct peer channels. The host creates the transport envelope, assigns identifiers, records the audit metadata, and decides which provider receives the next hop.

## Envelope

Every broker hop uses a versioned envelope with:

- `schema_version`
- `trace_id`
- `message_id`
- `sender`
- `recipient`
- `kind`
- `sequence`
- `created_at`
- optional `deadline_at`
- host-generated `nonce`
- `content`
- optional `model`
- optional `latency_ms`
- extensible `metadata`

The current schema version is **1.0**.

## Trust boundary

The OACG host owns the envelope. Model-generated text is payload, not transport metadata.

A model cannot set:

- message identifiers,
- trace identifiers,
- nonce values,
- recipient routing,
- schema version,
- deadline,
- or broker sequence.

Those values are generated or validated by the host.

## Message kinds

### request
A host-generated request to a provider.

### contribution
A provider response returned to the OACG host during collaboration.

### final_synthesis
A final provider response that the host returns to the caller after the bounded collaboration completes.

## Version handling

Unsupported schema versions fail closed. The broker must not silently coerce unknown versions into the current schema.

## Recipient semantics

For provider responses, the immediate recipient is the OACG host. The host may then create a new request envelope for another provider. This preserves the mediated-only architecture.

## Replay and deduplication

v1.0 includes a unique `message_id` and nonce on every envelope. Enforcement of replay windows, deduplication storage, and idempotent delivery is part of the v0.3 host-control work that follows this contract.

## Deadlines

The contract supports an optional `deadline_at`. Deadline enforcement is implemented by the host-control layer, not by models.

## Backward compatibility

The public API continues to expose the human-friendly message fields used by the v0.2 web console while adding broker identifiers and schema metadata to each returned message.

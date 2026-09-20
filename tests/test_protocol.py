from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from app.protocol import BROKER_SCHEMA_VERSION, BrokerEnvelope, MessageKind, new_envelope


def test_new_envelope_generates_host_owned_identifiers():
    first = new_envelope(
        trace_id="trace-123",
        sender="host",
        recipient="openai",
        kind=MessageKind.request,
        sequence=1,
        content="hello",
    )
    second = new_envelope(
        trace_id="trace-123",
        sender="host",
        recipient="openai",
        kind=MessageKind.request,
        sequence=2,
        content="again",
    )

    assert first.schema_version == BROKER_SCHEMA_VERSION
    assert first.trace_id == "trace-123"
    assert first.message_id != second.message_id
    assert first.nonce != second.nonce
    assert first.sender == "host"
    assert first.recipient == "openai"


def test_envelope_serializes_round_trip():
    envelope = new_envelope(
        trace_id="trace-abc",
        sender="grok",
        recipient="host",
        kind=MessageKind.contribution,
        sequence=2,
        content="review complete",
        model="test-grok",
        latency_ms=9,
        metadata={"turn": 1},
    )

    restored = BrokerEnvelope.model_validate(envelope.model_dump(mode="json"))
    assert restored == envelope


def test_unsupported_schema_version_fails_closed():
    now = datetime.now(timezone.utc)
    with pytest.raises((ValidationError, ValueError)):
        BrokerEnvelope(
            schema_version="99.0",
            trace_id="trace-1",
            message_id="message-1",
            sender="host",
            recipient="openai",
            kind=MessageKind.request,
            sequence=1,
            created_at=now,
            nonce="1234567890abcdef",
            content="hello",
        )


def test_unknown_envelope_fields_are_rejected():
    envelope = new_envelope(
        trace_id="trace-1",
        sender="host",
        recipient="openai",
        kind=MessageKind.request,
        sequence=1,
        content="hello",
    ).model_dump(mode="json")
    envelope["unexpected_transport_field"] = "model-controlled"

    with pytest.raises(ValidationError):
        BrokerEnvelope.model_validate(envelope)


def test_deadline_must_be_after_creation():
    now = datetime.now(timezone.utc)
    with pytest.raises((ValidationError, ValueError)):
        BrokerEnvelope(
            schema_version=BROKER_SCHEMA_VERSION,
            trace_id="trace-1",
            message_id="message-1",
            sender="host",
            recipient="openai",
            kind=MessageKind.request,
            sequence=1,
            created_at=now,
            deadline_at=now - timedelta(seconds=1),
            nonce="1234567890abcdef",
            content="hello",
        )


def test_direct_provider_to_provider_request_is_rejected():
    now = datetime.now(timezone.utc)
    with pytest.raises((ValidationError, ValueError)):
        BrokerEnvelope(
            schema_version=BROKER_SCHEMA_VERSION,
            trace_id="trace-direct",
            message_id="message-direct",
            sender="openai",
            recipient="grok",
            kind=MessageKind.request,
            sequence=1,
            created_at=now,
            nonce="1234567890abcdef",
            content="direct peer request",
        )


def test_direct_provider_to_provider_contribution_is_rejected():
    now = datetime.now(timezone.utc)
    with pytest.raises((ValidationError, ValueError)):
        BrokerEnvelope(
            schema_version=BROKER_SCHEMA_VERSION,
            trace_id="trace-direct",
            message_id="message-direct",
            sender="grok",
            recipient="openai",
            kind=MessageKind.contribution,
            sequence=2,
            created_at=now,
            nonce="1234567890abcdef",
            content="direct peer contribution",
        )


def test_host_cannot_impersonate_provider_contribution():
    now = datetime.now(timezone.utc)
    with pytest.raises((ValidationError, ValueError)):
        BrokerEnvelope(
            schema_version=BROKER_SCHEMA_VERSION,
            trace_id="trace-host",
            message_id="message-host",
            sender="host",
            recipient="host",
            kind=MessageKind.contribution,
            sequence=2,
            created_at=now,
            nonce="1234567890abcdef",
            content="invalid contribution",
        )


def test_provider_response_must_return_to_host():
    response = new_envelope(
        trace_id="trace-response",
        sender="openai",
        recipient="host",
        kind=MessageKind.contribution,
        sequence=2,
        content="valid response",
    )

    assert response.sender == "openai"
    assert response.recipient == "host"

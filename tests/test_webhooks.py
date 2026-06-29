"""Tests for webhook signature verification."""

import hashlib
import hmac
from typing import Any

from stableops.webhooks import (
    SIGNATURE_HEADER,
    AsyncWebhooksApi,
    WebhooksApi,
    verify_webhook_signature,
)

NOW = 1_780_000_000


def build_header(secret: str, timestamp: int, body: str) -> str:
    """Build the canonical X-Product-Signature header."""
    signed_payload = f"{timestamp}.{body}"
    signature = hmac.new(
        secret.encode("utf-8"),
        signed_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"t={timestamp},v1={signature}"


def test_signature_header_constant_matches_delivery_protocol() -> None:
    assert SIGNATURE_HEADER == "x-product-signature"


def test_valid_signature_header() -> None:
    secret = "whsec_test123"
    body = '{"type":"payment.finalized","data":{"payment_order_id":"po_123"}}'

    result = verify_webhook_signature(
        body=body,
        header=build_header(secret, NOW, body),
        secret=secret,
        now=NOW,
    )

    assert result.valid is True
    assert result.reason == "valid"


def test_accepts_any_v1_signature_during_rotation() -> None:
    old_secret = "whsec_old"
    new_secret = "whsec_new"
    body = '{"type":"payment.finalized"}'
    old_header = build_header(old_secret, NOW, body)
    new_header = build_header(new_secret, NOW, body)
    old_sig = old_header.split("v1=")[1]
    new_sig = new_header.split("v1=")[1]

    result = verify_webhook_signature(
        body=body,
        header=f"t={NOW},v1={new_sig},v1={old_sig}",
        secrets=[old_secret],
        now=NOW,
    )

    assert result.valid is True
    assert result.reason == "valid"


def test_invalid_signature() -> None:
    result = verify_webhook_signature(
        body='{"type":"payment.finalized"}',
        header=f"t={NOW},v1=invalid_signature",
        secret="whsec_test123",
        now=NOW,
    )

    assert result.valid is False
    assert result.reason == "invalid_signature"


def test_missing_header() -> None:
    result = verify_webhook_signature(
        body='{"type":"payment.finalized"}',
        header="",
        secret="whsec_test123",
        now=NOW,
    )

    assert result.valid is False
    assert result.reason == "missing_header"


def test_timestamp_too_old() -> None:
    result = verify_webhook_signature(
        body='{"type":"payment.finalized"}',
        header=f"t={NOW},v1=sig123",
        secret="whsec_test123",
        tolerance_seconds=300,
        now=NOW + 400,
    )

    assert result.valid is False
    assert result.reason == "timestamp_expired"


def test_invalid_header_format() -> None:
    result = verify_webhook_signature(
        body='{"type":"payment.finalized"}',
        header="t=not_a_number,v1=sig123",
        secret="whsec_test123",
        now=NOW,
    )

    assert result.valid is False
    assert result.reason == "invalid_format"


def test_webhooks_api_matches_server_routes() -> None:
    assert not hasattr(WebhooksApi, "retrieve")
    assert not hasattr(WebhooksApi, "delete")
    assert not hasattr(AsyncWebhooksApi, "retrieve")
    assert not hasattr(AsyncWebhooksApi, "delete")


def test_webhooks_api_exposes_delivery_and_replay_methods() -> None:
    for name in ("replay", "list_deliveries", "replay_delivery", "replay_dead_letters"):
        assert hasattr(WebhooksApi, name)
        assert hasattr(AsyncWebhooksApi, name)


class _FakeHttp:
    def __init__(self, response: Any) -> None:
        self.response = response
        self.last_request: dict[str, Any] = {}

    def request(self, **kwargs: Any) -> Any:
        self.last_request = kwargs
        return self.response


def test_create_endpoint_forwards_redact_metadata() -> None:
    http = _FakeHttp(
        {
            "id": "we_1",
            "url": "https://example.com/wh",
            "description": None,
            "enabled_events": ["payment.finalized"],
            "redact_metadata": True,
            "disabled_at": None,
            "created_at": "2026-06-01T00:00:00.000Z",
        }
    )
    api = WebhooksApi(http)  # type: ignore[arg-type]

    endpoint = api.create_endpoint(
        url="https://example.com/wh",
        enabled_events=["payment.finalized"],
        redact_metadata=True,
    )

    assert http.last_request["body"]["redact_metadata"] is True
    assert endpoint.redact_metadata is True


def test_list_deliveries_filters_and_parses() -> None:
    http = _FakeHttp(
        {
            "items": [
                {
                    "id": "wd_1",
                    "webhook_endpoint_id": "we_1",
                    "event_id": "evt_1",
                    "event_type": "payment.finalized",
                    "payment_order_id": "po_1",
                    "status": "failed",
                    "attempts": 3,
                    "response_status": 500,
                    "response_duration_ms": 120,
                    "error_message": "boom",
                    "next_retry_at": None,
                    "last_attempt_at": "2026-06-01T00:00:01.000Z",
                    "succeeded_at": None,
                    "dead_lettered_at": None,
                    "created_at": "2026-06-01T00:00:00.000Z",
                    "payload": {"type": "payment.finalized"},
                }
            ]
        }
    )
    api = WebhooksApi(http)  # type: ignore[arg-type]

    deliveries = api.list_deliveries(status="failed", endpoint_id="we_1", limit=20)

    assert http.last_request["query"] == {
        "status": "failed",
        "endpoint_id": "we_1",
        "payment_order_id": None,
        "limit": 20,
    }
    assert deliveries[0].attempts == 3
    assert deliveries[0].payload == {"type": "payment.finalized"}


def test_replay_dead_letters_parses_result() -> None:
    http = _FakeHttp(
        {
            "replayed": 2,
            "items": [
                {"original_id": "wd_1", "delivery_id": "wd_9"},
                {"original_id": "wd_2", "delivery_id": "wd_10"},
            ],
        }
    )
    api = WebhooksApi(http)  # type: ignore[arg-type]

    result = api.replay_dead_letters(endpoint_id="we_1", limit=100)

    assert http.last_request["path"] == "/v1/webhook-deliveries/replay-dead-letters"
    assert http.last_request["body"] == {"endpoint_id": "we_1", "limit": 100}
    assert result.replayed == 2
    assert result.items[0].delivery_id == "wd_9"

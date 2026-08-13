"""Tests for Payment Orders API wire mapping."""

from typing import Any, Dict

from stableops.payment_orders import PaymentOrdersApi


def _wire_order(**overrides: Any) -> Dict[str, Any]:
    wire = {
        "id": "po_1",
        "merchant_order_id": "m_1",
        "amount": "10.005",
        "requested_amount": "10.00",
        "settlement_asset": "USDC",
        "status": "created",
        "expires_at": None,
        "metadata": None,
        "created_at": "2026-06-01T00:00:00.000Z",
        "accepted_assets": [{"chain": "base-sepolia", "asset": "USDC"}],
        "payment_instructions": [{"chain": "base-sepolia", "asset": "USDC", "address": "0xabc"}],
    }
    wire.update(overrides)
    return wire


class FakeHttp:
    def __init__(self, response: Dict[str, Any]) -> None:
        self.response = response
        self.last_request: Dict[str, Any] = {}

    def request(self, **kwargs: Any) -> Dict[str, Any]:
        self.last_request = kwargs
        return self.response


def test_create_does_not_send_settlement_asset_and_forwards_amount_mode() -> None:
    http = FakeHttp(_wire_order())
    api = PaymentOrdersApi(http)  # type: ignore[arg-type]

    order = api.create(
        merchant_order_id="m_1",
        amount="10.00",
        accepted_assets=[{"chain": "base-sepolia", "asset": "USDC"}],
        expires_at="2026-06-20T12:30:00Z",
        amount_mode="auto",
    )

    body = http.last_request["body"]
    assert "settlement_asset" not in body
    assert body["amount_mode"] == "auto"
    assert http.last_request["idempotency_key"] == "m_1"
    assert http.last_request["retryable"] is True
    # requested_amount 透传，settlement_asset 可空
    assert order.requested_amount == "10.00"
    assert order.settlement_asset == "USDC"


def test_amount_mode_omitted_when_not_provided() -> None:
    http = FakeHttp(_wire_order())
    api = PaymentOrdersApi(http)  # type: ignore[arg-type]

    api.create(
        merchant_order_id="m_1",
        amount="10.00",
        accepted_assets=[{"chain": "base-sepolia", "asset": "USDC"}],
        expires_at="2026-06-20T12:30:00Z",
    )

    assert "amount_mode" not in http.last_request["body"]


def test_from_wire_tolerates_missing_settlement_asset() -> None:
    wire = _wire_order()
    wire.pop("settlement_asset")
    wire.pop("requested_amount")
    http = FakeHttp(wire)
    api = PaymentOrdersApi(http)  # type: ignore[arg-type]

    order = api.create(
        merchant_order_id="m_1",
        amount="10.00",
        accepted_assets=[{"chain": "base-sepolia", "asset": "USDC"}],
        expires_at="2026-06-20T12:30:00Z",
    )

    assert order.settlement_asset is None
    assert order.requested_amount is None


def test_list_page_preserves_pagination_metadata() -> None:
    http = FakeHttp({"items": [_wire_order()], "has_more": True, "total": 3})
    api = PaymentOrdersApi(http)  # type: ignore[arg-type]

    page = api.list_page(limit=1, offset=1)

    assert page.has_more is True
    assert page.total == 3
    assert http.last_request["query"]["offset"] == 1

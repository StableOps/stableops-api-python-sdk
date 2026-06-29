"""Tests for Checkout Sessions API."""

from typing import Any, Dict

from stableops.checkout_sessions import CheckoutSessionsApi


def _wire_session(**overrides: Any) -> Dict[str, Any]:
    wire = {
        "id": "cs_1",
        "client_secret": "cs_secret_abc",
        "status": "open",
        "title": "Pro plan",
        "description": None,
        "success_url": "https://shop.example/success",
        "cancel_url": None,
        "walletconnect_project_id": "wc_proj_1",
        "expires_at": None,
        "created_at": "2026-06-01T00:00:00.000Z",
        "payment_order": {
            "id": "po_1",
            "merchant_order_id": "m_1",
            "amount": "10.00",
            "requested_amount": "10.00",
            "settlement_asset": "USDC",
            "status": "created",
            "expires_at": None,
            "metadata": None,
            "created_at": "2026-06-01T00:00:00.000Z",
            "accepted_assets": [{"chain": "base-sepolia", "asset": "USDC"}],
            "payment_instructions": [{"chain": "base-sepolia", "asset": "USDC", "address": "0xabc"}],
        },
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


def test_create_builds_hosted_url_from_client_secret() -> None:
    http = FakeHttp(_wire_session())
    api = CheckoutSessionsApi(http, checkout_base_url="https://pay.example.com/")  # type: ignore[arg-type]

    session = api.create(
        merchant_order_id="m_1",
        amount="10.00",
        accepted_assets=[{"chain": "base-sepolia", "asset": "USDC"}],
        expires_at="2026-06-20T12:30:00Z",
        title="Pro plan",
        walletconnect_project_id="wc_proj_1",
    )

    assert http.last_request["path"] == "/v1/checkout-sessions"
    assert http.last_request["idempotency_key"] == "m_1"
    assert http.last_request["body"]["walletconnect_project_id"] == "wc_proj_1"
    # 末尾斜杠被去掉，url 由 client_secret 拼出
    assert session.url == "https://pay.example.com/c/cs_1?client_secret=cs_secret_abc"
    assert session.payment_order.id == "po_1"


def test_create_default_base_url() -> None:
    http = FakeHttp(_wire_session())
    api = CheckoutSessionsApi(http)  # type: ignore[arg-type]

    session = api.create(
        merchant_order_id="m_1",
        amount="10.00",
        accepted_assets=[{"chain": "base-sepolia", "asset": "USDC"}],
        expires_at="2026-06-20T12:30:00Z",
    )

    assert session.url is not None
    assert session.url.startswith("https://pay.stableops.dev/c/cs_1?client_secret=")


def test_url_is_none_without_client_secret() -> None:
    http = FakeHttp(_wire_session(client_secret=None))
    api = CheckoutSessionsApi(http)  # type: ignore[arg-type]

    session = api.create(
        merchant_order_id="m_1",
        amount="10.00",
        accepted_assets=[{"chain": "base-sepolia", "asset": "USDC"}],
        expires_at="2026-06-20T12:30:00Z",
    )

    assert session.url is None

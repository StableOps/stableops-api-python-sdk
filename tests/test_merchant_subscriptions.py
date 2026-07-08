"""Tests for merchant subscription APIs."""

from typing import Any, Dict

from stableops.client import StableOps
from stableops.merchant_subscriptions import MerchantPortalApi, MerchantSubscriptionsApi


def _wire_plan(**overrides: Any) -> Dict[str, Any]:
    wire = {
        "id": "plan_1",
        "code": "starter",
        "name": "Starter",
        "description": None,
        "group_key": "demo",
        "amount": "0.01",
        "interval": "month",
        "interval_count": 1,
        "trial_days": None,
        "metadata": {"source": "sdk"},
        "is_active": True,
        "is_template": False,
        "created_at": "2026-07-06T00:00:00.000Z",
        "updated_at": "2026-07-06T00:00:00.000Z",
    }
    wire.update(overrides)
    return wire


def _wire_subscription(**overrides: Any) -> Dict[str, Any]:
    wire = {
        "id": "sub_1",
        "merchant_user_id": "user_1",
        "plan_id": "plan_1",
        "status": "active",
        "current_period_start": "2026-07-01T00:00:00.000Z",
        "current_period_end": "2026-08-01T00:00:00.000Z",
        "cancel_at_period_end": False,
        "pending_plan_id": None,
        "pending_plan_change_at": None,
        "trial_ends_at": None,
        "canceled_at": None,
        "created_at": "2026-07-01T00:00:00.000Z",
        "updated_at": "2026-07-01T00:00:00.000Z",
    }
    wire.update(overrides)
    return wire


def _wire_invoice(**overrides: Any) -> Dict[str, Any]:
    wire = {
        "id": "inv_1",
        "subscription_id": "sub_1",
        "merchant_user_id": "user_1",
        "kind": "first",
        "period_start": "2026-07-01T00:00:00.000Z",
        "period_end": "2026-08-01T00:00:00.000Z",
        "amount": "0.01",
        "asset": None,
        "status": "open",
        "payment_order_id": "po_1",
        "target_plan_id": None,
        "due_at": "2026-07-08T00:00:00.000Z",
        "paid_at": None,
        "created_at": "2026-07-01T00:00:00.000Z",
        "updated_at": "2026-07-01T00:00:00.000Z",
    }
    wire.update(overrides)
    return wire


def _wire_payment_order(**overrides: Any) -> Dict[str, Any]:
    wire = {
        "id": "po_1",
        "merchant_order_id": "euinv_inv_1",
        "amount": "0.01",
        "requested_amount": "0.01",
        "settlement_asset": "USDC",
        "status": "created",
        "expires_at": "2026-07-06T00:30:00.000Z",
        "metadata": None,
        "created_at": "2026-07-06T00:00:00.000Z",
        "accepted_assets": [{"chain": "base-sepolia", "asset": "USDC"}],
        "payment_instructions": [
            {
                "chain": "base-sepolia",
                "asset": "USDC",
                "address": "0x0000000000000000000000000000000000000001",
            },
        ],
    }
    wire.update(overrides)
    return wire


class FakeHttp:
    def __init__(self, response: Any) -> None:
        self.response = response
        self.last_request: Dict[str, Any] = {}

    def request(self, **kwargs: Any) -> Any:
        self.last_request = kwargs
        return self.response


def test_plan_create_uses_snake_case_body_and_idempotency_key() -> None:
    http = FakeHttp(_wire_plan())
    api = MerchantSubscriptionsApi(http)  # type: ignore[arg-type]

    plan = api.plans.create(
        code="starter",
        name="Starter",
        group_key="demo",
        amount="0.01",
        interval="month",
        interval_count=1,
        idempotency_key="plan_starter",
    )

    assert http.last_request["path"] == "/v1/merchant/plans"
    assert http.last_request["idempotency_key"] == "plan_starter"
    assert http.last_request["body"] == {
        "code": "starter",
        "name": "Starter",
        "group_key": "demo",
        "amount": "0.01",
        "interval": "month",
        "interval_count": 1,
    }
    assert plan.group_key == "demo"
    assert plan.interval_count == 1
    assert plan.created_at == "2026-07-06T00:00:00.000Z"


def test_invoice_list_sends_filters_and_maps_fields() -> None:
    http = FakeHttp([_wire_invoice()])
    api = MerchantSubscriptionsApi(http)  # type: ignore[arg-type]

    invoices = api.invoices.list(
        status="open",
        merchant_user_id="user_1",
        subscription_id="sub_1",
    )

    assert http.last_request["path"] == "/v1/merchant/invoices"
    assert http.last_request["query"] == {
        "status": "open",
        "merchant_user_id": "user_1",
        "subscription_id": "sub_1",
    }
    assert invoices[0].subscription_id == "sub_1"
    assert invoices[0].merchant_user_id == "user_1"
    assert invoices[0].payment_order_id == "po_1"
    assert invoices[0].asset is None


def test_subscription_change_plan_maps_pending_result() -> None:
    http = FakeHttp(
        {
            "subscription": _wire_subscription(pending_plan_id="plan_2"),
            "invoice": _wire_invoice(kind="upgrade_proration", target_plan_id="plan_2"),
            "pending": False,
        }
    )
    api = MerchantSubscriptionsApi(http)  # type: ignore[arg-type]

    result = api.subscriptions.change_plan(
        "sub_1",
        plan_id="plan_2",
        idempotency_key="change_1",
    )

    assert http.last_request["path"] == "/v1/merchant/subscriptions/sub_1/change-plan"
    assert http.last_request["body"] == {"plan_id": "plan_2"}
    assert http.last_request["idempotency_key"] == "change_1"
    assert result.subscription.pending_plan_id == "plan_2"
    assert result.invoice is not None
    assert result.invoice.target_plan_id == "plan_2"
    assert result.pending is False


def test_portal_invoice_checkout_session_builds_checkout_url() -> None:
    http = FakeHttp(
        {
            "checkout_session_id": "cs_1",
            "client_secret": "cs_secret",
            "payment_order": _wire_payment_order(),
        }
    )
    api = MerchantPortalApi(
        http,  # type: ignore[arg-type]
        checkout_base_url="https://checkout.test/",
    )

    session = api.invoices.checkout_session(
        "inv_1",
        accepted_assets=[{"chain": "base-sepolia", "asset": "USDC"}],
        success_url="https://merchant.test/success",
        cancel_url="https://merchant.test/cancel",
        walletconnect_project_id="wc_123",
        idempotency_key="checkout_1",
    )

    assert http.last_request["path"] == "/v1/merchant/portal/invoices/inv_1/checkout-session"
    assert http.last_request["body"] == {
        "success_url": "https://merchant.test/success",
        "cancel_url": "https://merchant.test/cancel",
        "walletconnect_project_id": "wc_123",
        "accepted_assets": [{"chain": "base-sepolia", "asset": "USDC"}],
    }
    assert http.last_request["idempotency_key"] == "checkout_1"
    assert session.checkout_session_id == "cs_1"
    assert session.client_secret == "cs_secret"
    assert session.checkout_url == "https://checkout.test/c/cs_1?client_secret=cs_secret"


def test_portal_invoice_pay_sends_accepted_assets() -> None:
    http = FakeHttp(
        {
            "invoice_id": "inv_1",
            "payment_order_id": "po_1",
            "status": "open",
            "payment_order": _wire_payment_order(),
        }
    )
    api = MerchantPortalApi(http)  # type: ignore[arg-type]

    result = api.invoices.pay(
        "inv_1",
        accepted_assets=[{"chain": "base-sepolia", "asset": "USDC"}],
        idempotency_key="pay_1",
    )

    assert http.last_request["path"] == "/v1/merchant/portal/invoices/inv_1/pay"
    assert http.last_request["body"] == {
        "accepted_assets": [{"chain": "base-sepolia", "asset": "USDC"}],
    }
    assert http.last_request["idempotency_key"] == "pay_1"
    assert result.payment_order_id == "po_1"
    assert result.payment_order.merchant_order_id == "euinv_inv_1"


def test_stableops_portal_uses_portal_token_and_parent_options() -> None:
    client = StableOps(
        api_key="sk_sandbox_parent",
        base_url="https://api.test.local",
        checkout_base_url="https://checkout.test",
    )

    try:
        portal = client.portal("eps_token")
        assert portal.checkout_base_url == "https://checkout.test"
        assert portal.plans.http.client.headers["authorization"] == "Bearer eps_token"
        assert portal.plans.http.base_url == "https://api.test.local"
    finally:
        client.close()


def test_optional_fields_are_omitted_from_write_bodies() -> None:
    http = FakeHttp(_wire_plan())
    api = MerchantSubscriptionsApi(http)  # type: ignore[arg-type]

    api.plans.update("plan_1", name="Starter v2")

    assert http.last_request["path"] == "/v1/merchant/plans/plan_1"
    assert http.last_request["body"] == {"name": "Starter v2"}


def test_settings_update_uses_wire_field_names() -> None:
    http = FakeHttp(
        {
            "pay_window_days": 3,
            "renewal_lead_days": 2,
            "grace_days": 1,
            "payment_amount_mode": "auto",
        }
    )
    api = MerchantSubscriptionsApi(http)  # type: ignore[arg-type]

    settings = api.settings.update(
        pay_window_days=3,
        payment_amount_mode="auto",
    )

    assert http.last_request["path"] == "/v1/merchant/settings"
    assert http.last_request["body"] == {
        "pay_window_days": 3,
        "payment_amount_mode": "auto",
    }
    assert settings.pay_window_days == 3
    assert settings.payment_amount_mode == "auto"


def test_portal_session_create_maps_token_response() -> None:
    http = FakeHttp(
        {
            "id": "eps_1",
            "portal_token": "eps_token",
            "expires_at": "2026-07-07T00:00:00.000Z",
        }
    )
    api = MerchantSubscriptionsApi(http)  # type: ignore[arg-type]

    session = api.portal_sessions.create(
        merchant_user_id="user_1",
        expires_at="2026-07-07T00:00:00.000Z",
    )

    assert http.last_request["path"] == "/v1/merchant/portal-sessions"
    assert http.last_request["body"] == {
        "merchant_user_id": "user_1",
        "expires_at": "2026-07-07T00:00:00.000Z",
    }
    assert session.portal_token == "eps_token"


def test_portal_invoice_payment_status_allows_missing_payment_order() -> None:
    http = FakeHttp({"invoice_id": "inv_1", "status": "open", "payment_order": None})
    api = MerchantPortalApi(http)  # type: ignore[arg-type]

    status = api.invoices.payment_status("inv_1")

    assert http.last_request["path"] == "/v1/merchant/portal/invoices/inv_1/payment-status"
    assert status.invoice_id == "inv_1"
    assert status.payment_order is None

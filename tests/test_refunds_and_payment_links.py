"""退款与支付链接的请求、响应以及重试约束。"""

import inspect
import json
from typing import Any, Dict

import httpx
import pytest
import respx

from stableops import (
    AcceptedAssetInput,
    AsyncStableOps,
    CreatePaymentLinkInput,
    StableOps,
    StableOpsError,
    UpdatePaymentLinkInput,
)

BASE_URL = "https://api.test.local"
REFUND: Dict[str, Any] = {
    "id": "ref_1",
    "payment_order_id": "po_1",
    "source_payment_event_id": "evt_1",
    "chain": "base-sepolia",
    "asset": "USDC",
    "amount": "2.50",
    "amount_minor": "2500000",
    "source_address": "0xmerchant",
    "destination_address": "0xpayer",
    "status": "requested",
    "tx_hash": None,
    "failure_reason": None,
    "submitted_at": None,
    "confirmed_at": None,
    "canceled_at": None,
    "created_at": "2026-10-11T00:00:00.000Z",
    "updated_at": "2026-10-11T00:00:00.000Z",
}
LINK: Dict[str, Any] = {
    "id": "pl_1",
    "slug": "demo",
    "title": "Demo",
    "description": None,
    "amount": "10.00",
    "amount_mode": "auto",
    "settlement_asset": None,
    "accepted_assets": [{"chain": "base-sepolia", "asset": "USDC"}],
    "success_url": None,
    "cancel_url": None,
    "walletconnect_project_id": None,
    "expires_in_minutes": 25,
    "payer_fields": ["email"],
    "status": "active",
    "checkout_count": 3,
    "created_at": "2026-10-11T00:00:00.000Z",
    "updated_at": "2026-10-11T00:00:00.000Z",
}


async def resolve(result: Any) -> Any:
    if inspect.isawaitable(result):
        return await result
    return result


@pytest.mark.parametrize("asynchronous", [False, True])
async def test_refund_lifecycle_and_pagination(asynchronous: bool) -> None:
    client = (AsyncStableOps if asynchronous else StableOps)(base_url=BASE_URL)
    with respx.mock as mock:
        create = mock.post(f"{BASE_URL}/v1/refunds").respond(201, json=REFUND)
        mock.get(f"{BASE_URL}/v1/refunds/ref%2F1").respond(200, json=REFUND)
        submit = mock.post(f"{BASE_URL}/v1/refunds/ref%2F1/submit").respond(
            200, json={**REFUND, "status": "submitted", "tx_hash": "0xtx"}
        )
        mock.post(f"{BASE_URL}/v1/refunds/ref%2F1/cancel").respond(
            200, json={**REFUND, "status": "canceled"}
        )
        listing = mock.get(f"{BASE_URL}/v1/refunds").respond(
            200, json={"items": [REFUND], "has_more": True, "total": 21}
        )
        try:
            refund = await resolve(client.refunds.create("po_1", "2.50", "0xpayer"))
            assert json.loads(create.calls.last.request.content) == {
                "payment_order_id": "po_1",
                "amount": "2.50",
                "destination_address": "0xpayer",
            }
            assert refund.source_payment_event_id == "evt_1"
            assert refund.amount_minor == "2500000"
            assert refund.tx_hash is None
            assert (await resolve(client.refunds.retrieve("ref/1"))).id == "ref_1"
            assert (await resolve(client.refunds.submit("ref/1", "0xtx"))).status == "submitted"
            assert json.loads(submit.calls.last.request.content) == {"tx_hash": "0xtx"}
            assert (await resolve(client.refunds.cancel("ref/1"))).status == "canceled"
            page = await resolve(
                client.refunds.list_page(
                    payment_order_id="po_1", status="requested", limit=10, offset=10
                )
            )
            assert (page.total, page.has_more, page.items[0].id) == (21, True, "ref_1")
            assert dict(listing.calls.last.request.url.params) == {
                "payment_order_id": "po_1",
                "status": "requested",
                "limit": "10",
                "offset": "10",
            }
            assert (await resolve(client.refunds.list()))[0].id == "ref_1"
        finally:
            await resolve(client.close())


@pytest.mark.parametrize("asynchronous", [False, True])
async def test_payment_link_nullable_updates_and_order_details(asynchronous: bool) -> None:
    client = (AsyncStableOps if asynchronous else StableOps)(base_url=BASE_URL)
    with respx.mock as mock:
        create = mock.post(f"{BASE_URL}/v1/payment-links").respond(201, json=LINK)
        update = mock.patch(f"{BASE_URL}/v1/payment-links/pl%2F1").respond(200, json=LINK)
        mock.get(f"{BASE_URL}/v1/payment-links").respond(
            200, json={"items": [LINK], "has_more": True, "total": 12}
        )
        orders = mock.get(f"{BASE_URL}/v1/payment-links/pl_1/orders").respond(
            200,
            json={
                "link": LINK,
                "total": 1,
                "has_more": False,
                "completed": 1,
                "items": [
                    {
                        "id": "po_1",
                        "merchant_order_id": "merchant_1",
                        "amount": "10.005",
                        "status": "finalized",
                        "created_at": LINK["created_at"],
                        "payer": {"email": "payer@example.com"},
                        "payments": [
                            {
                                "chain": "base-sepolia",
                                "asset": "USDC",
                                "amount": "10.005",
                                "tx_hash": "0xtx",
                            }
                        ],
                    }
                ],
            },
        )
        try:
            link = await resolve(
                client.payment_links.create(
                    CreatePaymentLinkInput(
                        title="Demo",
                        amount="10.00",
                        amount_mode="auto",
                        accepted_assets=[AcceptedAssetInput(chain="base-sepolia", asset="USDC")],
                        expires_in_minutes=25,
                        payer_fields=["email"],
                    )
                )
            )
            assert json.loads(create.calls.last.request.content) == {
                "title": "Demo",
                "amount": "10.00",
                "amount_mode": "auto",
                "accepted_assets": [{"chain": "base-sepolia", "asset": "USDC"}],
                "expires_in_minutes": 25,
                "payer_fields": ["email"],
            }
            assert (link.checkout_count, link.settlement_asset) == (3, None)
            await resolve(
                client.payment_links.update(
                    "pl/1",
                    UpdatePaymentLinkInput(
                        description=None,
                        success_url=None,
                        payer_fields=[],
                    ),
                )
            )
            assert json.loads(update.calls.last.request.content) == {
                "description": None,
                "success_url": None,
                "payer_fields": [],
            }
            page = await resolve(client.payment_links.list_page(limit=5, offset=5))
            assert (page.total, page.has_more) == (12, True)
            assert (await resolve(client.payment_links.list()))[0].id == "pl_1"
            order_page = await resolve(
                client.payment_links.orders("pl_1", status="finalized", limit=5, offset=0)
            )
            assert dict(orders.calls.last.request.url.params) == {
                "status": "finalized",
                "limit": "5",
                "offset": "0",
            }
            assert (order_page.total, order_page.has_more, order_page.completed) == (1, False, 1)
            assert order_page.items[0].payer.email == "payer@example.com"
            assert order_page.items[0].payments[0].tx_hash == "0xtx"
        finally:
            await resolve(client.close())


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize(
    "operation", ["refund_create", "refund_submit", "refund_cancel", "link_create", "link_update"]
)
async def test_write_requests_do_not_retry(asynchronous: bool, operation: str) -> None:
    client = (AsyncStableOps if asynchronous else StableOps)(base_url=BASE_URL, max_retries=3)
    with respx.mock as mock:
        route = mock.route(host="api.test.local").mock(
            return_value=httpx.Response(503, json={"code": "unavailable"})
        )
        try:
            with pytest.raises(StableOpsError) as error:
                if operation == "refund_create":
                    await resolve(client.refunds.create("po_1", "2.50", "0xpayer"))
                elif operation == "refund_submit":
                    await resolve(client.refunds.submit("ref_1", "0xtx"))
                elif operation == "refund_cancel":
                    await resolve(client.refunds.cancel("ref_1"))
                elif operation == "link_create":
                    await resolve(
                        client.payment_links.create(
                            CreatePaymentLinkInput(
                                title="Demo",
                                amount="10.00",
                                accepted_assets=[
                                    AcceptedAssetInput(chain="base-sepolia", asset="USDC")
                                ],
                            )
                        )
                    )
                else:
                    await resolve(
                        client.payment_links.update(
                            "pl_1", UpdatePaymentLinkInput(status="inactive")
                        )
                    )
            assert error.value.status == 503
            assert route.call_count == 1
        finally:
            await resolve(client.close())

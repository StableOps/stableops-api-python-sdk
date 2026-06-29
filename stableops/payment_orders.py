"""Payment Orders API."""

from typing import Any, Dict, List, Optional

from stableops.http import AsyncHttpClient, HttpClient
from stableops.types import (
    AmountMode,
    PaymentOrder,
    PaymentOrderDetail,
)


def _normalize_iso_datetime(dt: str) -> str:
    """Convert ISO datetime to Zod 4-compatible format (requires 'Z' suffix for UTC).

    Python's datetime.isoformat() produces '+00:00' for UTC, but Zod 4's
    iso.datetime() only accepts the 'Z' suffix and rejects '+00:00'.
    """
    if dt.endswith('+00:00'):
        return dt[:-6] + 'Z'
    if dt.endswith('+00:00.000'):
        return dt[:-9] + 'Z'
    return dt


def _to_create_body(
    merchant_order_id: str,
    amount: str,
    accepted_assets: List[Dict[str, Any]],
    expires_at: str,
    amount_mode: Optional[AmountMode],
    metadata: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """组装 create 请求体（结算资产由服务端导出，不再传入）。"""
    body: Dict[str, Any] = {
        "merchant_order_id": merchant_order_id,
        "amount": amount,
        "accepted_assets": accepted_assets,
        "expires_at": _normalize_iso_datetime(expires_at),
    }
    if amount_mode is not None:
        body["amount_mode"] = amount_mode
    if metadata:
        body["metadata"] = metadata
    return body


def _from_wire(wire: Dict[str, Any]) -> Dict[str, Any]:
    """Convert wire format (snake_case) to SDK model kwargs."""
    return {
        "id": wire["id"],
        "merchant_order_id": wire["merchant_order_id"],
        "amount": wire["amount"],
        "requested_amount": wire.get("requested_amount"),
        "settlement_asset": wire.get("settlement_asset"),
        "status": wire["status"],
        "expires_at": wire.get("expires_at"),
        "metadata": wire.get("metadata"),
        "created_at": wire["created_at"],
        "accepted_assets": wire.get("accepted_assets"),
        "payment_instructions": wire.get("payment_instructions", []),
    }


def _from_wire_detail(wire: Dict[str, Any]) -> Dict[str, Any]:
    """Convert wire format to SDK model kwargs with timeline."""
    base = _from_wire(wire)
    base["timeline"] = [
        {
            "from_status": entry.get("from"),
            "to": entry["to"],
            "reason": entry.get("reason"),
            "at": entry["at"],
        }
        for entry in wire.get("timeline", [])
    ]
    return base


class PaymentOrdersApi:
    """Payment Orders API (synchronous)."""

    def __init__(self, http: HttpClient) -> None:
        """Initialize Payment Orders API."""
        self.http = http

    def create(
        self,
        merchant_order_id: str,
        amount: str,
        accepted_assets: List[Dict[str, Any]],
        expires_at: str,
        amount_mode: Optional[AmountMode] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PaymentOrder:
        """Create a payment order.

        Args:
            merchant_order_id: Your unique order ID (idempotency key)
            amount: Amount in settlement asset (e.g., "10.00")
            accepted_assets: List of accepted payment methods
            expires_at: ISO 8601 expiration timestamp (required; ≤30min in sandbox, ≤24h in live)
            amount_mode: 'auto' 让服务端微调金额到唯一；省略默认 'exact'
            metadata: Custom metadata (optional, max 16 keys)

        Returns:
            Created payment order

        Example:
            >>> order = client.payment_orders.create(
            ...     merchant_order_id="order_123",
            ...     amount="10.00",
            ...     accepted_assets=[{"chain": "base-sepolia", "asset": "USDC"}],
            ...     expires_at="2026-06-20T12:30:00Z",
            ... )
        """
        body = _to_create_body(
            merchant_order_id, amount, accepted_assets, expires_at, amount_mode, metadata
        )
        response = self.http.request(
            method="POST",
            path="/v1/payment-orders",
            body=body,
            idempotency_key=merchant_order_id,
        )
        return PaymentOrder(**_from_wire(response))

    def retrieve(self, order_id: str) -> PaymentOrderDetail:
        """Retrieve a payment order by ID.

        Args:
            order_id: Payment order ID

        Returns:
            Payment order with timeline

        Example:
            >>> order = client.payment_orders.retrieve("po_abc123")
        """
        response = self.http.request(
            method="GET",
            path=f"/v1/payment-orders/{order_id}",
        )
        return PaymentOrderDetail(**_from_wire_detail(response))

    def list(
        self,
        status: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[PaymentOrder]:
        """List payment orders.

        Args:
            status: Filter by status (optional)
            limit: Maximum number of results (optional)

        Returns:
            List of payment orders

        Example:
            >>> orders = client.payment_orders.list(status="finalized", limit=10)
        """
        response = self.http.request(
            method="GET",
            path="/v1/payment-orders",
            query={"status": status, "limit": limit},
        )
        return [PaymentOrder(**_from_wire(item)) for item in response["items"]]

    def cancel(self, order_id: str) -> PaymentOrder:
        """Cancel a payment order.

        Args:
            order_id: Payment order ID

        Returns:
            Cancelled payment order

        Example:
            >>> order = client.payment_orders.cancel("po_abc123")
        """
        response = self.http.request(
            method="POST",
            path=f"/v1/payment-orders/{order_id}/cancel",
        )
        return PaymentOrder(**_from_wire(response))


class AsyncPaymentOrdersApi:
    """Payment Orders API (asynchronous)."""

    def __init__(self, http: AsyncHttpClient) -> None:
        """Initialize async Payment Orders API."""
        self.http = http

    async def create(
        self,
        merchant_order_id: str,
        amount: str,
        accepted_assets: List[Dict[str, Any]],
        expires_at: str,
        amount_mode: Optional[AmountMode] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PaymentOrder:
        """Create a payment order (async).

        expires_at is required (≤30min in sandbox, ≤24h in live).
        amount_mode='auto' 让服务端微调金额到唯一；省略默认 'exact'。
        """
        body = _to_create_body(
            merchant_order_id, amount, accepted_assets, expires_at, amount_mode, metadata
        )
        response = await self.http.request(
            method="POST",
            path="/v1/payment-orders",
            body=body,
            idempotency_key=merchant_order_id,
        )
        return PaymentOrder(**_from_wire(response))

    async def retrieve(self, order_id: str) -> PaymentOrderDetail:
        """Retrieve a payment order by ID (async)."""
        response = await self.http.request(
            method="GET",
            path=f"/v1/payment-orders/{order_id}",
        )
        return PaymentOrderDetail(**_from_wire_detail(response))

    async def list(
        self,
        status: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[PaymentOrder]:
        """List payment orders (async)."""
        response = await self.http.request(
            method="GET",
            path="/v1/payment-orders",
            query={"status": status, "limit": limit},
        )
        return [PaymentOrder(**_from_wire(item)) for item in response["items"]]

    async def cancel(self, order_id: str) -> PaymentOrder:
        """Cancel a payment order (async)."""
        response = await self.http.request(
            method="POST",
            path=f"/v1/payment-orders/{order_id}/cancel",
        )
        return PaymentOrder(**_from_wire(response))

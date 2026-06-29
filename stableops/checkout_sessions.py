"""Checkout Sessions API (hosted WalletConnect checkout)."""

from typing import Any, Dict, List, Optional
from urllib.parse import quote

from stableops.http import AsyncHttpClient, HttpClient
from stableops.payment_orders import _from_wire as _order_from_wire
from stableops.types import AmountMode, CheckoutSession

DEFAULT_CHECKOUT_BASE_URL = "https://pay.stableops.dev"


def _to_create_body(
    merchant_order_id: str,
    amount: str,
    accepted_assets: List[Dict[str, Any]],
    expires_at: str,
    amount_mode: Optional[AmountMode],
    metadata: Optional[Dict[str, Any]],
    title: Optional[str],
    description: Optional[str],
    success_url: Optional[str],
    cancel_url: Optional[str],
    walletconnect_project_id: Optional[str],
) -> Dict[str, Any]:
    """组装 checkout session 创建请求体。"""
    body: Dict[str, Any] = {
        "merchant_order_id": merchant_order_id,
        "amount": amount,
        "accepted_assets": accepted_assets,
        "expires_at": expires_at,
    }
    if amount_mode is not None:
        body["amount_mode"] = amount_mode
    if metadata:
        body["metadata"] = metadata
    if title is not None:
        body["title"] = title
    if description is not None:
        body["description"] = description
    if success_url is not None:
        body["success_url"] = success_url
    if cancel_url is not None:
        body["cancel_url"] = cancel_url
    if walletconnect_project_id is not None:
        body["walletconnect_project_id"] = walletconnect_project_id
    return body


def _session_from_wire(wire: Dict[str, Any], checkout_base_url: str) -> Dict[str, Any]:
    """Convert checkout session wire format to SDK model kwargs."""
    client_secret = wire.get("client_secret")
    url: Optional[str] = None
    if client_secret:
        url = (
            f"{checkout_base_url}/c/{quote(wire['id'], safe='')}"
            f"?client_secret={quote(client_secret, safe='')}"
        )
    return {
        "id": wire["id"],
        "client_secret": client_secret,
        "url": url,
        "status": wire["status"],
        "title": wire.get("title"),
        "description": wire.get("description"),
        "success_url": wire.get("success_url"),
        "cancel_url": wire.get("cancel_url"),
        "walletconnect_project_id": wire.get("walletconnect_project_id"),
        "expires_at": wire.get("expires_at"),
        "created_at": wire["created_at"],
        "payment_order": _order_from_wire(wire["payment_order"]),
    }


class CheckoutSessionsApi:
    """Checkout Sessions API (synchronous)."""

    def __init__(self, http: HttpClient, checkout_base_url: Optional[str] = None) -> None:
        """Initialize Checkout Sessions API."""
        self.http = http
        self.checkout_base_url = (checkout_base_url or DEFAULT_CHECKOUT_BASE_URL).rstrip("/")

    def create(
        self,
        merchant_order_id: str,
        amount: str,
        accepted_assets: List[Dict[str, Any]],
        expires_at: str,
        amount_mode: Optional[AmountMode] = None,
        metadata: Optional[Dict[str, Any]] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None,
        walletconnect_project_id: Optional[str] = None,
    ) -> CheckoutSession:
        """Create a hosted checkout session.

        Returns a CheckoutSession whose ``url`` points at the hosted checkout page.

        Example:
            >>> session = client.checkout_sessions.create(
            ...     merchant_order_id="order_123",
            ...     amount="10.00",
            ...     accepted_assets=[{"chain": "base-sepolia", "asset": "USDC"}],
            ...     expires_at="2026-06-20T12:30:00Z",
            ...     title="Pro plan",
            ...     success_url="https://shop.example/success",
            ... )
            >>> print(session.url)
        """
        body = _to_create_body(
            merchant_order_id, amount, accepted_assets, expires_at, amount_mode, metadata,
            title, description, success_url, cancel_url, walletconnect_project_id,
        )
        response = self.http.request(
            method="POST",
            path="/v1/checkout-sessions",
            body=body,
            idempotency_key=merchant_order_id,
        )
        return CheckoutSession(**_session_from_wire(response, self.checkout_base_url))


class AsyncCheckoutSessionsApi:
    """Checkout Sessions API (asynchronous)."""

    def __init__(self, http: AsyncHttpClient, checkout_base_url: Optional[str] = None) -> None:
        """Initialize async Checkout Sessions API."""
        self.http = http
        self.checkout_base_url = (checkout_base_url or DEFAULT_CHECKOUT_BASE_URL).rstrip("/")

    async def create(
        self,
        merchant_order_id: str,
        amount: str,
        accepted_assets: List[Dict[str, Any]],
        expires_at: str,
        amount_mode: Optional[AmountMode] = None,
        metadata: Optional[Dict[str, Any]] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None,
        walletconnect_project_id: Optional[str] = None,
    ) -> CheckoutSession:
        """Create a hosted checkout session (async)."""
        body = _to_create_body(
            merchant_order_id, amount, accepted_assets, expires_at, amount_mode, metadata,
            title, description, success_url, cancel_url, walletconnect_project_id,
        )
        response = await self.http.request(
            method="POST",
            path="/v1/checkout-sessions",
            body=body,
            idempotency_key=merchant_order_id,
        )
        return CheckoutSession(**_session_from_wire(response, self.checkout_base_url))

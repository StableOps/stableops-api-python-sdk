"""StableOps client."""

from typing import Any, Optional

from stableops.addresses import AddressesApi, AsyncAddressesApi
from stableops.checkout_sessions import AsyncCheckoutSessionsApi, CheckoutSessionsApi
from stableops.http import AsyncHttpClient, DebugOption, HttpClient
from stableops.merchant_subscriptions import (
    AsyncMerchantPortalApi,
    AsyncMerchantSubscriptionsApi,
    MerchantPortalApi,
    MerchantSubscriptionsApi,
)
from stableops.payment_orders import AsyncPaymentOrdersApi, PaymentOrdersApi
from stableops.webhooks import AsyncWebhooksApi, WebhooksApi


class StableOps:
    """StableOps synchronous client.

    Example:
        >>> from stableops import StableOps
        >>> client = StableOps(
        ...     api_key="your_api_key",
        ... )
        >>> order = client.payment_orders.create(
        ...     merchant_order_id="order_123",
        ...     amount="10.00",
        ...     settlement_asset="USDC",
        ...     accepted_assets=[{"chain": "base-sepolia", "asset": "USDC"}],
        ...     expires_at="2026-06-20T12:30:00Z",
        ... )
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.stableops.dev",
        timeout: float = 30.0,
        max_retries: int = 2,
        debug: DebugOption = None,
        checkout_base_url: Optional[str] = None,
    ) -> None:
        """Initialize StableOps client.

        Args:
            api_key: API key for authentication
            base_url: Base API URL (default: "https://api.stableops.dev")
            timeout: Request timeout in seconds (default: 30.0)
            max_retries: Maximum number of retries (default: 2)
            debug: 打印初始化配置 / 请求 / 响应（敏感字段自动脱敏）；
                True 走 logging "stableops" logger，传可调用对象可自定义处理。
            checkout_base_url: 自定义收银台域名（默认 https://pay.stableops.dev），
                仅影响 checkout_sessions.create 返回的 url 拼接。
        """
        self._http = HttpClient(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            debug=debug,
        )
        self._base_url = base_url
        self._timeout = timeout
        self._max_retries = max_retries
        self._debug = debug
        self._checkout_base_url = checkout_base_url

        self.addresses = AddressesApi(self._http)
        self.merchant_subscriptions = MerchantSubscriptionsApi(self._http)
        self.payment_orders = PaymentOrdersApi(self._http)
        self.checkout_sessions = CheckoutSessionsApi(self._http, checkout_base_url)
        self.webhooks = WebhooksApi(self._http)

    def portal(self, portal_token: str) -> MerchantPortalApi:
        """Create an end-user portal client using a portal session token."""
        return MerchantPortalApi(
            HttpClient(
                api_key=portal_token,
                base_url=self._base_url,
                timeout=self._timeout,
                max_retries=self._max_retries,
                debug=self._debug,
            ),
            checkout_base_url=self._checkout_base_url,
        )

    def close(self) -> None:
        """Close HTTP client."""
        self._http.close()

    def __enter__(self) -> "StableOps":
        """Context manager entry."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        self.close()


class AsyncStableOps:
    """StableOps asynchronous client.

    Example:
        >>> import asyncio
        >>> from stableops import AsyncStableOps
        >>> async def main():
        ...     client = AsyncStableOps(api_key="your_api_key")
        ...     order = await client.payment_orders.create(
        ...         merchant_order_id="order_123",
        ...         amount="10.00",
        ...         settlement_asset="USDC",
        ...         accepted_assets=[{"chain": "base-sepolia", "asset": "USDC"}],
        ...         expires_at="2026-06-20T12:30:00Z",
        ...     )
        ...     print(f"Order created: {order.id}")
        >>> asyncio.run(main())
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.stableops.dev",
        timeout: float = 30.0,
        max_retries: int = 2,
        debug: DebugOption = None,
        checkout_base_url: Optional[str] = None,
    ) -> None:
        """Initialize async StableOps client.

        Args:
            api_key: API key for authentication
            base_url: Base API URL (default: "https://api.stableops.dev")
            timeout: Request timeout in seconds (default: 30.0)
            max_retries: Maximum number of retries (default: 2)
            debug: 见 StableOps 同名参数。
            checkout_base_url: 见 StableOps 同名参数。
        """
        self._http = AsyncHttpClient(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            debug=debug,
        )
        self._base_url = base_url
        self._timeout = timeout
        self._max_retries = max_retries
        self._debug = debug
        self._checkout_base_url = checkout_base_url

        self.addresses = AsyncAddressesApi(self._http)
        self.merchant_subscriptions = AsyncMerchantSubscriptionsApi(self._http)
        self.payment_orders = AsyncPaymentOrdersApi(self._http)
        self.checkout_sessions = AsyncCheckoutSessionsApi(self._http, checkout_base_url)
        self.webhooks = AsyncWebhooksApi(self._http)

    def portal(self, portal_token: str) -> AsyncMerchantPortalApi:
        """Create an async end-user portal client using a portal session token."""
        return AsyncMerchantPortalApi(
            AsyncHttpClient(
                api_key=portal_token,
                base_url=self._base_url,
                timeout=self._timeout,
                max_retries=self._max_retries,
                debug=self._debug,
            ),
            checkout_base_url=self._checkout_base_url,
        )

    async def close(self) -> None:
        """Close HTTP client."""
        await self._http.close()

    async def __aenter__(self) -> "AsyncStableOps":
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        await self.close()

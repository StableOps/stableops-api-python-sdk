"""StableOps Python SDK.

Official Python SDK for StableOps - Stablecoin payment infrastructure.

Example:
    >>> from stableops import StableOps
    >>> client = StableOps(api_key="your_api_key")
    >>> order = client.payment_orders.create(
    ...     merchant_order_id="order_123",
    ...     amount="10.00",
    ...     accepted_assets=[{"chain": "base", "asset": "USDC"}],
    ...     expires_at="2026-06-20T12:30:00Z",
    ... )
"""

from stableops.client import AsyncStableOps, StableOps
from stableops.errors import StableOpsError
from stableops.types import (
    AcceptedAssetInput,
    AmountMode,
    CheckoutSession,
    CheckoutSessionStatus,
    CreateCheckoutSessionInput,
    CreatePaymentOrderInput,
    CreateWebhookEndpointInput,
    PaymentOrder,
    PaymentOrderDetail,
    PaymentOrderInstruction,
    PaymentOrderStatus,
    PaymentOrderTimelineEntry,
    ReplayDeadLetterItem,
    ReplayDeadLettersResult,
    ReplayDeliveryResult,
    UpdateWebhookEndpointInput,
    WebhookDelivery,
    WebhookDeliveryStatus,
    WebhookEndpoint,
    WebhookEventType,
)
from stableops.webhooks import (
    DEFAULT_TOLERANCE_SECONDS,
    DELIVERY_ID_HEADER,
    EVENT_ID_HEADER,
    SIGNATURE_HEADER,
    verify_webhook_signature,
)

__version__ = "0.7.0"

__all__ = [
    # Client
    "StableOps",
    "AsyncStableOps",
    # Errors
    "StableOpsError",
    # Types
    "AcceptedAssetInput",
    "AmountMode",
    "CheckoutSession",
    "CheckoutSessionStatus",
    "CreateCheckoutSessionInput",
    "CreatePaymentOrderInput",
    "CreateWebhookEndpointInput",
    "PaymentOrder",
    "PaymentOrderDetail",
    "PaymentOrderInstruction",
    "PaymentOrderStatus",
    "PaymentOrderTimelineEntry",
    "ReplayDeadLetterItem",
    "ReplayDeadLettersResult",
    "ReplayDeliveryResult",
    "UpdateWebhookEndpointInput",
    "WebhookDelivery",
    "WebhookDeliveryStatus",
    "WebhookEndpoint",
    "WebhookEventType",
    # Webhooks
    "verify_webhook_signature",
    "SIGNATURE_HEADER",
    "EVENT_ID_HEADER",
    "DELIVERY_ID_HEADER",
    "DEFAULT_TOLERANCE_SECONDS",
]

"""Type definitions for StableOps SDK."""

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

# Type aliases
ChainId = Literal[
    "ethereum", "base", "base-sepolia", "arbitrum", "polygon",
    "optimism", "bsc", "tron", "solana",
    # 测试网（playground 用）
    "ethereum-sepolia", "arbitrum-sepolia", "polygon-amoy",
    "optimism-sepolia", "bsc-testnet", "solana-devnet", "tron-nile",
]
Asset = Literal["USDC", "USDT"]
# 'auto' 让服务端把金额微调到唯一（SHARED 地址免手动错开金额）；省略即默认 'exact'。
AmountMode = Literal["exact", "auto"]
PaymentOrderStatus = Literal[
    "created", "detected", "confirmed", "finalized", "reverted", "expired", "canceled"
]
CheckoutSessionStatus = Literal["open", "completed", "expired", "canceled"]
WebhookEventType = Literal[
    "payment_order.created",
    "payment.detected",
    "payment.confirmed",
    "payment.finalized",
    "payment.reverted",
    "payment.expired",
    "payment_order.canceled",
    "address.pool.low",
    "webhook.delivery.failed",
    "agent.action.requested",
    "agent.action.approved",
    "agent.action.executed",
]
WebhookDeliveryStatus = Literal["pending", "succeeded", "failed", "dead_letter"]


class AcceptedAssetInput(BaseModel):
    """Accepted asset configuration."""

    chain: ChainId
    asset: Asset


class CreatePaymentOrderInput(BaseModel):
    """Input for creating a payment order."""

    merchant_order_id: str = Field(..., description="Your unique order ID (idempotency key)")
    amount: str = Field(..., description="Amount in settlement asset (e.g., '10.00')")
    accepted_assets: List[AcceptedAssetInput] = Field(
        ..., description="List of accepted payment methods"
    )
    expires_at: str = Field(
        ...,
        description="ISO 8601 expiration timestamp (required; ≤30min in sandbox, ≤24h in live)",
    )
    amount_mode: Optional[AmountMode] = Field(
        None, description="'auto' 让服务端微调金额到唯一；省略默认 'exact'"
    )
    metadata: Optional[Dict[str, Any]] = Field(None, description="Custom metadata (max 16 keys)")


class PaymentOrderInstruction(BaseModel):
    """Payment instruction with address."""

    chain: ChainId
    asset: Asset
    address: str


class PaymentOrder(BaseModel):
    """Payment order response."""

    id: str
    merchant_order_id: str
    amount: str
    # 商户传入的基准金额；exact 单 == amount，auto 单为微调前金额（对账用）。
    requested_amount: Optional[str] = None
    # 结算资产由服务端导出；创建时不再传入，可能为空。
    settlement_asset: Optional[Asset] = None
    status: PaymentOrderStatus
    expires_at: Optional[str]
    metadata: Optional[Dict[str, Any]]
    created_at: str
    accepted_assets: Optional[List[AcceptedAssetInput]] = None
    payment_instructions: List[PaymentOrderInstruction] = Field(default_factory=list)


class PaymentOrderTimelineEntry(BaseModel):
    """Timeline entry for payment order status changes."""

    from_status: Optional[PaymentOrderStatus] = Field(None, alias="from")
    to: PaymentOrderStatus
    reason: Optional[str]
    at: str


class PaymentOrderDetail(PaymentOrder):
    """Detailed payment order with timeline."""

    timeline: List[PaymentOrderTimelineEntry]


class CreateCheckoutSessionInput(CreatePaymentOrderInput):
    """Input for creating a hosted checkout session."""

    title: Optional[str] = Field(None, description="Checkout page title")
    description: Optional[str] = Field(None, description="Checkout page description")
    success_url: Optional[str] = Field(None, description="Redirect URL after successful payment")
    cancel_url: Optional[str] = Field(None, description="Redirect URL after cancel")
    walletconnect_project_id: Optional[str] = Field(
        None, description="WalletConnect projectId for the hosted checkout"
    )


class CheckoutSession(BaseModel):
    """Hosted checkout session response."""

    id: str
    client_secret: Optional[str] = None
    # 由 client_secret + checkout_base_url 拼出的收银台链接。
    url: Optional[str] = None
    status: CheckoutSessionStatus
    title: Optional[str]
    description: Optional[str]
    success_url: Optional[str]
    cancel_url: Optional[str]
    walletconnect_project_id: Optional[str]
    expires_at: Optional[str]
    created_at: str
    payment_order: PaymentOrder


class NormalizedEvent(BaseModel):
    """Normalized blockchain event."""

    id: str
    chain: ChainId
    asset: Asset
    from_address: str
    to_address: str
    amount: str
    tx_hash: str
    log_index: int
    block_number: str
    payment_order_id: Optional[str]
    confirmations: int
    detected_at: str


class CreateWebhookEndpointInput(BaseModel):
    """Input for creating a webhook endpoint."""

    url: str = Field(..., description="Webhook URL (must be HTTPS in production)")
    description: Optional[str] = Field(None, description="Optional description")
    enabled_events: Optional[List[WebhookEventType]] = Field(
        None, description="List of event types to receive"
    )
    redact_metadata: Optional[bool] = Field(
        None, description="若为 true，投递 payload 中剔除订单 metadata"
    )


class UpdateWebhookEndpointInput(BaseModel):
    """Input for updating a webhook endpoint."""

    description: Optional[str] = None
    enabled_events: Optional[List[WebhookEventType]] = None
    redact_metadata: Optional[bool] = None


class WebhookEndpoint(BaseModel):
    """Webhook endpoint configuration."""

    id: str
    url: str
    description: Optional[str]
    enabled_events: List[WebhookEventType]
    redact_metadata: bool = False
    disabled_at: Optional[str]
    created_at: str
    secret: Optional[str] = None  # Only returned on create/rotate


class WebhookDelivery(BaseModel):
    """Webhook delivery record."""

    id: str
    webhook_endpoint_id: str
    event_id: str
    event_type: WebhookEventType
    payment_order_id: Optional[str]
    status: WebhookDeliveryStatus
    attempts: int
    response_status: Optional[int]
    response_duration_ms: Optional[int]
    error_message: Optional[str]
    next_retry_at: Optional[str]
    last_attempt_at: Optional[str]
    succeeded_at: Optional[str]
    dead_lettered_at: Optional[str]
    created_at: str
    # 完整事件 payload（与 replay 复用同一份）。
    payload: Dict[str, Any] = Field(default_factory=dict)


class ReplayDeliveryResult(BaseModel):
    """Result of replaying a single delivery / event."""

    delivery_id: str


class ReplayDeadLetterItem(BaseModel):
    """One replayed dead-letter mapping."""

    original_id: str
    delivery_id: str


class ReplayDeadLettersResult(BaseModel):
    """Result of batch replaying dead-letter deliveries."""

    replayed: int
    items: List[ReplayDeadLetterItem] = Field(default_factory=list)

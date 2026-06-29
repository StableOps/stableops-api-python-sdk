"""Webhooks API and signature verification."""

import hashlib
import hmac
import time
from typing import Any, Dict, List, NamedTuple, Optional, Sequence, Tuple, Union

from stableops.http import AsyncHttpClient, HttpClient
from stableops.types import (
    ReplayDeadLettersResult,
    ReplayDeliveryResult,
    WebhookDelivery,
    WebhookDeliveryStatus,
    WebhookEndpoint,
    WebhookEventType,
)

# ---- Signature verification constants ----

SIGNATURE_HEADER = "x-product-signature"
EVENT_ID_HEADER = "x-event-id"
DELIVERY_ID_HEADER = "x-delivery-id"

DEFAULT_TOLERANCE_SECONDS = 300  # 5 minutes


class VerificationResult(NamedTuple):
    """Result of webhook signature verification."""

    valid: bool
    reason: str


def verify_webhook_signature(
    body: Union[str, bytes],
    signature: Optional[str] = None,
    timestamp: Optional[str] = None,
    secret: Optional[str] = None,
    tolerance_seconds: int = DEFAULT_TOLERANCE_SECONDS,
    *,
    header: Optional[str] = None,
    secrets: Optional[Sequence[str]] = None,
    now: Optional[int] = None,
) -> VerificationResult:
    """Verify webhook signature.

    Args:
        body: Raw request body (string)
        header: X-Product-Signature header value (t=<unix_ts>,v1=<hmac>[,v1=<hmac>...])
        secret: Webhook secret from dashboard
        secrets: Optional rotation set of acceptable secrets
        tolerance_seconds: Maximum age of webhook (default 300 seconds)
        now: Current unix timestamp in seconds, primarily for tests
        signature/timestamp: Backward-compatible legacy arguments

    Returns:
        VerificationResult with valid flag and reason

    Example:
        >>> result = verify_webhook_signature(
        ...     body=request.body,
        ...     header=request.headers["X-Product-Signature"],
        ...     secret="whsec_...",
        ... )
        >>> if not result.valid:
        ...     return {"error": result.reason}, 401
    """
    legacy_mode = header is None and (signature is not None or timestamp is not None)
    if header is None:
        if legacy_mode:
            if not signature:
                return VerificationResult(False, "missing_signature")
            if not timestamp:
                return VerificationResult(False, "missing_timestamp")
            header = f"t={timestamp},v1={signature}"
        else:
            return VerificationResult(False, "missing_header")
    if not header:
        return VerificationResult(False, "missing_header")

    valid_secrets = [value for value in (secrets or ([secret] if secret else [])) if value]
    if not valid_secrets:
        return VerificationResult(False, "missing_secret")

    parsed = _parse_signature_header(header)
    if parsed is None:
        return VerificationResult(False, "invalid_timestamp" if legacy_mode else "invalid_format")
    ts, signatures = parsed

    current_time = int(time.time()) if now is None else now
    if abs(current_time - ts) > tolerance_seconds:
        return VerificationResult(False, "timestamp_too_old" if legacy_mode else "timestamp_expired")

    raw_body = body.decode("utf-8") if isinstance(body, bytes) else body
    signed_payload = f"{ts}.{raw_body}"
    for candidate_secret in valid_secrets:
        expected_signature = hmac.new(
            candidate_secret.encode("utf-8"),
            signed_payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        for candidate_signature in signatures:
            if hmac.compare_digest(candidate_signature, expected_signature):
                return VerificationResult(True, "valid")

    return VerificationResult(False, "invalid_signature")


def _parse_signature_header(header: str) -> Optional[Tuple[int, List[str]]]:
    timestamp: Optional[int] = None
    signatures: List[str] = []
    for segment in header.split(","):
        key, _, value = segment.strip().partition("=")
        if not key or not value:
            continue
        if key == "t":
            try:
                timestamp = int(value)
            except ValueError:
                return None
        elif key == "v1":
            signatures.append(value)
    if timestamp is None or not signatures:
        return None
    return timestamp, signatures


# ---- Webhook endpoints API ----

class WebhooksApi:
    """Webhooks API (synchronous)."""

    def __init__(self, http: HttpClient) -> None:
        """Initialize Webhooks API."""
        self.http = http

    def create_endpoint(
        self,
        url: str,
        description: Optional[str] = None,
        enabled_events: Optional[List[WebhookEventType]] = None,
        redact_metadata: Optional[bool] = None,
    ) -> WebhookEndpoint:
        """Create a webhook endpoint."""
        body: Dict[str, Any] = {"url": url}
        if description:
            body["description"] = description
        if enabled_events:
            body["enabled_events"] = enabled_events
        if redact_metadata is not None:
            body["redact_metadata"] = redact_metadata

        response = self.http.request(
            method="POST",
            path="/v1/webhook-endpoints",
            body=body,
        )
        return WebhookEndpoint(**response)

    def list_endpoints(self) -> List[WebhookEndpoint]:
        """List webhook endpoints."""
        response = self.http.request(
            method="GET",
            path="/v1/webhook-endpoints",
        )
        return [WebhookEndpoint(**item) for item in response["items"]]

    def update_endpoint(
        self,
        endpoint_id: str,
        description: Optional[str] = None,
        enabled_events: Optional[List[WebhookEventType]] = None,
        redact_metadata: Optional[bool] = None,
    ) -> WebhookEndpoint:
        """Update a webhook endpoint."""
        body: Dict[str, Any] = {}
        if description is not None:
            body["description"] = description
        if enabled_events is not None:
            body["enabled_events"] = enabled_events
        if redact_metadata is not None:
            body["redact_metadata"] = redact_metadata

        response = self.http.request(
            method="PATCH",
            path=f"/v1/webhook-endpoints/{endpoint_id}",
            body=body,
        )
        return WebhookEndpoint(**response)

    def rotate_secret(self, endpoint_id: str) -> WebhookEndpoint:
        """Rotate webhook endpoint secret."""
        response = self.http.request(
            method="POST",
            path=f"/v1/webhook-endpoints/{endpoint_id}/rotate-secret",
        )
        return WebhookEndpoint(**response)

    def replay(self, endpoint_id: str, event_id: str) -> ReplayDeliveryResult:
        """Replay an event to a specific endpoint (creates a fresh delivery)."""
        response = self.http.request(
            method="POST",
            path=f"/v1/webhook-endpoints/{endpoint_id}/replay",
            body={"event_id": event_id},
        )
        return ReplayDeliveryResult(**response)

    def list_deliveries(
        self,
        status: Optional[WebhookDeliveryStatus] = None,
        endpoint_id: Optional[str] = None,
        payment_order_id: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[WebhookDelivery]:
        """List webhook deliveries."""
        response = self.http.request(
            method="GET",
            path="/v1/webhook-deliveries",
            query={
                "status": status,
                "endpoint_id": endpoint_id,
                "payment_order_id": payment_order_id,
                "limit": limit,
            },
        )
        return [WebhookDelivery(**item) for item in response["items"]]

    def replay_delivery(self, delivery_id: str) -> ReplayDeliveryResult:
        """Replay a single delivery by its ID."""
        response = self.http.request(
            method="POST",
            path=f"/v1/webhook-deliveries/{delivery_id}/replay",
        )
        return ReplayDeliveryResult(**response)

    def replay_dead_letters(
        self,
        endpoint_id: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> ReplayDeadLettersResult:
        """Batch replay dead-lettered deliveries."""
        body: Dict[str, Any] = {}
        if endpoint_id is not None:
            body["endpoint_id"] = endpoint_id
        if limit is not None:
            body["limit"] = limit
        response = self.http.request(
            method="POST",
            path="/v1/webhook-deliveries/replay-dead-letters",
            body=body,
        )
        return ReplayDeadLettersResult(**response)


class AsyncWebhooksApi:
    """Webhooks API (asynchronous)."""

    def __init__(self, http: AsyncHttpClient) -> None:
        """Initialize async Webhooks API."""
        self.http = http

    async def create_endpoint(
        self,
        url: str,
        description: Optional[str] = None,
        enabled_events: Optional[List[WebhookEventType]] = None,
        redact_metadata: Optional[bool] = None,
    ) -> WebhookEndpoint:
        """Create a webhook endpoint (async)."""
        body: Dict[str, Any] = {"url": url}
        if description:
            body["description"] = description
        if enabled_events:
            body["enabled_events"] = enabled_events
        if redact_metadata is not None:
            body["redact_metadata"] = redact_metadata

        response = await self.http.request(
            method="POST",
            path="/v1/webhook-endpoints",
            body=body,
        )
        return WebhookEndpoint(**response)

    async def list_endpoints(self) -> List[WebhookEndpoint]:
        """List webhook endpoints (async)."""
        response = await self.http.request(
            method="GET",
            path="/v1/webhook-endpoints",
        )
        return [WebhookEndpoint(**item) for item in response["items"]]

    async def update_endpoint(
        self,
        endpoint_id: str,
        description: Optional[str] = None,
        enabled_events: Optional[List[WebhookEventType]] = None,
        redact_metadata: Optional[bool] = None,
    ) -> WebhookEndpoint:
        """Update a webhook endpoint (async)."""
        body: Dict[str, Any] = {}
        if description is not None:
            body["description"] = description
        if enabled_events is not None:
            body["enabled_events"] = enabled_events
        if redact_metadata is not None:
            body["redact_metadata"] = redact_metadata

        response = await self.http.request(
            method="PATCH",
            path=f"/v1/webhook-endpoints/{endpoint_id}",
            body=body,
        )
        return WebhookEndpoint(**response)

    async def rotate_secret(self, endpoint_id: str) -> WebhookEndpoint:
        """Rotate webhook endpoint secret (async)."""
        response = await self.http.request(
            method="POST",
            path=f"/v1/webhook-endpoints/{endpoint_id}/rotate-secret",
        )
        return WebhookEndpoint(**response)

    async def replay(self, endpoint_id: str, event_id: str) -> ReplayDeliveryResult:
        """Replay an event to a specific endpoint (async)."""
        response = await self.http.request(
            method="POST",
            path=f"/v1/webhook-endpoints/{endpoint_id}/replay",
            body={"event_id": event_id},
        )
        return ReplayDeliveryResult(**response)

    async def list_deliveries(
        self,
        status: Optional[WebhookDeliveryStatus] = None,
        endpoint_id: Optional[str] = None,
        payment_order_id: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[WebhookDelivery]:
        """List webhook deliveries (async)."""
        response = await self.http.request(
            method="GET",
            path="/v1/webhook-deliveries",
            query={
                "status": status,
                "endpoint_id": endpoint_id,
                "payment_order_id": payment_order_id,
                "limit": limit,
            },
        )
        return [WebhookDelivery(**item) for item in response["items"]]

    async def replay_delivery(self, delivery_id: str) -> ReplayDeliveryResult:
        """Replay a single delivery by its ID (async)."""
        response = await self.http.request(
            method="POST",
            path=f"/v1/webhook-deliveries/{delivery_id}/replay",
        )
        return ReplayDeliveryResult(**response)

    async def replay_dead_letters(
        self,
        endpoint_id: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> ReplayDeadLettersResult:
        """Batch replay dead-lettered deliveries (async)."""
        body: Dict[str, Any] = {}
        if endpoint_id is not None:
            body["endpoint_id"] = endpoint_id
        if limit is not None:
            body["limit"] = limit
        response = await self.http.request(
            method="POST",
            path="/v1/webhook-deliveries/replay-dead-letters",
            body=body,
        )
        return ReplayDeadLettersResult(**response)

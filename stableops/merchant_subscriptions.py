"""Merchant subscription APIs."""

from typing import Any, Dict, List, Optional, Union
from urllib.parse import quote

from stableops.checkout_sessions import DEFAULT_CHECKOUT_BASE_URL
from stableops.http import AsyncHttpClient, HttpClient
from stableops.payment_orders import _from_wire as _order_from_wire
from stableops.types import (
    AmountMode,
    EndUserInvoice,
    EndUserInvoiceStatus,
    EndUserSubscription,
    EndUserSubscriptionStatus,
    MerchantBillingSettings,
    MerchantInvoiceCheckoutSession,
    MerchantInvoicePaymentStatus,
    MerchantPlan,
    MerchantPlanInterval,
    MerchantSubscriptionChangePlanResult,
    MerchantSubscriptionCreateResult,
    PaymentOrder,
    PayMerchantInvoiceResponse,
    PortalSession,
)


def _compact(body: Dict[str, Any]) -> Dict[str, Any]:
    """Remove omitted optional fields from a request body."""
    return {key: value for key, value in body.items() if value is not None}


class _Unset:
    pass


_UNSET = _Unset()


def _plan_update_body(
    *,
    code: Optional[str],
    name: Optional[str],
    description: Union[str, None, _Unset],
    group_key: Optional[str],
    amount: Optional[str],
    interval: Optional[MerchantPlanInterval],
    interval_count: Optional[int],
    trial_days: Union[int, None, _Unset],
    metadata: Union[Dict[str, Any], None, _Unset],
    is_template: Optional[bool],
) -> Dict[str, Any]:
    """Build a plan update body while preserving explicit null values."""
    body = _compact(
        {
            "code": code,
            "name": name,
            "group_key": group_key,
            "amount": amount,
            "interval": interval,
            "interval_count": interval_count,
            "is_template": is_template,
        }
    )
    if description is not _UNSET:
        body["description"] = description
    if trial_days is not _UNSET:
        body["trial_days"] = trial_days
    if metadata is not _UNSET:
        body["metadata"] = metadata
    return body


def _path(value: str) -> str:
    """Encode a path segment."""
    return quote(value, safe="")


def _checkout_url(checkout_base_url: str, session_id: str, client_secret: str) -> str:
    """Build hosted checkout URL."""
    return (
        f"{checkout_base_url}/c/{quote(session_id, safe='')}"
        f"?client_secret={quote(client_secret, safe='')}"
    )


def _plan_from_wire(wire: Dict[str, Any]) -> MerchantPlan:
    return MerchantPlan(**wire)


def _subscription_from_wire(wire: Dict[str, Any]) -> EndUserSubscription:
    return EndUserSubscription(**wire)


def _invoice_from_wire(wire: Dict[str, Any]) -> EndUserInvoice:
    return EndUserInvoice(**wire)


def _create_result_from_wire(wire: Dict[str, Any]) -> MerchantSubscriptionCreateResult:
    invoice = wire.get("invoice")
    return MerchantSubscriptionCreateResult(
        subscription=_subscription_from_wire(wire["subscription"]),
        invoice=_invoice_from_wire(invoice) if invoice is not None else None,
    )


def _change_plan_result_from_wire(wire: Dict[str, Any]) -> MerchantSubscriptionChangePlanResult:
    invoice = wire.get("invoice")
    return MerchantSubscriptionChangePlanResult(
        subscription=_subscription_from_wire(wire["subscription"]),
        invoice=_invoice_from_wire(invoice) if invoice is not None else None,
        pending=wire["pending"],
    )


def _pay_invoice_from_wire(wire: Dict[str, Any]) -> PayMerchantInvoiceResponse:
    return PayMerchantInvoiceResponse(
        invoice_id=wire["invoice_id"],
        payment_order_id=wire["payment_order_id"],
        status=wire["status"],
        payment_order=PaymentOrder(**_order_from_wire(wire["payment_order"])),
    )


def _payment_status_from_wire(wire: Dict[str, Any]) -> MerchantInvoicePaymentStatus:
    payment_order = wire.get("payment_order")
    return MerchantInvoicePaymentStatus(
        invoice_id=wire["invoice_id"],
        status=wire["status"],
        payment_order=PaymentOrder(**_order_from_wire(payment_order))
        if payment_order is not None
        else None,
    )


def _checkout_session_from_wire(
    wire: Dict[str, Any],
    checkout_base_url: str,
) -> MerchantInvoiceCheckoutSession:
    return MerchantInvoiceCheckoutSession(
        checkout_session_id=wire["checkout_session_id"],
        client_secret=wire["client_secret"],
        checkout_url=_checkout_url(
            checkout_base_url,
            wire["checkout_session_id"],
            wire["client_secret"],
        ),
        payment_order=PaymentOrder(**_order_from_wire(wire["payment_order"])),
    )


class MerchantPlansResource:
    """Merchant plan APIs."""

    def __init__(self, http: HttpClient) -> None:
        self.http = http

    def list(
        self,
        group_key: Optional[str] = None,
        include_inactive: Optional[bool] = None,
    ) -> List[MerchantPlan]:
        response = self.http.request(
            method="GET",
            path="/v1/merchant/plans",
            query={
                "group_key": group_key,
                "include_inactive": "true" if include_inactive else None,
            },
        )
        return [_plan_from_wire(item) for item in response]

    def create(
        self,
        code: str,
        name: str,
        group_key: str,
        amount: str,
        interval: MerchantPlanInterval,
        interval_count: int,
        description: Optional[str] = None,
        trial_days: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        is_template: Optional[bool] = None,
        idempotency_key: Optional[str] = None,
    ) -> MerchantPlan:
        response = self.http.request(
            method="POST",
            path="/v1/merchant/plans",
            body=_compact(
                {
                    "code": code,
                    "name": name,
                    "description": description,
                    "group_key": group_key,
                    "amount": amount,
                    "interval": interval,
                    "interval_count": interval_count,
                    "trial_days": trial_days,
                    "metadata": metadata,
                    "is_template": is_template,
                }
            ),
            idempotency_key=idempotency_key,
        )
        return _plan_from_wire(response)

    def update(
        self,
        plan_id: str,
        code: Optional[str] = None,
        name: Optional[str] = None,
        description: Union[str, None, _Unset] = _UNSET,
        group_key: Optional[str] = None,
        amount: Optional[str] = None,
        interval: Optional[MerchantPlanInterval] = None,
        interval_count: Optional[int] = None,
        trial_days: Union[int, None, _Unset] = _UNSET,
        metadata: Union[Dict[str, Any], None, _Unset] = _UNSET,
        is_template: Optional[bool] = None,
        idempotency_key: Optional[str] = None,
    ) -> MerchantPlan:
        response = self.http.request(
            method="PUT",
            path=f"/v1/merchant/plans/{_path(plan_id)}",
            body=_plan_update_body(
                code=code,
                name=name,
                description=description,
                group_key=group_key,
                amount=amount,
                interval=interval,
                interval_count=interval_count,
                trial_days=trial_days,
                metadata=metadata,
                is_template=is_template,
            ),
            idempotency_key=idempotency_key,
        )
        return _plan_from_wire(response)

    def delete(self, plan_id: str, idempotency_key: Optional[str] = None) -> None:
        self.http.request(
            method="DELETE",
            path=f"/v1/merchant/plans/{_path(plan_id)}",
            idempotency_key=idempotency_key,
        )


class MerchantSubscriptionResource:
    """Merchant-managed end-user subscription APIs."""

    def __init__(self, http: HttpClient) -> None:
        self.http = http

    def create(
        self,
        plan_id: str,
        merchant_user_id: str,
        trial_days: Optional[int] = None,
        idempotency_key: Optional[str] = None,
    ) -> MerchantSubscriptionCreateResult:
        response = self.http.request(
            method="POST",
            path="/v1/merchant/subscriptions",
            body=_compact(
                {
                    "plan_id": plan_id,
                    "merchant_user_id": merchant_user_id,
                    "trial_days": trial_days,
                }
            ),
            idempotency_key=idempotency_key,
        )
        return _create_result_from_wire(response)

    def list(
        self,
        status: Optional[EndUserSubscriptionStatus] = None,
        merchant_user_id: Optional[str] = None,
    ) -> List[EndUserSubscription]:
        response = self.http.request(
            method="GET",
            path="/v1/merchant/subscriptions",
            query={"status": status, "merchant_user_id": merchant_user_id},
        )
        return [_subscription_from_wire(item) for item in response]

    def get(self, subscription_id: str) -> EndUserSubscription:
        response = self.http.request(
            method="GET",
            path=f"/v1/merchant/subscriptions/{_path(subscription_id)}",
        )
        return _subscription_from_wire(response)

    def get_by_merchant_user_id(self, merchant_user_id: str) -> EndUserSubscription:
        response = self.http.request(
            method="GET",
            path=f"/v1/merchant/subscriptions/by-user/{_path(merchant_user_id)}",
        )
        return _subscription_from_wire(response)

    def change_plan(
        self,
        subscription_id: str,
        plan_id: str,
        idempotency_key: Optional[str] = None,
    ) -> MerchantSubscriptionChangePlanResult:
        response = self.http.request(
            method="POST",
            path=f"/v1/merchant/subscriptions/{_path(subscription_id)}/change-plan",
            body={"plan_id": plan_id},
            idempotency_key=idempotency_key,
        )
        return _change_plan_result_from_wire(response)

    def cancel(
        self,
        subscription_id: str,
        immediate: Optional[bool] = None,
        idempotency_key: Optional[str] = None,
    ) -> EndUserSubscription:
        response = self.http.request(
            method="POST",
            path=f"/v1/merchant/subscriptions/{_path(subscription_id)}/cancel",
            body=_compact({"immediate": immediate}),
            idempotency_key=idempotency_key,
        )
        return _subscription_from_wire(response)

    def resume(
        self,
        subscription_id: str,
        idempotency_key: Optional[str] = None,
    ) -> EndUserSubscription:
        response = self.http.request(
            method="POST",
            path=f"/v1/merchant/subscriptions/{_path(subscription_id)}/resume",
            idempotency_key=idempotency_key,
        )
        return _subscription_from_wire(response)


class MerchantInvoicesResource:
    """Merchant invoice APIs."""

    def __init__(self, http: HttpClient) -> None:
        self.http = http

    def list(
        self,
        status: Optional[EndUserInvoiceStatus] = None,
        merchant_user_id: Optional[str] = None,
        subscription_id: Optional[str] = None,
    ) -> List[EndUserInvoice]:
        response = self.http.request(
            method="GET",
            path="/v1/merchant/invoices",
            query={
                "status": status,
                "merchant_user_id": merchant_user_id,
                "subscription_id": subscription_id,
            },
        )
        return [_invoice_from_wire(item) for item in response]

    def get(self, invoice_id: str) -> EndUserInvoice:
        response = self.http.request(
            method="GET",
            path=f"/v1/merchant/invoices/{_path(invoice_id)}",
        )
        return _invoice_from_wire(response)

    def pay(
        self,
        invoice_id: str,
        accepted_assets: List[Dict[str, Any]],
        idempotency_key: Optional[str] = None,
        amount_mode: Optional[AmountMode] = None,
    ) -> PayMerchantInvoiceResponse:
        response = self.http.request(
            method="POST",
            path=f"/v1/merchant/invoices/{_path(invoice_id)}/pay",
            body=_compact({"amount_mode": amount_mode, "accepted_assets": accepted_assets}),
            idempotency_key=idempotency_key,
        )
        return _pay_invoice_from_wire(response)

    def payment_status(self, invoice_id: str) -> MerchantInvoicePaymentStatus:
        response = self.http.request(
            method="GET",
            path=f"/v1/merchant/invoices/{_path(invoice_id)}/payment-status",
        )
        return _payment_status_from_wire(response)


class MerchantSettingsResource:
    """Merchant subscription billing settings APIs."""

    def __init__(self, http: HttpClient) -> None:
        self.http = http

    def get(self) -> MerchantBillingSettings:
        response = self.http.request(method="GET", path="/v1/merchant/settings")
        return MerchantBillingSettings(**response)

    def update(
        self,
        pay_window_days: Optional[int] = None,
        renewal_lead_days: Optional[int] = None,
        grace_days: Optional[int] = None,
        idempotency_key: Optional[str] = None,
    ) -> MerchantBillingSettings:
        response = self.http.request(
            method="PUT",
            path="/v1/merchant/settings",
            body=_compact(
                {
                    "pay_window_days": pay_window_days,
                    "renewal_lead_days": renewal_lead_days,
                    "grace_days": grace_days,
                }
            ),
            idempotency_key=idempotency_key,
        )
        return MerchantBillingSettings(**response)


class MerchantPortalSessionsResource:
    """Merchant-created end-user portal session APIs."""

    def __init__(self, http: HttpClient) -> None:
        self.http = http

    def create(
        self,
        merchant_user_id: str,
        expires_at: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> PortalSession:
        response = self.http.request(
            method="POST",
            path="/v1/merchant/portal-sessions",
            body=_compact({"merchant_user_id": merchant_user_id, "expires_at": expires_at}),
            idempotency_key=idempotency_key,
        )
        return PortalSession(**response)

    def revoke(self, session_id: str, idempotency_key: Optional[str] = None) -> None:
        self.http.request(
            method="DELETE",
            path=f"/v1/merchant/portal-sessions/{_path(session_id)}",
            idempotency_key=idempotency_key,
        )


class MerchantSubscriptionsApi:
    """Merchant subscriptions API (synchronous)."""

    def __init__(self, http: HttpClient) -> None:
        self.plans = MerchantPlansResource(http)
        self.subscriptions = MerchantSubscriptionResource(http)
        self.invoices = MerchantInvoicesResource(http)
        self.settings = MerchantSettingsResource(http)
        self.portal_sessions = MerchantPortalSessionsResource(http)


class MerchantPortalPlansResource:
    """End-user portal plan APIs."""

    def __init__(self, http: HttpClient) -> None:
        self.http = http

    def list(self) -> List[MerchantPlan]:
        response = self.http.request(method="GET", path="/v1/merchant/portal/plans")
        return [_plan_from_wire(item) for item in response]


class MerchantPortalSubscriptionResource:
    """End-user portal subscription APIs."""

    def __init__(self, http: HttpClient) -> None:
        self.http = http

    def get(self) -> EndUserSubscription:
        response = self.http.request(method="GET", path="/v1/merchant/portal/subscription")
        return _subscription_from_wire(response)

    def cancel(
        self,
        immediate: Optional[bool] = None,
        idempotency_key: Optional[str] = None,
    ) -> EndUserSubscription:
        response = self.http.request(
            method="POST",
            path="/v1/merchant/portal/subscription/cancel",
            body=_compact({"immediate": immediate}),
            idempotency_key=idempotency_key,
        )
        return _subscription_from_wire(response)

    def resume(self, idempotency_key: Optional[str] = None) -> EndUserSubscription:
        response = self.http.request(
            method="POST",
            path="/v1/merchant/portal/subscription/resume",
            idempotency_key=idempotency_key,
        )
        return _subscription_from_wire(response)

    def change_plan(
        self,
        plan_id: str,
        idempotency_key: Optional[str] = None,
    ) -> MerchantSubscriptionChangePlanResult:
        response = self.http.request(
            method="POST",
            path="/v1/merchant/portal/subscription/change-plan",
            body={"plan_id": plan_id},
            idempotency_key=idempotency_key,
        )
        return _change_plan_result_from_wire(response)


class MerchantPortalInvoicesResource:
    """End-user portal invoice APIs."""

    def __init__(self, http: HttpClient, checkout_base_url: str) -> None:
        self.http = http
        self.checkout_base_url = checkout_base_url

    def list(
        self,
        status: Optional[EndUserInvoiceStatus] = None,
        subscription_id: Optional[str] = None,
    ) -> List[EndUserInvoice]:
        response = self.http.request(
            method="GET",
            path="/v1/merchant/portal/invoices",
            query={"status": status, "subscription_id": subscription_id},
        )
        return [_invoice_from_wire(item) for item in response]

    def get(self, invoice_id: str) -> EndUserInvoice:
        response = self.http.request(
            method="GET",
            path=f"/v1/merchant/portal/invoices/{_path(invoice_id)}",
        )
        return _invoice_from_wire(response)

    def pay(
        self,
        invoice_id: str,
        accepted_assets: List[Dict[str, Any]],
        idempotency_key: Optional[str] = None,
        amount_mode: Optional[AmountMode] = None,
    ) -> PayMerchantInvoiceResponse:
        response = self.http.request(
            method="POST",
            path=f"/v1/merchant/portal/invoices/{_path(invoice_id)}/pay",
            body=_compact({"amount_mode": amount_mode, "accepted_assets": accepted_assets}),
            idempotency_key=idempotency_key,
        )
        return _pay_invoice_from_wire(response)

    def checkout_session(
        self,
        invoice_id: str,
        accepted_assets: List[Dict[str, Any]],
        title: Optional[str] = None,
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None,
        walletconnect_project_id: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        amount_mode: Optional[AmountMode] = None,
    ) -> MerchantInvoiceCheckoutSession:
        response = self.http.request(
            method="POST",
            path=f"/v1/merchant/portal/invoices/{_path(invoice_id)}/checkout-session",
            body=_compact(
                {
                    "title": title,
                    "success_url": success_url,
                    "cancel_url": cancel_url,
                    "walletconnect_project_id": walletconnect_project_id,
                    "amount_mode": amount_mode,
                    "accepted_assets": accepted_assets,
                }
            ),
            idempotency_key=idempotency_key,
        )
        return _checkout_session_from_wire(response, self.checkout_base_url)

    def payment_status(self, invoice_id: str) -> MerchantInvoicePaymentStatus:
        response = self.http.request(
            method="GET",
            path=f"/v1/merchant/portal/invoices/{_path(invoice_id)}/payment-status",
        )
        return _payment_status_from_wire(response)


class MerchantPortalApi:
    """End-user merchant portal API (synchronous)."""

    def __init__(self, http: HttpClient, checkout_base_url: Optional[str] = None) -> None:
        self.checkout_base_url = (checkout_base_url or DEFAULT_CHECKOUT_BASE_URL).rstrip("/")
        self.plans = MerchantPortalPlansResource(http)
        self.subscription = MerchantPortalSubscriptionResource(http)
        self.invoices = MerchantPortalInvoicesResource(http, self.checkout_base_url)


class AsyncMerchantPlansResource:
    """Merchant plan APIs (asynchronous)."""

    def __init__(self, http: AsyncHttpClient) -> None:
        self.http = http

    async def list(
        self,
        group_key: Optional[str] = None,
        include_inactive: Optional[bool] = None,
    ) -> List[MerchantPlan]:
        response = await self.http.request(
            method="GET",
            path="/v1/merchant/plans",
            query={
                "group_key": group_key,
                "include_inactive": "true" if include_inactive else None,
            },
        )
        return [_plan_from_wire(item) for item in response]

    async def create(
        self,
        code: str,
        name: str,
        group_key: str,
        amount: str,
        interval: MerchantPlanInterval,
        interval_count: int,
        description: Optional[str] = None,
        trial_days: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        is_template: Optional[bool] = None,
        idempotency_key: Optional[str] = None,
    ) -> MerchantPlan:
        response = await self.http.request(
            method="POST",
            path="/v1/merchant/plans",
            body=_compact(
                {
                    "code": code,
                    "name": name,
                    "description": description,
                    "group_key": group_key,
                    "amount": amount,
                    "interval": interval,
                    "interval_count": interval_count,
                    "trial_days": trial_days,
                    "metadata": metadata,
                    "is_template": is_template,
                }
            ),
            idempotency_key=idempotency_key,
        )
        return _plan_from_wire(response)

    async def update(
        self,
        plan_id: str,
        code: Optional[str] = None,
        name: Optional[str] = None,
        description: Union[str, None, _Unset] = _UNSET,
        group_key: Optional[str] = None,
        amount: Optional[str] = None,
        interval: Optional[MerchantPlanInterval] = None,
        interval_count: Optional[int] = None,
        trial_days: Union[int, None, _Unset] = _UNSET,
        metadata: Union[Dict[str, Any], None, _Unset] = _UNSET,
        is_template: Optional[bool] = None,
        idempotency_key: Optional[str] = None,
    ) -> MerchantPlan:
        response = await self.http.request(
            method="PUT",
            path=f"/v1/merchant/plans/{_path(plan_id)}",
            body=_plan_update_body(
                code=code,
                name=name,
                description=description,
                group_key=group_key,
                amount=amount,
                interval=interval,
                interval_count=interval_count,
                trial_days=trial_days,
                metadata=metadata,
                is_template=is_template,
            ),
            idempotency_key=idempotency_key,
        )
        return _plan_from_wire(response)

    async def delete(self, plan_id: str, idempotency_key: Optional[str] = None) -> None:
        await self.http.request(
            method="DELETE",
            path=f"/v1/merchant/plans/{_path(plan_id)}",
            idempotency_key=idempotency_key,
        )


class AsyncMerchantSubscriptionResource:
    """Merchant-managed end-user subscription APIs (asynchronous)."""

    def __init__(self, http: AsyncHttpClient) -> None:
        self.http = http

    async def create(
        self,
        plan_id: str,
        merchant_user_id: str,
        trial_days: Optional[int] = None,
        idempotency_key: Optional[str] = None,
    ) -> MerchantSubscriptionCreateResult:
        response = await self.http.request(
            method="POST",
            path="/v1/merchant/subscriptions",
            body=_compact(
                {
                    "plan_id": plan_id,
                    "merchant_user_id": merchant_user_id,
                    "trial_days": trial_days,
                }
            ),
            idempotency_key=idempotency_key,
        )
        return _create_result_from_wire(response)

    async def list(
        self,
        status: Optional[EndUserSubscriptionStatus] = None,
        merchant_user_id: Optional[str] = None,
    ) -> List[EndUserSubscription]:
        response = await self.http.request(
            method="GET",
            path="/v1/merchant/subscriptions",
            query={"status": status, "merchant_user_id": merchant_user_id},
        )
        return [_subscription_from_wire(item) for item in response]

    async def get(self, subscription_id: str) -> EndUserSubscription:
        response = await self.http.request(
            method="GET",
            path=f"/v1/merchant/subscriptions/{_path(subscription_id)}",
        )
        return _subscription_from_wire(response)

    async def get_by_merchant_user_id(self, merchant_user_id: str) -> EndUserSubscription:
        response = await self.http.request(
            method="GET",
            path=f"/v1/merchant/subscriptions/by-user/{_path(merchant_user_id)}",
        )
        return _subscription_from_wire(response)

    async def change_plan(
        self,
        subscription_id: str,
        plan_id: str,
        idempotency_key: Optional[str] = None,
    ) -> MerchantSubscriptionChangePlanResult:
        response = await self.http.request(
            method="POST",
            path=f"/v1/merchant/subscriptions/{_path(subscription_id)}/change-plan",
            body={"plan_id": plan_id},
            idempotency_key=idempotency_key,
        )
        return _change_plan_result_from_wire(response)

    async def cancel(
        self,
        subscription_id: str,
        immediate: Optional[bool] = None,
        idempotency_key: Optional[str] = None,
    ) -> EndUserSubscription:
        response = await self.http.request(
            method="POST",
            path=f"/v1/merchant/subscriptions/{_path(subscription_id)}/cancel",
            body=_compact({"immediate": immediate}),
            idempotency_key=idempotency_key,
        )
        return _subscription_from_wire(response)

    async def resume(
        self,
        subscription_id: str,
        idempotency_key: Optional[str] = None,
    ) -> EndUserSubscription:
        response = await self.http.request(
            method="POST",
            path=f"/v1/merchant/subscriptions/{_path(subscription_id)}/resume",
            idempotency_key=idempotency_key,
        )
        return _subscription_from_wire(response)


class AsyncMerchantInvoicesResource:
    """Merchant invoice APIs (asynchronous)."""

    def __init__(self, http: AsyncHttpClient) -> None:
        self.http = http

    async def list(
        self,
        status: Optional[EndUserInvoiceStatus] = None,
        merchant_user_id: Optional[str] = None,
        subscription_id: Optional[str] = None,
    ) -> List[EndUserInvoice]:
        response = await self.http.request(
            method="GET",
            path="/v1/merchant/invoices",
            query={
                "status": status,
                "merchant_user_id": merchant_user_id,
                "subscription_id": subscription_id,
            },
        )
        return [_invoice_from_wire(item) for item in response]

    async def get(self, invoice_id: str) -> EndUserInvoice:
        response = await self.http.request(
            method="GET",
            path=f"/v1/merchant/invoices/{_path(invoice_id)}",
        )
        return _invoice_from_wire(response)

    async def pay(
        self,
        invoice_id: str,
        accepted_assets: List[Dict[str, Any]],
        idempotency_key: Optional[str] = None,
        amount_mode: Optional[AmountMode] = None,
    ) -> PayMerchantInvoiceResponse:
        response = await self.http.request(
            method="POST",
            path=f"/v1/merchant/invoices/{_path(invoice_id)}/pay",
            body=_compact({"amount_mode": amount_mode, "accepted_assets": accepted_assets}),
            idempotency_key=idempotency_key,
        )
        return _pay_invoice_from_wire(response)

    async def payment_status(self, invoice_id: str) -> MerchantInvoicePaymentStatus:
        response = await self.http.request(
            method="GET",
            path=f"/v1/merchant/invoices/{_path(invoice_id)}/payment-status",
        )
        return _payment_status_from_wire(response)


class AsyncMerchantSettingsResource:
    """Merchant subscription billing settings APIs (asynchronous)."""

    def __init__(self, http: AsyncHttpClient) -> None:
        self.http = http

    async def get(self) -> MerchantBillingSettings:
        response = await self.http.request(method="GET", path="/v1/merchant/settings")
        return MerchantBillingSettings(**response)

    async def update(
        self,
        pay_window_days: Optional[int] = None,
        renewal_lead_days: Optional[int] = None,
        grace_days: Optional[int] = None,
        idempotency_key: Optional[str] = None,
    ) -> MerchantBillingSettings:
        response = await self.http.request(
            method="PUT",
            path="/v1/merchant/settings",
            body=_compact(
                {
                    "pay_window_days": pay_window_days,
                    "renewal_lead_days": renewal_lead_days,
                    "grace_days": grace_days,
                }
            ),
            idempotency_key=idempotency_key,
        )
        return MerchantBillingSettings(**response)


class AsyncMerchantPortalSessionsResource:
    """Merchant-created end-user portal session APIs (asynchronous)."""

    def __init__(self, http: AsyncHttpClient) -> None:
        self.http = http

    async def create(
        self,
        merchant_user_id: str,
        expires_at: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> PortalSession:
        response = await self.http.request(
            method="POST",
            path="/v1/merchant/portal-sessions",
            body=_compact({"merchant_user_id": merchant_user_id, "expires_at": expires_at}),
            idempotency_key=idempotency_key,
        )
        return PortalSession(**response)

    async def revoke(self, session_id: str, idempotency_key: Optional[str] = None) -> None:
        await self.http.request(
            method="DELETE",
            path=f"/v1/merchant/portal-sessions/{_path(session_id)}",
            idempotency_key=idempotency_key,
        )


class AsyncMerchantSubscriptionsApi:
    """Merchant subscriptions API (asynchronous)."""

    def __init__(self, http: AsyncHttpClient) -> None:
        self.plans = AsyncMerchantPlansResource(http)
        self.subscriptions = AsyncMerchantSubscriptionResource(http)
        self.invoices = AsyncMerchantInvoicesResource(http)
        self.settings = AsyncMerchantSettingsResource(http)
        self.portal_sessions = AsyncMerchantPortalSessionsResource(http)


class AsyncMerchantPortalPlansResource:
    """End-user portal plan APIs (asynchronous)."""

    def __init__(self, http: AsyncHttpClient) -> None:
        self.http = http

    async def list(self) -> List[MerchantPlan]:
        response = await self.http.request(method="GET", path="/v1/merchant/portal/plans")
        return [_plan_from_wire(item) for item in response]


class AsyncMerchantPortalSubscriptionResource:
    """End-user portal subscription APIs (asynchronous)."""

    def __init__(self, http: AsyncHttpClient) -> None:
        self.http = http

    async def get(self) -> EndUserSubscription:
        response = await self.http.request(method="GET", path="/v1/merchant/portal/subscription")
        return _subscription_from_wire(response)

    async def cancel(
        self,
        immediate: Optional[bool] = None,
        idempotency_key: Optional[str] = None,
    ) -> EndUserSubscription:
        response = await self.http.request(
            method="POST",
            path="/v1/merchant/portal/subscription/cancel",
            body=_compact({"immediate": immediate}),
            idempotency_key=idempotency_key,
        )
        return _subscription_from_wire(response)

    async def resume(self, idempotency_key: Optional[str] = None) -> EndUserSubscription:
        response = await self.http.request(
            method="POST",
            path="/v1/merchant/portal/subscription/resume",
            idempotency_key=idempotency_key,
        )
        return _subscription_from_wire(response)

    async def change_plan(
        self,
        plan_id: str,
        idempotency_key: Optional[str] = None,
    ) -> MerchantSubscriptionChangePlanResult:
        response = await self.http.request(
            method="POST",
            path="/v1/merchant/portal/subscription/change-plan",
            body={"plan_id": plan_id},
            idempotency_key=idempotency_key,
        )
        return _change_plan_result_from_wire(response)


class AsyncMerchantPortalInvoicesResource:
    """End-user portal invoice APIs (asynchronous)."""

    def __init__(self, http: AsyncHttpClient, checkout_base_url: str) -> None:
        self.http = http
        self.checkout_base_url = checkout_base_url

    async def list(
        self,
        status: Optional[EndUserInvoiceStatus] = None,
        subscription_id: Optional[str] = None,
    ) -> List[EndUserInvoice]:
        response = await self.http.request(
            method="GET",
            path="/v1/merchant/portal/invoices",
            query={"status": status, "subscription_id": subscription_id},
        )
        return [_invoice_from_wire(item) for item in response]

    async def get(self, invoice_id: str) -> EndUserInvoice:
        response = await self.http.request(
            method="GET",
            path=f"/v1/merchant/portal/invoices/{_path(invoice_id)}",
        )
        return _invoice_from_wire(response)

    async def pay(
        self,
        invoice_id: str,
        accepted_assets: List[Dict[str, Any]],
        idempotency_key: Optional[str] = None,
        amount_mode: Optional[AmountMode] = None,
    ) -> PayMerchantInvoiceResponse:
        response = await self.http.request(
            method="POST",
            path=f"/v1/merchant/portal/invoices/{_path(invoice_id)}/pay",
            body=_compact({"amount_mode": amount_mode, "accepted_assets": accepted_assets}),
            idempotency_key=idempotency_key,
        )
        return _pay_invoice_from_wire(response)

    async def checkout_session(
        self,
        invoice_id: str,
        accepted_assets: List[Dict[str, Any]],
        title: Optional[str] = None,
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None,
        walletconnect_project_id: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        amount_mode: Optional[AmountMode] = None,
    ) -> MerchantInvoiceCheckoutSession:
        response = await self.http.request(
            method="POST",
            path=f"/v1/merchant/portal/invoices/{_path(invoice_id)}/checkout-session",
            body=_compact(
                {
                    "title": title,
                    "success_url": success_url,
                    "cancel_url": cancel_url,
                    "walletconnect_project_id": walletconnect_project_id,
                    "amount_mode": amount_mode,
                    "accepted_assets": accepted_assets,
                }
            ),
            idempotency_key=idempotency_key,
        )
        return _checkout_session_from_wire(response, self.checkout_base_url)

    async def payment_status(self, invoice_id: str) -> MerchantInvoicePaymentStatus:
        response = await self.http.request(
            method="GET",
            path=f"/v1/merchant/portal/invoices/{_path(invoice_id)}/payment-status",
        )
        return _payment_status_from_wire(response)


class AsyncMerchantPortalApi:
    """End-user merchant portal API (asynchronous)."""

    def __init__(self, http: AsyncHttpClient, checkout_base_url: Optional[str] = None) -> None:
        self.checkout_base_url = (checkout_base_url or DEFAULT_CHECKOUT_BASE_URL).rstrip("/")
        self.plans = AsyncMerchantPortalPlansResource(http)
        self.subscription = AsyncMerchantPortalSubscriptionResource(http)
        self.invoices = AsyncMerchantPortalInvoicesResource(http, self.checkout_base_url)

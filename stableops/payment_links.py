"""PaymentLinks API resources."""

from typing import List, Optional
from urllib.parse import quote

from stableops.http import AsyncHttpClient, HttpClient
from stableops.types import (
    CreatePaymentLinkInput,
    PaymentLink,
    PaymentLinkList,
    PaymentLinkOrdersPage,
    PaymentOrderStatus,
    UpdatePaymentLinkInput,
)


class PaymentLinksApi:
    """PaymentLinks API (synchronous)."""

    def __init__(self, http: HttpClient) -> None:
        self.http = http

    def create(self, input: CreatePaymentLinkInput) -> PaymentLink:
        """Create a reusable payment link."""
        response = self.http.request(
            method="POST", path="/v1/payment-links", body=input.model_dump(exclude_none=True)
        )
        return PaymentLink(**response)

    def list(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[PaymentLink]:
        """List payment links."""
        page = self.list_page(limit, offset)
        return page.items

    def list_page(
        self, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> PaymentLinkList:
        """List payment links with pagination metadata."""
        response = self.http.request(
            method="GET", path="/v1/payment-links", query={"limit": limit, "offset": offset}
        )
        return PaymentLinkList(**response)

    def update(self, link_id: str, input: UpdatePaymentLinkInput) -> PaymentLink:
        """Update only the supplied fields. Explicit None clears nullable fields."""
        response = self.http.request(
            method="PATCH",
            path=f"/v1/payment-links/{quote(link_id, safe='')}",
            body=input.model_dump(exclude_unset=True),
        )
        return PaymentLink(**response)

    def orders(
        self,
        link_id: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        status: Optional[PaymentOrderStatus] = None,
    ) -> PaymentLinkOrdersPage:
        """List orders, collected payer details, and completed-order count."""
        response = self.http.request(
            method="GET",
            path=f"/v1/payment-links/{quote(link_id, safe='')}/orders",
            query={"limit": limit, "offset": offset, "status": status},
        )
        return PaymentLinkOrdersPage(**response)


class AsyncPaymentLinksApi:
    """PaymentLinks API (asynchronous)."""

    def __init__(self, http: AsyncHttpClient) -> None:
        self.http = http

    async def create(self, input: CreatePaymentLinkInput) -> PaymentLink:
        """Create a reusable payment link."""
        response = await self.http.request(
            method="POST", path="/v1/payment-links", body=input.model_dump(exclude_none=True)
        )
        return PaymentLink(**response)

    async def list(
        self, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> List[PaymentLink]:
        """List payment links."""
        page = await self.list_page(limit, offset)
        return page.items

    async def list_page(
        self, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> PaymentLinkList:
        """List payment links with pagination metadata."""
        response = await self.http.request(
            method="GET", path="/v1/payment-links", query={"limit": limit, "offset": offset}
        )
        return PaymentLinkList(**response)

    async def update(self, link_id: str, input: UpdatePaymentLinkInput) -> PaymentLink:
        """Update only the supplied fields. Explicit None clears nullable fields."""
        response = await self.http.request(
            method="PATCH",
            path=f"/v1/payment-links/{quote(link_id, safe='')}",
            body=input.model_dump(exclude_unset=True),
        )
        return PaymentLink(**response)

    async def orders(
        self,
        link_id: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        status: Optional[PaymentOrderStatus] = None,
    ) -> PaymentLinkOrdersPage:
        """List orders, collected payer details, and completed-order count."""
        response = await self.http.request(
            method="GET",
            path=f"/v1/payment-links/{quote(link_id, safe='')}/orders",
            query={"limit": limit, "offset": offset, "status": status},
        )
        return PaymentLinkOrdersPage(**response)

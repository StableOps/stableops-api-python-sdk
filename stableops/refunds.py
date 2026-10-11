"""Refunds API resources."""

from typing import List, Optional
from urllib.parse import quote

from stableops.http import AsyncHttpClient, HttpClient
from stableops.types import Refund, RefundList, RefundStatus


class RefundsApi:
    """Refunds API (synchronous)."""

    def __init__(self, http: HttpClient) -> None:
        self.http = http

    def create(self, payment_order_id: str, amount: str, destination_address: str) -> Refund:
        """Request a refund. The merchant signs and broadcasts the transfer separately."""
        response = self.http.request(
            method="POST",
            path="/v1/refunds",
            body={
                "payment_order_id": payment_order_id,
                "amount": amount,
                "destination_address": destination_address,
            },
        )
        return Refund(**response)

    def retrieve(self, refund_id: str) -> Refund:
        """Retrieve one refund."""
        response = self.http.request(method="GET", path=f"/v1/refunds/{quote(refund_id, safe='')}")
        return Refund(**response)

    def list(
        self,
        payment_order_id: Optional[str] = None,
        status: Optional[RefundStatus] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Refund]:
        """List refunds."""
        page = self.list_page(payment_order_id, status, limit, offset)
        return page.items

    def list_page(
        self,
        payment_order_id: Optional[str] = None,
        status: Optional[RefundStatus] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> RefundList:
        """List refunds with pagination metadata."""
        response = self.http.request(
            method="GET",
            path="/v1/refunds",
            query={
                "payment_order_id": payment_order_id,
                "status": status,
                "limit": limit,
                "offset": offset,
            },
        )
        return RefundList(**response)

    def submit(self, refund_id: str, tx_hash: str) -> Refund:
        """Register an already signed and broadcast refund transaction."""
        response = self.http.request(
            method="POST",
            path=f"/v1/refunds/{quote(refund_id, safe='')}/submit",
            body={"tx_hash": tx_hash},
        )
        return Refund(**response)

    def cancel(self, refund_id: str) -> Refund:
        """Cancel an unsubmitted refund request."""
        response = self.http.request(
            method="POST", path=f"/v1/refunds/{quote(refund_id, safe='')}/cancel"
        )
        return Refund(**response)


class AsyncRefundsApi:
    """Refunds API (asynchronous)."""

    def __init__(self, http: AsyncHttpClient) -> None:
        self.http = http

    async def create(self, payment_order_id: str, amount: str, destination_address: str) -> Refund:
        """Request a refund. The merchant signs and broadcasts the transfer separately."""
        response = await self.http.request(
            method="POST",
            path="/v1/refunds",
            body={
                "payment_order_id": payment_order_id,
                "amount": amount,
                "destination_address": destination_address,
            },
        )
        return Refund(**response)

    async def retrieve(self, refund_id: str) -> Refund:
        """Retrieve one refund."""
        response = await self.http.request(
            method="GET", path=f"/v1/refunds/{quote(refund_id, safe='')}"
        )
        return Refund(**response)

    async def list(
        self,
        payment_order_id: Optional[str] = None,
        status: Optional[RefundStatus] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Refund]:
        """List refunds."""
        page = await self.list_page(payment_order_id, status, limit, offset)
        return page.items

    async def list_page(
        self,
        payment_order_id: Optional[str] = None,
        status: Optional[RefundStatus] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> RefundList:
        """List refunds with pagination metadata."""
        response = await self.http.request(
            method="GET",
            path="/v1/refunds",
            query={
                "payment_order_id": payment_order_id,
                "status": status,
                "limit": limit,
                "offset": offset,
            },
        )
        return RefundList(**response)

    async def submit(self, refund_id: str, tx_hash: str) -> Refund:
        """Register an already signed and broadcast refund transaction."""
        response = await self.http.request(
            method="POST",
            path=f"/v1/refunds/{quote(refund_id, safe='')}/submit",
            body={"tx_hash": tx_hash},
        )
        return Refund(**response)

    async def cancel(self, refund_id: str) -> Refund:
        """Cancel an unsubmitted refund request."""
        response = await self.http.request(
            method="POST", path=f"/v1/refunds/{quote(refund_id, safe='')}/cancel"
        )
        return Refund(**response)

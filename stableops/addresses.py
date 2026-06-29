"""Addresses API."""

from typing import Any, Dict, List, Optional, Union, cast

from stableops.http import AsyncHttpClient, HttpClient


class _Unset:
    pass


_UNSET = _Unset()


class AddressesApi:
    """Addresses API (synchronous)."""

    def __init__(self, http: HttpClient) -> None:
        self.http = http

    def get_pools(self) -> List[Dict[str, Any]]:
        """Get address pool overview.

        Returns:
            List of address pools grouped by chain

        Example:
            >>> pools = client.addresses.get_pools()
            >>> for pool in pools:
            ...     print(pool["chain"], pool["available"], pool["total"])
        """
        response = self.http.request(
            method="GET",
            path="/v1/addresses/pools",
        )
        return cast(List[Dict[str, Any]], response["pools"])

    def import_addresses(
        self,
        chain: str,
        addresses: List[str],
        mode: Optional[str] = None,
        label: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Import receiving addresses.

        Args:
            chain: Blockchain chain identifier
            addresses: List of addresses to import
            mode: Allocation mode ("single" or "shared", default "single")
            label: Optional label applied to all addresses

        Returns:
            Import result with imported count and addresses

        Example:
            >>> result = client.addresses.import_addresses(
            ...     chain="base",
            ...     addresses=["0x1234..."],
            ...     mode="single",
            ... )
        """
        body: Dict[str, Any] = {
            "addresses": [
                {"chain": chain, "address": addr, **({"label": label} if label else {})}
                for addr in addresses
            ],
            "mode": mode or "single",
        }
        return cast(Dict[str, Any], self.http.request(
            method="POST",
            path="/v1/addresses/import",
            body=body,
        ))

    def list(
        self,
        chain: Optional[str] = None,
        status: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Dict[str, Any]:
        """List receiving addresses.

        Args:
            chain: Filter by chain (optional)
            status: Filter by status (optional)
            limit: Page size (optional)
            offset: Pagination offset (optional)

        Returns:
            Response with items and has_more

        Example:
            >>> result = client.addresses.list(chain="base", limit=20)
        """
        query: Dict[str, Any] = {}
        if chain:
            query["chain"] = chain
        if status:
            query["status"] = status
        if limit is not None:
            query["limit"] = limit
        if offset is not None:
            query["offset"] = offset

        return cast(Dict[str, Any], self.http.request(
            method="GET",
            path="/v1/addresses",
            query=query,
        ))

    def remove(self, address_id: str) -> Dict[str, Any]:
        """Delete an address.

        Args:
            address_id: Address ID

        Returns:
            Success status

        Example:
            >>> client.addresses.remove("addr_abc123")
        """
        return cast(Dict[str, Any], self.http.request(
            method="DELETE",
            path=f"/v1/addresses/{address_id}",
        ))

    def update(
        self,
        address_id: str,
        label: Union[str, None, _Unset] = _UNSET,
        mode: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update an address.

        Args:
            address_id: Address ID
            label: New label (optional, set null to clear)
            mode: New mode ("single" or "shared", optional)
            status: New status ("available", "reserved", or "disabled", optional)

        Returns:
            Updated address

        Example:
            >>> client.addresses.update("addr_abc123", label="hot wallet 1")
        """
        body: Dict[str, Any] = {}
        if label is not _UNSET:
            body["label"] = label
        if mode is not None:
            body["mode"] = mode
        if status is not None:
            body["status"] = status

        return cast(Dict[str, Any], self.http.request(
            method="PATCH",
            path=f"/v1/addresses/{address_id}",
            body=body,
        ))


class AsyncAddressesApi:
    """Addresses API (asynchronous)."""

    def __init__(self, http: AsyncHttpClient) -> None:
        self.http = http

    async def get_pools(self) -> List[Dict[str, Any]]:
        """Get address pool overview (async)."""
        response = await self.http.request(
            method="GET",
            path="/v1/addresses/pools",
        )
        return cast(List[Dict[str, Any]], response["pools"])

    async def import_addresses(
        self,
        chain: str,
        addresses: List[str],
        mode: Optional[str] = None,
        label: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Import receiving addresses (async)."""
        body: Dict[str, Any] = {
            "addresses": [
                {"chain": chain, "address": addr, **({"label": label} if label else {})}
                for addr in addresses
            ],
            "mode": mode or "single",
        }
        response = await self.http.request(
            method="POST",
            path="/v1/addresses/import",
            body=body,
        )
        return cast(Dict[str, Any], response)

    async def list(
        self,
        chain: Optional[str] = None,
        status: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Dict[str, Any]:
        """List receiving addresses (async)."""
        query: Dict[str, Any] = {}
        if chain:
            query["chain"] = chain
        if status:
            query["status"] = status
        if limit is not None:
            query["limit"] = limit
        if offset is not None:
            query["offset"] = offset

        response = await self.http.request(
            method="GET",
            path="/v1/addresses",
            query=query,
        )
        return cast(Dict[str, Any], response)

    async def remove(self, address_id: str) -> Dict[str, Any]:
        """Delete an address (async)."""
        response = await self.http.request(
            method="DELETE",
            path=f"/v1/addresses/{address_id}",
        )
        return cast(Dict[str, Any], response)

    async def update(
        self,
        address_id: str,
        label: Union[str, None, _Unset] = _UNSET,
        mode: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update an address (async)."""
        body: Dict[str, Any] = {}
        if label is not _UNSET:
            body["label"] = label
        if mode is not None:
            body["mode"] = mode
        if status is not None:
            body["status"] = status

        response = await self.http.request(
            method="PATCH",
            path=f"/v1/addresses/{address_id}",
            body=body,
        )
        return cast(Dict[str, Any], response)

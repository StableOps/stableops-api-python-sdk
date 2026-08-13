"""HTTP transport safety and compatibility tests."""

import json
from typing import Any, Dict, List

import httpx
import pytest

from stableops.errors import StableOpsError
from stableops.http import AsyncHttpClient, HttpClient


def _sync_client(handler: Any, **kwargs: Any) -> HttpClient:
    client = HttpClient(base_url="https://api.test.local", base_delay=0, **kwargs)
    client.client.close()
    client.client = httpx.Client(
        base_url=client.base_url,
        headers={"authorization": "Bearer sk_super_secret_value"},
        transport=httpx.MockTransport(handler),
    )
    return client


async def _async_client(handler: Any, **kwargs: Any) -> AsyncHttpClient:
    client = AsyncHttpClient(base_url="https://api.test.local", base_delay=0, **kwargs)
    await client.client.aclose()
    client.client = httpx.AsyncClient(
        base_url=client.base_url,
        headers={"authorization": "Bearer sk_super_secret_value"},
        transport=httpx.MockTransport(handler),
    )
    return client


def test_empty_success_response_returns_none() -> None:
    client = _sync_client(lambda request: httpx.Response(204, request=request))
    try:
        assert client.request("DELETE", "/v1/resource") is None
    finally:
        client.close()


@pytest.mark.asyncio
async def test_async_empty_success_response_returns_none() -> None:
    client = await _async_client(lambda request: httpx.Response(204, request=request))
    try:
        assert await client.request("DELETE", "/v1/resource") is None
    finally:
        await client.close()


def test_retries_get_but_not_unsafe_post_by_default() -> None:
    calls: Dict[str, int] = {"GET": 0, "POST": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls[request.method] += 1
        return httpx.Response(503, json={"message": "temporary"}, request=request)

    client = _sync_client(handler, max_retries=2)
    try:
        with pytest.raises(StableOpsError):
            client.request("POST", "/v1/write")
        with pytest.raises(StableOpsError):
            client.request("GET", "/v1/read")
    finally:
        client.close()

    assert calls == {"GET": 3, "POST": 1}


def test_debug_events_mask_request_and_response_secrets() -> None:
    events: List[Dict[str, Any]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "client_secret": "client_secret_unmasked_value",
                "nested": {"portalToken": "portal_token_unmasked_value"},
            },
            headers={"set-cookie": "session_cookie_unmasked_value"},
            request=request,
        )

    client = _sync_client(handler, debug=events.append)
    try:
        client.request(
            "POST",
            "/v1/resource",
            body={"secret": "request_secret_unmasked_value"},
            idempotency_key="idempotency_unmasked_value",
        )
    finally:
        client.close()

    serialized = json.dumps(events)
    for secret in (
        "sk_super_secret_value",
        "request_secret_unmasked_value",
        "idempotency_unmasked_value",
        "client_secret_unmasked_value",
        "portal_token_unmasked_value",
        "session_cookie_unmasked_value",
    ):
        assert secret not in serialized

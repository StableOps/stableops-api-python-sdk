"""Tests for Addresses API."""

from typing import Any, Dict

from stableops.addresses import AddressesApi


class FakeHttp:
    def __init__(self) -> None:
        self.last_request: Dict[str, Any] = {}

    def request(self, **kwargs: Any) -> Dict[str, Any]:
        self.last_request = kwargs
        return {
            "id": "addr_1",
            "chain": "base-sepolia",
            "address": "0xabc",
            "label": kwargs["body"].get("label"),
            "mode": "single",
            "status": "available",
            "created_at": "2026-06-01T00:00:00.000Z",
        }


def test_update_can_clear_label_with_none() -> None:
    http = FakeHttp()
    api = AddressesApi(http)  # type: ignore[arg-type]

    api.update("addr_1", label=None)

    assert http.last_request["body"] == {"label": None}

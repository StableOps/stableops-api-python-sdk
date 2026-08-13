"""Tests for the Python Agent API."""

from typing import Any, Dict

from stableops.agents import AgentsApi

SESSION = {
    "id": "as_1",
    "label": "ops-bot",
    "created_at": "2026-07-01T00:00:00.000Z",
    "expires_at": None,
    "revoked_at": None,
}

ACTION = {
    "id": "aa_1",
    "agent_session_id": "as_1",
    "tool": "create_payment_order",
    "input": {"amount": "1"},
    "status": "executed",
    "approver_id": None,
    "decided_at": None,
    "executed_at": "2026-07-01T00:01:00.000Z",
    "result": None,
    "error_message": "upstream failed",
    "created_at": "2026-07-01T00:00:00.000Z",
}


class FakeHttp:
    def __init__(self, responses: Dict[str, Any]) -> None:
        self.responses = responses
        self.last_request: Dict[str, Any] = {}

    def request(self, **kwargs: Any) -> Any:
        self.last_request = kwargs
        return self.responses[kwargs["path"]]


def test_restores_agent_session_and_lists_pagination_metadata() -> None:
    http = FakeHttp(
        {
            "/v1/agent/sessions/as_1/restore": SESSION,
            "/v1/agent/sessions": {"items": [SESSION], "has_more": False, "total": 1},
        }
    )
    api = AgentsApi(http)  # type: ignore[arg-type]

    assert api.restore_session("as_1").revoked_at is None
    page = api.list_sessions(limit=10, offset=20)

    assert page.total == 1
    assert page.items[0].id == "as_1"
    assert http.last_request["query"] == {"limit": 10, "offset": 20}


def test_requests_action_and_records_execution_error() -> None:
    http = FakeHttp(
        {
            "/v1/agent/actions": {
                "decision": "auto_allowed",
                "actionId": "aa_1",
            },
            "/v1/agent/actions/aa_1/executed": ACTION,
        }
    )
    api = AgentsApi(http)  # type: ignore[arg-type]

    decision = api.request_action("as_1", "create_payment_order", {"amount": "1"})
    assert decision.action_id == "aa_1"
    action = api.mark_executed("aa_1", "as_1", error_message="upstream failed")

    assert action.error_message == "upstream failed"
    assert http.last_request["body"] == {
        "agent_session_id": "as_1",
        "error_message": "upstream failed",
    }

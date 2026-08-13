"""Agent sessions, policies, and action audit APIs."""

from typing import Any, Dict, List, Optional
from urllib.parse import quote

from stableops.http import AsyncHttpClient, HttpClient
from stableops.types import (
    AgentAction,
    AgentActionList,
    AgentPolicy,
    AgentSession,
    AgentSessionList,
    RequestAgentActionResult,
)


def _path(value: str) -> str:
    return quote(value, safe="")


class AgentsApi:
    """Agent API (synchronous)."""

    def __init__(self, http: HttpClient) -> None:
        self.http = http

    def create_session(
        self, label: Optional[str] = None, expires_at: Optional[str] = None
    ) -> AgentSession:
        response = self.http.request(
            method="POST",
            path="/v1/agent/sessions",
            body={
                key: value
                for key, value in {"label": label, "expires_at": expires_at}.items()
                if value is not None
            },
        )
        return AgentSession(**response)

    def list_sessions(
        self, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> AgentSessionList:
        response = self.http.request(
            method="GET",
            path="/v1/agent/sessions",
            query={"limit": limit, "offset": offset},
        )
        return AgentSessionList(**response)

    def revoke_session(self, session_id: str) -> AgentSession:
        response = self.http.request(
            method="POST", path=f"/v1/agent/sessions/{_path(session_id)}/revoke"
        )
        return AgentSession(**response)

    def restore_session(self, session_id: str) -> AgentSession:
        response = self.http.request(
            method="POST", path=f"/v1/agent/sessions/{_path(session_id)}/restore"
        )
        return AgentSession(**response)

    def get_policy(self) -> AgentPolicy:
        return AgentPolicy(**self.http.request(method="GET", path="/v1/agent/policy"))

    def upsert_policy(
        self,
        allowed_tools: Optional[List[str]] = None,
        require_approval: Optional[bool] = None,
    ) -> AgentPolicy:
        body: Dict[str, Any] = {}
        if allowed_tools is not None:
            body["allowed_tools"] = allowed_tools
        if require_approval is not None:
            body["require_approval"] = require_approval
        response = self.http.request(method="POST", path="/v1/agent/policy", body=body)
        return AgentPolicy(**response)

    def request_action(
        self, agent_session_id: str, tool: str, input: Dict[str, Any]
    ) -> RequestAgentActionResult:
        response = self.http.request(
            method="POST",
            path="/v1/agent/actions",
            body={"agent_session_id": agent_session_id, "tool": tool, "input": input},
        )
        return RequestAgentActionResult(**response)

    def list_actions(
        self,
        session_id: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> AgentActionList:
        response = self.http.request(
            method="GET",
            path="/v1/agent/actions",
            query={"session_id": session_id, "limit": limit, "offset": offset},
        )
        return AgentActionList(**response)

    def approve_action(self, action_id: str, approver_id: Optional[str] = None) -> AgentAction:
        body = {} if approver_id is None else {"approver_id": approver_id}
        response = self.http.request(
            method="POST", path=f"/v1/agent/actions/{_path(action_id)}/approve", body=body
        )
        return AgentAction(**response)

    def reject_action(
        self,
        action_id: str,
        approver_id: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> AgentAction:
        body = {
            key: value
            for key, value in {"approver_id": approver_id, "reason": reason}.items()
            if value is not None
        }
        response = self.http.request(
            method="POST", path=f"/v1/agent/actions/{_path(action_id)}/reject", body=body
        )
        return AgentAction(**response)

    def mark_executed(
        self,
        action_id: str,
        agent_session_id: str,
        result: Any = None,
        error_message: Optional[str] = None,
    ) -> AgentAction:
        if result is not None and error_message is not None:
            raise ValueError("result and error_message are mutually exclusive")
        body: Dict[str, Any] = {"agent_session_id": agent_session_id}
        if error_message is not None:
            body["error_message"] = error_message
        else:
            body["result"] = result
        response = self.http.request(
            method="POST", path=f"/v1/agent/actions/{_path(action_id)}/executed", body=body
        )
        return AgentAction(**response)


class AsyncAgentsApi:
    """Agent API (asynchronous)."""

    def __init__(self, http: AsyncHttpClient) -> None:
        self.http = http

    async def create_session(
        self, label: Optional[str] = None, expires_at: Optional[str] = None
    ) -> AgentSession:
        response = await self.http.request(
            method="POST",
            path="/v1/agent/sessions",
            body={
                key: value
                for key, value in {"label": label, "expires_at": expires_at}.items()
                if value is not None
            },
        )
        return AgentSession(**response)

    async def list_sessions(
        self, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> AgentSessionList:
        response = await self.http.request(
            method="GET",
            path="/v1/agent/sessions",
            query={"limit": limit, "offset": offset},
        )
        return AgentSessionList(**response)

    async def revoke_session(self, session_id: str) -> AgentSession:
        response = await self.http.request(
            method="POST", path=f"/v1/agent/sessions/{_path(session_id)}/revoke"
        )
        return AgentSession(**response)

    async def restore_session(self, session_id: str) -> AgentSession:
        response = await self.http.request(
            method="POST", path=f"/v1/agent/sessions/{_path(session_id)}/restore"
        )
        return AgentSession(**response)

    async def get_policy(self) -> AgentPolicy:
        response = await self.http.request(method="GET", path="/v1/agent/policy")
        return AgentPolicy(**response)

    async def upsert_policy(
        self,
        allowed_tools: Optional[List[str]] = None,
        require_approval: Optional[bool] = None,
    ) -> AgentPolicy:
        body: Dict[str, Any] = {}
        if allowed_tools is not None:
            body["allowed_tools"] = allowed_tools
        if require_approval is not None:
            body["require_approval"] = require_approval
        response = await self.http.request(method="POST", path="/v1/agent/policy", body=body)
        return AgentPolicy(**response)

    async def request_action(
        self, agent_session_id: str, tool: str, input: Dict[str, Any]
    ) -> RequestAgentActionResult:
        response = await self.http.request(
            method="POST",
            path="/v1/agent/actions",
            body={"agent_session_id": agent_session_id, "tool": tool, "input": input},
        )
        return RequestAgentActionResult(**response)

    async def list_actions(
        self,
        session_id: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> AgentActionList:
        response = await self.http.request(
            method="GET",
            path="/v1/agent/actions",
            query={"session_id": session_id, "limit": limit, "offset": offset},
        )
        return AgentActionList(**response)

    async def approve_action(
        self, action_id: str, approver_id: Optional[str] = None
    ) -> AgentAction:
        body = {} if approver_id is None else {"approver_id": approver_id}
        response = await self.http.request(
            method="POST", path=f"/v1/agent/actions/{_path(action_id)}/approve", body=body
        )
        return AgentAction(**response)

    async def reject_action(
        self,
        action_id: str,
        approver_id: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> AgentAction:
        body = {
            key: value
            for key, value in {"approver_id": approver_id, "reason": reason}.items()
            if value is not None
        }
        response = await self.http.request(
            method="POST", path=f"/v1/agent/actions/{_path(action_id)}/reject", body=body
        )
        return AgentAction(**response)

    async def mark_executed(
        self,
        action_id: str,
        agent_session_id: str,
        result: Any = None,
        error_message: Optional[str] = None,
    ) -> AgentAction:
        if result is not None and error_message is not None:
            raise ValueError("result and error_message are mutually exclusive")
        body: Dict[str, Any] = {"agent_session_id": agent_session_id}
        if error_message is not None:
            body["error_message"] = error_message
        else:
            body["result"] = result
        response = await self.http.request(
            method="POST", path=f"/v1/agent/actions/{_path(action_id)}/executed", body=body
        )
        return AgentAction(**response)

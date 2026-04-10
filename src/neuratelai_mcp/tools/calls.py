"""Call management tools — make, list, get (with transcript), hangup, active."""

from __future__ import annotations

from typing import Any

import httpx
from fastmcp import FastMCP


def register(mcp: FastMCP, client: httpx.AsyncClient) -> None:

    @mcp.tool(name="make_call")
    async def make_call(
        agent_id: str,
        to_number: str,
        number_id: str,
        dynamic_variables: dict[str, Any] | None = None,
        caller_id_name: str | None = None,
    ) -> dict[str, Any]:
        """Place a single outbound phone call using a voice AI agent.

        Prerequisites: you need an agent_id (from list_agents) and a number_id
        (from list_numbers). Use get_balance first to verify sufficient credits.

        ⚠️ COST WARNING: Places a real phone call which incurs telephony and AI costs.
        Only use when explicitly requested by the user.

        Args:
            agent_id: ID of the agent to handle the call
            to_number: Phone number to call in E.164 format (e.g. +12125551234)
            number_id: ID of your phone number to use as caller ID (from list_numbers)
            dynamic_variables: Optional variables injected into the agent's prompt
                               (e.g. {"customer_name": "Alice", "account_id": "123"})
            caller_id_name: Optional display name shown to the recipient

        Returns: call_id for tracking, status, caller and callee numbers.
        """
        body: dict[str, Any] = {
            "agent_id": agent_id,
            "to_number": to_number,
            "number_id": number_id,
        }
        if dynamic_variables:
            body["dynamic_variables"] = dynamic_variables
        if caller_id_name:
            body["caller_id_name"] = caller_id_name

        r = await client.post("/calls/outbound", json=body)
        r.raise_for_status()
        d = r.json()
        return {
            "call_id": d.get("call_id"),
            "status": d.get("success"),
            "to_number": d.get("to_number"),
            "from_number": d.get("from_number"),
        }

    @mcp.tool(name="list_calls")
    async def list_calls(
        limit: int = 10,
        call_type: str | None = None,
        agent_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """List recent calls with a summary of each.

        Use this to see call history, check outcomes, or find a call_id
        before using get_call for full details including the transcript.

        Args:
            limit: Number of calls to return (default 10, max 100)
            call_type: Filter by "outbound", "inbound", or "webrtc"
            agent_id: Filter to calls handled by a specific agent

        Returns: list of calls with id, status, duration, phone numbers, and agent.
        """
        params: dict[str, Any] = {"limit": min(limit, 100), "skip": 0}
        if call_type:
            params["call_type"] = call_type
        if agent_id:
            params["agentIdAny"] = agent_id

        r = await client.get("/calls", params=params)
        r.raise_for_status()
        results = r.json().get("results", [])
        return [
            {
                "id": c.get("id"),
                "status": c.get("status"),
                "call_type": c.get("call_type"),
                "duration_seconds": c.get("duration_seconds"),
                "phone_number": c.get("phone_number"),
                "agent_id": c.get("agent_id"),
                "started_at": c.get("started_at"),
                "ended_at": c.get("ended_at"),
                "call_result": c.get("call_result"),
            }
            for c in results
        ]

    @mcp.tool(name="get_call")
    async def get_call(call_id: str) -> dict[str, Any]:
        """Get full details for a call including the complete transcript and recording.

        Use this to answer questions like: "What did the caller say?",
        "Was the agent successful?", "What was discussed on this call?",
        "Can I see the transcript?".

        This is the only tool you need for post-call analysis — it includes
        the transcript as a list of {role, text} turns, a call summary,
        and the success evaluation result.

        Returns: id, status, duration, phone numbers, full transcript,
                 recording_url, call summary, and success evaluation.
        """
        r = await client.get(f"/calls/{call_id}", params={"include": "full"})
        r.raise_for_status()
        d = r.json()
        recording = d.get("recording") or {}
        success_eval = d.get("success_evaluation") or {}
        return {
            "id": d.get("id"),
            "status": d.get("status"),
            "call_type": d.get("call_type"),
            "duration_seconds": d.get("duration_seconds"),
            "phone_number": d.get("phone_number"),
            "caller_id": d.get("caller_id"),
            "agent_id": d.get("agent_id"),
            "started_at": d.get("started_at"),
            "ended_at": d.get("ended_at"),
            "transcript": d.get("conversation", []),
            "recording_url": recording.get("recording_url"),
            "summary": d.get("call_summary"),
            "success": success_eval.get("success"),
            "topics_discussed": d.get("topics_discussed", []),
            "extracted_data": d.get("extracted_data"),
        }

    @mcp.tool(name="hangup_call")
    async def hangup_call(call_id: str) -> dict[str, Any]:
        """Terminate an active call immediately.

        Use this to end a call that is currently in progress. The call_id
        can be found from get_active_calls or list_calls.

        ⚠️ WARNING: Immediately disconnects all participants. Use only when
        explicitly requested or in clear emergency situations.

        Returns: confirmation with the call_id and terminated status.
        """
        r = await client.post(f"/calls/{call_id}/hangup")
        r.raise_for_status()
        return {"call_id": call_id, "status": "terminated"}

    @mcp.tool(name="get_active_calls")
    async def get_active_calls() -> dict[str, Any]:
        """Get all calls currently in progress.

        Use this for real-time monitoring — see who is on a call right now,
        which agents are active, and how long each call has been running.
        Also shows call type (inbound/outbound/webrtc) and participant count.

        Returns: list of active calls with id, type, duration, phone number,
                 agent, and connection status.
        """
        r = await client.get("/calls/active")
        r.raise_for_status()
        d = r.json()
        return {
            "total_active": d.get("total_active", 0),
            "calls": [
                {
                    "id": c.get("id"),
                    "type": c.get("type"),
                    "phone_number": c.get("phone_number"),
                    "agent_name": c.get("agent_name"),
                    "agent_id": c.get("agent_id"),
                    "duration_seconds": c.get("duration_seconds"),
                    "status": c.get("status"),
                    "connection_status": c.get("connection_status"),
                    "started_at": c.get("started_at"),
                }
                for c in d.get("calls", [])
            ],
        }

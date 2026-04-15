"""Call management tools — make, list, get (with transcript), hangup, active."""

from __future__ import annotations

import json
import re
from typing import Any

import httpx
from fastmcp import FastMCP


def _extract_template_vars(obj: Any) -> set[str]:
    """Recursively find all {{variable}} placeholders in any string field."""
    found: set[str] = set()
    if isinstance(obj, str):
        found.update(re.findall(r"\{\{(\w+)\}\}", obj))
    elif isinstance(obj, dict):
        for v in obj.values():
            found.update(_extract_template_vars(v))
    elif isinstance(obj, list):
        for item in obj:
            found.update(_extract_template_vars(item))
    return found


def register(mcp: FastMCP, client: httpx.AsyncClient) -> None:

    @mcp.tool(name="make_call")
    async def make_call(
        agent_id: str,
        to_number: str,
        number_id: str,
        dynamic_variables: dict[str, Any] | None = None,
        caller_id_name: str | None = None,
        caller_id_number: str | None = None,
        agent_override: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Place an outbound phone call using a voice AI agent.

        This connects a real phone call between your AI agent and the
        destination number. The agent handles the entire conversation
        autonomously using its configured instructions and voice.

        ## Prerequisites

        1. An agent must exist (use create_agent or list_agents to find one)
        2. A phone number must be provisioned (use list_numbers to find one)
        3. Account must have sufficient balance (use get_balance to check)

        ## Minimum required

        Just three fields: which agent talks, who to call, and which number
        to call from. Everything else is optional.

        ## Per-call customization

        Two powerful ways to customize each call without changing the agent:

        **dynamic_variables** — inject values into the agent's prompt template.
        If the agent's instructions contain `{{customer_name}}`, pass:
        `dynamic_variables={"customer_name": "Alice"}`

        **agent_override** — deep-merge config changes over the saved agent
        for this call only. The agent itself is not modified. Use this to:
        - Change the prompt for a specific call
        - Use a different voice or language
        - Adjust temperature for a sensitive conversation
        - Override any config section (brain, voice, transcriber, etc.)

        Example override:
        ```json
        {"brain": {"instructions": "Special prompt for this call only"}}
        ```

        Args:
            agent_id: The agent that will handle this call
            to_number: Destination in E.164 format (+12125551234)
            number_id: Your phone number ID to call from (from list_numbers)
            dynamic_variables: Template variables for the agent's prompt
            caller_id_name: Display name shown to the recipient (max 50 chars)
            caller_id_number: Override caller ID number (E.164). Defaults to
                              the number_id's phone number if not set.
            agent_override: Per-call config overrides. Same structure as the
                            agent config from get_agent. Deep-merged over the
                            saved agent — only affects this call.

        Returns: call_id for tracking via get_call, success status, and numbers.
        """
        # Pre-flight: fetch the agent and find all {{variable}} placeholders.
        # Fail early with a clear message instead of a raw 400 from the API.
        agent_r = await client.get(f"/agents/{agent_id}")
        if agent_r.status_code == 200:
            agent_data = agent_r.json()
            required_vars = _extract_template_vars(agent_data)
            provided_vars = set(dynamic_variables.keys()) if dynamic_variables else set()
            missing = required_vars - provided_vars
            if missing:
                missing_list = ", ".join(sorted(missing))
                example = {v: f"<{v}>" for v in sorted(missing)}
                raise ValueError(
                    f"This agent requires dynamic_variables that were not provided. "
                    f"Missing: {missing_list}. "
                    f"Call again with: dynamic_variables={json.dumps(example)}"
                )

        body: dict[str, Any] = {
            "agent_id": agent_id,
            "to_number": to_number,
            "number_id": number_id,
        }
        if dynamic_variables:
            body["dynamic_variables"] = dynamic_variables
        if caller_id_name:
            body["caller_id_name"] = caller_id_name
        if caller_id_number:
            body["caller_id_number"] = caller_id_number
        if agent_override:
            body["agent_override"] = agent_override

        r = await client.post("/calls/outbound", json=body)
        r.raise_for_status()
        d = r.json()
        return {
            "call_id": d.get("call_id"),
            "success": d.get("success"),
            "to_number": d.get("to_number"),
            "from_number": d.get("from_number"),
            "agent_id": str(d.get("agent_id", "")),
            "error": d.get("error"),
        }

    @mcp.tool(name="list_calls")
    async def list_calls(
        limit: int = 10,
        call_type: str | None = None,
        agent_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """List recent calls with a summary of each.

        Returns call history sorted by most recent first. Each entry includes
        status, duration, and outcome — but NOT the transcript. Use get_call
        with a specific call_id to read the full transcript.

        Filter by call_type to see only inbound, outbound, or browser calls.
        Filter by agent_id to see calls handled by a specific agent.

        Args:
            limit: How many calls to return (1-100, default 10)
            call_type: Filter: "outbound", "inbound", or "webrtc"
            agent_id: Filter to calls handled by this agent
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
        """Get full details for a specific call including the complete transcript.

        This is the primary tool for post-call analysis. Returns everything:
        the full conversation transcript (who said what, in order), call
        summary, recording URL, success evaluation, topics discussed, and
        any data extracted during the call.

        The transcript is a list of turns: [{"role": "agent", "text": "..."},
        {"role": "user", "text": "..."}, ...] — making it easy to review
        exactly what happened on the call.

        Use this when asked: "What happened on that call?", "What did the
        caller say?", "Was the agent successful?", "Show me the transcript."
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
        """Immediately terminate an active call.

        Disconnects all participants instantly — the caller hears the line
        drop. There is no graceful goodbye; the call just ends.

        Use get_active_calls first to find the call_id of a live call.
        Only works on calls that are currently in progress.

        Use this sparingly — for emergencies, stuck calls, or when
        explicitly asked to end a call. In most cases, the agent's own
        timeout and hangup logic will end calls naturally.
        """
        r = await client.post(f"/calls/{call_id}/hangup")
        r.raise_for_status()
        return {"call_id": call_id, "status": "terminated"}

    @mcp.tool(name="get_active_calls")
    async def get_active_calls() -> dict[str, Any]:
        """Get all calls happening right now across your organization.

        Returns real-time data: which agents are on calls, how long each
        call has been running, caller numbers, and connection status.

        Use this for live monitoring, to find a call_id for hangup_call,
        or to check system load before starting a campaign.

        Returns empty list when no calls are active — that's normal.
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

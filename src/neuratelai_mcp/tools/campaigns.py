"""Campaign management tools — create, list, get, start, pause, stop."""

from __future__ import annotations

from typing import Any

import httpx
from fastmcp import FastMCP


def register(mcp: FastMCP, client: httpx.AsyncClient) -> None:

    @mcp.tool(name="create_campaign")
    async def create_campaign(
        name: str,
        agent_id: str,
        phone_number_id: str,
        call_list_id: str | None = None,
        max_concurrent_calls: int = 5,
        scheduled_start: str | None = None,
    ) -> dict[str, Any]:
        """Create an outbound calling campaign to dial a list of contacts.

        A campaign automates outbound calling at scale — it takes an agent,
        a phone number, and a contact list, then systematically dials each
        contact using the AI agent to handle the conversation.

        ## How campaigns work

        1. Create the campaign (this tool) — defines who calls, from what number
        2. Start the campaign (start_campaign) — begins dialing contacts
        3. The system calls contacts in parallel (up to max_concurrent_calls)
        4. Each call is handled by the agent autonomously
        5. Monitor progress with get_campaign
        6. Pause/stop at any time with pause_campaign or stop_campaign

        ## Prerequisites

        - An agent configured for outbound calls (use create_agent)
        - A phone number to call from (use list_numbers)
        - A call list with contacts (upload via the dashboard, or pass call_list_id)
        - Sufficient account balance for the expected call volume

        ## Concurrency

        max_concurrent_calls controls how many calls run simultaneously.
        Start low (3-5) to validate agent performance before scaling up.
        Higher concurrency = faster completion but more simultaneous cost.

        Args:
            name: Campaign display name (e.g. "Q2 Renewal Outreach")
            agent_id: The agent that handles every call in this campaign
            phone_number_id: Phone number UUID for caller ID (from list_numbers)
            call_list_id: Contact list ID (contains numbers + variables to dial)
            max_concurrent_calls: Simultaneous call limit (default 5)
            scheduled_start: ISO 8601 datetime to auto-start (e.g. "2026-04-15T09:00:00Z").
                             Omit to start manually with start_campaign.
        """
        body: dict[str, Any] = {
            "name": name,
            "agent_id": agent_id,
            "phone_number_id": phone_number_id,
            "campaign_config": {"max_concurrent_calls": max_concurrent_calls},
        }
        if call_list_id:
            body["call_list_id"] = call_list_id
        if scheduled_start:
            body["scheduled_start"] = scheduled_start

        r = await client.post("/campaigns", json=body)
        r.raise_for_status()
        d = r.json()
        return {
            "id": d.get("id"),
            "name": d.get("name"),
            "status": d.get("status"),
            "agent_id": d.get("agent_id"),
            "created_at": d.get("created_at"),
        }

    @mcp.tool(name="list_campaigns")
    async def list_campaigns(limit: int = 20) -> list[dict[str, Any]]:
        """List all outbound campaigns with current status and progress.

        Shows each campaign's state (draft, running, paused, completed,
        stopped) and progress (total contacts vs completed calls).

        Use this to find campaign IDs for start/pause/stop operations,
        or to monitor overall campaign health at a glance.
        """
        r = await client.get("/campaigns", params={"limit": min(limit, 100), "skip": 0})
        r.raise_for_status()
        results = r.json().get("results", [])
        return [
            {
                "id": c.get("id"),
                "name": c.get("name"),
                "status": c.get("status"),
                "agent_id": c.get("agent_id"),
                "total_contacts": c.get("total_contacts"),
                "completed_calls": c.get("completed_calls"),
                "created_at": c.get("created_at"),
            }
            for c in results
        ]

    @mcp.tool(name="get_campaign")
    async def get_campaign(campaign_id: str) -> dict[str, Any]:
        """Get full details and real-time progress for a campaign.

        Returns the complete campaign configuration, execution stats
        (calls completed, failed, remaining), and performance data.

        Use this to monitor a running campaign, debug why calls are
        failing, or review results after completion.
        """
        r = await client.get(f"/campaigns/{campaign_id}")
        r.raise_for_status()
        return r.json()

    @mcp.tool(name="start_campaign")
    async def start_campaign(campaign_id: str) -> dict[str, Any]:
        """Start a campaign — begins dialing contacts immediately.

        The campaign must be in "draft" or "paused" status. Once started,
        the system begins placing calls up to the configured concurrency
        limit. Calls continue until all contacts are reached or the
        campaign is paused/stopped.

        Check get_balance before starting — insufficient credits will
        cause calls to fail mid-campaign.
        """
        r = await client.post(f"/campaigns/{campaign_id}/start")
        r.raise_for_status()
        return {"campaign_id": campaign_id, "status": "running"}

    @mcp.tool(name="pause_campaign")
    async def pause_campaign(campaign_id: str) -> dict[str, Any]:
        """Pause a running campaign — no new calls, active calls finish.

        Calls already in progress will complete naturally. No new calls
        are placed. The campaign retains its progress and can be resumed
        with start_campaign.

        Use this to throttle costs, investigate quality issues, or
        pause during off-hours before resuming later.
        """
        r = await client.post(f"/campaigns/{campaign_id}/pause")
        r.raise_for_status()
        return {"campaign_id": campaign_id, "status": "paused"}

    @mcp.tool(name="stop_campaign")
    async def stop_campaign(campaign_id: str) -> dict[str, Any]:
        """Stop a campaign permanently — remaining contacts will not be called.

        Unlike pause, stopping is final. The campaign cannot be restarted.
        Any contacts not yet called are abandoned. Calls in progress will
        finish, but the campaign is marked as stopped.

        Use pause_campaign instead if you might want to resume later.
        """
        r = await client.post(f"/campaigns/{campaign_id}/stop")
        r.raise_for_status()
        return {"campaign_id": campaign_id, "status": "stopped"}

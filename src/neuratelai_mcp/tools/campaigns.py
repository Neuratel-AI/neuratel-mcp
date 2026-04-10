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
        """Create a new outbound calling campaign.

        Use this to set up automated outbound calls to a list of contacts.
        Prerequisites: an agent_id (from list_agents) and a phone_number_id
        (from list_numbers) for caller ID.

        Args:
            name: Display name for the campaign
            agent_id: The agent that will handle all calls in this campaign
            phone_number_id: Phone number UUID to use as caller ID (from list_numbers)
            call_list_id: Optional ID of the call list containing contacts to dial
            max_concurrent_calls: How many calls to run simultaneously (default: 5)
            scheduled_start: ISO 8601 datetime to auto-start (e.g. "2026-04-15T09:00:00Z")

        Returns: campaign id, name, status, and configuration summary.
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
        """List all outbound campaigns with their current status.

        Use this to see running campaigns, check which are active vs paused,
        or find a campaign_id for other operations.

        Returns: list of campaigns with id, name, status, progress, and agent.
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
        """Get full details and current progress for a specific campaign.

        Use this after starting a campaign to check progress:
        how many calls completed, how many failed, current status.

        Returns: campaign configuration, progress stats, and performance summary.
        """
        r = await client.get(f"/campaigns/{campaign_id}")
        r.raise_for_status()
        return r.json()

    @mcp.tool(name="start_campaign")
    async def start_campaign(campaign_id: str) -> dict[str, Any]:
        """Start an outbound calling campaign.

        Use this to begin dialing contacts in a campaign that is in "draft"
        or "paused" status. The campaign will begin placing calls immediately.

        ⚠️ COST WARNING: Starts placing real phone calls at scale.
        Only use when explicitly requested.

        Returns: campaign id and new status ("running").
        """
        r = await client.post(f"/campaigns/{campaign_id}/start")
        r.raise_for_status()
        return {"campaign_id": campaign_id, "status": "running"}

    @mcp.tool(name="pause_campaign")
    async def pause_campaign(campaign_id: str) -> dict[str, Any]:
        """Pause a running campaign — calls in progress finish, no new calls start.

        Use this to temporarily halt a campaign without losing progress.
        The campaign can be resumed with start_campaign.

        Returns: campaign id and new status ("paused").
        """
        r = await client.post(f"/campaigns/{campaign_id}/pause")
        r.raise_for_status()
        return {"campaign_id": campaign_id, "status": "paused"}

    @mcp.tool(name="stop_campaign")
    async def stop_campaign(campaign_id: str) -> dict[str, Any]:
        """Stop and terminate a campaign permanently.

        Use this to end a campaign entirely. Unlike pause, stopping a campaign
        cannot be easily reversed — you would need to create a new campaign.

        ⚠️ WARNING: Terminates the campaign. Remaining contacts will not be called.

        Returns: campaign id and new status ("stopped").
        """
        r = await client.post(f"/campaigns/{campaign_id}/stop")
        r.raise_for_status()
        return {"campaign_id": campaign_id, "status": "stopped"}

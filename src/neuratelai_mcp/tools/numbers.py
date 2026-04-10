"""Phone number management tools — list, assign, unassign."""

from __future__ import annotations

from typing import Any

import httpx
from fastmcp import FastMCP


def register(mcp: FastMCP, client: httpx.AsyncClient) -> None:

    @mcp.tool(name="list_numbers")
    async def list_numbers() -> list[dict[str, Any]]:
        """List all phone numbers in your organization.

        Use this to find a number_id before making calls or assigning a number
        to an agent. Shows which agent each number is currently assigned to.

        Returns: list of numbers with id, phone number, display name,
                 assigned agent_id, and active status.
        """
        r = await client.get("/numbers", params={"limit": 100, "skip": 0})
        r.raise_for_status()
        results = r.json().get("results", [])
        return [
            {
                "id": n.get("id"),
                "number": n.get("did"),
                "name": n.get("name"),
                "agent_id": n.get("agent_id"),
                "is_active": n.get("is_active"),
                "capabilities": n.get("capabilities", []),
            }
            for n in results
        ]

    @mcp.tool(name="assign_number")
    async def assign_number(phone_number_id: str, agent_id: str) -> dict[str, Any]:
        """Assign a phone number to a voice AI agent.

        After assigning, inbound calls to this number will be handled by the
        specified agent. Use list_numbers to find the phone_number_id and
        list_agents to find the agent_id.

        ⚠️ WARNING: This immediately changes call routing. Any existing assignment
        on this number will be replaced.

        Returns: confirmation with phone_number_id and assigned agent_id.
        """
        r = await client.post(
            f"/numbers/{phone_number_id}/assign",
            json={"agent_id": agent_id},
        )
        r.raise_for_status()
        return {
            "phone_number_id": phone_number_id,
            "agent_id": agent_id,
            "status": "assigned",
        }

    @mcp.tool(name="unassign_number")
    async def unassign_number(phone_number_id: str) -> dict[str, Any]:
        """Remove the agent assignment from a phone number.

        After unassigning, inbound calls to this number will not be answered
        by any agent. Use this before reassigning to a different agent or
        when retiring a number from active use.

        Returns: confirmation with phone_number_id and unassigned status.
        """
        r = await client.post(f"/numbers/{phone_number_id}/unassign")
        r.raise_for_status()
        return {"phone_number_id": phone_number_id, "status": "unassigned"}

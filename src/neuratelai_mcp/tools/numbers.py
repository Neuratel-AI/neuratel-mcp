"""Phone number management tools — list, assign, unassign."""

from __future__ import annotations

from typing import Any

import httpx
from fastmcp import FastMCP


def register(mcp: FastMCP, client: httpx.AsyncClient) -> None:

    @mcp.tool(name="list_numbers")
    async def list_numbers() -> list[dict[str, Any]]:
        """List all phone numbers provisioned in your organization.

        Phone numbers are the entry point for inbound calls and the caller ID
        for outbound calls. Each number can be assigned to one agent at a time.

        Use this to:
        - Find a number_id for make_call or create_campaign
        - See which agent each number routes to
        - Check number capabilities (voice, SMS, etc.)
        - Find unassigned numbers available for new agents

        A number with agent_id=null is not answering inbound calls. Assign
        an agent with assign_number to start routing calls to it.
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
        """Route a phone number's inbound calls to an AI agent.

        After assignment, every inbound call to this number is automatically
        answered by the specified agent. The agent uses its configured
        first_message, instructions, voice, and all other settings.

        If the number was previously assigned to a different agent, the
        assignment is replaced — calls immediately start routing to the
        new agent.

        This only affects inbound calls. For outbound calls, you specify
        the agent and number separately in make_call.

        Args:
            phone_number_id: The number to configure (from list_numbers)
            agent_id: The agent that will answer calls (from list_agents)
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
        """Remove the agent from a phone number — inbound calls stop being answered.

        After unassigning, calls to this number will not be picked up by any
        agent. The number still exists and can be reassigned later.

        Use this when retiring a number, switching agents (unassign then
        assign_number to the new agent), or temporarily taking a number
        offline for maintenance.
        """
        r = await client.post(f"/numbers/{phone_number_id}/unassign")
        r.raise_for_status()
        return {"phone_number_id": phone_number_id, "status": "unassigned"}

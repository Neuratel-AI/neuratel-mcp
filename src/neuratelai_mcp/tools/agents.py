"""Agent management tools — create, list, get, update, delete."""

from __future__ import annotations

from typing import Any

import httpx
from fastmcp import FastMCP


def register(mcp: FastMCP, client: httpx.AsyncClient) -> None:

    @mcp.tool(name="create_agent")
    async def create_agent(
        name: str,
        instructions: str,
        voice_provider: str = "elevenlabs",
        voice_id: str = "gHu9GtaHOXcSqFTK06ux",
        brain_provider: str = "openai",
        brain_model: str = "gpt-4.1",
        transcriber_provider: str = "deepgram",
        transcriber_model: str = "nova-3",
        first_message: str = "",
    ) -> dict[str, Any]:
        """Create a new voice AI agent.

        Use this when asked to build, create, or set up a new agent.
        Provide a name and instructions (system prompt) at minimum.
        All other fields have production-ready defaults.

        ⚠️ COST WARNING: Creates a billable resource. Only use when explicitly requested.

        Returns: agent id, name, status, and full configuration.
        """
        body: dict[str, Any] = {
            "name": name,
            "brain": {
                "provider": brain_provider,
                "model": brain_model,
                "instructions": instructions,
            },
            "voice": {
                "provider": voice_provider,
                "voice_id": voice_id,
            },
            "transcriber": {
                "provider": transcriber_provider,
                "model": transcriber_model,
            },
        }
        if first_message:
            body["first_message"] = {"enabled": True, "text": first_message}

        r = await client.post("/agents", json=body)
        r.raise_for_status()
        d = r.json()
        return {
            "id": d.get("id"),
            "name": d.get("name"),
            "status": d.get("status"),
            "brain_model": (d.get("brain") or {}).get("model"),
            "voice_provider": (d.get("voice") or {}).get("provider"),
            "created_at": d.get("created_at"),
        }

    @mcp.tool(name="list_agents")
    async def list_agents(limit: int = 20) -> list[dict[str, Any]]:
        """List all voice AI agents in your organization.

        Use this to see what agents exist, find an agent_id for other operations,
        or get an overview of your agent setup.

        Returns: list of agents with id, name, status, brain model, and call count.
        """
        r = await client.get("/agents", params={"limit": min(limit, 100), "skip": 0})
        r.raise_for_status()
        results = r.json().get("results", [])
        return [
            {
                "id": a.get("id"),
                "name": a.get("name"),
                "status": a.get("status"),
                "is_active": a.get("is_active"),
                "brain_model": (a.get("brain") or {}).get("model"),
                "call_count": a.get("call_count", 0),
                "created_at": a.get("created_at"),
            }
            for a in results
        ]

    @mcp.tool(name="get_agent")
    async def get_agent(agent_id: str) -> dict[str, Any]:
        """Get full configuration details for a specific agent.

        Use this when you need to inspect an agent's instructions, voice settings,
        transcriber, transfer rules, or analytics config. Also useful before updating.

        Returns: complete agent configuration including brain, voice, transcriber,
                 conversation settings, tools, and transfer rules.
        """
        r = await client.get(f"/agents/{agent_id}")
        r.raise_for_status()
        return r.json()

    @mcp.tool(name="update_agent")
    async def update_agent(
        agent_id: str,
        name: str | None = None,
        instructions: str | None = None,
        brain_model: str | None = None,
        brain_provider: str | None = None,
        voice_id: str | None = None,
        voice_provider: str | None = None,
        first_message: str | None = None,
        is_active: bool | None = None,
    ) -> dict[str, Any]:
        """Update an existing agent's configuration.

        Only the fields you provide will be changed — all others stay as-is.
        Use get_agent first if you need to see the current configuration.

        Returns: updated agent with id, name, status, and key config fields.
        """
        body: dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        if is_active is not None:
            body["is_active"] = is_active
        if instructions is not None or brain_model is not None or brain_provider is not None:
            brain: dict[str, Any] = {}
            if instructions is not None:
                brain["instructions"] = instructions
            if brain_model is not None:
                brain["model"] = brain_model
            if brain_provider is not None:
                brain["provider"] = brain_provider
            body["brain"] = brain
        if voice_id is not None or voice_provider is not None:
            voice: dict[str, Any] = {}
            if voice_id is not None:
                voice["voice_id"] = voice_id
            if voice_provider is not None:
                voice["provider"] = voice_provider
            body["voice"] = voice
        if first_message is not None:
            body["first_message"] = {"enabled": True, "text": first_message}

        r = await client.patch(f"/agents/{agent_id}", json=body)
        r.raise_for_status()
        d = r.json()
        return {
            "id": d.get("id"),
            "name": d.get("name"),
            "status": d.get("status"),
            "updated_at": d.get("updated_at"),
        }

    @mcp.tool(name="delete_agent")
    async def delete_agent(agent_id: str) -> dict[str, Any]:
        """Permanently delete a voice AI agent.

        Use this to clean up agents that are no longer needed.

        ⚠️ WARNING: This is permanent and cannot be undone. Any phone numbers
        assigned to this agent will stop answering calls. Only use when explicitly requested.

        Returns: confirmation with the deleted agent id.
        """
        r = await client.delete(f"/agents/{agent_id}")
        r.raise_for_status()
        return {"deleted": True, "agent_id": agent_id}

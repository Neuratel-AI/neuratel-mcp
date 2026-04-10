"""Knowledge base tools — list, add from text/URL, attach to agent."""

from __future__ import annotations

from typing import Any

import httpx
from fastmcp import FastMCP


def register(mcp: FastMCP, client: httpx.AsyncClient) -> None:

    @mcp.tool(name="list_knowledge_bases")
    async def list_knowledge_bases() -> list[dict[str, Any]]:
        """List all knowledge bases in your organization.

        Use this to see existing knowledge sources before creating new ones
        or before attaching one to an agent. Shows each KB's name, type,
        status, and which agents it's attached to.

        Returns: list of knowledge bases with id, name, type, status, and source.
        """
        r = await client.get("/knowledge-base", params={"limit": 100, "skip": 0})
        r.raise_for_status()
        results = r.json().get("results", [])
        return [
            {
                "id": kb.get("id"),
                "name": kb.get("name"),
                "type": kb.get("kb_type"),
                "status": kb.get("status"),
                "source_url": kb.get("source_url"),
                "created_at": kb.get("created_at"),
            }
            for kb in results
        ]

    @mcp.tool(name="add_knowledge_from_text")
    async def add_knowledge_from_text(
        name: str,
        text: str,
        description: str = "",
    ) -> dict[str, Any]:
        """Create a knowledge base from plain text content.

        Use this to add FAQs, product information, policies, scripts,
        or any text-based content that the agent should know about.
        After creating, use attach_knowledge_to_agent to connect it.

        Args:
            name: Display name for this knowledge base (e.g. "FAQ - Returns Policy")
            text: The actual text content to store and index
            description: Optional description of what this knowledge covers

        Returns: knowledge base id, name, and processing status.
        """
        body: dict[str, Any] = {"name": name, "text": text}
        if description:
            body["description"] = description

        r = await client.post("/knowledge-base/from-text", json=body)
        r.raise_for_status()
        d = r.json()
        return {
            "id": d.get("id"),
            "name": d.get("name"),
            "status": d.get("status"),
            "created_at": d.get("created_at"),
        }

    @mcp.tool(name="add_knowledge_from_url")
    async def add_knowledge_from_url(
        name: str,
        url: str,
        description: str = "",
    ) -> dict[str, Any]:
        """Create a knowledge base by fetching and indexing a URL.

        Use this to add web pages, documentation, or online resources as
        knowledge sources. The platform will fetch and index the content.
        After creating, use attach_knowledge_to_agent to connect it.

        Args:
            name: Display name for this knowledge base (e.g. "Product Docs")
            url: The URL to fetch and index (must be publicly accessible)
            description: Optional description of what this knowledge covers

        Returns: knowledge base id, name, source URL, and processing status.
        """
        body: dict[str, Any] = {"name": name, "url": url}
        if description:
            body["description"] = description

        r = await client.post("/knowledge-base/from-url", json=body)
        r.raise_for_status()
        d = r.json()
        return {
            "id": d.get("id"),
            "name": d.get("name"),
            "source_url": url,
            "status": d.get("status"),
            "created_at": d.get("created_at"),
        }

    @mcp.tool(name="attach_knowledge_to_agent")
    async def attach_knowledge_to_agent(
        agent_id: str,
        knowledge_base_ids: list[str],
    ) -> dict[str, Any]:
        """Connect one or more knowledge bases to a voice AI agent.

        After attaching, the agent will use these knowledge bases to answer
        questions during calls via RAG (retrieval-augmented generation).
        Use list_knowledge_bases to find knowledge_base_ids.

        ⚠️ NOTE: This replaces all currently attached knowledge bases.
        Include all IDs you want attached, not just the new ones.

        Args:
            agent_id: The agent to connect knowledge bases to
            knowledge_base_ids: List of knowledge base IDs to attach

        Returns: confirmation with agent_id and list of attached KB IDs.
        """
        r = await client.put(
            f"/knowledge-base/agent/{agent_id}",
            json={"knowledge_base_ids": knowledge_base_ids},
        )
        r.raise_for_status()
        return {
            "agent_id": agent_id,
            "knowledge_base_ids": knowledge_base_ids,
            "status": "attached",
        }

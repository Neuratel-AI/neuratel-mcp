"""Knowledge base tools — list, add from text/URL, attach to agent."""

from __future__ import annotations

from typing import Any

import httpx
from fastmcp import FastMCP


def register(mcp: FastMCP, client: httpx.AsyncClient) -> None:

    @mcp.tool(name="list_knowledge_bases")
    async def list_knowledge_bases() -> list[dict[str, Any]]:
        """List all knowledge bases in your organization.

        Knowledge bases are documents, FAQs, and web content that agents
        can search during calls using RAG (retrieval-augmented generation).
        When a caller asks a question, the agent searches attached knowledge
        bases for relevant information before responding.

        Use this to see what knowledge exists before creating duplicates,
        or to find knowledge_base_ids for attach_knowledge_to_agent.
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

        The text is immediately chunked and indexed for RAG retrieval.
        After creating, use attach_knowledge_to_agent to connect it to
        an agent — the agent will then search this content during calls.

        Best for: FAQs, product specs, policies, scripts, pricing tables,
        troubleshooting guides, or any structured text content.

        Tips for good knowledge base content:
        - Use clear headings and Q&A format for best retrieval
        - Keep each topic self-contained (the system retrieves chunks)
        - Include the exact phrases callers would use, not just jargon
        - Max 500KB of text per knowledge base

        Args:
            name: Display name (e.g. "Returns Policy FAQ", "Product Catalog")
            text: The actual content to index. Plain text or markdown.
            description: What this knowledge covers (helps with organization)
        """
        body: dict[str, Any] = {"name": name, "content": text}
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
        """Create a knowledge base by scraping and indexing a web page.

        Fetches the URL, extracts the content (handles JavaScript-rendered
        pages), converts to clean text, chunks it, and indexes for RAG.
        Processing happens asynchronously — check the status field.

        Best for: product documentation, help center articles, pricing
        pages, company info, or any publicly accessible web content.

        The URL must be publicly accessible. Status will be "processing"
        initially, then "ready" when indexing completes (usually <30 seconds),
        or "error" if the page couldn't be fetched.

        Args:
            name: Display name (e.g. "Product Documentation", "Pricing Page")
            url: Public URL to scrape (https://docs.example.com/faq)
            description: What this knowledge covers
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
        """Connect knowledge bases to an agent for RAG-powered conversations.

        Once attached, the agent automatically searches these knowledge bases
        when callers ask questions. The agent retrieves relevant chunks and
        uses them to give accurate, grounded answers instead of hallucinating.

        This REPLACES all current attachments — pass the complete list of
        knowledge base IDs you want attached, not just new additions. To
        add a new KB without removing existing ones, include all current
        IDs plus the new one.

        Multiple knowledge bases can be attached to the same agent. The
        system searches across all of them and returns the most relevant
        chunks regardless of which KB they came from.

        Args:
            agent_id: The agent to connect knowledge to
            knowledge_base_ids: Complete list of KB IDs to attach
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

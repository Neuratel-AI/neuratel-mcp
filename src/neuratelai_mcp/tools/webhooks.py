"""Webhook management tools — create and list."""

from __future__ import annotations

from typing import Any

import httpx
from fastmcp import FastMCP


def register(mcp: FastMCP, client: httpx.AsyncClient) -> None:

    @mcp.tool(name="create_webhook")
    async def create_webhook(
        name: str,
        url: str,
        events: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create a webhook to receive real-time notifications for call events.

        Webhooks send HTTP POST requests to your URL when events occur.
        Use them to trigger workflows, update CRMs, log call outcomes,
        or build real-time dashboards.

        ## Available event types (dotted notation)

        Call lifecycle:
        - "call.started" — call connected, conversation beginning
        - "call.ended" — call disconnected, final data available
        - "call.ringing" — outbound call is ringing
        - "call.answered" — outbound call was picked up
        - "call.failed" — call could not connect
        - "call.transferred" — call was transferred to another number
        - "call.summary.ready" — post-call summary and analytics available

        Transcript events:
        - "transcript.partial" — real-time partial transcript update
        - "transcript.final" — final transcript segment
        - "transcript.ready" — complete transcript available

        Recording:
        - "recording.ready" — call recording is available for download

        Agent events:
        - "agent.turn.started" — agent began generating a response
        - "agent.turn.ended" — agent finished speaking
        - "agent.tool.called" — agent invoked a tool (RAG, transfer, hangup, etc.)

        Pass an empty list or omit events to subscribe to ALL event types.

        The signing secret is returned ONCE in the response. Save it
        immediately — use it to verify webhook requests via HMAC-SHA256
        to ensure they're genuinely from Neuratel.

        Args:
            name: Display name for this webhook (e.g. "CRM Integration")
            url: Your HTTPS endpoint to receive events. Must use HTTPS.
            events: Event types to subscribe to (dotted format). Empty = all.
        """
        body: dict[str, Any] = {
            "name": name,
            "url": url,
            "events": events or [],
        }

        r = await client.post("/webhooks", json=body)
        r.raise_for_status()
        d = r.json()
        return {
            "id": d.get("id"),
            "url": d.get("url"),
            "events": d.get("events", []),
            "secret": d.get("secret"),  # shown once — must be saved
            "is_active": d.get("is_active"),
            "created_at": d.get("created_at"),
        }

    @mcp.tool(name="list_webhooks")
    async def list_webhooks() -> list[dict[str, Any]]:
        """List all configured webhook subscriptions.

        Shows each webhook's URL, subscribed events, active status, and
        delivery health (failure count, last successful delivery).

        Use this to audit integrations, check for delivery failures,
        or verify that the right events are being captured.

        A high failure_count indicates the endpoint is down or rejecting
        requests — investigate the URL or check your server logs.
        """
        r = await client.get("/webhooks", params={"limit": 100, "skip": 0})
        r.raise_for_status()
        results = r.json().get("results", [])
        return [
            {
                "id": w.get("id"),
                "url": w.get("url"),
                "name": w.get("name"),
                "events": w.get("events", []),
                "is_active": w.get("is_active"),
                "failure_count": w.get("failure_count", 0),
                "last_success_at": w.get("last_success_at"),
                "created_at": w.get("created_at"),
            }
            for w in results
        ]

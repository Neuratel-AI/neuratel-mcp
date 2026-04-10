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
        """Create a webhook to receive real-time event notifications.

        Use this to set up HTTP callbacks for call events. Common event types:
        - "session_report" — fires when a call ends with full transcript
        - "call_ended" — fires immediately when a call disconnects
        - "recording_ready" — fires when recording is available
        - "analysis_complete" — fires when post-call AI analysis finishes

        ⚠️ The signing secret is returned ONCE — store it securely.
        Use it to verify webhook requests with HMAC-SHA256.

        Args:
            name: Display name for this webhook (required)
            url: Your HTTPS endpoint to receive events
            events: Event types to subscribe to
                (default: session_report, call_ended, recording_ready)

        Returns: webhook id, secret (shown once), and subscribed event types.
        """
        body: dict[str, Any] = {
            "name": name,
            "url": url,
            "events": events or ["session_report", "call_ended", "recording_ready"],
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
        """List all active webhook subscriptions.

        Use this to see what webhooks are configured, check delivery health,
        or find a webhook_id before updating or deleting one.

        Returns: list of webhooks with id, URL, event types, active status,
                 and delivery health (failure count, last delivery).
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

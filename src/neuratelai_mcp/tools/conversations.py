"""Conversation tools — unified inbox for SMS, WhatsApp, and voice threads."""

from __future__ import annotations

from typing import Any

import httpx
from fastmcp import FastMCP


def register(mcp: FastMCP, client: httpx.AsyncClient) -> None:

    @mcp.tool(name="list_conversations")
    async def list_conversations(
        channel: str | None = None,
        status: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        """List conversation threads across SMS, WhatsApp, and voice.

        A conversation groups all messages and voice sessions exchanged with
        one contact through one channel. Use this for inbox-style review.

        Args:
            channel: "sms" | "whatsapp" | "voice" (omit for all channels)
            status: Conversation lifecycle filter
            limit: Max threads (default 20, max 100)
        """
        params: dict[str, Any] = {"limit": min(limit, 100), "skip": 0}
        if channel:
            params["channel"] = channel
        if status:
            params["status"] = status
        r = await client.get("/conversations", params=params)
        r.raise_for_status()
        return r.json()

    @mcp.tool(name="get_conversation")
    async def get_conversation(conversation_id: str) -> dict[str, Any]:
        """Get a single conversation thread including its current state.

        Returns the conversation envelope (channel, contact, agent assignment,
        dynamic_variables, last activity) but NOT the message history. Use
        list_conversation_messages for the messages.
        """
        r = await client.get(f"/conversations/{conversation_id}")
        r.raise_for_status()
        return r.json()

    @mcp.tool(name="list_conversation_messages")
    async def list_conversation_messages(
        conversation_id: str,
        limit: int = 50,
        since: str | None = None,
        before: str | None = None,
    ) -> dict[str, Any]:
        """List messages exchanged in a conversation, newest first.

        Args:
            conversation_id: From list_conversations
            limit: Max messages (default 50)
            since: ISO 8601 — return messages after this timestamp
            before: ISO 8601 — return messages before this timestamp
        """
        params: dict[str, Any] = {"limit": min(limit, 200), "skip": 0}
        if since:
            params["since"] = since
        if before:
            params["before"] = before
        r = await client.get(f"/conversations/{conversation_id}/messages", params=params)
        r.raise_for_status()
        return r.json()

    @mcp.tool(name="send_conversation_message")
    async def send_conversation_message(
        conversation_id: str,
        body: str,
        media_urls: list[str] | None = None,
        client_temp_id: str | None = None,
    ) -> dict[str, Any]:
        """Send an outbound message into an existing conversation.

        For SMS / WhatsApp freeform replies. Templated WhatsApp sends should
        use the agent's WhatsApp template config instead of this tool.

        Args:
            conversation_id: Target thread
            body: Message text (required by backend ConversationSendRequest)
            media_urls: Optional list of media URLs for MMS / WhatsApp media
            client_temp_id: Optional client-supplied dedup key
        """
        payload: dict[str, Any] = {"body": body}
        if media_urls:
            payload["media_urls"] = media_urls
        if client_temp_id:
            payload["client_temp_id"] = client_temp_id
        r = await client.post(f"/conversations/{conversation_id}/messages", json=payload)
        r.raise_for_status()
        return r.json()

    @mcp.tool(name="mark_conversation_read")
    async def mark_conversation_read(conversation_id: str) -> dict[str, Any]:
        """Mark all messages in a conversation as read."""
        r = await client.post(f"/conversations/{conversation_id}/read")
        r.raise_for_status()
        return r.json()

    @mcp.tool(name="get_conversation_timeline")
    async def get_conversation_timeline(
        conversation_id: str,
        limit: int = 50,
        since: str | None = None,
        before: str | None = None,
    ) -> dict[str, Any]:
        """Get a unified timeline of messages + voice sessions for a conversation.

        Useful when a contact has both chat exchanges and call attempts on the
        same thread — the timeline interleaves them chronologically.
        """
        params: dict[str, Any] = {"limit": min(limit, 200)}
        if since:
            params["since"] = since
        if before:
            params["before"] = before
        r = await client.get(f"/conversations/{conversation_id}/timeline", params=params)
        r.raise_for_status()
        return r.json()

    @mcp.tool(name="update_conversation_variables")
    async def update_conversation_variables(
        conversation_id: str,
        dynamic_variables: dict[str, Any],
        replace: bool = False,
    ) -> dict[str, Any]:
        """Set or update dynamic_variables on a conversation thread.

        These variables are inherited by any subsequent voice/chat turn that
        renders the agent's prompt template. Useful when context arrives
        out-of-band (CRM sync, webhook from your system, etc.).

        Args:
            conversation_id: Target thread
            dynamic_variables: dict of {name: value}
            replace: If True, replaces the existing dict entirely. If False
                     (default), merges into the existing dict.
        """
        body = {"dynamic_variables": dynamic_variables, "replace": replace}
        r = await client.patch(f"/conversations/{conversation_id}/dynamic_variables", json=body)
        r.raise_for_status()
        return r.json()

    @mcp.tool(name="get_chat_analytics")
    async def get_chat_analytics(
        start_date: str | None = None,
        end_date: str | None = None,
        channel: str | None = None,
        agent_id: str | None = None,
        interval: str | None = None,
    ) -> dict[str, Any]:
        """Get chat-channel KPIs (SMS + WhatsApp).

        Returns inbound / outbound message counts, response latency, agent
        utilisation, and per-conversation outcomes for the requested window.
        For combined voice + chat KPIs use get_combined_analytics instead.
        """
        params: dict[str, Any] = {}
        for k, v in [
            ("start_date", start_date),
            ("end_date", end_date),
            ("channel", channel),
            ("agent_id", agent_id),
            ("interval", interval),
        ]:
            if v is not None:
                params[k] = v
        r = await client.get("/conversations/analytics/dashboard", params=params)
        r.raise_for_status()
        return r.json()

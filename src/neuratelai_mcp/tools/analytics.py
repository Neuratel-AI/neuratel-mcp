"""Cross-channel analytics tools."""

from __future__ import annotations

from typing import Any

import httpx
from fastmcp import FastMCP


def register(mcp: FastMCP, client: httpx.AsyncClient) -> None:

    @mcp.tool(name="get_combined_analytics")
    async def get_combined_analytics(
        start_date: str | None = None,
        end_date: str | None = None,
        agent_id: str | None = None,
        channel: str | None = None,
        direction: str | None = None,
        interval: str | None = None,
    ) -> dict[str, Any]:
        """Get combined voice + chat KPI dashboard.

        Returns total volume, success rate, average sentiment score, total
        cost, and per-bucket time series across both voice sessions and chat
        conversations. For per-channel breakdowns use get_chat_analytics or
        list_calls instead.

        Args:
            start_date: ISO date for the lookback window start
            end_date: ISO date for window end (defaults to now)
            agent_id: Filter to one agent
            channel: "phone" | "web" | "whatsapp_voice" | "sms" | "whatsapp"
            direction: "inbound" | "outbound"
            interval: Bucket granularity — "hour" | "day" | "week" | "month"
        """
        params: dict[str, Any] = {}
        for k, v in [
            ("start_date", start_date),
            ("end_date", end_date),
            ("agent_id", agent_id),
            ("channel", channel),
            ("direction", direction),
            ("interval", interval),
        ]:
            if v is not None:
                params[k] = v
        r = await client.get("/analytics/dashboard", params=params)
        r.raise_for_status()
        return r.json()

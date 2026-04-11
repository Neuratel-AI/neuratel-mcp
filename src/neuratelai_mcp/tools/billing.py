"""Billing tools — balance and usage."""

from __future__ import annotations

from typing import Any

import httpx
from fastmcp import FastMCP


def register(mcp: FastMCP, client: httpx.AsyncClient) -> None:

    @mcp.tool(name="get_balance")
    async def get_balance() -> dict[str, Any]:
        """Check the current account balance and credit status.

        Returns the available balance in the account's billing currency
        (set in organization settings — defaults to USD).

        Always check this before:
        - Making outbound calls (make_call)
        - Starting campaigns (start_campaign)
        - Any operation that incurs telephony or AI costs

        A zero or negative balance means calls will fail. The has_credits
        field is a quick boolean check for sufficient funds.
        """
        r = await client.get("/billing/balance")
        r.raise_for_status()
        d = r.json()
        return {
            "balance": d.get("balance_dollars"),
            "balance_cents": d.get("balance_cents"),
            "has_credits": d.get("has_credits", False),
            "currency": d.get("currency", "USD"),
        }

    @mcp.tool(name="get_usage")
    async def get_usage(days: int = 30) -> dict[str, Any]:
        """Get usage summary for a time period.

        Returns aggregate stats: how many calls were made, total minutes
        consumed, and total amount billed. Useful for cost monitoring,
        capacity planning, and usage reporting.

        Args:
            days: Look-back period in days (default 30, max 365).
                  Use 1 for today's usage, 7 for the past week.
        """
        r = await client.get("/billing/usage", params={"days": days})
        r.raise_for_status()
        d = r.json()
        return {
            "call_count": d.get("call_count"),
            "total_minutes": d.get("total_minutes"),
            "total_billed": d.get("total_billed"),
            "period_start": d.get("period_start"),
            "period_end": d.get("period_end"),
        }

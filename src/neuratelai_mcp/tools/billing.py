"""Billing tools — balance and usage."""

from __future__ import annotations

from typing import Any

import httpx
from fastmcp import FastMCP


def register(mcp: FastMCP, client: httpx.AsyncClient) -> None:

    @mcp.tool(name="get_balance")
    async def get_balance() -> dict[str, Any]:
        """Get the current account balance and credit status.

        Use this before making calls or starting campaigns to verify there
        are sufficient credits. A balance check is good practice before any
        operation that incurs telephony costs.

        Returns: balance in USD and cents, whether credits are available,
                 and the account currency.
        """
        r = await client.get("/billing/balance")
        r.raise_for_status()
        d = r.json()
        return {
            "balance_usd": d.get("balance_dollars"),
            "balance_cents": d.get("balance_cents"),
            "has_credits": (d.get("balance_cents", 0) or 0) > 0,
            "currency": d.get("currency", "USD"),
        }

    @mcp.tool(name="get_usage")
    async def get_usage(days: int = 30) -> dict[str, Any]:
        """Get usage summary for the last N days.

        Use this to see how many calls were made, total minutes used,
        and total cost over a time period. Useful for reporting and
        capacity planning.

        Args:
            days: Number of days to look back (default: 30)

        Returns: call count, total minutes, total cost, and time period.
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

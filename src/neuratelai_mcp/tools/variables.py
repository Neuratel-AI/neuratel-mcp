"""Template variable catalog tools."""

from __future__ import annotations

from typing import Any

import httpx
from fastmcp import FastMCP


def register(mcp: FastMCP, client: httpx.AsyncClient) -> None:

    @mcp.tool(name="get_system_variables_catalog")
    async def get_system_variables_catalog() -> dict[str, Any]:
        """List the platform's built-in `system__*` template variables.

        These are auto-injected at call time by the platform — you never pass
        them in dynamic_variables. Examples include system__org_id,
        system__channel, system__time_utc, system__caller_region,
        system__call_duration_secs, etc.

        Use this catalog to:
        - Validate which {{system__*}} placeholders are safe to embed in agent prompts
        - Distinguish auto-injected variables from user-supplied ones when
          building dynamic_variables payloads for make_call

        Returns a list of {name, description, type, available_in} entries
        describing each system variable's semantics and channel availability.
        """
        r = await client.get("/variables/system-catalog")
        r.raise_for_status()
        return r.json()

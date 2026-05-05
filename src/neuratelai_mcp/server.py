"""
Neuratel MCP Server

46 hand-crafted tools covering every agentic workflow on Neuratel Studio:
agents (incl. templates + required variables), voice sessions, conversations
(SMS / WhatsApp), campaigns, phone numbers, knowledge bases, billing,
webhooks, DNC directory, system variable catalog, combined analytics.

Usage:
    NEURATEL_API_KEY=nk_live_... uvx neuratel-mcp
    NEURATEL_API_KEY=nk_live_... neuratel-mcp --transport http --port 8000

Environment variables:
    NEURATEL_API_KEY   (required) Your Neuratel API key
    NEURATEL_BASE_URL  (optional) Override API base URL (default: https://api.neuratel.ai/v1)
"""

from __future__ import annotations

import os

from fastmcp import FastMCP

from ._client import make_client
from .tools import (
    agents,
    analytics,
    billing,
    calls,
    campaigns,
    conversations,
    dnc,
    knowledge,
    numbers,
    variables,
    webhooks,
)

_BASE_URL = os.environ.get("NEURATEL_BASE_URL", "https://api.neuratel.ai/v1")


def _require_api_key() -> str:
    key = os.environ.get("NEURATEL_API_KEY")
    if not key:
        raise RuntimeError(
            "NEURATEL_API_KEY environment variable is required.\n"
            "Get your API key at https://app.neuratel.ai/api-keys"
        )
    return key


def create_server() -> FastMCP:
    """Build and return the configured MCP server with all 46 tools."""
    api_key = _require_api_key()
    client = make_client(api_key, _BASE_URL)

    mcp = FastMCP(
        name="Neuratel",
        instructions=(
            "You are connected to Neuratel Studio — an AI voice agent platform. "
            "You can create and manage voice AI agents, place outbound calls, "
            "run calling campaigns, manage phone numbers, add knowledge bases, "
            "and monitor call activity. "
            "Always check get_balance before making calls or starting campaigns. "
            "Always get a number_id from list_numbers before using make_call. "
            "Use get_call to read transcripts and analyze what happened on a call."
        ),
    )

    agents.register(mcp, client)
    calls.register(mcp, client)
    campaigns.register(mcp, client)
    numbers.register(mcp, client)
    knowledge.register(mcp, client)
    billing.register(mcp, client)
    webhooks.register(mcp, client)
    conversations.register(mcp, client)
    dnc.register(mcp, client)
    variables.register(mcp, client)
    analytics.register(mcp, client)

    return mcp


_server: FastMCP | None = None


def get_server() -> FastMCP:
    global _server
    if _server is None:
        _server = create_server()
    return _server

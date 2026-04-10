"""Tests for MCP server tool count and structure."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

EXPECTED_TOOLS = {
    # Agents (5)
    "create_agent",
    "list_agents",
    "get_agent",
    "update_agent",
    "delete_agent",
    # Calls (5)
    "make_call",
    "list_calls",
    "get_call",
    "hangup_call",
    "get_active_calls",
    # Campaigns (6)
    "create_campaign",
    "list_campaigns",
    "get_campaign",
    "start_campaign",
    "pause_campaign",
    "stop_campaign",
    # Numbers (3)
    "list_numbers",
    "assign_number",
    "unassign_number",
    # Knowledge Base (4)
    "list_knowledge_bases",
    "add_knowledge_from_text",
    "add_knowledge_from_url",
    "attach_knowledge_to_agent",
    # Billing (2)
    "get_balance",
    "get_usage",
    # Webhooks (2)
    "create_webhook",
    "list_webhooks",
}


@pytest.fixture
def mcp_server():
    with patch.dict(os.environ, {"NEURATEL_API_KEY": "nk_live_test"}):
        from neuratelai_mcp.server import create_server

        return create_server()


@pytest.fixture
async def tools(mcp_server):
    return await mcp_server.list_tools()


async def test_tool_count(tools):
    """Server must expose exactly 27 tools."""
    names = {t.name for t in tools}
    assert len(names) == 27, (
        f"Expected 27 tools, got {len(names)}.\n"
        f"Extra: {names - EXPECTED_TOOLS}\n"
        f"Missing: {EXPECTED_TOOLS - names}"
    )


async def test_all_expected_tools_present(tools):
    """Every tool in the expected set must be registered."""
    names = {t.name for t in tools}
    missing = EXPECTED_TOOLS - names
    assert not missing, f"Missing tools: {missing}"


async def test_no_auto_generated_tools(tools):
    """No auto-generated operationId-style tool names."""
    names = {t.name for t in tools}
    auto_gen = [n for n in names if "_v1_" in n]
    assert not auto_gen, f"Auto-generated tools leaked: {auto_gen}"


async def test_no_legacy_custom_tools(tools):
    """Old custom tools from the previous implementation must not exist."""
    names = {t.name for t in tools}
    banned = {
        "create_voice_agent",
        "make_outbound_call",
        "get_account_balance",
        "list_recent_calls",
        "assign_number_to_agent",
        "get_platform_status",
        "start_web_call",
    }
    present = banned & names
    assert not present, f"Legacy tools still present: {present}"


async def test_all_tools_have_descriptions(tools):
    """Every tool must have a non-empty description."""
    missing = [t.name for t in tools if not (t.description or "").strip()]
    assert not missing, f"Tools missing descriptions: {missing}"


def test_server_requires_api_key():
    """Server raises RuntimeError when NEURATEL_API_KEY is not set."""
    env = {k: v for k, v in os.environ.items() if k != "NEURATEL_API_KEY"}
    with patch.dict(os.environ, env, clear=True):
        from neuratelai_mcp.server import create_server

        with pytest.raises(RuntimeError, match="NEURATEL_API_KEY"):
            create_server()

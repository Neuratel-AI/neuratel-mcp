"""Tests for MCP server tool count and structure."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

EXPECTED_TOOLS = {
    # Agents (8)
    "create_agent",
    "list_agents",
    "get_agent",
    "update_agent",
    "delete_agent",
    "duplicate_agent",
    "list_agent_templates",
    "get_agent_required_variables",
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
    # Conversations (8)
    "list_conversations",
    "get_conversation",
    "list_conversation_messages",
    "send_conversation_message",
    "mark_conversation_read",
    "get_conversation_timeline",
    "update_conversation_variables",
    "get_chat_analytics",
    # DNC (6)
    "dnc_check",
    "dnc_list_entries",
    "dnc_add_entry",
    "dnc_delete_entry",
    "dnc_get_settings",
    "dnc_update_settings",
    # Variables (1)
    "get_system_variables_catalog",
    # Analytics (1)
    "get_combined_analytics",
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
    """Server must expose exactly 46 tools."""
    names = {t.name for t in tools}
    assert len(names) == 46, (
        f"Expected 46 tools, got {len(names)}.\n"
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


# ── Parameter-schema spot checks (catch param-name drift in new tools) ────


async def test_dnc_check_takes_phone_param(tools):
    """dnc_check must accept `phone` (matches backend /v1/dnc/check?phone=...)."""
    tool = next(t for t in tools if t.name == "dnc_check")
    props = tool.parameters.get("properties", {})
    assert "phone" in props, f"dnc_check must accept phone, got: {list(props)}"


async def test_dnc_update_settings_uses_canonical_field_names(tools):
    """dnc_update_settings field names must match backend DNCSettingsRequest.

    Catches accidental drift to obvious-but-wrong shorthand like `enabled` /
    `auto_opt_out_detection`. Backend canonical names per shared schemas:
    `protection_enabled` and `auto_add_inbound_optouts`.
    """
    tool = next(t for t in tools if t.name == "dnc_update_settings")
    props = set(tool.parameters.get("properties", {}).keys())
    assert "protection_enabled" in props, f"got: {props}"
    assert "auto_add_inbound_optouts" in props, f"got: {props}"


async def test_send_conversation_message_uses_body_field(tools):
    """send_conversation_message must use `body` (matches backend ConversationSendRequest).

    Catches the wrong-field bug class — backend's required field is `body`,
    not `text` (which several tools/SDK methods initially used by guesswork).
    """
    tool = next(t for t in tools if t.name == "send_conversation_message")
    props = set(tool.parameters.get("properties", {}).keys())
    assert "body" in props, f"got: {props}"
    required = set(tool.parameters.get("required", []))
    assert "body" in required, f"body must be required, got required: {required}"


async def test_make_call_skips_system_vars_in_preflight(tools):
    """make_call's pre-flight extractor must not warn on {{system__*}} placeholders.

    Regression guard for the false-positive fix in calls.py:_extract_template_vars.
    The system catalog (system__org_id, system__channel, system__time_utc, ...)
    is auto-injected by the platform; users never supply those.
    """
    from neuratelai_mcp.tools.calls import _extract_template_vars

    found = _extract_template_vars(
        "Hello {{customer_name}}, calling on {{system__channel}} for {{system__org_name}}"
    )
    assert "customer_name" in found
    assert "system__channel" not in found
    assert "system__org_name" not in found

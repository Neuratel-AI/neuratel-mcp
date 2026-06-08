#!/usr/bin/env python3
"""Read-only smoke test for the Neuratel MCP server against live prod API.

Calls every read-only MCP tool through FastMCP's programmatic interface.
Never creates, updates, or deletes data (no make_call, no create_agent, etc.).

Usage:
    NEURATEL_API_KEY=nk_live_xxx uv run python scripts/smoke_prod.py
"""

from __future__ import annotations

import asyncio
import os
import sys

API_KEY = os.environ.get("NEURATEL_API_KEY")
if not API_KEY:
    sys.exit("NEURATEL_API_KEY env var required")

PASS: list[str] = []
FAIL: list[tuple[str, str]] = []


def _ok(label: str) -> None:
    PASS.append(label)
    print(f"  ✓ {label}")


def _fail(label: str, detail: str) -> None:
    FAIL.append((label, detail))
    print(f"  ✗ {label}  {detail[:120]}")


async def run() -> None:
    from neuratelai_mcp.server import create_server

    server = create_server()
    print("neuratel-mcp smoke — read-only prod tools\n")

    async def call(name: str, args: dict | None = None) -> object:
        result = await server.call_tool(name, args)
        if hasattr(result, "content"):
            return result.content
        return result

    # ── Agents (read-only subset) ──
    try:
        await call("list_agents", {"limit": 1})
        _ok("list_agents")
    except Exception as e:
        _fail("list_agents", str(e))

    try:
        await call("list_agent_templates")
        _ok("list_agent_templates")
    except Exception as e:
        _fail("list_agent_templates", str(e))

    # ── Calls (read-only subset) ──
    try:
        await call("list_calls", {"limit": 1})
        _ok("list_calls")
    except Exception as e:
        _fail("list_calls", str(e))

    try:
        await call("get_active_calls")
        _ok("get_active_calls")
    except Exception as e:
        _fail("get_active_calls", str(e))

    # ── Campaigns (read-only subset) ──
    try:
        await call("list_campaigns", {"limit": 1})
        _ok("list_campaigns")
    except Exception as e:
        _fail("list_campaigns", str(e))

    # ── Numbers ──
    try:
        await call("list_numbers")
        _ok("list_numbers")
    except Exception as e:
        _fail("list_numbers", str(e))

    # ── Knowledge Base ──
    try:
        await call("list_knowledge_bases")
        _ok("list_knowledge_bases")
    except Exception as e:
        _fail("list_knowledge_bases", str(e))

    # ── Billing ──
    try:
        await call("get_balance")
        _ok("get_balance")
    except Exception as e:
        _fail("get_balance", str(e))

    try:
        await call("get_usage")
        _ok("get_usage")
    except Exception as e:
        _fail("get_usage", str(e))

    # ── Webhooks ──
    try:
        await call("list_webhooks")
        _ok("list_webhooks")
    except Exception as e:
        _fail("list_webhooks", str(e))

    # ── Conversations (read-only subset) ──
    try:
        await call("list_conversations", {"limit": 1})
        _ok("list_conversations")
    except Exception as e:
        _fail("list_conversations", str(e))

    try:
        await call("get_chat_analytics")
        _ok("get_chat_analytics")
    except Exception as e:
        _fail("get_chat_analytics", str(e))

    # ── DNC (read-only subset) ──
    try:
        await call("dnc_list_entries", {"limit": 1})
        _ok("dnc_list_entries")
    except Exception as e:
        _fail("dnc_list_entries", str(e))

    try:
        await call("dnc_get_settings")
        _ok("dnc_get_settings")
    except Exception as e:
        _fail("dnc_get_settings", str(e))

    try:
        await call("dnc_check", {"phone": "+12125551234"})
        _ok("dnc_check")
    except Exception as e:
        _fail("dnc_check", str(e))

    # ── Variables (local catalog, no backend call) ──
    try:
        await call("get_system_variables_catalog")
        _ok("get_system_variables_catalog")
    except Exception as e:
        _fail("get_system_variables_catalog", str(e))

    # ── Analytics ──
    try:
        await call("get_combined_analytics")
        _ok("get_combined_analytics")
    except Exception as e:
        _fail("get_combined_analytics", str(e))

    # ── Summary ──
    print(f"\n{'='*50}")
    total = len(PASS) + len(FAIL)
    print(f"  {len(PASS)}/{total} passed, {len(FAIL)} failed")
    if FAIL:
        print("\n  FAILURES:")
        for label, detail in FAIL:
            print(f"    {label}: {detail[:80]}")
        sys.exit(1)
    else:
        print("  ALL GREEN ✓")


if __name__ == "__main__":
    asyncio.run(run())

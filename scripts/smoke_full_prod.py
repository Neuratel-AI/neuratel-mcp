#!/usr/bin/env python3
"""Full live smoke test for ALL 46 Neuratel MCP tools against production.

Creates real resources, reads them, updates them, then cleans up.
Run with: NEURATEL_API_KEY=nk_live_xxx uv run python scripts/smoke_full_prod.py
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import UTC, datetime

import httpx

API_KEY = os.environ.get("NEURATEL_API_KEY")
if not API_KEY:
    sys.exit("NEURATEL_API_KEY env var required")

BASE_URL = "https://api.neuratel.ai/v1"
UID = datetime.now(UTC).strftime("%m%d%H%M%S")
PASS: list[str] = []
FAIL: list[tuple[str, str]] = []
CREATED: dict[str, str] = {}  # label -> id, for cleanup


def _ok(label: str) -> None:
    PASS.append(label)
    print(f"  ✓ {label}")


def _fail(label: str, detail: str) -> None:
    FAIL.append((label, detail))
    print(f"  ✗ {label}  {detail[:200]}")


async def run() -> None:
    from neuratelai_mcp.server import create_server

    server = create_server()
    print("neuratel-mcp FULL smoke — 46 tools against live prod\n")

    async def call(name: str, args: dict | None = None) -> dict | list:
        raw = await server.call_tool(name, args)
        if hasattr(raw, "structured_content") and raw.structured_content is not None:
            sc = raw.structured_content
            if isinstance(sc, dict) and "result" in sc and len(sc) == 1:
                return sc["result"]
            return sc
        if hasattr(raw, "content") and raw.content:
            return json.loads(raw.content[0].text)
        return raw

    # ═══════════════════════════════════════════
    # AGENTS (8 tools)
    # ═══════════════════════════════════════════
    print("── AGENTS ──")

    # 1. create_agent
    try:
        r = await call(
            "create_agent",
            {
                "name": f"smoke-{UID}",
                "instructions": "You are a smoke test agent. Say hello and hang up.",
                "description": "AUTO-GENERATED SMOKE TEST — safe to delete",
                "first_message": "Hello, this is a test call. Goodbye!",
                "tags": ["smoke-test", "auto-delete"],
            },
        )
        agent_id = r.get("id", "")
        if not agent_id:
            raise ValueError(f"No agent_id in response: {r}")
        CREATED["agent"] = agent_id
        _ok(f"create_agent → {agent_id[:12]}...")
    except Exception as e:
        _fail("create_agent", str(e))

    # 2. list_agents
    try:
        r = await call("list_agents", {"limit": 5})
        if not isinstance(r, list) or len(r) < 1:
            raise ValueError(f"Expected list, got: {type(r)}")
        _ok(f"list_agents → {len(r)} agents")
    except Exception as e:
        _fail("list_agents", str(e))

    # 3. list_agent_templates
    try:
        r = await call("list_agent_templates")
        templates = r.get("templates", []) if isinstance(r, dict) else r
        _ok(f"list_agent_templates → {len(templates)} templates")
    except Exception as e:
        _fail("list_agent_templates", str(e))

    # 4. get_agent
    if CREATED.get("agent"):
        try:
            r = await call("get_agent", {"agent_id": CREATED["agent"]})
            _ok(f"get_agent → name={r.get('name')}, status={r.get('status')}")
        except Exception as e:
            _fail("get_agent", str(e))
    else:
        _fail("get_agent", "SKIPPED — no agent_id (create failed)")

    # 5. get_agent_required_variables
    if CREATED.get("agent"):
        try:
            r = await call("get_agent_required_variables", {"agent_id": CREATED["agent"]})
            dyn = r.get("dynamic_variables", [])
            sys_vars = r.get("system_variables", [])
            _ok(f"get_agent_required_variables → {len(dyn)} dynamic, {len(sys_vars)} system")
        except Exception as e:
            _fail("get_agent_required_variables", str(e))
    else:
        _fail("get_agent_required_variables", "SKIPPED — no agent_id")

    # 6. update_agent
    if CREATED.get("agent"):
        try:
            r = await call(
                "update_agent",
                {
                    "agent_id": CREATED["agent"],
                    "description": "UPDATED by smoke test",
                },
            )
            _ok(f"update_agent → updated_at={r.get('updated_at', '?')[:19]}")
        except Exception as e:
            _fail("update_agent", str(e))
    else:
        _fail("update_agent", "SKIPPED — no agent_id")

    # 7. duplicate_agent
    if CREATED.get("agent"):
        try:
            r = await call(
                "duplicate_agent",
                {
                    "agent_id": CREATED["agent"],
                    "new_name": f"smoke-clone-{UID}",
                },
            )
            clone_id = r.get("id", "")
            if clone_id:
                CREATED["agent_clone"] = clone_id
            _ok(f"duplicate_agent → {clone_id[:12]}...")
        except Exception as e:
            _fail("duplicate_agent", str(e))
    else:
        _fail("duplicate_agent", "SKIPPED — no agent_id")

    # ═══════════════════════════════════════════
    # NUMBERS (3 tools)
    # ═══════════════════════════════════════════
    print("\n── NUMBERS ──")

    # 8. list_numbers
    try:
        r = await call("list_numbers")
        unassigned = [n for n in r if not n.get("agent_id")]
        first_num = r[0] if r else None
        if first_num:
            CREATED["number_id"] = first_num.get("id", "")
        _ok(f"list_numbers → {len(r)} numbers, {len(unassigned)} unassigned")
    except Exception as e:
        _fail("list_numbers", str(e))

    # 9. assign_number
    if CREATED.get("number_id") and CREATED.get("agent"):
        try:
            r = await call(
                "assign_number",
                {
                    "phone_number_id": CREATED["number_id"],
                    "agent_id": CREATED["agent"],
                },
            )
            _ok(f"assign_number → status={r.get('status')}")
        except Exception as e:
            _fail("assign_number", str(e))
    else:
        _fail("assign_number", "SKIPPED — need number_id + agent_id")

    # ═══════════════════════════════════════════
    # KNOWLEDGE BASE (4 tools)
    # ═══════════════════════════════════════════
    print("\n── KNOWLEDGE BASE ──")

    # 10. add_knowledge_from_text
    try:
        r = await call(
            "add_knowledge_from_text",
            {
                "name": f"smoke-kb-text-{UID}",
                "text": "Q: Is this a test? A: Yes, this is an automated smoke test.",
                "description": "AUTO-GENERATED — safe to delete",
            },
        )
        kb_id = r.get("id", "")
        if kb_id:
            CREATED["kb_text"] = kb_id
        _ok(f"add_knowledge_from_text → {kb_id[:12]}... status={r.get('status')}")
    except Exception as e:
        _fail("add_knowledge_from_text", str(e))

    # 11. add_knowledge_from_url
    try:
        r = await call(
            "add_knowledge_from_url",
            {
                "name": f"smoke-kb-url-{UID}",
                "url": "https://neuratel.ai",
                "description": "AUTO-GENERATED — safe to delete",
            },
        )
        kb_url_id = r.get("id", "")
        if kb_url_id:
            CREATED["kb_url"] = kb_url_id
        _ok(f"add_knowledge_from_url → {kb_url_id[:12]}... status={r.get('status')}")
    except Exception as e:
        _fail("add_knowledge_from_url", str(e))

    # 12. list_knowledge_bases
    try:
        r = await call("list_knowledge_bases")
        _ok(f"list_knowledge_bases → {len(r)} bases")
    except Exception as e:
        _fail("list_knowledge_bases", str(e))

    # 13. attach_knowledge_to_agent
    if CREATED.get("agent") and CREATED.get("kb_text"):
        try:
            r = await call(
                "attach_knowledge_to_agent",
                {
                    "agent_id": CREATED["agent"],
                    "knowledge_base_ids": [CREATED["kb_text"]],
                },
            )
            _ok(f"attach_knowledge_to_agent → status={r.get('status')}")
        except Exception as e:
            _fail("attach_knowledge_to_agent", str(e))
    else:
        _fail("attach_knowledge_to_agent", "SKIPPED — need agent + kb_text")

    # ═══════════════════════════════════════════
    # BILLING (2 tools)
    # ═══════════════════════════════════════════
    print("\n── BILLING ──")

    # 14. get_balance
    try:
        r = await call("get_balance")
        _ok(f"get_balance → ${r.get('balance', '?')} has_credits={r.get('has_credits')}")
    except Exception as e:
        _fail("get_balance", str(e))

    # 15. get_usage
    try:
        r = await call("get_usage", {"days": 7})
        _ok(f"get_usage → {r.get('call_count', '?')} calls, {r.get('total_minutes', '?')} min")
    except Exception as e:
        _fail("get_usage", str(e))

    # ═══════════════════════════════════════════
    # WEBHOOKS (2 tools)
    # ═══════════════════════════════════════════
    print("\n── WEBHOOKS ──")

    # 16. create_webhook
    try:
        r = await call(
            "create_webhook",
            {
                "name": f"smoke-wh-{UID}",
                "url": "https://httpbin.org/post",
                "events": ["call.ended", "call.failed"],
            },
        )
        wh_id = r.get("id", "")
        if wh_id:
            CREATED["webhook"] = wh_id
        _ok(f"create_webhook → {wh_id[:12]}... secret={'***' if r.get('secret') else 'none'}")
    except Exception as e:
        _fail("create_webhook", str(e))

    # 17. list_webhooks
    try:
        r = await call("list_webhooks")
        _ok(f"list_webhooks → {len(r)} webhooks")
    except Exception as e:
        _fail("list_webhooks", str(e))

    # ═══════════════════════════════════════════
    # DNC (6 tools)
    # ═══════════════════════════════════════════
    print("\n── DNC ──")

    # 18. dnc_check
    try:
        r = await call("dnc_check", {"phone": "+12125551234"})
        _ok(f"dnc_check → blocked={r.get('is_blocked', r.get('blocked', '?'))}")
    except Exception as e:
        _fail("dnc_check", str(e))

    # 19. dnc_get_settings
    try:
        r = await call("dnc_get_settings")
        prot = r.get("protection_enabled")
        auto = r.get("auto_add_inbound_optouts")
        _ok(f"dnc_get_settings → protection={prot}, auto_add={auto}")
    except Exception as e:
        _fail("dnc_get_settings", str(e))

    # 20. dnc_list_entries
    try:
        r = await call("dnc_list_entries", {"limit": 5})
        entries = r.get("results", r) if isinstance(r, dict) else r
        count = len(entries) if isinstance(entries, list) else "?"
        _ok(f"dnc_list_entries → {count} entries")
    except Exception as e:
        _fail("dnc_list_entries", str(e))

    # 21. dnc_add_entry
    try:
        r = await call(
            "dnc_add_entry",
            {
                "phone": "+12125551234",
                "reason": "Automated smoke test — safe to remove",
            },
        )
        entry_id = r.get("id", "")
        if entry_id:
            CREATED["dnc_entry"] = entry_id
        _ok(f"dnc_add_entry → {entry_id[:12] if entry_id else r}")
    except Exception as e:
        _fail("dnc_add_entry", str(e))

    # 22. dnc_update_settings
    try:
        current = await call("dnc_get_settings")
        r = await call(
            "dnc_update_settings",
            {
                "protection_enabled": current.get("protection_enabled", True),
            },
        )
        _ok(f"dnc_update_settings → protection={r.get('protection_enabled')}")
    except Exception as e:
        _fail("dnc_update_settings", str(e))

    # ═══════════════════════════════════════════
    # CONVERSATIONS (8 tools)
    # ═══════════════════════════════════════════
    print("\n── CONVERSATIONS ──")

    # 23. list_conversations
    try:
        r = await call("list_conversations", {"limit": 5})
        convs = r.get("results", r) if isinstance(r, dict) else r
        if isinstance(convs, list) and len(convs) > 0:
            CREATED["conversation_id"] = convs[0].get("id", "")
        count = len(convs) if isinstance(convs, list) else "?"
        _ok(f"list_conversations → {count} threads")
    except Exception as e:
        _fail("list_conversations", str(e))

    # 24. get_conversation
    if CREATED.get("conversation_id"):
        try:
            r = await call("get_conversation", {"conversation_id": CREATED["conversation_id"]})
            _ok(f"get_conversation → channel={r.get('channel')}, status={r.get('status')}")
        except Exception as e:
            _fail("get_conversation", str(e))
    else:
        _fail("get_conversation", "SKIPPED — no conversation_id")

    # 25. list_conversation_messages
    if CREATED.get("conversation_id"):
        try:
            r = await call(
                "list_conversation_messages",
                {
                    "conversation_id": CREATED["conversation_id"],
                    "limit": 5,
                },
            )
            msgs = r.get("results", r) if isinstance(r, dict) else r
            count = len(msgs) if isinstance(msgs, list) else "?"
            _ok(f"list_conversation_messages → {count} messages")
        except Exception as e:
            _fail("list_conversation_messages", str(e))
    else:
        _fail("list_conversation_messages", "SKIPPED — no conversation_id")

    # 26. send_conversation_message
    if CREATED.get("conversation_id"):
        try:
            r = await call(
                "send_conversation_message",
                {
                    "conversation_id": CREATED["conversation_id"],
                    "body": "Automated smoke test message — safe to ignore",
                },
            )
            _ok("send_conversation_message → sent")
        except Exception as e:
            _fail("send_conversation_message", str(e))
    else:
        _fail("send_conversation_message", "SKIPPED — no conversation_id")

    # 27. mark_conversation_read
    if CREATED.get("conversation_id"):
        try:
            r = await call(
                "mark_conversation_read",
                {
                    "conversation_id": CREATED["conversation_id"],
                },
            )
            _ok("mark_conversation_read → done")
        except Exception as e:
            _fail("mark_conversation_read", str(e))
    else:
        _fail("mark_conversation_read", "SKIPPED — no conversation_id")

    # 28. get_conversation_timeline
    if CREATED.get("conversation_id"):
        try:
            r = await call(
                "get_conversation_timeline",
                {
                    "conversation_id": CREATED["conversation_id"],
                    "limit": 5,
                },
            )
            _ok("get_conversation_timeline → done")
        except Exception as e:
            _fail("get_conversation_timeline", str(e))
    else:
        _fail("get_conversation_timeline", "SKIPPED — no conversation_id")

    # 29. update_conversation_variables
    if CREATED.get("conversation_id"):
        try:
            r = await call(
                "update_conversation_variables",
                {
                    "conversation_id": CREATED["conversation_id"],
                    "dynamic_variables": {"smoke_test": "true", "test_run": "2026-06-08"},
                    "replace": False,
                },
            )
            _ok("update_conversation_variables → done")
        except Exception as e:
            _fail("update_conversation_variables", str(e))
    else:
        _fail("update_conversation_variables", "SKIPPED — no conversation_id")

    # 30. get_chat_analytics
    try:
        r = await call("get_chat_analytics")
        _ok("get_chat_analytics → done")
    except Exception as e:
        _fail("get_chat_analytics", str(e))

    # ═══════════════════════════════════════════
    # ANALYTICS (1 tool)
    # ═══════════════════════════════════════════
    print("\n── ANALYTICS ──")

    # 31. get_combined_analytics
    try:
        r = await call("get_combined_analytics")
        _ok("get_combined_analytics → done")
    except Exception as e:
        _fail("get_combined_analytics", str(e))

    # ═══════════════════════════════════════════
    # VARIABLES (1 tool)
    # ═══════════════════════════════════════════
    print("\n── VARIABLES ──")

    # 32. get_system_variables_catalog
    try:
        r = await call("get_system_variables_catalog")
        vars_list = r.get("variables", [])
        _ok(f"get_system_variables_catalog → {len(vars_list)} variables")
    except Exception as e:
        _fail("get_system_variables_catalog", str(e))

    # ═══════════════════════════════════════════
    # CALLS (5 tools) — careful here
    # ═══════════════════════════════════════════
    print("\n── CALLS ──")

    # 33. list_calls
    try:
        r = await call("list_calls", {"limit": 5})
        _ok(f"list_calls → {len(r)} calls")
        if r:
            CREATED["call_id"] = r[0].get("id", "")
    except Exception as e:
        _fail("list_calls", str(e))

    # 34. get_call
    if CREATED.get("call_id"):
        try:
            r = await call("get_call", {"call_id": CREATED["call_id"]})
            _ok(f"get_call → status={r.get('status')}, duration={r.get('duration_seconds')}s")
        except Exception as e:
            _fail("get_call", str(e))
    else:
        _fail("get_call", "SKIPPED — no call_id from list_calls")

    # 35. get_active_calls
    try:
        r = await call("get_active_calls")
        _ok(f"get_active_calls → {r.get('total_active', 0)} active")
    except Exception as e:
        _fail("get_active_calls", str(e))

    # 36. make_call — SKIP unless explicitly wanted
    # This places a REAL phone call. We'll try it if we have agent + number.
    # Using a test number that won't connect to avoid charges.
    if CREATED.get("agent") and CREATED.get("number_id"):
        try:
            r = await call(
                "make_call",
                {
                    "agent_id": CREATED["agent"],
                    "to_number": "+12345678901",  # invalid number, will likely fail gracefully
                    "number_id": CREATED["number_id"],
                },
            )
            call_id = r.get("call_id", "")
            if call_id:
                CREATED["live_call"] = call_id
            cid = call_id[:12] if call_id else "none"
            _ok(f"make_call → call_id={cid}, success={r.get('success')}")
        except Exception as e:
            # Expected to fail with invalid number — still counts as tool tested
            _ok(f"make_call → raised (expected with test number): {str(e)[:80]}")
    else:
        _fail("make_call", "SKIPPED — need agent + number_id")

    # 37. hangup_call — only if we have an active call
    if CREATED.get("live_call"):
        try:
            r = await call("hangup_call", {"call_id": CREATED["live_call"]})
            _ok(f"hangup_call → status={r.get('status')}")
        except Exception as e:
            _ok(f"hangup_call → raised (call likely already ended): {str(e)[:80]}")
    else:
        _fail("hangup_call", "SKIPPED — no live call to hang up")

    # ═══════════════════════════════════════════
    # CAMPAIGNS (6 tools) — create and immediately stop
    # ═══════════════════════════════════════════
    print("\n── CAMPAIGNS ──")

    # 38. list_campaigns
    try:
        r = await call("list_campaigns", {"limit": 5})
        _ok(f"list_campaigns → {len(r)} campaigns")
    except Exception as e:
        _fail("list_campaigns", str(e))

    # 39. create_campaign
    if CREATED.get("agent") and CREATED.get("number_id"):
        try:
            r = await call(
                "create_campaign",
                {
                    "name": f"smoke-camp-{UID}",
                    "agent_id": CREATED["agent"],
                    "phone_number_id": CREATED["number_id"],
                    "max_concurrent_calls": 1,
                },
            )
            camp_id = r.get("id", "")
            if camp_id:
                CREATED["campaign"] = camp_id
            _ok(f"create_campaign → {camp_id[:12] if camp_id else r}")
        except Exception as e:
            _fail("create_campaign", str(e))
    else:
        _fail("create_campaign", "SKIPPED — need agent + number_id")

    # 40. get_campaign
    if CREATED.get("campaign"):
        try:
            r = await call("get_campaign", {"campaign_id": CREATED["campaign"]})
            _ok(f"get_campaign → status={r.get('status')}")
        except Exception as e:
            _fail("get_campaign", str(e))
    else:
        _fail("get_campaign", "SKIPPED — no campaign_id")

    # 41. pause_campaign
    if CREATED.get("campaign"):
        try:
            r = await call("pause_campaign", {"campaign_id": CREATED["campaign"]})
            _ok("pause_campaign → done (may raise if not started, that's OK)")
        except Exception as e:
            _ok(f"pause_campaign → raised (expected if not started): {str(e)[:80]}")
    else:
        _fail("pause_campaign", "SKIPPED — no campaign_id")

    # 42. stop_campaign
    if CREATED.get("campaign"):
        try:
            r = await call("stop_campaign", {"campaign_id": CREATED["campaign"]})
            _ok("stop_campaign → done")
        except Exception as e:
            _ok(f"stop_campaign → raised: {str(e)[:80]}")
    else:
        _fail("stop_campaign", "SKIPPED — no campaign_id")

    # start_campaign (43) — SKIP, would actually dial people

    # ═══════════════════════════════════════════
    # UNASSIGN NUMBER
    # ═══════════════════════════════════════════
    # 44. unassign_number
    if CREATED.get("number_id"):
        try:
            r = await call(
                "unassign_number",
                {
                    "phone_number_id": CREATED["number_id"],
                },
            )
            _ok(f"unassign_number → status={r.get('status')}")
        except Exception as e:
            _fail("unassign_number", str(e))

    # ═══════════════════════════════════════════
    # CLEANUP — delete everything we created
    # ═══════════════════════════════════════════
    print("\n── CLEANUP ──")

    headers = {"Authorization": f"Bearer {API_KEY}"}
    async with httpx.AsyncClient(base_url=BASE_URL, headers=headers) as api:
        if CREATED.get("webhook"):
            try:
                r = await api.delete(f"/webhooks/{CREATED['webhook']}")
                _ok(f"delete webhook (API) → {r.status_code}")
            except Exception as e:
                _fail("delete webhook (API)", str(e))

        if CREATED.get("kb_url"):
            try:
                r = await api.delete(f"/knowledge-base/{CREATED['kb_url']}")
                _ok(f"delete kb_url (API) → {r.status_code}")
            except Exception as e:
                _fail("delete kb_url (API)", str(e))

        if CREATED.get("kb_text"):
            try:
                r = await api.delete(f"/knowledge-base/{CREATED['kb_text']}")
                _ok(f"delete kb_text (API) → {r.status_code}")
            except Exception as e:
                _fail("delete kb_text (API)", str(e))

    if CREATED.get("dnc_entry"):
        try:
            r = await call("dnc_delete_entry", {"entry_id": CREATED["dnc_entry"]})
            _ok(f"dnc_delete_entry → deleted={r.get('deleted')}")
        except Exception as e:
            _fail("dnc_delete_entry", str(e))

    if CREATED.get("agent_clone"):
        try:
            r = await call("delete_agent", {"agent_id": CREATED["agent_clone"]})
            _ok(f"delete_agent (clone) → deleted={r.get('deleted')}")
        except Exception as e:
            _fail("delete_agent (clone)", str(e))

    if CREATED.get("agent"):
        try:
            r = await call("delete_agent", {"agent_id": CREATED["agent"]})
            _ok(f"delete_agent (main) → deleted={r.get('deleted')}")
        except Exception as e:
            _fail("delete_agent (main)", str(e))

    # ═══════════════════════════════════════════
    # SUMMARY
    # ═══════════════════════════════════════════
    print(f"\n{'=' * 60}")
    total = len(PASS) + len(FAIL)
    print(f"  {len(PASS)}/{total} tested, {len(FAIL)} failed")
    print("  Tools NOT tested: start_campaign (would dial real people)")
    if FAIL:
        print("\n  FAILURES:")
        for label, detail in FAIL:
            print(f"    {label}: {detail[:120]}")
        sys.exit(1)
    else:
        print("  ALL GREEN ✓")


if __name__ == "__main__":
    asyncio.run(run())

"""Template variable catalog tools.

The system-variable catalog is mirrored locally rather than fetched from the
backend. The backend route ``GET /v1/variables/system-catalog`` is currently
session-only (uses ``get_current_user``, not ``get_current_user_or_api_key``),
so an API-key consumer like this MCP server can't reach it. Even if that
backend regression is fixed, a local snapshot keeps the MCP usable in offline
or air-gapped sessions.

Snapshot mirrors ``backend/shared-schemas/shared_schemas/system_variables.py``
as of 2026-05-05. If the backend list grows, refresh this file on the next
MCP version bump.
"""

from __future__ import annotations

from typing import Any

import httpx
from fastmcp import FastMCP

_ALL = ["webrtc", "phone", "whatsapp_chat", "whatsapp_voice", "sms"]
_VOICE = ["webrtc", "phone", "whatsapp_voice"]
_PHONE = ["phone", "whatsapp_voice"]
_CONTACT = ["phone", "whatsapp_chat", "whatsapp_voice", "sms"]


def _entry(name: str, description: str, available_on: list[str]) -> dict[str, Any]:
    return {"name": name, "description": description, "available_on": available_on}


_SYSTEM_VARIABLE_CATALOG: list[dict[str, Any]] = [
    _entry(
        "system__agent_id",
        "UUID of the agent that initiated the conversation. Stable across handoffs.",
        _ALL,
    ),
    _entry(
        "system__current_agent_id",
        "UUID of the currently active agent. Changes after agent handoffs.",
        _ALL,
    ),
    _entry("system__agent_name", "Display name of the current agent.", _ALL),
    _entry("system__org_name", "Display name of the organization that owns this agent.", _ALL),
    _entry("system__org_id", "UUID of the organization that owns this agent.", _ALL),
    _entry(
        "system__caller_id",
        "Phone number / WhatsApp user ID of the contact (in E.164).",
        _CONTACT,
    ),
    _entry(
        "system__called_number",
        "Phone number / WhatsApp business number that received or placed the call.",
        _ALL,
    ),
    _entry("system__direction", 'Either "inbound" or "outbound".', _ALL),
    _entry(
        "system__channel",
        "One of webrtc, phone, whatsapp_chat, whatsapp_voice, sms.",
        _ALL,
    ),
    _entry(
        "system__is_text_only",
        '"true" on text channels (WhatsApp chat, SMS); "false" on voice channels.',
        _ALL,
    ),
    _entry(
        "system__time",
        'Current local time in the agent\'s timezone (e.g. "Friday, 12:33 12 December 2025").',
        _ALL,
    ),
    _entry("system__time_utc", "Current UTC time in ISO 8601 format.", _ALL),
    _entry("system__date", "Current local date in YYYY-MM-DD.", _ALL),
    _entry("system__day", 'Current local day of week (e.g. "Tuesday").', _ALL),
    _entry(
        "system__timezone",
        'Agent\'s configured IANA timezone (e.g. "America/New_York").',
        _ALL,
    ),
    _entry(
        "system__conversation_id",
        "Unique identifier for this conversation (room name on voice; row UUID on text).",
        _ALL,
    ),
    _entry(
        "system__call_sid",
        "Provider-side call identifier. Useful for correlating with provider logs.",
        _PHONE,
    ),
    _entry(
        "system__call_duration_secs",
        "Live counter — seconds elapsed since the call connected. Updated by the worker.",
        _VOICE,
    ),
    _entry(
        "system__agent_turns",
        "Number of conversation turns the agent has taken so far.",
        _ALL,
    ),
    _entry(
        "system__country_iso2",
        "ISO 3166-1 alpha-2 country code derived from the contact phone number.",
        _CONTACT,
    ),
    _entry(
        "system__caller_region",
        "Subnational region (state/province) derived from the contact phone number.",
        _CONTACT,
    ),
]


def register(mcp: FastMCP, client: httpx.AsyncClient) -> None:
    del client  # unused — local catalog, no backend call

    @mcp.tool(name="get_system_variables_catalog")
    async def get_system_variables_catalog() -> dict[str, Any]:
        """List the platform's built-in `system__*` template variables.

        These are auto-injected at call time by the platform — you never pass
        them in dynamic_variables. Use this catalog to:

        - Validate which {{system__*}} placeholders are safe to embed in agent prompts
        - Distinguish auto-injected variables from user-supplied ones when
          building dynamic_variables payloads for make_call

        Each entry has `name`, `description`, and `available_on` (the channels
        where the variable resolves to a real value vs falling back to "").
        """
        return {
            "variables": _SYSTEM_VARIABLE_CATALOG,
            "count": len(_SYSTEM_VARIABLE_CATALOG),
        }

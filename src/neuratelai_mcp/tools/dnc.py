"""DNC (Do Not Call) tools — directory check, entries CRUD, settings toggle."""

from __future__ import annotations

from typing import Any

import httpx
from fastmcp import FastMCP


def register(mcp: FastMCP, client: httpx.AsyncClient) -> None:

    @mcp.tool(name="dnc_check")
    async def dnc_check(phone: str) -> dict[str, Any]:
        """Check a phone number against the platform DNC directory.

        Hits the global directory (federal/state lists where applicable plus
        platform-curated entries) and any per-org entries. Returns whether
        the number is blocked, the source list, and timestamps.

        Always check before placing an outbound call to a new contact —
        dialing a DNC-listed number can carry per-call regulatory penalties.

        Args:
            phone: E.164 formatted number (e.g. "+12125551234")
        """
        r = await client.get("/dnc/check", params={"phone": phone})
        r.raise_for_status()
        return r.json()

    @mcp.tool(name="dnc_list_entries")
    async def dnc_list_entries(source: str | None = None, limit: int = 100) -> dict[str, Any]:
        """List DNC entries visible to your organization.

        Returns both your own org_upload entries and any platform-managed
        entries that block dialing org-wide. Filter by source to see only
        org-uploaded vs platform-curated.

        Args:
            source: Optional filter — "org_upload" | "inbound_optout" | "platform"
            limit: Max entries to return (default 100)
        """
        params: dict[str, Any] = {"limit": limit}
        if source:
            params["source"] = source
        r = await client.get("/dnc/entries", params=params)
        r.raise_for_status()
        return r.json()

    @mcp.tool(name="dnc_add_entry")
    async def dnc_add_entry(phone: str, reason: str | None = None) -> dict[str, Any]:
        """Add a number to your organization's DNC list.

        Once added, all subsequent outbound calls (manual or campaign) to
        this number from your org will be blocked at dial time.

        Args:
            phone: E.164 formatted number
            reason: Optional human-readable reason (e.g. "customer requested",
                    "STOP received via SMS")
        """
        body: dict[str, Any] = {"phone": phone}
        if reason:
            body["reason"] = reason
        r = await client.post("/dnc/entries", json=body)
        r.raise_for_status()
        return r.json()

    @mcp.tool(name="dnc_delete_entry")
    async def dnc_delete_entry(entry_id: str) -> dict[str, Any]:
        """Soft-expire an org_upload DNC entry.

        Only org_upload entries can be removed. Platform-managed entries are
        immutable to org admins. The entry is soft-expired (audit-preserved),
        not hard-deleted.

        Args:
            entry_id: ID returned by dnc_list_entries or dnc_add_entry
        """
        r = await client.delete(f"/dnc/entries/{entry_id}")
        r.raise_for_status()
        return {"deleted": True, "entry_id": entry_id}

    @mcp.tool(name="dnc_get_settings")
    async def dnc_get_settings() -> dict[str, Any]:
        """Get the organisation's DNC protection settings.

        Returns whether DNC checks block outbound calls (protection_enabled)
        and whether STOP-style replies on inbound chat auto-add the sender
        (auto_add_inbound_optouts).
        """
        r = await client.get("/dnc/settings")
        r.raise_for_status()
        return r.json()

    @mcp.tool(name="dnc_update_settings")
    async def dnc_update_settings(
        protection_enabled: bool | None = None,
        auto_add_inbound_optouts: bool | None = None,
    ) -> dict[str, Any]:
        """Toggle DNC protection and inbound STOP auto-detection.

        Args:
            protection_enabled: Master switch — if False, DNC checks are
                                logged but not enforced at dial time.
            auto_add_inbound_optouts: If True, the platform watches inbound
                                     SMS/WhatsApp for STOP-style language and
                                     adds the sender to your org DNC list.
        """
        body: dict[str, Any] = {}
        if protection_enabled is not None:
            body["protection_enabled"] = protection_enabled
        if auto_add_inbound_optouts is not None:
            body["auto_add_inbound_optouts"] = auto_add_inbound_optouts
        r = await client.patch("/dnc/settings", json=body)
        r.raise_for_status()
        return r.json()

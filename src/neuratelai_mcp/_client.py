"""Shared httpx.AsyncClient factory for MCP tool handlers."""

from __future__ import annotations

import httpx

from . import __version__ as VERSION

_BASE_URL = "https://api.neuratel.ai/v1"


def make_client(api_key: str, base_url: str = _BASE_URL) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=base_url.rstrip("/"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "User-Agent": f"neuratelai-mcp/{VERSION}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        timeout=30.0,
    )

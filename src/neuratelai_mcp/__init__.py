"""Neuratel MCP Server."""

try:
    from importlib.metadata import version as _version

    __version__ = _version("neuratelai-mcp")
except Exception:
    __version__ = "unknown"

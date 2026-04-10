"""Entry point for `python -m neuratelai_mcp` and `uvx neuratelai-mcp`."""

from __future__ import annotations

import argparse
import sys


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="neuratelai-mcp",
        description="Neuratel MCP Server — connect AI assistants to Neuratel Studio",
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "http", "sse"],
        default="stdio",
        help="Transport to use (default: stdio for Claude Desktop / Cursor)",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind (http/sse transport only, default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind (http/sse transport only, default: 8000)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"neuratelai-mcp {__import__('neuratelai_mcp').__version__}",
    )

    args = parser.parse_args()

    try:
        from .server import get_server

        mcp = get_server()
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.transport == "stdio":
        mcp.run(transport="stdio")
    elif args.transport == "http":
        mcp.run(transport="streamable-http", host=args.host, port=args.port)
    elif args.transport == "sse":
        mcp.run(transport="sse", host=args.host, port=args.port)


if __name__ == "__main__":
    main()

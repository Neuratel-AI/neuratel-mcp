# Neuratel AI — MCP Server

[![PyPI](https://img.shields.io/pypi/v/neuratelai-mcp)](https://pypi.org/project/neuratelai-mcp/)
[![Python](https://img.shields.io/pypi/pyversions/neuratelai-mcp)](https://pypi.org/project/neuratelai-mcp/)
[![Docs](https://img.shields.io/badge/docs-docs.neuratel.ai-black)](https://docs.neuratel.ai/mcp/overview)

Official MCP Server for [Neuratel Studio](https://neuratel.ai) — control your voice AI platform through natural language from Claude, Cursor, Windsurf, and any MCP-compatible assistant.

28 hand-crafted tools. Every destructive operation carries an explicit cost warning.

## Quick Start

```bash
NEURATEL_API_KEY=nk_live_... uvx neuratelai-mcp@latest
```

Or install permanently:

```bash
pip install neuratelai-mcp
```

## Claude Desktop Setup

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "neuratel": {
      "command": "uvx",
      "args": ["neuratelai-mcp@latest"],
      "env": {
        "NEURATEL_API_KEY": "nk_live_your_key_here"
      }
    }
  }
}
```

Restart Claude Desktop. You'll see **neuratel** in the tools panel with 28 tools available.

## Claude Code

```bash
claude mcp add neuratel -e NEURATEL_API_KEY=nk_live_... -- uvx neuratelai-mcp@latest
```

## Cursor / Windsurf

Add to `~/.cursor/mcp.json` (Cursor) or Codeium MCP config (Windsurf):

```json
{
  "mcpServers": {
    "neuratel": {
      "command": "uvx",
      "args": ["neuratelai-mcp@latest"],
      "env": {
        "NEURATEL_API_KEY": "nk_live_your_key_here"
      }
    }
  }
}
```

## HTTP / SSE Transport

For remote deployment or web-based clients:

```bash
NEURATEL_API_KEY=nk_live_... neuratelai-mcp --transport http --port 8000
```

Connect to `http://your-host:8000/mcp`.

## Environment Variables

| Variable | Required | Default |
|----------|----------|---------|
| `NEURATEL_API_KEY` | Yes | — |
| `NEURATEL_BASE_URL` | No | `https://api.neuratel.ai/v1` |

## Tools

| Domain | Count | What you can do |
|--------|-------|-----------------|
| Agents | 6 | Create, inspect, update, duplicate, delete agents |
| Calls | 5 | Place calls, read transcripts, monitor live, hang up |
| Campaigns | 6 | Full campaign lifecycle — create through stop |
| Numbers | 3 | List numbers, assign and unassign agents |
| Knowledge Base | 4 | Add content from text or URL, attach to agent |
| Billing | 2 | Check balance, view usage |
| Webhooks | 2 | Create and list event subscriptions |

## Requirements

Python 3.11+ · `uv` recommended · [Full docs](https://docs.neuratel.ai/mcp/overview)

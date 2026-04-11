# Changelog

## 0.1.1b1 (2026-04-11)

### Agent tools overhaul
- `create_agent` now exposes 18 parameters: temperature, max_tokens, voice speed/stability, language, endpointing, interruption, call duration, tags, description
- `update_agent` now exposes 24 parameters plus a `config` escape hatch for advanced nested config (transfer rules, analytics, tools, background audio)
- New `duplicate_agent` tool for cloning agents with all configuration

### Bug fixes
- Fixed `add_knowledge_from_text` — was sending `text` field, backend expects `content` (422 error)
- Fixed `create_webhook` — was sending invalid event names (`session_report`), now uses correct dotted format (`call.ended`) and defaults to all events
- Fixed `attach_knowledge_to_agent` — backend was calling non-existent `get_entity()`, now uses `get_by_id()` (500 error)

## 0.1.1 (2026-04-11)

Initial public release.

- 27 hand-crafted MCP tools across 7 domains: agents, calls, campaigns, numbers, knowledge base, billing, webhooks
- stdio transport for Claude Desktop, Cursor, Windsurf, Claude Code
- Streamable HTTP and SSE transports for remote/web clients (`--transport http`)
- Cost warnings on every destructive or billable operation
- Full call transcripts via `get_call` — unique among voice AI MCP servers
- Live call supervision via `get_active_calls`
- `NEURATEL_BASE_URL` override for custom API endpoints

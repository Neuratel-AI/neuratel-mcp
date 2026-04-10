# Changelog

## 0.1.1 (2026-04-11)

Initial public release.

- 27 hand-crafted MCP tools across 7 domains: agents, calls, campaigns, numbers, knowledge base, billing, webhooks
- stdio transport for Claude Desktop, Cursor, Windsurf, Claude Code
- Streamable HTTP and SSE transports for remote/web clients (`--transport http`)
- Cost warnings on every destructive or billable operation
- Full call transcripts via `get_call` — unique among voice AI MCP servers
- Live call supervision via `get_active_calls`
- `NEURATEL_BASE_URL` override for custom API endpoints

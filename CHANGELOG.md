# Changelog

## 0.1.4 (2026-04-15)

### Agent tools — full platform sync

- `create_agent`: only `name` + `instructions` required — all provider defaults applied server-side. Added `voice_model` param. Added `config` dict for full 80+ field coverage (turn_detection, timeout, background_audio, transfer, tools, analytics, etc.) — now a complete replica of the agent studio form
- `update_agent`: same convenience params as create + `config` dict. Voice/transcriber sections now correctly require `provider` field (discriminated union)
- `duplicate_agent`: fixed `new_name` sent as JSON body — backend expects query param
- `get_call`: now passes `?include=full` — transcript, recording URL, and call summary are populated
- `create_webhook`: added 4 missing event types: `agent.turn.started`, `agent.turn.ended`, `agent.tool.called`, `call.summary.ready`

### Breaking: default providers changed

Old hardcoded defaults are gone. Backend now sets actual platform defaults:
- Brain: **Groq** `llama-4-scout-17b-16e-instruct` (was OpenAI `gpt-4.1`)
- Voice: **Cartesia** `sonic-3` (was ElevenLabs Aria)
- Transcriber: **OpenAI** `gpt-4o-mini-transcribe` (was Deepgram `nova-3`)

Existing agents are unaffected. New agents created without explicit provider params get the new defaults.

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

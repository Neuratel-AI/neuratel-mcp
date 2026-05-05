# Changelog

## 0.2.0 (2026-05-05)

### Tool count: 28 → 46 — three new domains plus catalog/analytics endpoints

**New tool modules** (18 tools):
- `dnc.py` (6 tools): `dnc_check`, `dnc_list_entries`, `dnc_add_entry`, `dnc_delete_entry`, `dnc_get_settings`, `dnc_update_settings`. Wraps the platform DNC directory shipped on the backend 2026-04-27. Settings uses canonical backend names (`protection_enabled`, `auto_add_inbound_optouts`).
- `conversations.py` (8 tools): `list_conversations`, `get_conversation`, `list_conversation_messages`, `send_conversation_message`, `mark_conversation_read`, `get_conversation_timeline`, `update_conversation_variables`, `get_chat_analytics`. Wraps `/v1/conversations/*` (the unified SMS / WhatsApp / voice inbox shipped during the comms taxonomy unification 2026-04-26). `send_conversation_message` uses `body` field (matches `ConversationSendRequest`).
- `variables.py` (1 tool): `get_system_variables_catalog` — calls `/v1/variables/system-catalog` so AI assistants can distinguish auto-injected `system__*` variables from user-supplied `dynamic_variables`.
- `analytics.py` (1 tool): `get_combined_analytics` — wraps `/v1/analytics/dashboard` (combined voice + chat KPIs).

**`agents.py` additions** (2 tools):
- `list_agent_templates`: GET `/v1/agents/templates` — read-only catalog of starter templates.
- `get_agent_required_variables`: GET `/v1/agents/{id}/required-variables` — saves a round-trip when validating `dynamic_variables` payloads before `make_call`.

### Critical fixes (also shipped to docstrings AI assistants read)

- `agents.py:88-97`: transcriber section listed `openai` as default. Backend default is **Deepgram Nova-3 en-US** per `shared_schemas/defaults.py:43-47`. Also added the missing `soniox` (Soniox v4, semantic EOU built in) and `phantom` provider entries.
- `calls.py` `get_call` return now surfaces flat session_report columns: `analysis_status` (pending|completed|failed), `user_sentiment`, `user_sentiment_score`, `call_successful`, `call_successful_rationale`. These were dropped by the previous return shape.
- `calls.py` `make_call` pre-flight: `_extract_template_vars` now skips `system__*` placeholders. Previously false-positive warned about platform-injected vars (`system__org_id`, `system__channel`, etc.) when scanning agent prompts.
- `server.py:4,39`: tool count docstrings 27 → 28 (now 46), and resource list refreshed.

### Infra

- `pyrightconfig.json`: point Pyright at `.venv` so `fastmcp` imports resolve in IDEs.
- `tests/test_server.py`: EXPECTED_TOOLS extended by 18 names; added 4 spot checks for new-tool parameter schemas (`dnc_check` exposes `phone`, `dnc_update_settings` uses canonical names, `send_conversation_message` requires `body`, `_extract_template_vars` excludes `system__*`).

## 0.1.7 (2026-04-26)

- `fix(make_call)`: retarget `/calls/*` → `/voice-sessions/*` after the backend deleted the legacy comms surface.

## 0.1.6 (~2026-04-22)

- `fix(make_call)`: pre-flight `dynamic_variables` check — fail early with a clear "missing variable: customer_name" message instead of letting the backend return a raw 400.
- `fix(create_agent)`: corrected default provider docstring and voice ID guidance. (Earlier docstrings claimed OpenAI was the default transcriber — this was incorrect; backend default has always been Deepgram. The actual fix to the openai-as-default lie shipped in 0.2.0.)

## 0.1.5 (~2026-04-20)

- `fix(agents)`: `create_agent` and `update_agent` now require `provider` field inside `brain` / `voice` / `transcriber` sections. Backend uses Pydantic discriminated unions and rejects sections without a provider.

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

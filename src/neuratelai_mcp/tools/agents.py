"""Agent management tools — create, list, get, update, delete, duplicate."""

from __future__ import annotations

from typing import Any

import httpx
from fastmcp import FastMCP


def register(mcp: FastMCP, client: httpx.AsyncClient) -> None:

    @mcp.tool(name="create_agent")
    async def create_agent(
        name: str,
        instructions: str,
        # Brain (LLM) — defaults applied server-side if not provided
        brain_provider: str | None = None,
        brain_model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        # Voice (TTS)
        voice_provider: str | None = None,
        voice_id: str | None = None,
        voice_model: str | None = None,
        voice_speed: float | None = None,
        # Transcriber (STT)
        transcriber_provider: str | None = None,
        transcriber_model: str | None = None,
        language: str | None = None,
        # Conversation behavior
        first_message: str | None = None,
        first_message_delay_ms: int | None = None,
        interruption_enabled: bool | None = None,
        max_call_duration: int | None = None,
        # Metadata
        description: str = "",
        tags: list[str] | None = None,
        # Advanced — full config sections mirroring get_agent response structure.
        # Use this for anything not covered by the named params above:
        # turn_detection, timeout, background_audio, transfer, tools, analytics, etc.
        # Named params above override the corresponding sections in config.
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a new voice AI agent.

        Only `name` and `instructions` are required. All provider defaults are
        applied server-side — if you don't specify brain/voice/transcriber, the
        platform picks its current production defaults (Phantom brain, Cartesia
        sonic-3 voice with Fatima — Arabic, Soniox stt-rt-v4 transcriber with
        EN+AR language hints — pairs natively with Fatima for code-switching).
        Behavior defaults: turn_detection.mode=stt (Soniox owns endpointing),
        preemptive_generation=true, recording on with 30-day retention,
        post-call analysis on (PassFail rubric).

        ## Brain (LLM) providers

        **phantom** — default, Neuratel AI (~178ms TTFT)
        - model: "phantom"

        **groq** — Groq fast inference (~443ms TTFT)
        - model: "meta-llama/llama-4-scout-17b-16e-instruct" (recommended)
        - model: "llama-3.1-8b-instant" (fastest)
        - model: "openai/gpt-oss-20b" (with reasoning)

        **openai** — OpenAI GPT (~583-1213ms TTFT)
        - model: "gpt-5.4", "gpt-5.4-mini", "gpt-5.4-nano"
        - model: "gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano"

        **xai** — xAI Grok (~93-180ms TTFT)
        - model: "grok-4-1-fast-non-reasoning" (recommended)
        - model: "grok-4.20-0309-non-reasoning"

        ## Voice (TTS) providers

        **cartesia** — default, best quality (~37ms latency)
        - voice_model: "sonic-3"
        - voice_id: "731ace69-ee17-41bc-8c6f-665c9f1db95c" (default, Fatima — Arabic;
          pairs with default Soniox EN+AR hints)
        - voice_speed: float or preset ("fastest","fast","normal","slow","slowest")

        **elevenlabs** — most expressive (~71ms latency)
        - voice_model: "eleven_flash_v2_5"
        - voice_id: any ElevenLabs voice ID
        - voice_speed: float (0.25–4.0), stability via config dict

        **phantom** — Neuratel native voices (~100ms latency)
        - voice_model: "phantom-english-speech-preview" or "phantom-arabic-speech-preview"
        - voice_id not used; set voice name in config: {"voice": {"voice": "aria"}}
        - English voices: aria, bella, claire, alex, david, marcus
        - Arabic voices: omar, tariq, layla, nour

        ## Transcriber (STT) providers

        **soniox** — default, Soniox v4 with semantic end-of-utterance built in
        - transcriber_model: "stt-rt-v4" (single unified model, 60+ languages)
        - Default language_hints: ["en", "ar"], language_hints_strict: true
        - When transcriber.provider="soniox", the worker auto-routes
          turn_detection.mode to "stt" (Soniox owns endpointing)
        - Requires per-org soniox_api_key (BYOK)

        **deepgram** — best accuracy for telephony-only English (~83ms latency)
        - transcriber_model: "nova-3" (recommended), "nova-3-medical"
        - language: BCP-47 e.g. "en-US", "ar", "multi" (auto-detect)

        **openai** — GPT-4o powered (~138ms latency)
        - transcriber_model: "gpt-4o-mini-transcribe"
        - language: ISO code e.g. "en", "ar", "es"

        **phantom** — Neuratel native STT
        - transcriber_model: "phantom-stt-v1"
        - language: "auto" (auto-detect)

        ## Advanced config

        Use the `config` dict for anything not covered by named params. It accepts
        the full agent config structure — same shape as `get_agent` returns.

        ```python
        config={
            "turn_detection": {
                "mode": "semantic_vad",   # or "vad"
                "min_delay": 0.5,
                "max_delay": 6.0,
                "endpointing_mode": "dynamic"  # or "fixed"
            },
            "timeout": {
                "enabled": True,
                "trigger_seconds": 15.0,
                "warning_messages": ["Are you still there?"],
                "final_message": "Goodbye!"
            },
            "background_audio": {
                "ambient": {"enabled": True, "source": "office_ambience", "volume": 0.3},
                "thinking": {"enabled": True, "source": "keyboard_typing", "volume": 0.5}
            },
            "tools": {
                "rag": {"enabled": True, "knowledge_base_ids": ["kb-id"], "top_k": 5},
                "voicemail": {"enabled": True, "action": "hangup"},
                "hangup": {"enabled": True, "keywords": ["goodbye", "bye"]}
            },
            "transfer": {
                "enabled": True,
                "mode": "blind",
                "destinations": [{"name": "Support", "number": "+15551234567",
                                  "description": "Human agent", "keywords": ["human", "agent"]}]
            },
            "analytics": {
                "recording": {"enabled": True},
                "summary": {"enabled": True},
                "success_evaluation": {
                    "enabled": True,
                    "criteria": "Did the agent resolve the issue?",
                },
            },
            "interruption": {
                "enabled": True,
                "min_duration": 0.5,
                "min_words": 0,
                "false_interruption_timeout": 2.0,
                "resume_false_interruption": True
            }
        }
        ```

        Returns: agent id, name, status, brain provider/model, voice provider.
        """
        # Start with raw config sections if provided
        body: dict[str, Any] = {}
        if config:
            body.update(config)

        # Top-level metadata
        body["name"] = name
        if description:
            body["description"] = description
        if tags:
            body["tags"] = tags

        # Brain — always include (has instructions); named params override config.
        # provider is required by backend discriminated union — default to groq
        # (the platform default) if not explicitly set.
        brain: dict[str, Any] = {**body.get("brain", {})}
        brain["instructions"] = instructions
        brain.setdefault("provider", brain_provider or "groq")
        if brain_provider is not None:
            brain["provider"] = brain_provider
        if brain_model is not None:
            brain["model"] = brain_model
        if temperature is not None:
            brain["temperature"] = temperature
        if max_tokens is not None:
            brain["max_completion_tokens"] = max_tokens
        body["brain"] = brain

        # Voice — only include if any voice param provided or config had voice section
        voice_params_set = any(
            p is not None for p in [voice_provider, voice_id, voice_model, voice_speed]
        )
        if voice_params_set or "voice" in body:
            voice: dict[str, Any] = {**body.get("voice", {})}
            if voice_provider is not None:
                voice["provider"] = voice_provider
            if voice_id is not None:
                voice["voice_id"] = voice_id
            if voice_model is not None:
                voice["model"] = voice_model
            if voice_speed is not None:
                voice["speed"] = voice_speed
            body["voice"] = voice

        # Transcriber — only include if any transcriber param provided or config had it
        transcriber_params_set = any(
            p is not None for p in [transcriber_provider, transcriber_model, language]
        )
        if transcriber_params_set or "transcriber" in body:
            transcriber: dict[str, Any] = {**body.get("transcriber", {})}
            if transcriber_provider is not None:
                transcriber["provider"] = transcriber_provider
            if transcriber_model is not None:
                transcriber["model"] = transcriber_model
            if language is not None:
                transcriber["language"] = language
            body["transcriber"] = transcriber

        # First message
        if first_message is not None or first_message_delay_ms is not None:
            fm: dict[str, Any] = {**body.get("first_message", {})}
            if first_message is not None:
                fm["enabled"] = bool(first_message)
                fm["text"] = first_message
            if first_message_delay_ms is not None:
                fm["delay_ms"] = first_message_delay_ms
            body["first_message"] = fm

        # Interruption
        if interruption_enabled is not None:
            interruption: dict[str, Any] = {**body.get("interruption", {})}
            interruption["enabled"] = interruption_enabled
            body["interruption"] = interruption

        # Call duration
        if max_call_duration is not None:
            call_duration: dict[str, Any] = {**body.get("call_duration", {})}
            call_duration["enabled"] = True
            call_duration["max_seconds"] = max_call_duration
            body["call_duration"] = call_duration

        r = await client.post("/agents", json=body)
        r.raise_for_status()
        d = r.json()
        brain_resp = d.get("brain") or {}
        voice_resp = d.get("voice") or {}
        return {
            "id": d.get("id"),
            "name": d.get("name"),
            "status": d.get("status"),
            "brain": f"{brain_resp.get('provider')}/{brain_resp.get('model')}",
            "voice": (
                f"{voice_resp.get('provider')}/"
                f"{voice_resp.get('voice_id') or voice_resp.get('voice', '')}"
            ),
            "language": (d.get("transcriber") or {}).get("language"),
            "created_at": d.get("created_at"),
        }

    @mcp.tool(name="list_agents")
    async def list_agents(limit: int = 20) -> list[dict[str, Any]]:
        """List all voice AI agents in your organization.

        Use this to find agent IDs for making calls, starting campaigns, or
        assigning to phone numbers. Also useful to audit what agents exist
        and whether they're active.

        Returns a summary for each agent — use get_agent for full configuration.
        """
        r = await client.get("/agents", params={"limit": min(limit, 100), "skip": 0})
        r.raise_for_status()
        results = r.json().get("results", [])
        return [
            {
                "id": a.get("id"),
                "name": a.get("name"),
                "status": a.get("status"),
                "is_active": a.get("is_active"),
                "brain": (
                    f"{(a.get('brain') or {}).get('provider')}"
                    f"/{(a.get('brain') or {}).get('model')}"
                ),
                "voice_provider": (a.get("voice") or {}).get("provider"),
                "call_count": a.get("call_count", 0),
                "created_at": a.get("created_at"),
            }
            for a in results
        ]

    @mcp.tool(name="get_agent")
    async def get_agent(agent_id: str) -> dict[str, Any]:
        """Get the complete configuration of a specific agent.

        Returns every field and setting — brain, voice, transcriber, transfer
        rules, analytics, tools, interruption, timeout, background audio, and
        more. This is the full picture of how the agent behaves.

        Use this before calling update_agent to understand current state, or
        to inspect how an agent is configured for debugging call quality issues.

        The response structure matches what update_agent's `config` parameter
        accepts — you can read a section here, modify it, and pass it back.
        """
        r = await client.get(f"/agents/{agent_id}")
        r.raise_for_status()
        return r.json()

    @mcp.tool(name="update_agent")
    async def update_agent(
        agent_id: str,
        # Top-level
        name: str | None = None,
        instructions: str | None = None,
        is_active: bool | None = None,
        description: str | None = None,
        tags: list[str] | None = None,
        # Brain (LLM)
        brain_provider: str | None = None,
        brain_model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        # Voice (TTS) — MUST include voice_provider when setting voice fields
        voice_provider: str | None = None,
        voice_id: str | None = None,
        voice_model: str | None = None,
        voice_speed: float | None = None,
        # Transcriber (STT) — MUST include transcriber_provider when setting transcriber fields
        transcriber_provider: str | None = None,
        transcriber_model: str | None = None,
        language: str | None = None,
        # Conversation behavior
        first_message: str | None = None,
        first_message_delay_ms: int | None = None,
        interruption_enabled: bool | None = None,
        max_call_duration: int | None = None,
        # Advanced — full config sections (same structure as get_agent response).
        # Use for: turn_detection, timeout, background_audio, transfer, tools,
        # analytics, tts_text_transforms, preemptive_generation, etc.
        # Named params above override corresponding sections in config.
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Update any part of an agent's configuration.

        Only the fields you provide are changed — everything else stays as-is.
        The backend deep-merges your changes, so you can update a single field
        inside a nested config without affecting sibling fields.

        ## Two ways to update

        **Named parameters** — for common changes:
        ```
        update_agent(agent_id="...", temperature=0.5, voice_speed=1.1)
        ```

        **config parameter** — for any section not covered by named params.
        Use get_agent first to see the current structure, then pass sections.
        Named params always override the corresponding section in config.

        ## IMPORTANT: provider field required for voice/transcriber

        The backend uses discriminated unions — voice and transcriber sections
        MUST include the `provider` field or validation fails. Always pair
        voice_id/voice_model/voice_speed with voice_provider. Same for transcriber.

        ## Available config sections

        ```python
        config={
            "turn_detection": {
                "mode": "semantic_vad",   # or "vad"
                "min_delay": 0.5,
                "max_delay": 6.0,
                "endpointing_mode": "dynamic"
            },
            "timeout": {
                "enabled": True,
                "trigger_seconds": 15.0,
                "warning_messages": ["Are you still there?"],
                "final_message": "Goodbye!"
            },
            "background_audio": {
                "ambient": {"enabled": True, "source": "office_ambience", "volume": 0.3},
                "thinking": {"enabled": True, "source": "keyboard_typing", "volume": 0.5}
            },
            "tools": {
                "rag": {"enabled": True, "knowledge_base_ids": ["kb-id"], "top_k": 5},
                "voicemail": {"enabled": True, "action": "hangup"},
                "hangup": {"enabled": True, "keywords": ["goodbye", "bye"]}
            },
            "transfer": {
                "enabled": True,
                "mode": "blind",
                "destinations": [{"name": "Support", "number": "+15551234567",
                                  "description": "Human agent", "keywords": ["human"]}]
            },
            "analytics": {
                "recording": {"enabled": True},
                "summary": {"enabled": True},
                "success_evaluation": {
                    "enabled": True,
                    "criteria": "Did the agent resolve the issue?",
                },
            },
            "tts_text_transforms": ["filter_markdown", "filter_emoji"],
            "preemptive_generation": False,
            "min_consecutive_speech_delay": 0.0
        }
        ```
        """
        body: dict[str, Any] = {}

        # Apply raw config sections first — named params override
        if config:
            body.update(config)

        # Top-level fields
        if name is not None:
            body["name"] = name
        if is_active is not None:
            body["is_active"] = is_active
        if description is not None:
            body["description"] = description
        if tags is not None:
            body["tags"] = tags

        # Brain — provider is required by backend discriminated union.
        # If user sets brain fields without provider, default to "groq" only
        # as a fallback; recommend always passing brain_provider explicitly.
        brain_fields: dict[str, Any] = {}
        if instructions is not None:
            brain_fields["instructions"] = instructions
        if brain_model is not None:
            brain_fields["model"] = brain_model
        if brain_provider is not None:
            brain_fields["provider"] = brain_provider
        if temperature is not None:
            brain_fields["temperature"] = temperature
        if max_tokens is not None:
            brain_fields["max_completion_tokens"] = max_tokens
        if brain_fields:
            if "provider" not in brain_fields:
                brain_fields["provider"] = "groq"
            body["brain"] = {**body.get("brain", {}), **brain_fields}

        # Voice — provider required when setting voice fields
        voice_fields: dict[str, Any] = {}
        if voice_provider is not None:
            voice_fields["provider"] = voice_provider
        if voice_id is not None:
            voice_fields["voice_id"] = voice_id
        if voice_model is not None:
            voice_fields["model"] = voice_model
        if voice_speed is not None:
            voice_fields["speed"] = voice_speed
        if voice_fields:
            body["voice"] = {**body.get("voice", {}), **voice_fields}

        # Transcriber — provider required when setting transcriber fields
        transcriber_fields: dict[str, Any] = {}
        if transcriber_provider is not None:
            transcriber_fields["provider"] = transcriber_provider
        if transcriber_model is not None:
            transcriber_fields["model"] = transcriber_model
        if language is not None:
            transcriber_fields["language"] = language
        if transcriber_fields:
            body["transcriber"] = {**body.get("transcriber", {}), **transcriber_fields}

        # First message
        if first_message is not None or first_message_delay_ms is not None:
            fm: dict[str, Any] = {**body.get("first_message", {})}
            if first_message is not None:
                fm["enabled"] = bool(first_message)
                fm["text"] = first_message
            if first_message_delay_ms is not None:
                fm["delay_ms"] = first_message_delay_ms
            body["first_message"] = fm

        # Interruption
        if interruption_enabled is not None:
            body["interruption"] = {
                **body.get("interruption", {}),
                "enabled": interruption_enabled,
            }

        # Call duration
        if max_call_duration is not None:
            body["call_duration"] = {
                **body.get("call_duration", {}),
                "enabled": True,
                "max_seconds": max_call_duration,
            }

        r = await client.patch(f"/agents/{agent_id}", json=body)
        r.raise_for_status()
        d = r.json()
        brain_resp = d.get("brain") or {}
        voice_resp = d.get("voice") or {}
        return {
            "id": d.get("id"),
            "name": d.get("name"),
            "status": d.get("status"),
            "is_active": d.get("is_active"),
            "brain": f"{brain_resp.get('provider')}/{brain_resp.get('model')}",
            "voice": (
                f"{voice_resp.get('provider')}/"
                f"{voice_resp.get('voice_id') or voice_resp.get('voice', '')}"
            ),
            "updated_at": d.get("updated_at"),
        }

    @mcp.tool(name="delete_agent")
    async def delete_agent(agent_id: str) -> dict[str, Any]:
        """Permanently delete a voice AI agent.

        This is irreversible. Any phone numbers assigned to this agent will
        stop answering calls immediately. Active calls in progress will not
        be affected, but no new calls can be made or received.

        Before deleting, consider using update_agent with is_active=False
        to disable the agent without destroying its configuration.
        """
        r = await client.delete(f"/agents/{agent_id}")
        r.raise_for_status()
        return {"deleted": True, "agent_id": agent_id}

    @mcp.tool(name="list_agent_templates")
    async def list_agent_templates() -> dict[str, Any]:
        """List the platform's pre-built agent templates.

        Returns the read-only catalog of template configurations the platform
        ships — useful as starting points before customising via create_agent.
        Each template includes a name, description, and full agent config
        block you can deep-merge with your own overrides.
        """
        r = await client.get("/agents/templates")
        r.raise_for_status()
        # Backend returns a bare list; FastMCP requires a dict for structured
        # content. Wrap so the tool result is always {"templates": [...]}.
        return {"templates": r.json()}

    @mcp.tool(name="get_agent_required_variables")
    async def get_agent_required_variables(agent_id: str) -> dict[str, Any]:
        """List the {{variable}} placeholders an agent needs at call time.

        Returns the names (and where possible, sources/categories) of every
        template variable the agent's prompt references — split into:
        - system_variables: platform-injected (`system__*`) — never supply these
        - dynamic_variables: caller-supplied at make_call / inbound webhook time

        Use this before placing an outbound call to verify the dynamic_variables
        payload covers every required name. Saves a round-trip vs trial-and-error.
        """
        r = await client.get(f"/agents/{agent_id}/required-variables")
        r.raise_for_status()
        return r.json()

    @mcp.tool(name="duplicate_agent")
    async def duplicate_agent(
        agent_id: str,
        new_name: str | None = None,
    ) -> dict[str, Any]:
        """Create an exact copy of an agent with all its configuration.

        Duplicates everything: brain settings, voice, transcriber, transfer
        rules, analytics config, tools, and conversation settings. The copy
        is independent — changes to one don't affect the other.

        Great for:
        - A/B testing different prompts or voices on the same setup
        - Creating language variants (duplicate, then change language + instructions)
        - Branching a proven agent before making experimental changes
        - Setting up dev/staging/prod versions of the same agent
        """
        params: dict[str, Any] = {}
        if new_name:
            params["new_name"] = new_name

        r = await client.post(f"/agents/{agent_id}/duplicate", params=params)
        r.raise_for_status()
        d = r.json()
        return {
            "id": d.get("id"),
            "name": d.get("name"),
            "status": d.get("status"),
            "created_at": d.get("created_at"),
        }

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
        first_message: str = "",
        # Brain
        brain_provider: str = "openai",
        brain_model: str = "gpt-4.1",
        temperature: float = 0.8,
        max_tokens: int = 4096,
        # Voice
        voice_provider: str = "elevenlabs",
        voice_id: str = "gHu9GtaHOXcSqFTK06ux",
        voice_speed: float = 1.0,
        voice_stability: float = 0.5,
        # Transcriber
        transcriber_provider: str = "deepgram",
        transcriber_model: str = "nova-3",
        language: str = "en-US",
        # Conversation behavior
        endpointing_ms: int = 300,
        interruption_enabled: bool = True,
        first_message_delay_ms: int = 1100,
        max_call_duration: int = 1800,
        # Extras
        description: str = "",
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create a new voice AI agent that can make and receive phone calls.

        This is the core tool for building AI telephony agents. Only `name` and
        `instructions` are required — everything else has production-ready defaults
        that work well for most use cases.

        ## How to write great agent instructions

        The `instructions` field is the system prompt — it defines everything about
        how the agent behaves on calls. Great instructions include:
        - **Identity**: Who the agent is (name, role, company)
        - **Objective**: What the agent should accomplish on each call
        - **Personality**: Tone, speaking style, energy level
        - **Knowledge boundaries**: What to say when asked something unknown
        - **Call flow**: Steps to follow (greeting → discovery → resolution → close)
        - **Constraints**: What never to say, topics to avoid, compliance rules

        Example: "You are Alex from Acme Insurance. Your goal is to help callers
        file claims quickly. Be warm and empathetic. Always verify the caller's
        policy number before discussing details. Never provide legal advice.
        If the caller is upset, acknowledge their frustration before problem-solving."

        ## Choosing a voice

        The voice is the single biggest factor in how natural the agent sounds.
        Test different voices for your use case:

        ElevenLabs voices (highest quality, default provider):
        - "gHu9GtaHOXcSqFTK06ux" — Aria (default, warm female, great all-rounder)
        - "pFZP5JQG7iQjIQuC4Bku" — Lily (soft female, good for support)
        - "bIHbv24MWmeRgasZH58o" — Will (confident male, good for sales)
        - "EXAVITQu4vr4xnSDxMaL" — Sarah (professional female, good for business)
        - "onwK4e9ZLuTAKqWW03F9" — Daniel (authoritative male, good for enterprise)

        Cartesia voices (lower latency, good for fast-paced conversations):
        Set voice_provider="cartesia" and use Cartesia voice IDs.

        ## Tuning conversation dynamics

        - **temperature**: Controls creativity. 0.3 = focused/factual (support bots),
          0.8 = balanced (default), 1.2+ = creative/spontaneous (sales, entertainment)
        - **voice_speed**: 0.8 = calm/deliberate, 1.0 = natural, 1.2 = energetic
        - **voice_stability**: 0.3 = expressive/emotional, 0.7 = consistent/professional
        - **endpointing_ms**: How long to wait after the caller stops speaking before
          responding. 200 = very responsive (interrupty), 300 = natural (default),
          500+ = patient (let caller think). Lower = faster but may cut people off.
        - **interruption_enabled**: True (default) lets callers interrupt the agent
          mid-sentence. Set False for IVR-style or legal-disclosure agents.

        ## First message strategy

        The `first_message` is what the agent says immediately when answering:
        - Set it for inbound agents: "Hi, thanks for calling Acme. How can I help?"
        - Leave empty for outbound agents that should wait for "Hello?" first
        - first_message_delay_ms controls the pause before speaking (1100ms default
          feels natural — too fast sounds robotic, too slow feels laggy)

        ## Language support

        Set `language` to match your callers: "en-US", "en-GB", "es", "fr", "de",
        "pt-BR", "ja", "ko", "zh", "ar", "hi", etc. This affects speech recognition
        accuracy. Write instructions in the same language for best results.

        Returns: agent id, name, status, and configuration summary.
        """
        body: dict[str, Any] = {
            "name": name,
            "brain": {
                "provider": brain_provider,
                "model": brain_model,
                "instructions": instructions,
                "temperature": temperature,
                "max_completion_tokens": max_tokens,
            },
            "voice": {
                "provider": voice_provider,
                "voice_id": voice_id,
                "speed": voice_speed,
                "stability": voice_stability,
            },
            "transcriber": {
                "provider": transcriber_provider,
                "model": transcriber_model,
                "language": language,
                "endpointing_ms": endpointing_ms,
            },
            "interruption": {
                "enabled": interruption_enabled,
            },
            "call_duration": {
                "enabled": True,
                "max_seconds": max_call_duration,
            },
        }

        if first_message:
            body["first_message"] = {
                "enabled": True,
                "text": first_message,
                "delay_ms": first_message_delay_ms,
            }

        if description:
            body["description"] = description
        if tags:
            body["tags"] = tags

        r = await client.post("/agents", json=body)
        r.raise_for_status()
        d = r.json()
        brain = d.get("brain") or {}
        voice = d.get("voice") or {}
        return {
            "id": d.get("id"),
            "name": d.get("name"),
            "status": d.get("status"),
            "brain": f"{brain.get('provider')}/{brain.get('model')}",
            "voice": f"{voice.get('provider')}/{voice.get('voice_id', '')}",
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
        first_message: str | None = None,
        # Brain
        brain_model: str | None = None,
        brain_provider: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        # Voice
        voice_id: str | None = None,
        voice_provider: str | None = None,
        voice_speed: float | None = None,
        voice_stability: float | None = None,
        # Transcriber
        transcriber_model: str | None = None,
        transcriber_provider: str | None = None,
        language: str | None = None,
        endpointing_ms: int | None = None,
        # Conversation
        interruption_enabled: bool | None = None,
        max_call_duration: int | None = None,
        first_message_delay_ms: int | None = None,
        # Advanced — raw config sections (read get_agent output for structure)
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Update any part of an agent's configuration.

        Only the fields you provide are changed — everything else stays as-is.
        The backend deep-merges your changes, so you can update a single field
        inside a nested config without affecting sibling fields.

        ## Two ways to update

        **Named parameters** — for common changes. Just pass what you want:
        ```
        update_agent(agent_id="...", temperature=0.5, voice_speed=1.1)
        ```

        **config parameter** — for advanced settings not covered by named params.
        Use get_agent first to see the current structure, then pass sections:
        ```
        update_agent(agent_id="...", config={
            "transfer": {
                "enabled": True,
                "mode": "blind",
                "destinations": [{
                    "name": "Human Support",
                    "number": "+15551234567",
                    "description": "Transfer when caller requests a human",
                    "keywords": ["human", "representative", "real person"]
                }]
            }
        })
        ```

        ## Available config sections

        - **transfer** — call transfer rules: destinations, warm/blind mode,
          hold music, warm intro templates, failure handling
        - **tools.rag** — RAG knowledge retrieval: enable/disable, top_k,
          score threshold, knowledge_base_ids
        - **tools.hangup** — call termination: keywords, farewell message,
          confirmation prompt
        - **tools.voicemail** — voicemail detection: action (hangup/leave_message),
          message text, wait_for_beep
        - **timeout** — silence timeout: trigger_seconds, warning messages,
          final message before hanging up
        - **turn_detection** — conversation pacing: semantic_vad vs vad mode,
          min/max delay, endpointing_mode (fixed/dynamic)
        - **interruption** — caller interruption handling: min_duration,
          min_words, false interruption recovery
        - **background_audio** — ambient sound and thinking indicators:
          office_ambience, keyboard_typing, volume levels
        - **analytics** — recording, post-call summary, sentiment tracking,
          success evaluation, data collection fields
        - **call_duration** — max call length, warning messages before cutoff

        Named params and config are merged — named params take precedence.
        """
        body: dict[str, Any] = {}

        # Apply raw config sections first (named params override)
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

        # Brain section
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
            body["brain"] = {**body.get("brain", {}), **brain_fields}

        # Voice section
        voice_fields: dict[str, Any] = {}
        if voice_id is not None:
            voice_fields["voice_id"] = voice_id
        if voice_provider is not None:
            voice_fields["provider"] = voice_provider
        if voice_speed is not None:
            voice_fields["speed"] = voice_speed
        if voice_stability is not None:
            voice_fields["stability"] = voice_stability
        if voice_fields:
            body["voice"] = {**body.get("voice", {}), **voice_fields}

        # Transcriber section
        transcriber_fields: dict[str, Any] = {}
        if transcriber_model is not None:
            transcriber_fields["model"] = transcriber_model
        if transcriber_provider is not None:
            transcriber_fields["provider"] = transcriber_provider
        if language is not None:
            transcriber_fields["language"] = language
        if endpointing_ms is not None:
            transcriber_fields["endpointing_ms"] = endpointing_ms
        if transcriber_fields:
            body["transcriber"] = {**body.get("transcriber", {}), **transcriber_fields}

        # First message
        if first_message is not None:
            fm: dict[str, Any] = {"enabled": bool(first_message), "text": first_message}
            if first_message_delay_ms is not None:
                fm["delay_ms"] = first_message_delay_ms
            body["first_message"] = fm
        elif first_message_delay_ms is not None:
            body["first_message"] = {"delay_ms": first_message_delay_ms}

        # Conversation settings
        if interruption_enabled is not None:
            body["interruption"] = {
                **body.get("interruption", {}),
                "enabled": interruption_enabled,
            }
        if max_call_duration is not None:
            body["call_duration"] = {
                **body.get("call_duration", {}),
                "enabled": True,
                "max_seconds": max_call_duration,
            }

        r = await client.patch(f"/agents/{agent_id}", json=body)
        r.raise_for_status()
        d = r.json()
        brain = d.get("brain") or {}
        voice = d.get("voice") or {}
        return {
            "id": d.get("id"),
            "name": d.get("name"),
            "status": d.get("status"),
            "is_active": d.get("is_active"),
            "brain": f"{brain.get('provider')}/{brain.get('model')}",
            "voice": f"{voice.get('provider')}/{voice.get('voice_id', '')}",
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
        body: dict[str, Any] = {}
        if new_name:
            body["new_name"] = new_name

        r = await client.post(f"/agents/{agent_id}/duplicate", json=body)
        r.raise_for_status()
        d = r.json()
        return {
            "id": d.get("id"),
            "name": d.get("name"),
            "status": d.get("status"),
            "created_at": d.get("created_at"),
        }

"""Real backend: ElevenLabs Conversational AI over Twilio.

Imports the `elevenlabs` SDK lazily so it is only required when
VOICE_PROVIDER=elevenlabs — the mock backend has no dependency on it.
Install with: uv sync --extra elevenlabs
"""
from __future__ import annotations

from typing import Any

from outreachiq.config import settings
from outreachiq.providers.base import VoiceProvider


class ElevenLabsVoiceProvider(VoiceProvider):
    def __init__(self) -> None:
        if not settings.elevenlabs_api_key:
            raise RuntimeError("ELEVENLABS_API_KEY is not set")
        try:
            from elevenlabs import ElevenLabs
        except ImportError as exc:  # pragma: no cover - exercised only without the extra installed
            raise RuntimeError(
                "The 'elevenlabs' package is required for VOICE_PROVIDER=elevenlabs. "
                "Install it with: uv sync --extra elevenlabs"
            ) from exc

        self._client = ElevenLabs(api_key=settings.elevenlabs_api_key)

    def initiate_call(self, *, customer_name: str, phone: str, guidance_text: str) -> dict[str, Any]:
        from elevenlabs.conversational_ai.conversation import ConversationInitiationData

        call_config = ConversationInitiationData(
            dynamic_variables={"customer_name": customer_name, "call_guidance": guidance_text}
        )
        response = self._client.conversational_ai.twilio.outbound_call(
            agent_id=settings.elevenlabs_agent_id,
            agent_phone_number_id=settings.elevenlabs_phone_number_id,
            to_number=phone,
            conversation_initiation_client_data=call_config,
        )
        if not response.success:
            return {"status": "failed", "conversation_id": None}
        return {
            "status": "initiated",
            "conversation_id": response.conversation_id,
            "call_sid": response.call_sid,
        }

    def get_call_status(self, conversation_id: str) -> dict[str, Any]:
        conv = self._client.conversational_ai.conversations.get(conversation_id=conversation_id)
        error = getattr(conv.metadata, "error", None) if hasattr(conv, "metadata") else None
        return {"raw_status": conv.status, "error": error}

    def get_transcript(self, conversation_id: str) -> dict[str, Any]:
        conv = self._client.conversational_ai.conversations.get(conversation_id=conversation_id)
        lines = []
        if hasattr(conv, "transcript") and isinstance(conv.transcript, list):
            for turn in conv.transcript:
                message = getattr(turn, "message", None)
                if message:
                    lines.append(f"{getattr(turn, 'role', 'unknown')}: {message.strip()}")
        return {"transcript": "\n".join(lines), "analysis": str(conv.analysis or "")}

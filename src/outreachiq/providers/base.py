"""Provider interfaces. Agents and tools depend only on these, never on a
specific vendor SDK — that's what lets the whole pipeline run against the
mock backends with zero external credentials, and swap in a real backend
(ElevenLabs+Twilio, Gmail) behind the same contract.
"""
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any


class VoiceProvider(ABC):
    @abstractmethod
    def initiate_call(self, *, customer_name: str, phone: str, guidance_text: str) -> dict[str, Any]:
        """Places an outbound call. Returns at least {'status', 'conversation_id'}."""

    @abstractmethod
    def get_call_status(self, conversation_id: str) -> dict[str, Any]:
        """Returns at least {'raw_status': str, 'error': str | None}."""

    @abstractmethod
    def get_transcript(self, conversation_id: str) -> dict[str, Any]:
        """Returns at least {'transcript': str, 'analysis': str}."""

    def wait_for_terminal_status(
        self,
        conversation_id: str,
        *,
        max_wait_seconds: int,
        poll_interval_seconds: int,
        no_pickup_after_seconds: int,
    ) -> dict[str, Any]:
        """Shared polling loop so every backend gets identical outcome detection."""
        elapsed = 0
        while elapsed < max_wait_seconds:
            status = self.get_call_status(conversation_id)
            raw_status = status.get("raw_status")

            if raw_status in ("done", "completed"):
                return {"outcome": "completed", "raw_status": raw_status, "conversation_id": conversation_id}
            if raw_status == "failed":
                return {
                    "outcome": "failed",
                    "raw_status": raw_status,
                    "conversation_id": conversation_id,
                    "error": status.get("error"),
                }
            if raw_status == "initiated" and elapsed >= no_pickup_after_seconds:
                return {
                    "outcome": "did_not_pick",
                    "raw_status": raw_status,
                    "conversation_id": conversation_id,
                    "message": f"Call remained 'initiated' for {elapsed}s",
                }

            time.sleep(poll_interval_seconds)
            elapsed += poll_interval_seconds

        return {
            "outcome": "error",
            "raw_status": "timeout",
            "conversation_id": conversation_id,
            "error": f"Timed out after {max_wait_seconds}s waiting for call completion",
        }


class EmailProvider(ABC):
    @abstractmethod
    def send_email(self, *, to: str, sender: str, subject: str, html_body: str) -> dict[str, Any]:
        """Returns at least {'status': 'sent' | 'failed', 'message_id': str | None}."""

"""Deterministic, zero-dependency stand-in for a real voice API.

Outcomes are derived from a hash of the phone number, so the same customer
always simulates the same way (useful for demos and tests) unless overridden
with `settings.mock_call_outcome` or the constructor's `forced_outcome`.
No real time is spent waiting — status is terminal on the first poll, so a
full campaign runs in well under a second.
"""
from __future__ import annotations

import random
import uuid
from datetime import UTC, datetime
from typing import Any

from outreachiq.config import settings
from outreachiq.providers.base import VoiceProvider

_OUTCOME_WEIGHTS = [("completed", 0.6), ("did_not_pick", 0.25), ("failed", 0.15)]


def _deterministic_outcome(phone: str) -> str:
    rng = random.Random(phone)
    outcomes, weights = zip(*_OUTCOME_WEIGHTS)
    return rng.choices(outcomes, weights=weights, k=1)[0]


class MockVoiceProvider(VoiceProvider):
    def __init__(self, forced_outcome: str | None = None) -> None:
        self._forced_outcome = forced_outcome or settings.mock_call_outcome
        self._calls: dict[str, dict[str, Any]] = {}

    def initiate_call(self, *, customer_name: str, phone: str, guidance_text: str) -> dict[str, Any]:
        conversation_id = f"mock-{uuid.uuid4().hex[:12]}"
        outcome = self._forced_outcome or _deterministic_outcome(phone)
        self._calls[conversation_id] = {
            "customer_name": customer_name,
            "phone": phone,
            "guidance_text": guidance_text,
            "outcome": outcome,
        }
        return {
            "status": "initiated",
            "conversation_id": conversation_id,
            "call_sid": f"CA{uuid.uuid4().hex[:20]}",
            "initiated_at": datetime.now(UTC).isoformat(),
        }

    def get_call_status(self, conversation_id: str) -> dict[str, Any]:
        call = self._calls.get(conversation_id)
        if call is None:
            return {"raw_status": "failed", "error": "Unknown conversation_id"}

        outcome = call["outcome"]
        if outcome == "completed":
            return {"raw_status": "done"}
        if outcome == "failed":
            return {"raw_status": "failed", "error": "Simulated call failure"}
        # did_not_pick: report "initiated" so the shared polling loop's
        # no-pickup timeout logic is what actually classifies it.
        return {"raw_status": "initiated"}

    def get_transcript(self, conversation_id: str) -> dict[str, Any]:
        call = self._calls.get(conversation_id)
        if call is None or call["outcome"] != "completed":
            return {"transcript": "", "analysis": "No transcript available."}

        name = call["customer_name"]
        transcript = "\n".join(
            [
                f"agent: Hi {name}, this is Alex from OutreachIQ, thanks for taking my call.",
                "user: Sure, happy to chat.",
                f"agent: {call['guidance_text'].splitlines()[0] if call['guidance_text'] else 'How has your experience been so far?'}",
                "user: It's been going well, though I'd like more advanced material.",
                "agent: Noted, I'll pass that along and follow up by email with next steps.",
            ]
        )
        return {
            "transcript": transcript,
            "analysis": "Customer engaged positively and requested more advanced content.",
        }

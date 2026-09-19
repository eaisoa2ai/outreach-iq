"""CrewAI tools. Each one is a thin adapter between an agent and a provider —
all the real logic (polling, transcript formatting, email delivery) lives in
the provider implementations so it stays testable without CrewAI involved.
"""
from __future__ import annotations

import json

from crewai.tools import tool

from outreachiq.config import settings
from outreachiq.providers.registry import get_email_provider, get_voice_provider


def _normalize_phone(phone: str) -> str:
    phone = phone.strip()
    if phone.startswith("+"):
        return phone
    return settings.default_country_code + phone.lstrip("0")


@tool("Initiate outbound call")
def make_call_tool(customer_name: str, phone: str, guidance_text: str) -> str:
    """Places an outbound AI voice call to the customer using the configured
    voice provider and returns the initiation result as JSON."""
    provider = get_voice_provider()
    result = provider.initiate_call(
        customer_name=customer_name,
        phone=_normalize_phone(phone),
        guidance_text=guidance_text,
    )
    return json.dumps(result)


@tool("Wait for call outcome")
def check_call_status_tool(conversation_id: str) -> str:
    """Polls the voice provider until the call reaches a terminal outcome
    (completed, failed, did_not_pick) or times out, returning that outcome
    as JSON."""
    provider = get_voice_provider()
    thresholds = settings.thresholds
    result = provider.wait_for_terminal_status(
        conversation_id,
        max_wait_seconds=thresholds.max_call_wait_seconds,
        poll_interval_seconds=thresholds.call_poll_interval_seconds,
        no_pickup_after_seconds=thresholds.no_pickup_after_seconds,
    )
    return json.dumps(result)


@tool("Fetch call transcript")
def fetch_transcript_tool(conversation_id: str) -> str:
    """Fetches the transcript and analysis for a completed call as JSON.
    Only call this after the outcome is 'completed'."""
    provider = get_voice_provider()
    return json.dumps(provider.get_transcript(conversation_id))


@tool("Send follow-up email")
def send_email_tool(recipient_email: str, subject: str, html_body: str) -> str:
    """Sends a follow-up email via the configured email provider and returns
    the send result as JSON."""
    provider = get_email_provider()
    result = provider.send_email(
        to=recipient_email, sender=settings.sender_email, subject=subject, html_body=html_body
    )
    return json.dumps(result)

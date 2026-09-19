"""CrewAI tools. Each one is a thin adapter between an agent and a provider —
all the real logic (polling, transcript formatting, email delivery) lives in
the provider implementations so it stays testable without CrewAI involved.
"""
from __future__ import annotations

import json

from crewai.tools import tool

from outreachiq.config import settings
from outreachiq.guardrails import check_outgoing_email_content
from outreachiq.observability import get_tracer
from outreachiq.providers.registry import get_email_provider, get_voice_provider

tracer = get_tracer()


def _normalize_phone(phone: str) -> str:
    phone = phone.strip()
    if phone.startswith("+"):
        return phone
    return settings.default_country_code + phone.lstrip("0")


@tool("Initiate outbound call")
def make_call_tool(customer_name: str, phone: str, guidance_text: str) -> str:
    """Places an outbound AI voice call to the customer using the configured
    voice provider and returns the initiation result as JSON."""
    with tracer.start_as_current_span("voice.initiate_call") as span:
        provider = get_voice_provider()
        result = provider.initiate_call(
            customer_name=customer_name,
            phone=_normalize_phone(phone),
            guidance_text=guidance_text,
        )
        span.set_attribute("status", result.get("status", "unknown"))
        if result.get("conversation_id"):
            span.set_attribute("conversation_id", result["conversation_id"])
        return json.dumps(result)


@tool("Wait for call outcome")
def check_call_status_tool(conversation_id: str) -> str:
    """Polls the voice provider until the call reaches a terminal outcome
    (completed, failed, did_not_pick) or times out, returning that outcome
    as JSON."""
    with tracer.start_as_current_span("voice.wait_for_terminal_status") as span:
        span.set_attribute("conversation_id", conversation_id)
        provider = get_voice_provider()
        thresholds = settings.thresholds
        result = provider.wait_for_terminal_status(
            conversation_id,
            max_wait_seconds=thresholds.max_call_wait_seconds,
            poll_interval_seconds=thresholds.call_poll_interval_seconds,
            no_pickup_after_seconds=thresholds.no_pickup_after_seconds,
        )
        span.set_attribute("outcome", result.get("outcome", "unknown"))
        return json.dumps(result)


@tool("Fetch call transcript")
def fetch_transcript_tool(conversation_id: str) -> str:
    """Fetches the transcript and analysis for a completed call as JSON.
    Only call this after the outcome is 'completed'."""
    with tracer.start_as_current_span("voice.get_transcript") as span:
        span.set_attribute("conversation_id", conversation_id)
        provider = get_voice_provider()
        return json.dumps(provider.get_transcript(conversation_id))


@tool("Send follow-up email")
def send_email_tool(recipient_email: str, subject: str, html_body: str) -> str:
    """Sends a follow-up email via the configured email provider and returns
    the send result as JSON. Blocks the send (status='blocked') instead of
    delivering it if the content fails an automated safety check."""
    with tracer.start_as_current_span("email.send") as span:
        span.set_attribute("recipient", recipient_email)

        violations = check_outgoing_email_content(subject, html_body)
        if violations:
            span.set_attribute("status", "blocked")
            span.add_event("guardrail.blocked", {"violations": violations})
            return json.dumps(
                {
                    "status": "blocked",
                    "message_id": None,
                    "violations": violations,
                    "subject": subject,
                    "content": html_body,
                }
            )

        provider = get_email_provider()
        result = provider.send_email(
            to=recipient_email, sender=settings.sender_email, subject=subject, html_body=html_body
        )
        span.set_attribute("status", result.get("status", "unknown"))
        return json.dumps(result)

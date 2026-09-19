"""Content-safety checks on what the Email Agent produces, split into two
layers the same way a real system would need them:

- `check_outgoing_email_content` is a *preventive* control: it runs inside
  `send_email_tool` itself, before any provider (mock or real) is called, so
  a bad email is blocked rather than sent and cleaned up after.
- `check_email_matches_call_outcome` is a *detective* control: it needs both
  the email and the call analysis together, which only exist once the whole
  crew has finished, so it runs afterward in `routing.py` and flags the
  campaign for human review rather than blocking anything retroactively.

Both are pure functions — no LLM, no network — for the same reason
`routing.py` is: every case is a plain input/output pair a unit test can
assert on directly.

This is deliberately a fixed keyword/pattern check, not an LLM-based content
classifier. It catches the specific failure modes this pipeline can actually
produce (an unfilled prompt template, a promise no one authorized, a claim
about a call that didn't happen) — it is not a general-purpose safety
filter, and a production system handling more open-ended content would want
to combine this with a classifier rather than rely on keywords alone.
"""
from __future__ import annotations

from outreachiq.models import CallAnalysis, CallOutcome, EmailOutcome

_UNFILLED_TEMPLATE_MARKERS = ["{{", "}}", "{customer_name}"]

_UNAUTHORIZED_OFFER_PHRASES = [
    "refund",
    "discount code",
    "% off",
    "free trial",
    "money back",
    "money-back",
]

_CALL_HAPPENED_PHRASES = [
    "our call",
    "our conversation",
    "talking to you today",
    "on the phone with you",
    "during our chat",
]

MIN_BODY_LENGTH = 20


def check_outgoing_email_content(subject: str, html_body: str) -> list[str]:
    """Local checks the send tool can run with no context beyond the message
    itself. Returns a list of human-readable violations; empty means clean."""
    violations: list[str] = []
    body = html_body or ""

    if len(body.strip()) < MIN_BODY_LENGTH:
        violations.append("Email body is suspiciously short or empty")

    if not (subject or "").strip():
        violations.append("Email has no subject line")

    for marker in _UNFILLED_TEMPLATE_MARKERS:
        if marker in body:
            violations.append(f"Email contains an unfilled template marker: {marker!r}")
            break

    body_lower = body.lower()
    for phrase in _UNAUTHORIZED_OFFER_PHRASES:
        if phrase in body_lower:
            violations.append(f"Email makes an unauthorized offer or promise: {phrase!r}")

    return violations


def check_email_matches_call_outcome(
    email: EmailOutcome, call_analysis: CallAnalysis | None
) -> list[str]:
    """Cross-references the sent email against what the call actually did.
    Needs both objects, so it can only run after the full campaign state
    exists — see routing.py."""
    call_completed = call_analysis is not None and call_analysis.outcome == CallOutcome.COMPLETED
    if call_completed:
        return []

    body_lower = (email.html_body or "").lower()
    outcome_label = call_analysis.outcome.value if call_analysis else "not_attempted"
    for phrase in _CALL_HAPPENED_PHRASES:
        if phrase in body_lower:
            return [
                f"Email references a call that didn't complete (outcome={outcome_label}): "
                f"{phrase!r}"
            ]
    return []

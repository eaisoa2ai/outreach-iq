"""Pure routing logic — no LLM calls, no I/O, so it is fully unit-testable.

`evaluate_routing` inspects a CampaignState and decides whether the campaign
needs a human to step in. It is called after every stage so a campaign can be
flagged as early as possible instead of only at the very end.
"""
from __future__ import annotations

from outreachiq.config import Thresholds
from outreachiq.guardrails import check_email_matches_call_outcome
from outreachiq.models import CallOutcome, CampaignState


def evaluate_routing(state: CampaignState, thresholds: Thresholds) -> CampaignState:
    reasons: list[str] = []

    if not state.context.profile.phone:
        reasons.append("Customer has no phone number on file")

    for label, output in (
        ("call guidance", state.guidance),
        ("call initiation", state.call_initiation),
        ("call analysis", state.call_analysis),
        ("email", state.email_outcome),
    ):
        if output is not None and output.confidence < thresholds.confidence_floor:
            reasons.append(
                f"{label} confidence {output.confidence:.2f} below floor "
                f"{thresholds.confidence_floor:.2f}"
            )

    if state.call_analysis is not None and state.call_analysis.outcome == CallOutcome.ERROR:
        reasons.append("Call ended in an error outcome")

    if state.email_outcome is not None:
        if state.email_outcome.status in ("failed", "blocked"):
            reasons.append(f"Follow-up email was not sent (status={state.email_outcome.status})")
        reasons.extend(
            check_email_matches_call_outcome(state.email_outcome, state.call_analysis)
        )

    if state.errors:
        reasons.append(f"{len(state.errors)} error(s) recorded during the campaign")

    state.review_reasons = reasons
    state.requires_human_review = bool(reasons)
    return state

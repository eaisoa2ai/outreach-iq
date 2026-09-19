"""Routing is pure logic, so every combination of flags is tested directly
against `evaluate_routing` without touching CrewAI, the database, or any
provider.
"""
from datetime import UTC, datetime

import pytest

from outreachiq.config import Thresholds
from outreachiq.models import CallAnalysis, CallOutcome, CampaignState, EmailOutcome
from outreachiq.routing import evaluate_routing

THRESHOLDS = Thresholds(confidence_floor=0.6)


def _base_state(sample_context) -> CampaignState:
    return CampaignState(
        campaign_id="camp_1",
        customer_id=sample_context.profile.customer_id,
        started_at=datetime.now(UTC),
        context=sample_context,
    )


def test_happy_path_does_not_require_review(sample_context):
    state = _base_state(sample_context)
    state.call_analysis = CallAnalysis(
        confidence=0.9,
        reasoning_summary="ok",
        outcome=CallOutcome.COMPLETED,
        raw_status="done",
        email_guidance="reference the call",
    )
    state.email_outcome = EmailOutcome(
        confidence=0.9, reasoning_summary="ok", subject="Hi", html_body="<p>Hi</p>", status="sent"
    )

    result = evaluate_routing(state, THRESHOLDS)

    assert result.requires_human_review is False
    assert result.review_reasons == []


def test_missing_phone_number_requires_review(sample_context):
    sample_context.profile.phone = None
    state = _base_state(sample_context)

    result = evaluate_routing(state, THRESHOLDS)

    assert result.requires_human_review is True
    assert any("phone" in r.lower() for r in result.review_reasons)


@pytest.mark.parametrize(
    "confidence,expect_flagged",
    [
        (0.60, False),  # exactly at the floor is acceptable
        (0.59, True),   # just below the floor is not
        (0.0, True),
        (1.0, False),
    ],
)
def test_confidence_floor_boundary(sample_context, confidence, expect_flagged):
    state = _base_state(sample_context)
    state.email_outcome = EmailOutcome(
        confidence=confidence, reasoning_summary="ok", subject="Hi", html_body="<p>Hi</p>", status="sent"
    )

    result = evaluate_routing(state, THRESHOLDS)

    assert result.requires_human_review is expect_flagged


def test_call_error_outcome_requires_review(sample_context):
    state = _base_state(sample_context)
    state.call_analysis = CallAnalysis(
        confidence=0.9,
        reasoning_summary="ok",
        outcome=CallOutcome.ERROR,
        raw_status="timeout",
        email_guidance="offer an alternative contact method",
    )

    result = evaluate_routing(state, THRESHOLDS)

    assert result.requires_human_review is True
    assert any("error" in r.lower() for r in result.review_reasons)


def test_failed_email_send_requires_review(sample_context):
    state = _base_state(sample_context)
    state.email_outcome = EmailOutcome(
        confidence=0.9, reasoning_summary="ok", subject="Hi", html_body="<p>Hi</p>", status="failed"
    )

    result = evaluate_routing(state, THRESHOLDS)

    assert result.requires_human_review is True
    assert any("email" in r.lower() for r in result.review_reasons)


def test_recorded_errors_require_review(sample_context):
    state = _base_state(sample_context)
    state.errors = ["Something went wrong"]

    result = evaluate_routing(state, THRESHOLDS)

    assert result.requires_human_review is True
    assert any("error(s) recorded" in r for r in result.review_reasons)

import pytest

from outreachiq.guardrails import check_email_matches_call_outcome, check_outgoing_email_content
from outreachiq.models import CallAnalysis, CallOutcome, EmailOutcome

VALID_BODY = "<p>Hi Ada, thanks for your time. Best regards, Alex.</p>"


def test_clean_email_has_no_violations():
    assert check_outgoing_email_content("Following up", VALID_BODY) == []


@pytest.mark.parametrize("body", ["", "   ", "<p>Hi</p>"])
def test_short_or_empty_body_is_flagged(body):
    violations = check_outgoing_email_content("Subject", body)
    assert any("short" in v.lower() for v in violations)


def test_missing_subject_is_flagged():
    violations = check_outgoing_email_content("", VALID_BODY)
    assert any("subject" in v.lower() for v in violations)


@pytest.mark.parametrize("body", [
    "<p>Hi {{customer_name}}, thanks!</p>",
    "<p>Hi {customer_name}, thanks for your time today and more.</p>",
])
def test_unfilled_template_marker_is_flagged(body):
    violations = check_outgoing_email_content("Subject", body)
    assert any("template marker" in v.lower() for v in violations)


@pytest.mark.parametrize("phrase", ["refund", "discount code", "20% off", "free trial", "money back"])
def test_unauthorized_offer_is_flagged(phrase):
    body = f"<p>As a thank you, here is a {phrase} just for you, we really appreciate it!</p>"
    violations = check_outgoing_email_content("Subject", body)
    assert any("unauthorized offer" in v.lower() for v in violations)


def _analysis(outcome: CallOutcome) -> CallAnalysis:
    return CallAnalysis(
        confidence=0.9, reasoning_summary="ok", outcome=outcome, raw_status="x", email_guidance="x"
    )


def test_completed_call_may_reference_the_call():
    email = EmailOutcome(
        confidence=0.9,
        reasoning_summary="ok",
        subject="Great chat!",
        html_body="<p>Thanks for our call today, here are the next steps.</p>",
        status="sent",
    )
    assert check_email_matches_call_outcome(email, _analysis(CallOutcome.COMPLETED)) == []


@pytest.mark.parametrize(
    "outcome", [CallOutcome.DID_NOT_PICK, CallOutcome.FAILED, CallOutcome.ERROR, CallOutcome.NOT_ATTEMPTED]
)
def test_non_completed_call_referencing_the_call_is_flagged(outcome):
    email = EmailOutcome(
        confidence=0.9,
        reasoning_summary="ok",
        subject="Great chat!",
        html_body="<p>Thanks for our call today, here are the next steps.</p>",
        status="sent",
    )
    violations = check_email_matches_call_outcome(email, _analysis(outcome))
    assert any("didn't complete" in v for v in violations)


def test_missing_call_analysis_referencing_a_call_is_flagged():
    email = EmailOutcome(
        confidence=0.9,
        reasoning_summary="ok",
        subject="Great chat!",
        html_body="<p>Great talking to you today!</p>",
        status="sent",
    )
    violations = check_email_matches_call_outcome(email, None)
    assert violations != []


def test_non_completed_call_without_call_reference_is_clean():
    email = EmailOutcome(
        confidence=0.9,
        reasoning_summary="ok",
        subject="Sorry we missed you",
        html_body="<p>We tried reaching you regarding your recent course activity.</p>",
        status="sent",
    )
    assert check_email_matches_call_outcome(email, _analysis(CallOutcome.DID_NOT_PICK)) == []

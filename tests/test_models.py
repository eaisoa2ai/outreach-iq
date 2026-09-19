from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from outreachiq.models import (
    AgentOutput,
    CallOutcome,
    CampaignState,
    CustomerContext,
    CustomerProfile,
)


def _profile() -> CustomerProfile:
    return CustomerProfile(customer_id="C1", name="Ada Lovelace", email="ada@example.com", phone="+15551234567")


@pytest.mark.parametrize("confidence", [-0.01, 1.01])
def test_agent_output_rejects_out_of_range_confidence(confidence):
    with pytest.raises(ValidationError):
        AgentOutput(confidence=confidence, reasoning_summary="test")


@pytest.mark.parametrize("confidence", [0.0, 0.5, 1.0])
def test_agent_output_accepts_boundary_confidence(confidence):
    output = AgentOutput(confidence=confidence, reasoning_summary="test")
    assert output.confidence == confidence
    assert output.evidence == []
    assert output.warnings == []


def test_campaign_state_defaults_to_not_requiring_review():
    state = CampaignState(
        campaign_id="camp_1",
        customer_id="C1",
        started_at=datetime.now(UTC),
        context=CustomerContext(profile=_profile()),
    )
    assert state.requires_human_review is False
    assert state.completed is False
    assert state.errors == []


def test_call_outcome_values_match_expected_set():
    assert {o.value for o in CallOutcome} == {
        "not_attempted",
        "completed",
        "failed",
        "did_not_pick",
        "error",
    }

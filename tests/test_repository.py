from datetime import UTC, datetime

from outreachiq.db.repository import CampaignRepository, CustomerRepository
from outreachiq.models import CampaignState


def test_get_context_returns_none_for_unknown_customer(db_session):
    assert CustomerRepository.get_context(db_session, "does-not-exist", days_back=30) is None


def test_get_context_assembles_profile_engagement_and_feedback(db_session, seeded_customer):
    context = CustomerRepository.get_context(db_session, seeded_customer, days_back=30)

    assert context is not None
    assert context.profile.name == "Ada Lovelace"
    assert context.profile.phone == "+15551234567"
    assert len(context.engagements) == 1
    assert context.engagements[0].course_title == "Intro to ML"
    assert len(context.feedback) == 1
    assert context.last_active_at is not None


def test_get_context_respects_lookback_window(db_session, seeded_customer):
    # The seeded engagement/feedback are "now", so a 0-day lookback should exclude them.
    context = CustomerRepository.get_context(db_session, seeded_customer, days_back=0)
    assert context is not None
    assert context.engagements == []
    assert context.feedback == []


def test_list_customers_returns_all_profiles(db_session, seeded_customer):
    customers = CustomerRepository.list_customers(db_session)
    assert [c.customer_id for c in customers] == ["C1"]


def test_campaign_repository_save_and_list_roundtrip(db_session, sample_context):
    state = CampaignState(
        campaign_id="camp_1",
        customer_id="C1",
        started_at=datetime.now(UTC),
        context=sample_context,
        completed=True,
    )

    CampaignRepository.save(db_session, state)
    db_session.commit()

    roundtripped = CampaignRepository.list_campaigns(db_session, customer_id="C1")
    assert len(roundtripped) == 1
    assert roundtripped[0].campaign_id == "camp_1"
    assert roundtripped[0].completed is True


def test_campaign_repository_save_is_idempotent_upsert(db_session, sample_context):
    state = CampaignState(
        campaign_id="camp_1",
        customer_id="C1",
        started_at=datetime.now(UTC),
        context=sample_context,
    )
    CampaignRepository.save(db_session, state)
    db_session.commit()

    state.completed = True
    CampaignRepository.save(db_session, state)
    db_session.commit()

    roundtripped = CampaignRepository.list_campaigns(db_session, customer_id="C1")
    assert len(roundtripped) == 1
    assert roundtripped[0].completed is True

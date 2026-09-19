"""Top-level entry point: run one outreach campaign for one customer,
route it for human review if needed, audit every stage, and persist the
result.
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from outreachiq.audit import write_audit_entry
from outreachiq.config import settings
from outreachiq.db.repository import CampaignRepository, CustomerRepository
from outreachiq.db.session import get_session, init_db
from outreachiq.models import CampaignState
from outreachiq.routing import evaluate_routing
from outreachiq.workflow import run_crew_for_campaign


def run_campaign(customer_id: str, days_back: int | None = None) -> CampaignState:
    init_db()
    days_back = days_back or settings.thresholds.days_back_default
    campaign_id = f"campaign_{uuid.uuid4().hex[:12]}"

    with get_session() as session:
        context = CustomerRepository.get_context(session, customer_id, days_back)

    if context is None:
        raise ValueError(f"No customer found with id={customer_id!r}")

    try:
        state = run_crew_for_campaign(campaign_id, context)
        state.completed = True
        state.completed_at = datetime.now(UTC)
    except Exception as exc:
        state = CampaignState(
            campaign_id=campaign_id,
            customer_id=customer_id,
            started_at=datetime.now(UTC),
            context=context,
            errors=[str(exc)],
        )

    state = evaluate_routing(state, settings.thresholds)

    write_audit_entry(
        agent="Campaign",
        input_summary={"customer_id": customer_id, "days_back": days_back},
        output=state.model_dump(mode="json"),
        routing_decision="human_review" if state.requires_human_review else "auto_complete",
        warnings=state.review_reasons,
    )

    with get_session() as session:
        CampaignRepository.save(session, state)

    return state

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from outreachiq.db.schema import (
    CampaignRecordORM,
    CustomerProfileORM,
    EngagementORM,
    FeedbackORM,
)
from outreachiq.models import (
    CampaignState,
    CustomerContext,
    CustomerProfile,
    EngagementRecord,
    FeedbackRecord,
)


class CustomerRepository:
    """Read-only access to enrollment, engagement, and feedback data."""

    @staticmethod
    def list_customers(session: Session) -> list[CustomerProfile]:
        rows = session.scalars(select(CustomerProfileORM)).all()
        return [
            CustomerProfile(
                customer_id=row.customer_id,
                name=row.name,
                email=row.email,
                phone=row.phone,
                profession=row.profession,
                field_of_interest=row.field_of_interest,
                date_joined=row.date_joined,
            )
            for row in rows
        ]

    @staticmethod
    def get_context(
        session: Session, customer_id: str, days_back: int
    ) -> CustomerContext | None:
        profile_row = session.get(CustomerProfileORM, customer_id)
        if profile_row is None:
            return None

        cutoff = datetime.now() - timedelta(days=days_back)

        engagement_rows = session.scalars(
            select(EngagementORM).where(
                EngagementORM.customer_id == customer_id,
                EngagementORM.viewed_at >= cutoff,
            )
        ).all()
        feedback_rows = session.scalars(
            select(FeedbackORM).where(
                FeedbackORM.customer_id == customer_id,
                FeedbackORM.created_at >= cutoff,
            )
        ).all()

        last_active_at = max(
            (row.viewed_at for row in engagement_rows), default=None
        )

        return CustomerContext(
            profile=CustomerProfile(
                customer_id=profile_row.customer_id,
                name=profile_row.name,
                email=profile_row.email,
                phone=profile_row.phone,
                profession=profile_row.profession,
                field_of_interest=profile_row.field_of_interest,
                date_joined=profile_row.date_joined,
            ),
            engagements=[
                EngagementRecord(
                    course_title=row.course_title,
                    course_type=row.course_type,
                    view_minutes=row.view_minutes,
                )
                for row in engagement_rows
            ],
            feedback=[
                FeedbackRecord(
                    course_title=row.course_title,
                    question=row.question,
                    answer=row.answer,
                    created_at=row.created_at,
                )
                for row in feedback_rows
            ],
            last_active_at=last_active_at,
            lookback_days=days_back,
        )


class CampaignRepository:
    """Persists campaign state for audit and dashboard display."""

    @staticmethod
    def save(session: Session, state: CampaignState) -> None:
        status = "completed" if state.completed else ("failed" if state.errors else "in_progress")
        existing = session.get(CampaignRecordORM, state.campaign_id)
        if existing is None:
            existing = CampaignRecordORM(campaign_id=state.campaign_id)
            session.add(existing)

        existing.customer_id = state.customer_id
        existing.started_at = state.started_at
        existing.completed_at = state.completed_at
        existing.status = status
        existing.requires_human_review = state.requires_human_review
        existing.state_json = state.model_dump_json()

    @staticmethod
    def list_campaigns(session: Session, customer_id: str | None = None) -> list[CampaignState]:
        query = select(CampaignRecordORM)
        if customer_id:
            query = query.where(CampaignRecordORM.customer_id == customer_id)
        rows = session.scalars(query.order_by(CampaignRecordORM.started_at.desc())).all()
        return [CampaignState.model_validate_json(row.state_json) for row in rows]

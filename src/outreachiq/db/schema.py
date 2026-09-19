from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class CustomerProfileORM(Base):
    __tablename__ = "customer_profiles"

    customer_id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    email: Mapped[str] = mapped_column(String)
    phone: Mapped[str | None] = mapped_column(String, nullable=True)
    profession: Mapped[str] = mapped_column(String, default="")
    field_of_interest: Mapped[str] = mapped_column(String, default="")
    date_joined: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class EngagementORM(Base):
    __tablename__ = "engagements"

    engagement_id: Mapped[str] = mapped_column(String, primary_key=True)
    customer_id: Mapped[str] = mapped_column(String, index=True)
    course_title: Mapped[str] = mapped_column(String)
    course_type: Mapped[str] = mapped_column(String)
    view_minutes: Mapped[float] = mapped_column(Float)
    viewed_at: Mapped[datetime] = mapped_column(DateTime)


class FeedbackORM(Base):
    __tablename__ = "feedback"

    feedback_id: Mapped[str] = mapped_column(String, primary_key=True)
    customer_id: Mapped[str] = mapped_column(String, index=True)
    course_title: Mapped[str] = mapped_column(String)
    question: Mapped[str] = mapped_column(String)
    answer: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime)


class CampaignRecordORM(Base):
    __tablename__ = "campaigns"

    campaign_id: Mapped[str] = mapped_column(String, primary_key=True)
    customer_id: Mapped[str] = mapped_column(String, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String, default="in_progress")
    requires_human_review: Mapped[bool] = mapped_column(Boolean, default=False)
    state_json: Mapped[str] = mapped_column(Text)

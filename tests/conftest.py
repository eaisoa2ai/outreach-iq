from __future__ import annotations

from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from outreachiq.db.schema import Base, CustomerProfileORM, EngagementORM, FeedbackORM
from outreachiq.models import CustomerContext, CustomerProfile


@pytest.fixture()
def db_session():
    """An isolated in-memory SQLite session, independent of the app's configured database."""
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, future=True)
    session: Session = TestSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def seeded_customer(db_session):
    profile = CustomerProfileORM(
        customer_id="C1",
        name="Ada Lovelace",
        email="ada@example.com",
        phone="+15551234567",
        profession="Data Scientist",
        field_of_interest="Machine Learning",
        date_joined=datetime(2025, 1, 1),
    )
    db_session.add(profile)
    db_session.add(
        EngagementORM(
            engagement_id="E1",
            customer_id="C1",
            course_title="Intro to ML",
            course_type="course",
            view_minutes=42.0,
            viewed_at=datetime.now(),
        )
    )
    db_session.add(
        FeedbackORM(
            feedback_id="F1",
            customer_id="C1",
            course_title="Intro to ML",
            question="How was the pacing?",
            answer="Good.",
            created_at=datetime.now(),
        )
    )
    db_session.commit()
    return "C1"


@pytest.fixture()
def sample_context() -> CustomerContext:
    return CustomerContext(
        profile=CustomerProfile(
            customer_id="C1",
            name="Ada Lovelace",
            email="ada@example.com",
            phone="+15551234567",
        ),
        engagements=[],
        feedback=[],
    )

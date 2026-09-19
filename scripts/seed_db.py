"""Loads data/seed/*.csv into the configured database. Idempotent — skips a
table that already has rows.

Run with: uv run python scripts/seed_db.py
"""
from __future__ import annotations

from datetime import datetime

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

from outreachiq.config import PROJECT_ROOT  # noqa: E402
from outreachiq.db.schema import CustomerProfileORM, EngagementORM, FeedbackORM  # noqa: E402
from outreachiq.db.session import SessionLocal, init_db  # noqa: E402

SEED_DIR = PROJECT_ROOT / "data" / "seed"


def _parse_dt(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")


def load_customers(session) -> None:
    if session.query(CustomerProfileORM).count() > 0:
        print("customer_profiles already populated, skipping.")
        return
    df = pd.read_csv(SEED_DIR / "customers.csv", dtype=str).fillna("")
    for _, row in df.iterrows():
        session.add(
            CustomerProfileORM(
                customer_id=row["customer_id"],
                name=row["customer_name"],
                email=row["customer_email"],
                phone=row["phone_number"] or None,
                profession=row["profession"],
                field_of_interest=row["field_of_interest"],
                date_joined=_parse_dt(row["date_joined"]),
            )
        )
    print(f"Loaded {len(df)} customer profiles.")


def load_engagements(session) -> None:
    if session.query(EngagementORM).count() > 0:
        print("engagements already populated, skipping.")
        return
    df = pd.read_csv(SEED_DIR / "engagements.csv", dtype=str)
    for _, row in df.iterrows():
        session.add(
            EngagementORM(
                engagement_id=row["engage_id"],
                customer_id=row["customer_id"],
                course_title=row["course_title"],
                course_type=row["course_type"],
                view_minutes=float(row["view_time"]),
                viewed_at=_parse_dt(row["date_viewed"]),
            )
        )
    print(f"Loaded {len(df)} engagement rows.")


def load_feedback(session) -> None:
    if session.query(FeedbackORM).count() > 0:
        print("feedback already populated, skipping.")
        return
    df = pd.read_csv(SEED_DIR / "feedback.csv", dtype=str)
    for _, row in df.iterrows():
        session.add(
            FeedbackORM(
                feedback_id=row["feedback_id"],
                customer_id=row["customer_id"],
                course_title=row["course_title"],
                question=row["question"],
                answer=row["answer"],
                created_at=_parse_dt(row["date_created"]),
            )
        )
    print(f"Loaded {len(df)} feedback rows.")


def main() -> None:
    init_db()
    session = SessionLocal()
    try:
        load_customers(session)
        load_engagements(session)
        load_feedback(session)
        session.commit()
    finally:
        session.close()
    print("Seed complete.")


if __name__ == "__main__":
    main()

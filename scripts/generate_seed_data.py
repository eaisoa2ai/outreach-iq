"""Generates fully synthetic sample data into data/seed/*.csv.

Deterministic (fixed seed) so the committed CSVs are reproducible. No real
customer data is used anywhere in this project — every name, email, and
phone number here is fabricated.

Run with: uv run python scripts/generate_seed_data.py
"""
from __future__ import annotations

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

SEED_DIR = Path(__file__).resolve().parents[1] / "data" / "seed"
RNG = random.Random(42)

FIRST_NAMES = [
    "Trisha", "Karan", "Daniel", "Traci", "Amara", "Ivan", "Priya", "Marcus",
    "Sofia", "Noah", "Leila", "Owen", "Yuki", "Diego", "Grace",
]
LAST_NAMES = [
    "Brooks", "Mehta", "Allen", "Smith", "Okafor", "Petrov", "Iyer", "Chen",
    "Rossi", "Baker", "Haddad", "Murphy", "Tanaka", "Alvarez", "Kim",
]
PROFESSIONS = ["Learner", "Data Scientist", "Data Analyst", "Software Engineer", "Product Manager"]
FIELDS = ["Data Science", "Big Data", "Machine Learning", "Data Engineering", "MLOps"]
COURSES = [
    ("Intro to Machine Learning", "course"),
    ("Advanced SQL for Analytics", "course"),
    ("Building Data Pipelines", "project"),
    ("Deep Learning Fundamentals", "course"),
    ("End-to-End MLOps", "project"),
    ("Natural Language Processing", "course"),
    ("Time Series Forecasting", "project"),
]
FEEDBACK_QA = [
    ("How would you rate the pacing of this course?", "A bit fast in the middle sections."),
    ("What would you like to see more of?", "More real-world case studies."),
    ("Did the project meet your expectations?", "Yes, especially the deployment section."),
    ("Any blockers you ran into?", "Environment setup took longer than expected."),
]

NUM_CUSTOMERS = 18


def random_date(days_back_max: int) -> datetime:
    return datetime.now() - timedelta(
        days=RNG.randint(0, days_back_max), hours=RNG.randint(0, 23), minutes=RNG.randint(0, 59)
    )


def build_customers() -> list[dict]:
    customers = []
    for i in range(NUM_CUSTOMERS):
        first, last = RNG.choice(FIRST_NAMES), RNG.choice(LAST_NAMES)
        customer_id = f"C{100 + i}"
        # A couple of customers intentionally have no phone on file, to exercise
        # the "skip call, still email" routing path.
        phone = "" if i in (4, 11) else f"+1{RNG.randint(2000000000, 9999999999)}"
        customers.append(
            {
                "customer_id": customer_id,
                "customer_name": f"{first} {last}",
                "customer_email": f"{first.lower()}.{last.lower()}{i}@example.com",
                "phone_number": phone,
                "date_joined": random_date(400).strftime("%Y-%m-%d %H:%M:%S"),
                "profession": RNG.choice(PROFESSIONS),
                "field_of_interest": RNG.choice(FIELDS),
            }
        )
    return customers


def build_engagements(customers: list[dict]) -> list[dict]:
    rows = []
    engage_id = 0
    for customer in customers:
        for _ in range(RNG.randint(0, 6)):
            engage_id += 1
            title, course_type = RNG.choice(COURSES)
            rows.append(
                {
                    "engage_id": f"E{engage_id:05d}",
                    "customer_id": customer["customer_id"],
                    "course_title": title,
                    "course_type": course_type,
                    "view_time": round(RNG.uniform(5, 120), 1),
                    "date_viewed": random_date(45).strftime("%Y-%m-%d %H:%M:%S"),
                }
            )
    return rows


def build_feedback(customers: list[dict]) -> list[dict]:
    rows = []
    feedback_id = 0
    for customer in customers:
        for _ in range(RNG.randint(0, 2)):
            feedback_id += 1
            title, _ = RNG.choice(COURSES)
            question, answer = RNG.choice(FEEDBACK_QA)
            rows.append(
                {
                    "feedback_id": f"F{feedback_id:05d}",
                    "customer_id": customer["customer_id"],
                    "course_title": title,
                    "question": question,
                    "answer": answer,
                    "date_created": random_date(45).strftime("%Y-%m-%d %H:%M:%S"),
                }
            )
    return rows


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    customers = build_customers()
    engagements = build_engagements(customers)
    feedback = build_feedback(customers)

    write_csv(
        SEED_DIR / "customers.csv",
        customers,
        ["customer_id", "customer_name", "customer_email", "phone_number", "date_joined", "profession", "field_of_interest"],
    )
    write_csv(
        SEED_DIR / "engagements.csv",
        engagements,
        ["engage_id", "customer_id", "course_title", "course_type", "view_time", "date_viewed"],
    )
    write_csv(
        SEED_DIR / "feedback.csv",
        feedback,
        ["feedback_id", "customer_id", "course_title", "question", "answer", "date_created"],
    )
    print(f"Wrote {len(customers)} customers, {len(engagements)} engagements, {len(feedback)} feedback rows to {SEED_DIR}")


if __name__ == "__main__":
    main()

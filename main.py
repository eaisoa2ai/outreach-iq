"""Entry point: run one outreach campaign from the command line.

    uv run python main.py --customer-id C001
    uv run python main.py --customer-id C001 --days-back 60
"""
from __future__ import annotations

import argparse
import json
import sys

from dotenv import load_dotenv

load_dotenv()  # must run before importing anything that reads env-backed settings

from outreachiq.campaign import run_campaign  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run an OutreachIQ campaign for one customer.")
    parser.add_argument("--customer-id", required=True, help="Customer ID from the seeded database")
    parser.add_argument("--days-back", type=int, default=None, help="Lookback window in days")
    args = parser.parse_args()

    print(f"Starting outreach campaign for customer {args.customer_id}...")
    try:
        state = run_campaign(args.customer_id, days_back=args.days_back)
    except ValueError as exc:
        print(f"Error: {exc}")
        print("Tip: run `uv run python scripts/seed_db.py` first to load the sample dataset.")
        return 1

    print("\n=== Campaign Summary ===")
    print(f"Campaign ID: {state.campaign_id}")
    print(f"Completed: {state.completed}")
    if state.guidance:
        print(f"Call goal: {state.guidance.goal}")
    if state.call_analysis:
        print(f"Call outcome: {state.call_analysis.outcome.value}")
    if state.email_outcome:
        print(f"Email: {state.email_outcome.status} — \"{state.email_outcome.subject}\"")
    print(f"Requires human review: {state.requires_human_review}")
    if state.review_reasons:
        print("Reasons:")
        for reason in state.review_reasons:
            print(f"  - {reason}")
    if state.errors:
        print(f"Errors: {state.errors}")

    print("\nFull state:")
    print(json.dumps(state.model_dump(mode="json"), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

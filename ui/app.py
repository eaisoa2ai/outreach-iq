"""Single-page Gradio dashboard: pick a customer, run a campaign, see every
agent's output plus the routing decision and audit trail on one screen.

Run with: uv run python ui/app.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import gradio as gr  # noqa: E402

from outreachiq.audit import read_audit_trail  # noqa: E402
from outreachiq.campaign import run_campaign  # noqa: E402
from outreachiq.db.repository import CustomerRepository  # noqa: E402
from outreachiq.db.session import get_session, init_db  # noqa: E402


def list_customer_choices() -> list[str]:
    init_db()
    with get_session() as session:
        customers = CustomerRepository.list_customers(session)
    return [f"{c.customer_id} — {c.name}" for c in customers]


def run(customer_choice: str, days_back: int):
    if not customer_choice:
        return "Pick a customer first.", "", "", "", "", "{}"

    customer_id = customer_choice.split(" — ")[0]
    try:
        state = run_campaign(customer_id, days_back=int(days_back))
    except Exception as exc:
        return f"Campaign failed: {exc}", "", "", "", "", "{}"

    guidance_md = "_No guidance produced._"
    if state.guidance:
        g = state.guidance
        guidance_md = (
            f"**Goal:** {g.goal}\n\n"
            f"**Key points:**\n" + "\n".join(f"- {p}" for p in g.key_points) + "\n\n"
            f"**Question:** {g.open_question}\n\n"
            f"**Next step:** {g.next_step}\n\n"
            f"_Confidence: {g.confidence:.2f}_"
        )

    call_md = "_No call analysis produced._"
    if state.call_analysis:
        c = state.call_analysis
        call_md = (
            f"**Outcome:** {c.outcome.value}\n\n"
            f"**Transcript:**\n```\n{c.transcript or '(none)'}\n```\n\n"
            f"**Email guidance given to email agent:** {c.email_guidance}"
        )

    email_md = "_No email produced._"
    if state.email_outcome:
        e = state.email_outcome
        email_md = f"**Subject:** {e.subject}\n\n**Status:** {e.status}\n\n---\n\n{e.html_body}"

    review_md = "No human review required."
    if state.requires_human_review:
        review_md = "**Flagged for human review:**\n" + "\n".join(f"- {r}" for r in state.review_reasons)

    audit_trail = read_audit_trail()[-5:]
    audit_json = json.dumps(audit_trail, indent=2)

    summary = f"Campaign `{state.campaign_id}` completed: {state.completed}"
    return summary, guidance_md, call_md, email_md, review_md, audit_json


with gr.Blocks(title="OutreachIQ") as demo:
    gr.Markdown("# OutreachIQ — AI Customer Outreach Dashboard")
    gr.Markdown(
        "Pick a seeded customer and run a full campaign: insight generation, "
        "a simulated voice call, outcome analysis, and a follow-up email — "
        "all through mock providers by default, so this runs with just an OpenAI key."
    )

    with gr.Row():
        customer_dropdown = gr.Dropdown(
            choices=list_customer_choices(), label="Customer", scale=3
        )
        days_back_input = gr.Number(value=30, label="Days back", precision=0, scale=1)
        run_button = gr.Button("Run Campaign", variant="primary", scale=1)

    summary_output = gr.Markdown()

    with gr.Row():
        guidance_output = gr.Markdown(label="Call Guidance")
        call_output = gr.Markdown(label="Call Analysis")
        email_output = gr.Markdown(label="Follow-up Email")

    review_output = gr.Markdown(label="Routing Decision")
    audit_output = gr.Code(label="Recent Audit Trail (JSONL tail)", language="json")

    run_button.click(
        run,
        inputs=[customer_dropdown, days_back_input],
        outputs=[summary_output, guidance_output, call_output, email_output, review_output, audit_output],
    )

if __name__ == "__main__":
    demo.launch()

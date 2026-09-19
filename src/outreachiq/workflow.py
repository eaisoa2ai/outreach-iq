"""Builds the CrewAI crew and turns its typed task outputs into a CampaignState.

Deliberately does not use a shared mutable state object across tools (the
source pattern this project moved away from) — each task declares
`output_pydantic`, CrewAI validates the LLM's output against that schema, and
this module just reads `task.output.pydantic` after `crew.kickoff()`.
"""
from __future__ import annotations

from datetime import UTC, datetime

from crewai import LLM, Crew, Process

from outreachiq.agents.call_agent import build_call_agent, build_call_task
from outreachiq.agents.decision_agent import build_decision_agent, build_decision_task
from outreachiq.agents.email_agent import build_email_agent, build_email_task
from outreachiq.agents.insight_agent import build_insight_agent, build_insight_task
from outreachiq.config import settings
from outreachiq.models import CampaignState, CustomerContext


def build_llm() -> LLM:
    if not settings.openai_api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Add it to your .env — the agents need it to reason "
            "and write text even though calling/emailing run against mock providers by default."
        )
    return LLM(model=settings.openai_model, temperature=0.3, api_key=settings.openai_api_key)


def run_crew_for_campaign(campaign_id: str, context: CustomerContext) -> CampaignState:
    llm = build_llm()

    insight_agent = build_insight_agent(llm)
    call_agent = build_call_agent(llm)
    decision_agent = build_decision_agent(llm)
    email_agent = build_email_agent(llm)

    insight_task = build_insight_task(insight_agent, context)
    call_task = build_call_task(call_agent, context.profile, insight_task)
    decision_task = build_decision_task(decision_agent, insight_task, call_task)
    email_task = build_email_task(email_agent, context.profile, insight_task, decision_task)

    crew = Crew(
        agents=[insight_agent, call_agent, decision_agent, email_agent],
        tasks=[insight_task, call_task, decision_task, email_task],
        process=Process.sequential,
        verbose=True,
    )
    crew.kickoff()

    return CampaignState(
        campaign_id=campaign_id,
        customer_id=context.profile.customer_id,
        started_at=datetime.now(UTC),
        context=context,
        guidance=insight_task.output.pydantic,
        call_initiation=call_task.output.pydantic,
        call_analysis=decision_task.output.pydantic,
        email_outcome=email_task.output.pydantic,
    )

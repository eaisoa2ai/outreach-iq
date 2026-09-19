from __future__ import annotations

from collections.abc import Callable

from crewai import LLM, Agent, Task

from outreachiq.agents.prompts import INSIGHT_AGENT_BACKSTORY
from outreachiq.models import CallGuidance, CustomerContext


def build_insight_agent(llm: LLM) -> Agent:
    return Agent(
        role="Customer Insight Strategist",
        goal="Turn a customer's activity data into a short, actionable call guidance script.",
        backstory=INSIGHT_AGENT_BACKSTORY,
        tools=[],
        llm=llm,
        allow_delegation=False,
        verbose=True,
    )


def build_insight_task(
    agent: Agent, context: CustomerContext, on_complete: Callable | None = None
) -> Task:
    profile = context.profile
    engagement_lines = "\n".join(
        f"- {e.course_title} ({e.course_type}): {e.view_minutes:.0f} min"
        for e in context.engagements
    ) or "- No engagement recorded in the lookback window"
    feedback_lines = "\n".join(
        f"- Q: {f.question} | A: {f.answer}" for f in context.feedback
    ) or "- No feedback recorded in the lookback window"

    description = f"""Analyze this customer's data and produce call guidance.

Customer: {profile.name} ({profile.profession or "profession unknown"})
Field of interest: {profile.field_of_interest or "unknown"}
Last active: {context.last_active_at or "unknown"}

Recent engagement (last {context.lookback_days} days):
{engagement_lines}

Recent feedback (last {context.lookback_days} days):
{feedback_lines}

Produce:
- goal: one sentence describing the point of this call
- key_points: 2-3 talking points, each referencing a specific fact above
- open_question: one personalized, open-ended question to ask
- next_step: one concrete recommendation or call to action

Set confidence based on how much real signal you had to work with — if
engagement and feedback are both empty, confidence should be low and you
must say so in warnings rather than inventing detail."""

    return Task(
        description=description,
        agent=agent,
        expected_output="A CallGuidance object with goal, key_points, open_question, and next_step.",
        output_pydantic=CallGuidance,
        callback=on_complete,
    )

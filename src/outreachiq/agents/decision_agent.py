from __future__ import annotations

from collections.abc import Callable

from crewai import LLM, Agent, Task

from outreachiq.agents.prompts import DECISION_AGENT_BACKSTORY
from outreachiq.agents.tools import check_call_status_tool, fetch_transcript_tool
from outreachiq.models import CallAnalysis


def build_decision_agent(llm: LLM) -> Agent:
    return Agent(
        role="Call Outcome Analyst",
        goal="Determine exactly how the call went and what the follow-up email should say.",
        backstory=DECISION_AGENT_BACKSTORY,
        tools=[check_call_status_tool, fetch_transcript_tool],
        llm=llm,
        allow_delegation=False,
        verbose=True,
    )


def build_decision_task(
    agent: Agent, insight_task: Task, call_task: Task, on_complete: Callable | None = None
) -> Task:
    description = """Using the call initiation result from the previous task:

1. If the call was skipped or failed to initiate, set outcome accordingly
   (there is nothing to poll) and set email_guidance to explain the
   situation without referencing a call that never happened.
2. Otherwise, call "Wait for call outcome" with the conversation_id and wait
   for it to return a terminal outcome (completed, failed, did_not_pick, or
   error).
3. If the outcome is "completed", call "Fetch call transcript" and use it to
   ground your email_guidance in what was actually said.
4. Write email_guidance as instructions for the email agent — not a full
   email — covering: what tone to use, what to reference from the call (or
   the fact there was no call), and what the ask should be.

Always report outcome as exactly one of: completed, failed, did_not_pick,
error, not_attempted."""

    return Task(
        description=description,
        agent=agent,
        expected_output="A CallAnalysis with outcome, raw_status, transcript, and email_guidance.",
        output_pydantic=CallAnalysis,
        context=[insight_task, call_task],
        callback=on_complete,
    )

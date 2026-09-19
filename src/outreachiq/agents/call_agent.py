from __future__ import annotations

from crewai import LLM, Agent, Task

from outreachiq.agents.prompts import CALL_AGENT_BACKSTORY
from outreachiq.agents.tools import make_call_tool
from outreachiq.models import CallInitiationResult, CustomerProfile


def build_call_agent(llm: LLM) -> Agent:
    return Agent(
        role="Outbound Call Specialist",
        goal="Place one outbound call per customer using the prepared call guidance.",
        backstory=CALL_AGENT_BACKSTORY,
        tools=[make_call_tool],
        llm=llm,
        allow_delegation=False,
        verbose=True,
    )


def build_call_task(agent: Agent, profile: CustomerProfile, insight_task: Task) -> Task:
    if not profile.phone:
        description = f"""The customer {profile.name} has no phone number on file.
Do not call the tool. Report status "skipped" with confidence 1.0 and a
warning explaining that no phone number was available."""
    else:
        description = f"""Using the call guidance from the previous task, place an
outbound call to {profile.name} at {profile.phone}.

Call the "Initiate outbound call" tool exactly once with:
- customer_name: "{profile.name}"
- phone: "{profile.phone}"
- guidance_text: the key_points and open_question from the call guidance, joined into one string

Report the tool's status and conversation_id verbatim — do not guess an
outcome yourself, the next agent will determine that."""

    return Task(
        description=description,
        agent=agent,
        expected_output="A CallInitiationResult with status and conversation_id (if any).",
        output_pydantic=CallInitiationResult,
        context=[insight_task],
    )

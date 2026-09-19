from __future__ import annotations

from collections.abc import Callable

from crewai import LLM, Agent, Task

from outreachiq.agents.prompts import EMAIL_AGENT_BACKSTORY
from outreachiq.agents.tools import send_email_tool
from outreachiq.models import CustomerProfile, EmailOutcome

EMAIL_SIGNATURE = "<p>Best regards,<br>Alex, OutreachIQ</p>"


def build_email_agent(llm: LLM) -> Agent:
    return Agent(
        role="Follow-Up Email Specialist",
        goal="Write and send one follow-up email that matches exactly what happened on the call.",
        backstory=EMAIL_AGENT_BACKSTORY,
        tools=[send_email_tool],
        llm=llm,
        allow_delegation=False,
        verbose=True,
    )


def build_email_task(
    agent: Agent,
    profile: CustomerProfile,
    insight_task: Task,
    decision_task: Task,
    on_complete: Callable | None = None,
) -> Task:
    description = f"""Using the call guidance and call analysis from the previous
tasks, write a follow-up email to {profile.name} ({profile.email}) and send
it with the "Send follow-up email" tool.

- Match the tone and content to the actual outcome (completed / failed /
  did_not_pick / error / not_attempted) — never reference a conversation
  that didn't happen.
- Choose a subject line that reflects the outcome.
- End the email body with exactly this signature: {EMAIL_SIGNATURE}
- Call the tool exactly once with recipient_email="{profile.email}".
- The tool may return status "blocked" if the content fails an automated
  safety check (e.g. an unfilled template placeholder, or an unauthorized
  offer/discount). If that happens, do not retry with different wording to
  get around it — report status "blocked" honestly along with the
  violations the tool returned.
- Report the subject, html_body, and the tool's status/message id back."""

    return Task(
        description=description,
        agent=agent,
        expected_output="An EmailOutcome with subject, html_body, status, and provider_message_id.",
        output_pydantic=EmailOutcome,
        context=[insight_task, decision_task],
        callback=on_complete,
    )

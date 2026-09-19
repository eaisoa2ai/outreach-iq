"""Typed contracts for every value that moves between agents.

No agent may pass a bare string or dict to another agent or to persistence —
every input and output here is a Pydantic model. `AgentOutput` is the base
every agent result extends, so confidence, evidence, and warnings are always
available for routing decisions and the audit trail.
"""
from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, EmailStr, Field


class CallOutcome(StrEnum):
    NOT_ATTEMPTED = "not_attempted"
    COMPLETED = "completed"
    FAILED = "failed"
    DID_NOT_PICK = "did_not_pick"
    ERROR = "error"


class AgentOutput(BaseModel):
    """Common contract every agent output satisfies."""

    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)
    reasoning_summary: str
    warnings: list[str] = Field(default_factory=list)


# --- Customer data -----------------------------------------------------------


class CustomerProfile(BaseModel):
    customer_id: str
    name: str
    email: EmailStr
    phone: str | None = None
    profession: str = ""
    field_of_interest: str = ""
    date_joined: datetime | None = None


class EngagementRecord(BaseModel):
    course_title: str
    course_type: str
    view_minutes: float


class FeedbackRecord(BaseModel):
    course_title: str
    question: str
    answer: str
    created_at: datetime


class CustomerContext(BaseModel):
    """Everything downstream agents need about one customer, assembled once."""

    profile: CustomerProfile
    engagements: list[EngagementRecord] = Field(default_factory=list)
    feedback: list[FeedbackRecord] = Field(default_factory=list)
    last_active_at: datetime | None = None
    lookback_days: int = 30


# --- Agent outputs -------------------------------------------------------------


class CallGuidance(AgentOutput):
    goal: str
    key_points: list[str]
    open_question: str
    next_step: str


class CallInitiationResult(AgentOutput):
    status: str  # "initiated" | "failed" | "skipped"
    conversation_id: str | None = None
    provider_call_id: str | None = None
    initiated_at: datetime | None = None


class CallAnalysis(AgentOutput):
    """Decision agent's read on how the call went and what the email should do."""

    outcome: CallOutcome
    raw_status: str
    transcript: str = ""
    email_guidance: str


class EmailOutcome(AgentOutput):
    """The email agent both drafts and sends within one task, so its result
    carries the content that was sent alongside the delivery outcome."""

    subject: str
    html_body: str
    status: str  # "sent" | "failed" | "skipped"
    provider_message_id: str | None = None
    sent_at: datetime | None = None


# --- Campaign state ------------------------------------------------------------


class CampaignState(BaseModel):
    """The full, typed record of one outreach campaign run for one customer."""

    campaign_id: str
    customer_id: str
    started_at: datetime
    context: CustomerContext

    guidance: CallGuidance | None = None
    call_initiation: CallInitiationResult | None = None
    call_analysis: CallAnalysis | None = None
    email_outcome: EmailOutcome | None = None

    requires_human_review: bool = False
    review_reasons: list[str] = Field(default_factory=list)

    errors: list[str] = Field(default_factory=list)
    completed: bool = False
    completed_at: datetime | None = None

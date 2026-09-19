# Case study: from this repo to a real client engagement

This repo is a reference architecture, built and tested end-to-end with mock
providers. This document is the other half of that story: **how an AI
Solution Architect would actually take this from a working demo to a live
system for a paying client**, using a retail scenario as the running
example. Every phase below maps to something concrete already in this
codebase — that mapping is the point.

**Scenario:** "NorthStar Retail" wants to re-engage lapsed loyalty members
and recover abandoned high-value carts. Today, a call center team manually
dials a spreadsheet of names with no personalization and no way to measure
what's working.

## 1. Discovery and business case

Before any architecture gets drawn, you sit with stakeholders — marketing,
customer service ops, legal/compliance, IT — and pin down:

- **What does the current process cost?** e.g., agents spend ~15 minutes per
  call, at a known cost, for a known conversion rate.
- **What does success look like, as a number?** Re-engagement rate lift,
  revenue recovered per campaign, cost per contact — not "AI agents are
  cool."
- **What's off-limits?** No unauthorized discounts, no contacting anyone on
  a do-not-call list, calls only within permitted hours (TCPA), CAN-SPAM
  compliance on email.

*Maps to:* the [Cost model](README.md#cost-model) and
[Data governance and compliance](README.md#data-governance-and-compliance)
sections exist because a real engagement starts with these questions, not
with code.

## 2. Current-state and data assessment

You audit what actually exists: CRM (Salesforce/Shopify), loyalty platform,
order/POS history, the existing contact center platform (Five9/Genesys/
Twilio Flex), the email platform (SendGrid/Marketing Cloud), and — critically
— data quality. Is consent tracked anywhere? Are phone numbers verified? A
very common finding: customer history lives in three systems that don't
talk to each other.

*Maps to:* `CustomerRepository.get_context()` — in the demo it reads three
CSVs; in production it becomes a real integration layer against the
client's actual systems, behind the exact same typed interface.

## 3. Solution architecture design

This is where the interfaces in this repo pay off directly — the same
agent logic, pointed at different infrastructure:

| This repo | Retail production mapping |
|---|---|
| `VoiceProvider` interface | `MockVoiceProvider` / `ElevenLabsVoiceProvider` become the client's actual Five9 or Twilio Flex integration — zero agent code changes |
| `EmailProvider` interface | Gmail becomes SendGrid or Marketing Cloud |
| `CustomerRepository` | CSV loader becomes a real integration against Salesforce + the order/POS system |
| `AgentOutput` (confidence / evidence / warnings) | Same contract; "evidence" now cites real purchase history instead of course engagement |
| `evaluate_routing()` | Extended with retail-specific rules: no discount without merchandising sign-off, no contact during an open support ticket |

You present this as an architecture diagram to stakeholders — the same
shape as [the one in the README](README.md#architecture), with the
client's systems in the boxes instead of the demo's.

## 4. Non-functional requirements

Retail is a scale-and-seasonality problem in a way a demo isn't: "500,000
lapsed customers, campaign must complete before Black Friday, peak
concurrency during a flash sale." This turns the
[target production architecture](README.md#target-production-architecture)
— queue, worker pool, Postgres — from aspirational into a sized spec against
a real SLA and real volume.

## 5. Proof of concept, on mock providers first

You do not call real customers on day one. You run the pipeline against a
held-out sample with mock providers — exactly the demo's default setup —
to validate the *logic*: does the Insight Agent produce sensible guidance
from real purchase data? Does routing flag the right cases? This de-risks
the pilot before a single dollar is spent on real calls or emails.

*Maps to:* the mock-first provider architecture wasn't built for
convenience — it's how you'd actually validate an agent pipeline before it
touches a client's customers or budget.

## 6. Guardrails and compliance sign-off

Before any real customer is contacted, legal and compliance review and sign
off on the guardrail rules: consent verification before a call, do-not-call
list checks, permitted calling hours, and — concretely — the same pattern as
[`check_outgoing_email_content`](src/outreachiq/guardrails.py): no email
goes out promising a discount unless that specific offer was authorized by
marketing for that campaign. In a real engagement this list is much longer
than this repo's four checks, and it's usually where the project timeline
actually lives or dies — not the ML.

## 7. Pilot with real providers, small and controlled

Real ElevenLabs/Twilio and real SendGrid, but scoped — one segment (say,
2,000 customers) with a held-out control group, so lift is measurable, not
just "the AI completed some campaigns." Every campaign `evaluate_routing()`
flags goes to a human review queue: a pilot needs a human safety net while
trust in the system is still being built.

## 8. Build-out, integration, and testing

Real integration work: auth against the client's CRM API, webhook/event
handling instead of batch CSVs, load testing at real volume, and — most
importantly — UAT where the marketing/CS team actually uses the dashboard
(this repo's Gradio UI, upgraded with real auth for production) to review
flagged campaigns and give feedback on tone and guidance quality.

## 9. Phased rollout

Canary at 1% of the target segment, then 10%, then full, with the ability
to kill the campaign and fall back to the manual process at any point. This
is a standard SRE pattern, and it's exactly why
["human review is a terminal flag, not a resumable checkpoint"](README.md#system-design-and-trade-offs)
matters in production: campaigns need to complete and be auditable, not
silently hang waiting for approval, while confidence in the system is still
being built.

## 10. Monitoring, iteration, and governance

Post-launch, the [OpenTelemetry tracing](README.md#observability) built
into this repo stops being a nice-to-have and becomes load-bearing:
dashboards on cost per campaign, confidence-vs-actual-outcome calibration
(does a stated 0.9 confidence actually correlate with a good outcome?), and
a regular review of what's getting flagged and why, feeding back into
prompt and guardrail iteration. This is also when the retention and
right-to-erasure jobs described in
[Data governance and compliance](README.md#data-governance-and-compliance)
go from "designed for" to "actually running," because by this point real
PII is flowing through the system.

## What this demonstrates

Every item in this repo's [Limitations and possible extensions](README.md#limitations-and-possible-extensions)
section is, in a real engagement, the actual next phase of work — the demo
proves the design is sound before a client's budget is spent proving it at
scale. That is the intended reading of this project: not a finished
product, but a reference architecture with the trade-offs, guardrails, and
observability already in place to make phases 4 through 10 additive rather
than a rewrite.

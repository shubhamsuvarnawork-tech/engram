# Engram

*organizational memory, made executable*

**A living operating system that learns how a company makes decisions and compiles
that knowledge into executable, provenance-linked skills AI agents can run safely.**

LLMs are becoming a commodity; company knowledge is not. Most of that knowledge
isn't in documents — it lives in *decisions*: the refund that gets auto-approved,
the incident that gets escalated, the discount that needs VP sign-off. Glean,
Notion AI, Guru and Copilot **retrieve** that knowledge. Engram goes one
step further and **compiles it into something an agent can execute**.

This repository is a runnable MVP of the vertical slice that proves the core
idea, with the **Skill Generation Engine** as the centerpiece.

---

## The slice this MVP proves

```
  raw policy prose
        │  (1) extraction  — LLM turns prose into structured decisions
        ▼
  Knowledge / Decision Graph        (Neo4j in prod · in-memory for tests/demo)
        │  (2) SKILL GENERATION  ◀── the moat: graph → executable workflow
        ▼
  Skill  (JSON: inputs · fetch→decide→act steps · guards · provenance · confidence)
        │  (3) agent runtime
        ▼
  Execution  ──► auto-run when safe  ──► PAUSE for human when a guard/approval fires
        │  (4) human override
        ▼
  Learning loop  — the correction is written back, lowering the decision's
                   confidence and flagging it for review (organizational memory)
```

Everything runs **offline by default** (a mock extractor + an in-memory graph +
mocked connectors), so you can see the whole loop end-to-end with zero services.

---

## Quickstart

### See it run in 10 seconds (no services needed)

```bash
cd backend
pip install -r requirements.txt
PYTHONPATH=. python -m app.seed.demo      # the full slice, narrated
PYTHONPATH=. pytest                        # 20 tests, all green
```

The demo ingests a sample refund policy, compiles it into a `refund_customer`
skill, then runs it for four customers — showing an auto-approval, a fraud
escalation, a guard-triggered approval on a large refund, and a human override
that feeds back into the brain.

### Run the full stack

```bash
cp .env.example .env
docker compose up --build
# API docs:  http://localhost:8000/docs
# Frontend:  http://localhost:3000   (click "Ingest + Generate")
```

Compose wires up Postgres, Neo4j, Redis, the FastAPI backend, and the Next.js
frontend. Set `GRAPH_BACKEND=neo4j` (compose does this) to move the graph from
the in-memory store to Neo4j with no code change. Set `ANTHROPIC_API_KEY` to
swap the mock extractor for the real Claude-backed one.

---

## Why the Skill Generation Engine is the moat

Retrieval shows you the policy. This engine **compiles** the decision into a
deterministic, ordered, *runnable* workflow (`backend/app/skills/generator.py`):

1. **resolve** the entry decision for a goal (e.g. `refund_customer`),
2. **collect** any chained decisions,
3. emit one **fetch** step per variable a decision needs — discovering the
   skill's required **inputs** from `{{placeholder}}` references,
4. emit the **decision** step(s),
5. emit one **action** step per outcome,
6. distill **guards** (conditional human-in-the-loop gates) from Exception nodes,
7. **score** confidence & freshness from the source nodes' trust and staleness,
8. **validate** that the order is safe — fetches before decisions before actions,
   and no decision consumes a variable that wasn't produced first.

The output is **provenance-linked** (it knows exactly which knowledge nodes and
sources it came from) and **confidence-scored** (so the runtime knows what is
safe to automate vs. gate). That auditability is what makes "AI runs the
company" defensible instead of reckless.

### The compiled `refund_customer` skill (abridged)

```jsonc
{
  "name": "refund_customer",
  "inputs": [{ "name": "customer_id" }],          // discovered from the graph
  "steps": [
    { "type": "data_fetch", "tool": "billing.get_subscription", "produces": "subscription_months" },
    { "type": "data_fetch", "tool": "crm.get_customer",        "produces": "ltv" },
    { "type": "data_fetch", "tool": "support.get_history",     "produces": "risk_flags" },
    { "type": "data_fetch", "tool": "billing.get_open_refund", "produces": "refund_amount" },
    { "type": "decision",   "decision_ref": "…", "produces": "decision" },
    { "type": "action", "action": "escalate_to_finance", "requires_approval": true },
    { "type": "action", "action": "approve_refund",      "requires_approval": false },
    { "type": "action", "action": "manual_review",       "requires_approval": true }
  ],
  "guards": [
    { "description": "Refunds ≥ $5,000 need Finance approval",
      "action": "approve_refund", "condition": { "var": "refund_amount", "op": "gte", "value": 5000 } }
  ],
  "confidence": 0.81,
  "provenance": { "sources": ["notion://wiki/refund-policy"], "node_ids": ["…"] }
}
```

---

## Repository layout

```
backend/
  app/
    graph/        schema, DecisionRule (executable decisions), GraphStore
                  (InMemory + Neo4j), confidence/freshness scoring
    extraction/   LLMClient (Mock + Anthropic) and the graph materializer
    skills/       Skill models + the Skill Generation Engine  ◀── start here
    runtime/      executor (with HITL), mock connector registry, learning loop
    db/           SQLAlchemy models + session (Postgres / SQLite)
    api/          FastAPI app + routes
    seed/         sample policy + narrated end-to-end demo
  tests/          20 tests: generator, executor, extractor, API
frontend/         Next.js + TS + Tailwind: dashboard, skill viewer, executions
infra/k8s/        reference Kubernetes manifests
docker-compose.yml · .github/workflows/ci.yml · Makefile
```

## API surface

```
POST /companies                            create a tenant
POST /companies/{cid}/ingest               document → extraction → graph
GET  /companies/{cid}/graph                inspect the knowledge graph
POST /companies/{cid}/skills/generate      graph → executable skill   ← the moat
GET  /companies/{cid}/skills
GET  /skills/{sid}
POST /skills/{sid}/execute                 run a skill (may pause for approval)
GET  /executions/{eid}
POST /approvals/{aid}/decision             resolve a human-in-the-loop gate
```

---

## What's real vs. deliberately stubbed

This is an MVP scaffold, honest about its edges.

**Real and tested:** the decision model and safe evaluator, the full Skill
Generation Engine (input discovery, step ordering, guard distillation,
confidence/freshness scoring, ordering validation), the agent runtime with the
human-in-the-loop boundary, the override/learning-loop capture, the FastAPI
surface, multi-tenant `company_id` scoping, and the pluggable graph store.

**Stubbed for the MVP:** real connectors (Gmail/Slack/Jira/Salesforce are
mocked in `runtime/tools.py`), auth/RBAC enforcement (the `User.role` column and
`company_id` scoping are present; middleware is not), the event-driven ingestion
pipeline (ingestion is synchronous here; Redis is provisioned for the queue),
and the learning loop's re-extraction step (the override capture + confidence
nudge are implemented; auto-proposing a new branch is the next increment).

## Suggested next increments

Wire one real connector end-to-end (Zendesk → refund tickets), add JWT/RBAC
middleware on top of the existing tenant scoping, move ingestion onto a Redis/
worker queue, add skill versioning + diffing in the UI, and close the learning
loop by having a captured correction propose a new decision branch for human
review.

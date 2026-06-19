"""HTTP surface wiring the slice together:

    POST /companies                      create tenant
    POST /companies/{cid}/ingest         doc -> extraction -> graph
    GET  /companies/{cid}/graph          inspect the knowledge graph
    POST /companies/{cid}/skills/generate  graph -> executable skill   <-- the moat
    GET  /companies/{cid}/skills
    GET  /skills/{sid}
    POST /skills/{sid}/execute           run a skill (may pause for approval)
    GET  /executions/{eid}
    POST /approvals/{aid}/decision       resolve a human-in-the-loop gate
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import models
from app.db.postgres import get_db
from app.extraction.extractor import KnowledgeExtractor
from app.runtime.executor import AgentRuntime, ExecStatus, ExecutionResult
from app.skills.generator import SkillGenerationError, SkillGenerator
from app.skills.models import Skill

router = APIRouter()


def _slug(s: str) -> str:
    return "".join(c.lower() if c.isalnum() else "-" for c in s).strip("-")


# --------------------------- request bodies --------------------------------- #
class CompanyIn(BaseModel):
    name: str


class IngestIn(BaseModel):
    text: str
    source: str | None = None


class GenerateIn(BaseModel):
    goal: str


class ExecuteIn(BaseModel):
    inputs: dict


class DecisionIn(BaseModel):
    decision: str  # "approve" | "override"
    action: str | None = None
    reason: str | None = None
    decided_by: str | None = None


# --------------------------- tenants ---------------------------------------- #
@router.post("/companies")
def create_company(body: CompanyIn, db: Session = Depends(get_db)):
    company = models.Company(id=f"co_{uuid.uuid4().hex[:8]}", name=body.name, slug=_slug(body.name))
    db.add(company)
    db.commit()
    return {"id": company.id, "name": company.name, "slug": company.slug}


@router.get("/companies")
def list_companies(db: Session = Depends(get_db)):
    return [
        {"id": c.id, "name": c.name, "slug": c.slug}
        for c in db.query(models.Company).all()
    ]


# --------------------------- ingestion + graph ------------------------------ #
@router.post("/companies/{cid}/ingest")
def ingest(cid: str, body: IngestIn, request: Request):
    extractor = KnowledgeExtractor(request.app.state.graph)
    created = extractor.ingest_document(body.text, cid, body.source)
    return {"company_id": cid, "nodes_created": created}


@router.get("/companies/{cid}/graph")
def get_graph(cid: str, request: Request):
    store = request.app.state.graph
    return {
        "nodes": [n.model_dump(mode="json") for n in store.all_nodes(cid)],
        "edges": [e.model_dump(mode="json") for e in store.all_edges(cid)],
    }


# --------------------------- skill generation (the moat) -------------------- #
@router.post("/companies/{cid}/skills/generate")
def generate_skill(cid: str, body: GenerateIn, request: Request, db: Session = Depends(get_db)):
    try:
        skill = SkillGenerator(request.app.state.graph).generate(body.goal, cid)
    except SkillGenerationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    rec = models.SkillRecord(
        id=f"skill_{uuid.uuid4().hex[:8]}",
        company_id=cid,
        name=skill.name,
        goal=skill.goal,
        version=skill.version,
        confidence=skill.confidence,
        freshness=skill.freshness,
        definition=skill.model_dump(mode="json"),
    )
    db.add(rec)
    db.commit()
    return {"id": rec.id, **skill.model_dump(mode="json")}


@router.get("/companies/{cid}/skills")
def list_skills(cid: str, db: Session = Depends(get_db)):
    rows = db.query(models.SkillRecord).filter_by(company_id=cid).all()
    return [
        {"id": r.id, "name": r.name, "goal": r.goal, "version": r.version,
         "confidence": r.confidence, "freshness": r.freshness}
        for r in rows
    ]


@router.get("/skills/{sid}")
def get_skill(sid: str, db: Session = Depends(get_db)):
    rec = db.get(models.SkillRecord, sid)
    if not rec:
        raise HTTPException(404, "skill not found")
    return {"id": rec.id, **rec.definition}


# --------------------------- execution + approvals -------------------------- #
@router.post("/skills/{sid}/execute")
def execute_skill(sid: str, body: ExecuteIn, request: Request, db: Session = Depends(get_db)):
    rec = db.get(models.SkillRecord, sid)
    if not rec:
        raise HTTPException(404, "skill not found")
    skill = Skill(**rec.definition)
    runtime = AgentRuntime(request.app.state.graph, request.app.state.registry)
    result = runtime.execute(skill, body.inputs)
    _persist_execution(db, rec, result)
    response = result.model_dump(mode="json")
    if result.status == ExecStatus.PENDING_APPROVAL:
        approval = models.ApprovalRecord(
            id=f"appr_{uuid.uuid4().hex[:8]}",
            company_id=rec.company_id,
            execution_id=result.id,
            action=result.pending.action,
            reason=result.pending.reason,
        )
        db.add(approval)
        db.commit()
        response["approval_id"] = approval.id
    return response


@router.get("/executions/{eid}")
def get_execution(eid: str, db: Session = Depends(get_db)):
    rec = db.get(models.ExecutionRecord, eid)
    if not rec:
        raise HTTPException(404, "execution not found")
    return rec.result


@router.post("/approvals/{aid}/decision")
def decide_approval(aid: str, body: DecisionIn, request: Request, db: Session = Depends(get_db)):
    approval = db.get(models.ApprovalRecord, aid)
    if not approval:
        raise HTTPException(404, "approval not found")
    if approval.status != "pending":
        raise HTTPException(409, f"approval already {approval.status}")
    exec_rec = db.get(models.ExecutionRecord, approval.execution_id)
    skill_rec = db.get(models.SkillRecord, exec_rec.skill_id)
    result = ExecutionResult(**exec_rec.result)
    skill = Skill(**skill_rec.definition)
    runtime = AgentRuntime(request.app.state.graph, request.app.state.registry)
    result = runtime.resume(
        result, skill, body.decision, body.action, body.reason, body.decided_by
    )
    _persist_execution(db, skill_rec, result, existing=exec_rec)

    approval.status = "approved" if body.decision == "approve" else "overridden"
    approval.reason = body.reason or ""
    approval.decided_by = body.decided_by or ""
    if body.decision == "override":
        db.add(models.CorrectionRecord(
            id=f"corr_{uuid.uuid4().hex[:8]}",
            company_id=skill_rec.company_id,
            execution_id=result.id,
            original_action=approval.action,
            corrected_action=body.action or "no_action",
            reason=body.reason or "",
        ))
        # propagate the confidence nudge from the learning loop back to the skill row
        from app.graph.schema import NodeType
        decisions = request.app.state.graph.find_nodes(skill_rec.company_id, type=NodeType.DECISION)
        if decisions:
            skill_rec.confidence = round(min(skill_rec.confidence, min(d.confidence for d in decisions)), 4)
    db.commit()
    return result.model_dump(mode="json")


# --------------------------- helpers ---------------------------------------- #
def _persist_execution(db, skill_rec, result, existing=None):
    if existing is None:
        existing = models.ExecutionRecord(
            id=result.id, company_id=skill_rec.company_id, skill_id=skill_rec.id
        )
        db.add(existing)
    existing.status = result.status.value
    existing.result = result.model_dump(mode="json")
    db.commit()

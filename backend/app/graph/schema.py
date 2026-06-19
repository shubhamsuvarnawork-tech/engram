"""Core graph primitives for the Company Brain knowledge graph.

Everything the brain learns is stored as typed nodes and typed edges. Nodes are
deliberately generic (a `properties` bag) so the same store works across tenants
and across very different kinds of knowledge (a refund policy, an on-call
runbook, an HR leave rule). Two scores ride along on every node:

* ``confidence``     - how sure we are the extracted knowledge is correct (0..1)
* ``freshness_days`` - age of the underlying evidence; older = more likely stale

Those two numbers are what let the Skill Generation Engine decide what is safe to
automate versus what should be gated behind a human.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class NodeType(str, Enum):
    FACT = "Fact"
    POLICY = "Policy"
    PROCESS = "Process"
    DECISION = "Decision"
    EXCEPTION = "Exception"
    STAKEHOLDER = "Stakeholder"
    SYSTEM = "System"
    ENTITY = "Entity"
    ACTION = "Action"


class EdgeType(str, Enum):
    USES = "USES"
    HAS = "HAS"
    APPROVED_BY = "APPROVED_BY"
    GOVERNS = "GOVERNS"          # policy/exception -> decision it constrains
    TRIGGERS = "TRIGGERS"
    ESCALATES_TO = "ESCALATES_TO"
    DEPENDS_ON = "DEPENDS_ON"
    PRODUCES = "PRODUCES"
    NEXT = "NEXT"               # decision -> decision (chaining)
    RELATED_TO = "RELATED_TO"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class GraphNode(BaseModel):
    id: str
    type: NodeType
    name: str
    company_id: str
    properties: dict[str, Any] = Field(default_factory=dict)
    confidence: float = 0.7
    freshness_days: float = 0.0
    source: Optional[str] = None
    version: int = 1
    created_at: datetime = Field(default_factory=_utcnow)


class GraphEdge(BaseModel):
    id: str
    type: EdgeType
    src: str
    dst: str
    company_id: str
    properties: dict[str, Any] = Field(default_factory=dict)

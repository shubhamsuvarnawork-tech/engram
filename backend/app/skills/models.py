"""The Skill: the executable artifact the whole platform exists to produce.

A Skill is a deterministic, ordered workflow compiled from the knowledge graph.
It is intentionally *data*, not code — a JSON object an agent runtime can load,
render, diff, version, and execute. Every skill carries:

* ``inputs``     - what the caller must supply (discovered from the graph).
* ``steps``      - fetch -> decide -> act, in a guaranteed-safe order.
* ``guards``     - conditional human-in-the-loop gates from exception knowledge.
* ``provenance`` - exactly which knowledge nodes/sources it was compiled from.
* ``confidence`` / ``freshness`` - how much to trust it / how stale it may be.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.graph.decision import Expr


class StepType(str, Enum):
    DATA_FETCH = "data_fetch"
    DECISION = "decision"
    ACTION = "action"
    TRANSFORM = "transform"
    NOTIFY = "notify"


class SkillInput(BaseModel):
    name: str
    type: str = "string"
    required: bool = True
    description: Optional[str] = None


class SkillStep(BaseModel):
    id: str
    type: StepType
    title: str
    description: Optional[str] = None
    # data_fetch
    tool: Optional[str] = None
    params: dict[str, Any] = Field(default_factory=dict)
    output_field: Optional[str] = None
    produces: Optional[str] = None
    # decision
    decision_ref: Optional[str] = None
    consumes: list[str] = Field(default_factory=list)
    # action
    action: Optional[str] = None
    requires_approval: bool = False
    when_outcome: Optional[str] = None   # run only if the decision selected this action


class Guard(BaseModel):
    """A conditional human-in-the-loop gate distilled from an Exception node."""
    id: str
    description: str
    requires_approval: bool = True
    action: Optional[str] = None         # action this guard gates (None = any)
    condition: Optional[Expr] = None     # when the guard applies (None = always)
    source_node: Optional[str] = None


class Provenance(BaseModel):
    node_ids: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)


class Skill(BaseModel):
    name: str
    goal: str
    company_id: str
    version: int = 1
    description: str = ""
    inputs: list[SkillInput] = Field(default_factory=list)
    steps: list[SkillStep] = Field(default_factory=list)
    guards: list[Guard] = Field(default_factory=list)
    provenance: Provenance = Field(default_factory=Provenance)
    confidence: float = 0.0
    freshness: float = 0.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

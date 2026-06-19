"""The organizational learning loop.

When a human overrides an agent's recommendation, that correction is the most
valuable signal in the system: it is tribal knowledge being written back into the
brain. We capture every override and, as an immediate feedback effect, nudge the
source decision's confidence down and flag it for review so future skill
generations reflect that the rule was wrong in this case.

(In production this feeds a re-extraction / human-review queue that proposes a
new branch or exception for the decision; here we implement the capture + the
confidence nudge, which is the part the rest of the system depends on.)
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field

from app.graph.schema import NodeType
from app.graph.store import GraphStore

CORRECTIONS: list["Correction"] = []  # process-local log; persisted via the API layer


class Correction(BaseModel):
    id: str
    execution_id: str
    company_id: str
    original_action: str
    corrected_action: str
    reason: Optional[str] = None
    decided_by: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


def capture_correction(
    store: GraphStore,
    execution,
    original_action: str,
    corrected_action: str,
    reason: Optional[str],
    decided_by: Optional[str],
) -> Correction:
    correction = Correction(
        id=f"corr_{uuid.uuid4().hex[:10]}",
        execution_id=execution.id,
        company_id=execution.company_id,
        original_action=original_action,
        corrected_action=corrected_action,
        reason=reason,
        decided_by=decided_by,
    )
    CORRECTIONS.append(correction)
    _nudge_decision_confidence(store, execution.company_id)
    return correction


def _nudge_decision_confidence(store: GraphStore, company_id: str) -> None:
    """Lower confidence on the company's decision nodes and flag for review."""
    for node in store.find_nodes(company_id, type=NodeType.DECISION):
        node.confidence = round(max(0.3, node.confidence - 0.05), 4)
        reviews = node.properties.get("pending_reviews", 0)
        node.properties["pending_reviews"] = reviews + 1
        store.upsert_node(node)

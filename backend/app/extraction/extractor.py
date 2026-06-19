"""Materialize extracted knowledge into the graph.

Takes the structured JSON an ``LLMClient`` returns and writes typed nodes and
edges into the ``GraphStore``. Nodes can be referenced by a stable "key" so the
extractor can wire up edges before the final node ids exist.
"""
from __future__ import annotations

import uuid
from typing import Optional

from app.extraction.llm import LLMClient, get_llm_client
from app.graph.schema import EdgeType, GraphEdge, GraphNode, NodeType
from app.graph.store import GraphStore

_COLLECTIONS = [
    ("facts", NodeType.FACT),
    ("policies", NodeType.POLICY),
    ("processes", NodeType.PROCESS),
    ("decisions", NodeType.DECISION),
    ("exceptions", NodeType.EXCEPTION),
    ("stakeholders", NodeType.STAKEHOLDER),
    ("systems", NodeType.SYSTEM),
    ("entities", NodeType.ENTITY),
]
_RESERVED = {"id", "key", "name", "type", "confidence", "freshness_days", "source"}


class KnowledgeExtractor:
    def __init__(self, store: GraphStore, llm: Optional[LLMClient] = None):
        self.store = store
        self.llm = llm or get_llm_client()

    def ingest_document(
        self, text: str, company_id: str, source: Optional[str] = None
    ) -> list[str]:
        data = self.llm.extract(text)
        return self._materialize(data, company_id, source)

    def _materialize(self, data: dict, company_id: str, source: Optional[str]) -> list[str]:
        created: list[str] = []
        idmap: dict[str, str] = {}

        for coll_key, ntype in _COLLECTIONS:
            for spec in data.get(coll_key, []):
                nid = spec.get("id") or f"{ntype.value.lower()}_{uuid.uuid4().hex[:8]}"
                props = {k: v for k, v in spec.items() if k not in _RESERVED}
                node = GraphNode(
                    id=nid,
                    type=ntype,
                    name=spec.get("name", nid),
                    company_id=company_id,
                    properties=props,
                    confidence=spec.get("confidence", 0.7),
                    freshness_days=spec.get("freshness_days", 0.0),
                    source=spec.get("source", source),
                )
                self.store.upsert_node(node)
                created.append(nid)
                for alias in {spec.get("key"), spec.get("id"), spec.get("name")}:
                    if alias:
                        idmap[alias] = nid

        for e in data.get("edges", []):
            self.store.upsert_edge(
                GraphEdge(
                    id=f"edge_{uuid.uuid4().hex[:8]}",
                    type=EdgeType(e["type"]),
                    src=idmap.get(e["src"], e["src"]),
                    dst=idmap.get(e["dst"], e["dst"]),
                    company_id=company_id,
                    properties=e.get("properties", {}),
                )
            )
        return created

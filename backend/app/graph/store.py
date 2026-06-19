"""Pluggable graph storage.

The engine talks to an abstract ``GraphStore`` so the exact same Skill
Generation / runtime code runs against an in-memory graph (tests, demos, local
dev) or Neo4j (production) with no changes. ``make_graph_store()`` picks the
backend from the ``GRAPH_BACKEND`` env var.
"""
from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Optional

from .schema import EdgeType, GraphEdge, GraphNode, NodeType


class GraphStore(ABC):
    @abstractmethod
    def upsert_node(self, node: GraphNode) -> None: ...
    @abstractmethod
    def get_node(self, node_id: str) -> Optional[GraphNode]: ...
    @abstractmethod
    def upsert_edge(self, edge: GraphEdge) -> None: ...
    @abstractmethod
    def neighbors(
        self, node_id: str, edge_type: Optional[EdgeType] = None, direction: str = "out"
    ) -> list[tuple[GraphEdge, GraphNode]]: ...
    @abstractmethod
    def find_nodes(
        self, company_id: str, type: Optional[NodeType] = None, name: Optional[str] = None
    ) -> list[GraphNode]: ...
    @abstractmethod
    def all_nodes(self, company_id: str) -> list[GraphNode]: ...
    @abstractmethod
    def all_edges(self, company_id: str) -> list[GraphEdge]: ...


class InMemoryGraphStore(GraphStore):
    """Dependency-free reference implementation. Authoritative for tests."""

    def __init__(self) -> None:
        self._nodes: dict[str, GraphNode] = {}
        self._edges: dict[str, GraphEdge] = {}

    def upsert_node(self, node: GraphNode) -> None:
        self._nodes[node.id] = node

    def get_node(self, node_id: str) -> Optional[GraphNode]:
        return self._nodes.get(node_id)

    def upsert_edge(self, edge: GraphEdge) -> None:
        self._edges[edge.id] = edge

    def neighbors(self, node_id, edge_type=None, direction="out"):
        out: list[tuple[GraphEdge, GraphNode]] = []
        for e in self._edges.values():
            if edge_type is not None and e.type != edge_type:
                continue
            if direction == "out" and e.src == node_id:
                other = e.dst
            elif direction == "in" and e.dst == node_id:
                other = e.src
            elif direction == "any" and node_id in (e.src, e.dst):
                other = e.dst if e.src == node_id else e.src
            else:
                continue
            n = self._nodes.get(other)
            if n is not None:
                out.append((e, n))
        return out

    def find_nodes(self, company_id, type=None, name=None):
        res = []
        for n in self._nodes.values():
            if n.company_id != company_id:
                continue
            if type is not None and n.type != type:
                continue
            if name is not None and n.name.lower() != name.lower():
                continue
            res.append(n)
        return res

    def all_nodes(self, company_id):
        return [n for n in self._nodes.values() if n.company_id == company_id]

    def all_edges(self, company_id):
        return [e for e in self._edges.values() if e.company_id == company_id]


def make_graph_store() -> GraphStore:
    backend = os.environ.get("GRAPH_BACKEND", "memory").lower()
    if backend == "neo4j":
        from .neo4j_store import Neo4jGraphStore  # lazy: keeps neo4j optional

        return Neo4jGraphStore(
            uri=os.environ.get("NEO4J_URI", "bolt://localhost:7687"),
            user=os.environ.get("NEO4J_USER", "neo4j"),
            password=os.environ.get("NEO4J_PASSWORD", "password"),
            database=os.environ.get("NEO4J_DATABASE", "neo4j"),
        )
    return InMemoryGraphStore()

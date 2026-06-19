"""Production graph store backed by Neo4j.

Nodes are labelled ``:Knowledge`` and keyed by ``id``; the flexible
``properties`` bag is serialized to JSON so the schema stays tenant-agnostic.
The ``neo4j`` driver is imported lazily (in ``__init__``) so the rest of the
platform — including the whole test suite — runs without a Neo4j install.
"""
from __future__ import annotations

import json
from typing import Optional

from .schema import EdgeType, GraphEdge, GraphNode, NodeType
from .store import GraphStore


def _to_node(rec) -> GraphNode:
    return GraphNode(
        id=rec["id"],
        type=NodeType(rec["type"]),
        name=rec["name"],
        company_id=rec["company_id"],
        properties=json.loads(rec.get("props") or "{}"),
        confidence=rec.get("confidence", 0.7),
        freshness_days=rec.get("freshness_days", 0.0),
        source=rec.get("source"),
        version=rec.get("version", 1),
    )


def _to_edge(rec) -> GraphEdge:
    return GraphEdge(
        id=rec["id"],
        type=EdgeType(rec["type"]),
        src=rec["src"],
        dst=rec["dst"],
        company_id=rec["company_id"],
        properties=json.loads(rec.get("props") or "{}"),
    )


class Neo4jGraphStore(GraphStore):
    def __init__(self, uri: str, user: str, password: str, database: str = "neo4j"):
        from neo4j import GraphDatabase  # lazy import

        self._driver = GraphDatabase.driver(uri, auth=(user, password))
        self._db = database
        self._ensure_constraints()

    def close(self) -> None:
        self._driver.close()

    def _session(self):
        return self._driver.session(database=self._db)

    def _ensure_constraints(self) -> None:
        with self._session() as s:
            s.run(
                "CREATE CONSTRAINT knowledge_id IF NOT EXISTS "
                "FOR (n:Knowledge) REQUIRE n.id IS UNIQUE"
            )

    def upsert_node(self, node: GraphNode) -> None:
        with self._session() as s:
            s.run(
                "MERGE (n:Knowledge {id:$id}) "
                "SET n.type=$type, n.name=$name, n.company_id=$company_id, "
                "n.confidence=$confidence, n.freshness_days=$freshness_days, "
                "n.source=$source, n.version=$version, n.props=$props",
                id=node.id, type=node.type.value, name=node.name,
                company_id=node.company_id, confidence=node.confidence,
                freshness_days=node.freshness_days, source=node.source,
                version=node.version, props=json.dumps(node.properties),
            )

    def get_node(self, node_id: str) -> Optional[GraphNode]:
        with self._session() as s:
            rec = s.run("MATCH (n:Knowledge {id:$id}) RETURN n", id=node_id).single()
            return _to_node(rec["n"]) if rec else None

    def upsert_edge(self, edge: GraphEdge) -> None:
        with self._session() as s:
            s.run(
                "MATCH (a:Knowledge {id:$src}),(b:Knowledge {id:$dst}) "
                "MERGE (a)-[r:REL {id:$id}]->(b) "
                "SET r.type=$type, r.company_id=$company_id, r.props=$props",
                id=edge.id, src=edge.src, dst=edge.dst, type=edge.type.value,
                company_id=edge.company_id, props=json.dumps(edge.properties),
            )

    def neighbors(self, node_id, edge_type=None, direction="out"):
        if direction == "out":
            pat = "(a:Knowledge {id:$id})-[r:REL]->(b:Knowledge)"
        elif direction == "in":
            pat = "(a:Knowledge {id:$id})<-[r:REL]-(b:Knowledge)"
        else:
            pat = "(a:Knowledge {id:$id})-[r:REL]-(b:Knowledge)"
        where = "" if edge_type is None else "WHERE r.type=$etype "
        out = []
        with self._session() as s:
            for rec in s.run(
                f"MATCH {pat} {where}RETURN r, b",
                id=node_id, etype=(edge_type.value if edge_type else None),
            ):
                out.append((_to_edge(rec["r"]), _to_node(rec["b"])))
        return out

    def find_nodes(self, company_id, type=None, name=None):
        clauses = ["n.company_id=$cid"]
        params = {"cid": company_id}
        if type is not None:
            clauses.append("n.type=$type")
            params["type"] = type.value
        if name is not None:
            clauses.append("toLower(n.name)=toLower($name)")
            params["name"] = name
        q = "MATCH (n:Knowledge) WHERE " + " AND ".join(clauses) + " RETURN n"
        with self._session() as s:
            return [_to_node(r["n"]) for r in s.run(q, **params)]

    def all_nodes(self, company_id):
        with self._session() as s:
            return [
                _to_node(r["n"])
                for r in s.run(
                    "MATCH (n:Knowledge {company_id:$cid}) RETURN n", cid=company_id
                )
            ]

    def all_edges(self, company_id):
        with self._session() as s:
            return [
                _to_edge(r["r"])
                for r in s.run(
                    "MATCH (:Knowledge)-[r:REL {company_id:$cid}]->(:Knowledge) RETURN r",
                    cid=company_id,
                )
            ]

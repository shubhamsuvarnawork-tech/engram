"""FastAPI application factory.

Holds the shared graph store and tool registry on ``app.state`` so ingestion,
skill generation, and execution all operate over the same Company Brain. Swap
``GRAPH_BACKEND=neo4j`` to move the graph to Neo4j with no code change.
"""
from __future__ import annotations

from fastapi import FastAPI

from app.api.routes import router
from app.db.postgres import init_db
from app.graph.store import make_graph_store
from app.runtime.tools import default_registry


def create_app() -> FastAPI:
    app = FastAPI(title="Engram", version="0.1.0")
    init_db()
    app.state.graph = make_graph_store()
    app.state.registry = default_registry()
    app.include_router(router)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()

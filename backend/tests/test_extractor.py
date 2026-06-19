from app.graph.schema import EdgeType, NodeType


def test_ingest_creates_typed_nodes(store):
    assert len(store.find_nodes("acme", type=NodeType.POLICY)) == 1
    assert len(store.find_nodes("acme", type=NodeType.DECISION)) == 1
    assert len(store.find_nodes("acme", type=NodeType.EXCEPTION)) == 1
    assert len(store.find_nodes("acme", type=NodeType.STAKEHOLDER)) == 1


def test_decision_has_executable_rule(store):
    d = store.find_nodes("acme", type=NodeType.DECISION)[0]
    rule = d.properties["rule"]
    assert len(rule["variables"]) == 4
    assert len(rule["branches"]) == 2
    assert rule["default"]["action"] == "manual_review"


def test_edges_materialized(store):
    edges = store.all_edges("acme")
    assert any(e.type == EdgeType.GOVERNS for e in edges)
    assert any(e.type == EdgeType.APPROVED_BY for e in edges)

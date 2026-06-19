from app.graph.schema import NodeType
from app.runtime.executor import AgentRuntime, ExecStatus


def run(store, registry, skill, customer):
    return AgentRuntime(store, registry).execute(skill, {"customer_id": customer})


def test_loyal_customer_auto_approved(store, registry, skill):
    r = run(store, registry, skill, "cust_loyal")
    assert r.status == ExecStatus.COMPLETED
    assert r.outcome == "approve_refund"
    assert r.pending is None


def test_fraud_customer_escalates_and_pauses(store, registry, skill):
    r = run(store, registry, skill, "cust_fraud")
    assert r.status == ExecStatus.PENDING_APPROVAL
    assert r.pending.action == "escalate_to_finance"


def test_high_value_trips_guard_even_when_qualified(store, registry, skill):
    r = run(store, registry, skill, "cust_highvalue")
    assert r.status == ExecStatus.PENDING_APPROVAL
    assert r.pending.action == "approve_refund"
    assert "guard_high_value_refund_hold" in r.pending.triggered_guards


def test_new_customer_manual_review(store, registry, skill):
    r = run(store, registry, skill, "cust_new")
    assert r.status == ExecStatus.PENDING_APPROVAL
    assert r.pending.action == "manual_review"


def test_resume_approve_completes(store, registry, skill):
    rt = AgentRuntime(store, registry)
    r = rt.execute(skill, {"customer_id": "cust_fraud"})
    r = rt.resume(r, skill, decision="approve", decided_by="finance@acme.com")
    assert r.status == ExecStatus.COMPLETED
    assert r.outcome == "escalate_to_finance"


def test_override_captures_correction_and_nudges_confidence(store, registry, skill):
    rt = AgentRuntime(store, registry)
    before = store.find_nodes("acme", type=NodeType.DECISION)[0].confidence
    r = rt.execute(skill, {"customer_id": "cust_highvalue"})
    r = rt.resume(r, skill, decision="override", action="deny_refund",
                  reason="disputed", decided_by="cfo@acme.com")
    assert r.status == ExecStatus.COMPLETED_OVERRIDDEN
    assert r.outcome == "deny_refund"
    after = store.find_nodes("acme", type=NodeType.DECISION)[0].confidence
    assert after < before  # learning loop wrote back

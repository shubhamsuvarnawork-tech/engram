"""End-to-end demo of the full vertical slice, no external services required.

    raw policy text  ->  extraction  ->  knowledge/decision graph
                      ->  SKILL GENERATION  ->  agent runtime (+ HITL + learning)

Run:  PYTHONPATH=. python -m app.seed.demo
"""
from __future__ import annotations

from app.extraction.extractor import KnowledgeExtractor
from app.extraction.llm import MockLLMClient
from app.graph.store import InMemoryGraphStore
from app.runtime.executor import AgentRuntime, ExecStatus
from app.runtime.tools import default_registry
from app.seed.sample_docs import SAMPLE_REFUND_DOC
from app.skills.generator import SkillGenerator

LINE = "-" * 72


def banner(title: str) -> None:
    print("\n" + LINE + f"\n{title}\n" + LINE)


def main() -> None:
    company = "acme"
    store = InMemoryGraphStore()
    registry = default_registry()

    banner("1. INGEST  -  raw policy prose -> knowledge/decision graph")
    extractor = KnowledgeExtractor(store, MockLLMClient())
    created = extractor.ingest_document(SAMPLE_REFUND_DOC, company, "notion://wiki/refund-policy")
    for nid in created:
        n = store.get_node(nid)
        print(f"  + {n.type.value:11} {n.name!r}  (confidence={n.confidence}, age={n.freshness_days}d)")

    banner("2. GENERATE  -  graph -> executable skill  [THE MOAT]")
    skill = SkillGenerator(store).generate("refund_customer", company)
    print(f"  skill      : {skill.name}  v{skill.version}")
    print(f"  inputs     : {[i.name for i in skill.inputs]}")
    print(f"  confidence : {skill.confidence}   freshness: {skill.freshness}")
    print("  workflow   :")
    for s in skill.steps:
        tag = "  <APPROVAL>" if s.requires_approval else ""
        produces = f" -> {s.produces}" if s.produces else ""
        print(f"     [{s.type.value:10}] {s.title}{produces}{tag}")
    for g in skill.guards:
        print(f"  guard      : {g.description}  (gates: {g.action})")

    runtime = AgentRuntime(store, registry)

    banner("3. EXECUTE  -  loyal customer -> AUTO-APPROVED (no human)")
    r = runtime.execute(skill, {"customer_id": "cust_loyal"})
    print(f"  status={r.status.value}  outcome={r.outcome}")

    banner("4. EXECUTE  -  fraud flag -> ESCALATE -> pauses for human")
    r = runtime.execute(skill, {"customer_id": "cust_fraud"})
    print(f"  status={r.status.value}  pending_action={r.pending.action}  reason={r.pending.reason}")
    r = runtime.resume(r, skill, decision="approve", decided_by="finance@acme.com")
    print(f"  after approval -> status={r.status.value}  outcome={r.outcome}")

    banner("5. EXECUTE  -  $8k refund -> qualifies BUT guard trips -> human")
    r = runtime.execute(skill, {"customer_id": "cust_highvalue"})
    print(f"  status={r.status.value}  pending_action={r.pending.action}")
    print(f"  triggered_guards={r.pending.triggered_guards}")

    banner("6. LEARN  -  human OVERRIDES approve -> deny (writes back to brain)")
    from app.graph.schema import NodeType
    dnode = store.find_nodes(company, type=NodeType.DECISION)[0]
    print(f"  decision confidence before: {dnode.confidence}")
    r = runtime.resume(r, skill, decision="override", action="deny_refund",
                       reason="Refund amount disputed by Finance.", decided_by="cfo@acme.com")
    print(f"  status={r.status.value}  outcome={r.outcome}")
    dnode = store.find_nodes(company, type=NodeType.DECISION)[0]
    print(f"  decision confidence after : {dnode.confidence}  "
          f"(pending_reviews={dnode.properties.get('pending_reviews')})")
    print("\nThe override is now organizational memory: the next skill generation "
          "will reflect the lowered confidence and review flag.\n")


if __name__ == "__main__":
    main()

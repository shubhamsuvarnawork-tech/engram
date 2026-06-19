"""The Skill Generation Engine — the core of Company Brain.

Glean/Copilot/Guru stop at *retrieval*: they find the policy and show it to you.
This engine goes one step further and *compiles* the decision knowledge in the
graph into an executable Skill an agent can actually run safely.

Pipeline (all deterministic — the LLM's job was upstream, turning prose into the
decision graph; here we only compile what's already structured):

    1. resolve  - find the entry Decision node for the requested goal
    2. collect  - gather chained decisions (Outcome.next_decision / NEXT edges)
    3. fetch    - one DATA_FETCH step per distinct variable the decisions need
    4. inputs   - discover required inputs from "{{placeholder}}" refs in params
    5. decide   - one DECISION step per decision node
    6. act      - one ACTION step per distinct outcome action
    7. guard    - turn Exception nodes into conditional human-in-the-loop gates
    8. score    - confidence/freshness from the provenance nodes
    9. validate - prove the step order is safe (fetch -> decide -> act, no
                  decision consuming an unresolved variable)

The output is provenance-linked and confidence-scored, which is what makes the
downstream automation auditable and safe.
"""
from __future__ import annotations

import re
from typing import Optional

from app.graph.decision import DecisionRule, referenced_vars
from app.graph.schema import EdgeType, GraphNode, NodeType
from app.graph.store import GraphStore
from app.skills.confidence import confidence_score, freshness_score
from app.skills.models import (
    Guard,
    Provenance,
    Skill,
    SkillInput,
    SkillStep,
    StepType,
)

_INPUT_RE = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}")
# Phase ordering that guarantees a runnable workflow.
_PHASE = {
    StepType.DATA_FETCH: 0,
    StepType.TRANSFORM: 0,
    StepType.DECISION: 1,
    StepType.NOTIFY: 1,
    StepType.ACTION: 2,
}


class SkillGenerationError(Exception):
    """Raised when a goal cannot be compiled into a skill."""


class SkillGenerator:
    def __init__(self, store: GraphStore):
        self.store = store

    # ------------------------------------------------------------------ #
    # Public API                                                         #
    # ------------------------------------------------------------------ #
    def generate(self, goal: str, company_id: str) -> Skill:
        entry = self._resolve_entry(goal, company_id)
        decisions = self._collect_decisions(entry)
        rules = {d.id: self._rule_of(d) for d in decisions}

        fetch_steps, input_names = self._build_fetch_steps(decisions, rules)
        decision_steps = self._build_decision_steps(decisions, rules)
        action_steps = self._build_action_steps(decisions, rules)
        guards = self._collect_guards(decisions)

        steps = fetch_steps + decision_steps + action_steps
        touched = self._provenance_nodes(entry, decisions, guards)

        skill = Skill(
            name=_normalize(goal),
            goal=goal,
            company_id=company_id,
            description=(
                entry.properties.get("description")
                or f"Auto-generated skill for goal '{goal}'."
            ),
            inputs=[
                SkillInput(name=n, description=f"Identifier required to resolve '{n}'.")
                for n in sorted(input_names)
            ],
            steps=steps,
            guards=guards,
            provenance=Provenance(
                node_ids=[n.id for n in touched],
                sources=sorted({n.source for n in touched if n.source}),
            ),
            confidence=confidence_score(touched),
            freshness=freshness_score(touched),
        )
        self._validate_ordering(skill)
        return skill

    # ------------------------------------------------------------------ #
    # 1. resolve entry decision                                          #
    # ------------------------------------------------------------------ #
    def _resolve_entry(self, goal: str, company_id: str) -> GraphNode:
        norm = _normalize(goal)
        # (a) a Decision node directly tagged with this goal / named for it
        for n in self.store.find_nodes(company_id, type=NodeType.DECISION):
            if _normalize(n.properties.get("goal", "")) == norm or _normalize(n.name) == norm:
                return n
        # (b) a Policy node matching the goal -> follow GOVERNS to its decision
        for n in self.store.find_nodes(company_id, type=NodeType.POLICY):
            if norm in _normalize(n.name) or _normalize(n.properties.get("goal", "")) == norm:
                for _, dn in self.store.neighbors(n.id, EdgeType.GOVERNS, "out"):
                    if dn.type == NodeType.DECISION:
                        return dn
        raise SkillGenerationError(
            f"No decision or policy in the graph matches goal '{goal}'. "
            "Ingest the relevant policy first."
        )

    # ------------------------------------------------------------------ #
    # 2. collect chained decisions                                       #
    # ------------------------------------------------------------------ #
    def _collect_decisions(self, entry: GraphNode) -> list[GraphNode]:
        ordered: list[GraphNode] = []
        seen: set[str] = set()
        frontier = [entry]
        while frontier:
            node = frontier.pop(0)
            if node.id in seen:
                continue
            seen.add(node.id)
            ordered.append(node)
            # explicit NEXT edges...
            for _, nxt in self.store.neighbors(node.id, EdgeType.NEXT, "out"):
                if nxt.type == NodeType.DECISION:
                    frontier.append(nxt)
            # ...and Outcome.next_decision references inside the rule
            for oc in self._outcomes_of(self._rule_of(node)):
                if oc.next_decision:
                    nxt = self.store.get_node(oc.next_decision)
                    if nxt and nxt.type == NodeType.DECISION:
                        frontier.append(nxt)
        return ordered

    # ------------------------------------------------------------------ #
    # 3 + 4. fetch steps and discovered inputs                           #
    # ------------------------------------------------------------------ #
    def _build_fetch_steps(self, decisions, rules):
        steps: list[SkillStep] = []
        seen_vars: set[str] = set()
        input_names: set[str] = set()
        for d in decisions:
            for var in rules[d.id].variables:
                input_names |= _inputs_in(var.params)
                if var.name in seen_vars:
                    continue
                seen_vars.add(var.name)
                steps.append(
                    SkillStep(
                        id=f"fetch_{var.name}",
                        type=StepType.DATA_FETCH,
                        title=f"Fetch {var.name}",
                        tool=var.tool,
                        params=dict(var.params),
                        output_field=var.output_field,
                        produces=var.name,
                        description=var.description or f"Resolve '{var.name}' via {var.tool}.",
                    )
                )
        return steps, input_names

    # ------------------------------------------------------------------ #
    # 5. decision steps                                                  #
    # ------------------------------------------------------------------ #
    def _build_decision_steps(self, decisions, rules):
        steps = []
        for d in decisions:
            consumes = sorted(
                {v for b in rules[d.id].branches for v in referenced_vars(b.when)}
            )
            steps.append(
                SkillStep(
                    id=f"decide_{_slug(d.name)}",
                    type=StepType.DECISION,
                    title=f"Evaluate {d.name}",
                    decision_ref=d.id,
                    consumes=consumes,
                    produces="decision",
                    description=d.properties.get("description") or f"Apply '{d.name}'.",
                )
            )
        return steps

    # ------------------------------------------------------------------ #
    # 6. action steps                                                    #
    # ------------------------------------------------------------------ #
    def _build_action_steps(self, decisions, rules):
        steps = []
        seen: set[str] = set()
        for d in decisions:
            for oc in self._outcomes_of(rules[d.id]):
                if oc.next_decision:           # chained -> handled as a decision
                    continue
                if oc.action in seen:
                    continue
                seen.add(oc.action)
                steps.append(
                    SkillStep(
                        id=f"act_{oc.action}",
                        type=StepType.ACTION,
                        title=_titalize(oc.action),
                        action=oc.action,
                        params=dict(oc.params),
                        requires_approval=oc.requires_approval,
                        when_outcome=oc.action,
                        description=oc.label or f"Perform '{oc.action}'.",
                    )
                )
        return steps

    # ------------------------------------------------------------------ #
    # 7. guards from exceptions                                          #
    # ------------------------------------------------------------------ #
    def _collect_guards(self, decisions):
        guards: list[Guard] = []
        seen: set[str] = set()
        targets = list(decisions)
        # include the policies governing those decisions (exceptions often hang
        # off the policy, not the decision)
        for d in decisions:
            for _, p in self.store.neighbors(d.id, EdgeType.GOVERNS, "in"):
                if p.type == NodeType.POLICY:
                    targets.append(p)
        for node in targets:
            for _, ex in self.store.neighbors(node.id, EdgeType.GOVERNS, "in"):
                if ex.type == NodeType.EXCEPTION and ex.id not in seen:
                    seen.add(ex.id)
                    guards.append(
                        Guard(
                            id=f"guard_{_slug(ex.name)}",
                            description=ex.properties.get("description") or ex.name,
                            requires_approval=bool(
                                ex.properties.get("requires_approval", True)
                            ),
                            action=ex.properties.get("action"),
                            condition=ex.properties.get("condition"),
                            source_node=ex.id,
                        )
                    )
        return guards

    # ------------------------------------------------------------------ #
    # 8. provenance set                                                  #
    # ------------------------------------------------------------------ #
    def _provenance_nodes(self, entry, decisions, guards):
        out: dict[str, GraphNode] = {}

        def add(n: Optional[GraphNode]):
            if n is not None:
                out[n.id] = n

        add(entry)
        for d in decisions:
            add(d)
            for _, p in self.store.neighbors(d.id, EdgeType.GOVERNS, "in"):
                add(p)
                for _, st in self.store.neighbors(p.id, EdgeType.APPROVED_BY, "out"):
                    add(st)
        for g in guards:
            if g.source_node:
                add(self.store.get_node(g.source_node))
        return list(out.values())

    # ------------------------------------------------------------------ #
    # 9. ordering / safety validation                                    #
    # ------------------------------------------------------------------ #
    def _validate_ordering(self, skill: Skill) -> None:
        produced: set[str] = set()
        last_phase = -1
        for st in skill.steps:
            phase = _PHASE[st.type]
            if phase < last_phase:
                raise SkillGenerationError(
                    f"step '{st.id}' breaks fetch->decide->act ordering"
                )
            last_phase = phase
            if st.type == StepType.DATA_FETCH and st.produces:
                produced.add(st.produces)
            if st.type == StepType.DECISION:
                missing = [v for v in st.consumes if v not in produced]
                if missing:
                    raise SkillGenerationError(
                        f"decision '{st.id}' consumes unresolved variables: {missing}"
                    )

    # ------------------------------------------------------------------ #
    # helpers                                                            #
    # ------------------------------------------------------------------ #
    def _rule_of(self, node: GraphNode) -> DecisionRule:
        return DecisionRule(**node.properties.get("rule", {}))

    def _outcomes_of(self, rule: DecisionRule):
        outcomes = [b.then for b in rule.branches]
        if rule.default is not None:
            outcomes.append(rule.default)
        return outcomes


def _normalize(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", (s or "").lower()).strip("_")


def _slug(s: str) -> str:
    return _normalize(s)


def _titalize(s: str) -> str:
    return s.replace("_", " ").title()


def _inputs_in(params: dict) -> set[str]:
    found: set[str] = set()
    for v in params.values():
        if isinstance(v, str):
            found |= set(_INPUT_RE.findall(v))
    return found

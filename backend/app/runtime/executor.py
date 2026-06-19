"""Agent runtime: execute a generated Skill, safely.

The runtime walks the skill's steps in order:

* ``data_fetch`` - resolve ``{{input}}`` params, call the tool, bind the result
* ``decision``   - evaluate the referenced DecisionRule against gathered context
* ``action``     - run *only* the action the decision selected; if the action
                   itself requires approval, or any guard's condition fires,
                   PAUSE and emit an approval request instead of acting.

Pausing returns a ``PENDING_APPROVAL`` result that a human resolves via
``resume()`` - that is the human-in-the-loop boundary. Every step is recorded in
a trace so executions are fully auditable.
"""
from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.graph.decision import DecisionRule, eval_expr, evaluate_rule
from app.graph.store import GraphStore
from app.runtime.tools import ToolNotFound, ToolRegistry
from app.skills.models import Skill, SkillStep, StepType

_INPUT_RE = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}")


class ExecStatus(str, Enum):
    COMPLETED = "completed"
    PENDING_APPROVAL = "pending_approval"
    COMPLETED_OVERRIDDEN = "completed_overridden"
    FAILED = "failed"


class StepTrace(BaseModel):
    step_id: str
    type: str
    detail: dict[str, Any] = Field(default_factory=dict)


class PendingApproval(BaseModel):
    action: str
    reason: str
    triggered_guards: list[str] = Field(default_factory=list)


class ExecutionResult(BaseModel):
    id: str
    skill_name: str
    company_id: str
    status: ExecStatus
    inputs: dict[str, Any]
    context: dict[str, Any] = Field(default_factory=dict)
    trace: list[StepTrace] = Field(default_factory=list)
    pending: Optional[PendingApproval] = None
    outcome: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AgentRuntime:
    def __init__(self, store: GraphStore, registry: ToolRegistry):
        self.store = store
        self.registry = registry

    # ------------------------------------------------------------------ #
    def execute(self, skill: Skill, inputs: dict[str, Any]) -> ExecutionResult:
        result = ExecutionResult(
            id=f"exec_{uuid.uuid4().hex[:10]}",
            skill_name=skill.name,
            company_id=skill.company_id,
            status=ExecStatus.COMPLETED,
            inputs=dict(inputs),
            context=dict(inputs),
        )
        try:
            chosen_action: Optional[str] = None
            for step in skill.steps:
                if step.type in (StepType.DATA_FETCH, StepType.TRANSFORM):
                    self._run_fetch(step, result)
                elif step.type == StepType.DECISION:
                    chosen_action = self._run_decision(step, result)
                elif step.type == StepType.ACTION:
                    if step.when_outcome and step.when_outcome != chosen_action:
                        continue  # not the branch the decision picked
                    paused = self._run_action(step, skill, result)
                    if paused:
                        return result  # stop at the human-in-the-loop boundary
            return result
        except (ToolNotFound, ValueError) as exc:
            result.status = ExecStatus.FAILED
            result.trace.append(
                StepTrace(step_id="*", type="error", detail={"error": str(exc)})
            )
            return result

    def resume(
        self,
        result: ExecutionResult,
        skill: Skill,
        decision: str,
        action: Optional[str] = None,
        reason: Optional[str] = None,
        decided_by: Optional[str] = None,
    ) -> ExecutionResult:
        """Resolve a pending approval. ``decision`` is 'approve' or 'override'."""
        if result.status != ExecStatus.PENDING_APPROVAL or result.pending is None:
            return result
        pending = result.pending
        if decision == "approve":
            self._perform(pending.action, result)
            result.outcome = pending.action
            result.status = ExecStatus.COMPLETED
            result.trace.append(
                StepTrace(
                    step_id="approval",
                    type="approval",
                    detail={"decision": "approved", "by": decided_by},
                )
            )
        else:  # override
            corrected = action or "no_action"
            from app.runtime.learning import capture_correction

            capture_correction(
                self.store, result, pending.action, corrected, reason, decided_by
            )
            if corrected != "no_action":
                self._perform(corrected, result)
            result.outcome = corrected
            result.status = ExecStatus.COMPLETED_OVERRIDDEN
            result.trace.append(
                StepTrace(
                    step_id="approval",
                    type="override",
                    detail={
                        "from": pending.action,
                        "to": corrected,
                        "reason": reason,
                        "by": decided_by,
                    },
                )
            )
        result.pending = None
        return result

    # ------------------------------------------------------------------ #
    def _run_fetch(self, step: SkillStep, result: ExecutionResult) -> None:
        params = self._resolve_params(step.params, result.context)
        out = self.registry.call(step.tool, params)
        value = out.get(step.output_field) if step.output_field else out
        if step.produces:
            result.context[step.produces] = value
        result.trace.append(
            StepTrace(
                step_id=step.id,
                type=step.type.value,
                detail={"tool": step.tool, "params": params, "produced": {step.produces: value}},
            )
        )

    def _run_decision(self, step: SkillStep, result: ExecutionResult) -> str:
        node = self.store.get_node(step.decision_ref)
        if node is None:
            raise ValueError(f"decision node '{step.decision_ref}' not found")
        rule = DecisionRule(**node.properties.get("rule", {}))
        outcome, idx = evaluate_rule(rule, result.context)
        result.context["decision"] = outcome.action
        result.context["_outcome"] = outcome.model_dump()
        result.trace.append(
            StepTrace(
                step_id=step.id,
                type=step.type.value,
                detail={
                    "matched_branch": idx,
                    "action": outcome.action,
                    "requires_approval": outcome.requires_approval,
                    "label": outcome.label,
                },
            )
        )
        return outcome.action

    def _run_action(self, step: SkillStep, skill: Skill, result: ExecutionResult) -> bool:
        """Run the chosen action, or pause for approval. Returns True if paused."""
        triggered = self._triggered_guards(skill, step.action, result.context)
        needs_approval = step.requires_approval or bool(triggered)
        if needs_approval:
            reason = (
                "step requires approval"
                if step.requires_approval and not triggered
                else "guard(s) triggered: " + ", ".join(g.id for g in triggered)
            )
            result.status = ExecStatus.PENDING_APPROVAL
            result.pending = PendingApproval(
                action=step.action,
                reason=reason,
                triggered_guards=[g.id for g in triggered],
            )
            result.trace.append(
                StepTrace(
                    step_id=step.id,
                    type="await_approval",
                    detail={"action": step.action, "reason": reason},
                )
            )
            return True
        self._perform(step.action, result)
        result.outcome = step.action
        return False

    def _perform(self, action: str, result: ExecutionResult) -> None:
        receipt: dict[str, Any] = {"action": action, "status": "skipped_no_tool"}
        tool_name = f"action.{action}"
        if self.registry.has(tool_name):
            receipt = self.registry.call(tool_name, {"context_keys": list(result.context.keys())})
        result.trace.append(
            StepTrace(step_id=f"perform_{action}", type="action", detail={"receipt": receipt})
        )

    def _triggered_guards(self, skill: Skill, action: Optional[str], ctx: dict):
        out = []
        for g in skill.guards:
            if not g.requires_approval:
                continue
            if g.action is not None and g.action != action:
                continue
            if g.condition is not None and not eval_expr(g.condition, ctx):
                continue
            out.append(g)
        return out

    def _resolve_params(self, params: dict, ctx: dict) -> dict:
        resolved: dict[str, Any] = {}
        for k, v in params.items():
            if isinstance(v, str):
                m = _INPUT_RE.fullmatch(v.strip())
                if m:
                    resolved[k] = ctx.get(m.group(1))
                    continue
                resolved[k] = _INPUT_RE.sub(lambda mm: str(ctx.get(mm.group(1), "")), v)
            else:
                resolved[k] = v
        return resolved

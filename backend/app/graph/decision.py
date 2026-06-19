"""Structured, executable representation of an organizational *decision*.

The central thesis of Company Brain is that companies run on decisions, not
documents. A ``DecisionRule`` captures one decision in a form that is both
human-auditable and machine-executable:

* ``variables`` - the facts the decision needs and *how to fetch them*
  (which connector/tool, with which params, reading which field).
* ``branches``  - ordered ``when -> then`` rules. First match wins.
* ``default``   - fallback outcome when no branch matches.

Conditions are a small boolean expression tree (``all`` / ``any`` / predicate)
so they are safe to evaluate without ``eval`` and trivial to render in a UI.
"""
from __future__ import annotations

from enum import Enum
from typing import Annotated, Any, List, Literal, Optional, Union

from pydantic import BaseModel, Field


class Op(str, Enum):
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    EQ = "eq"
    NE = "ne"
    IN = "in"
    CONTAINS = "contains"
    EXISTS = "exists"


class Predicate(BaseModel):
    kind: Literal["predicate"] = "predicate"
    var: str
    op: Op
    value: Any = None


class All(BaseModel):
    kind: Literal["all"] = "all"
    all: List["Expr"]


class Any_(BaseModel):
    kind: Literal["any"] = "any"
    any: List["Expr"]


# Discriminated union keeps (de)serialization unambiguous and recursive-safe.
Expr = Annotated[Union[Predicate, All, Any_], Field(discriminator="kind")]
All.model_rebuild()
Any_.model_rebuild()


class VariableSource(BaseModel):
    """How to obtain one variable the decision depends on."""
    name: str
    tool: str                       # connector/tool id, e.g. "billing.get_subscription"
    params: dict[str, Any] = Field(default_factory=dict)  # values may hold "{{input}}" refs
    output_field: str               # field to read off the tool's result
    type: str = "any"
    description: Optional[str] = None


class Outcome(BaseModel):
    action: str                     # e.g. "approve_refund"
    requires_approval: bool = False
    params: dict[str, Any] = Field(default_factory=dict)
    next_decision: Optional[str] = None   # node id, for chaining decisions
    label: Optional[str] = None


class Branch(BaseModel):
    when: Expr
    then: Outcome


class DecisionRule(BaseModel):
    variables: List[VariableSource] = Field(default_factory=list)
    branches: List[Branch] = Field(default_factory=list)
    default: Optional[Outcome] = None


# --------------------------------------------------------------------------- #
# Pure, side-effect-free evaluation helpers (shared by runtime + generator).   #
# --------------------------------------------------------------------------- #
def eval_predicate(p: Predicate, ctx: dict) -> bool:
    v = ctx.get(p.var)
    if p.op == Op.EXISTS:
        return v is not None
    if v is None:
        return False
    try:
        if p.op == Op.GT:
            return v > p.value
        if p.op == Op.GTE:
            return v >= p.value
        if p.op == Op.LT:
            return v < p.value
        if p.op == Op.LTE:
            return v <= p.value
        if p.op == Op.EQ:
            return v == p.value
        if p.op == Op.NE:
            return v != p.value
        if p.op == Op.IN:
            return v in p.value
        if p.op == Op.CONTAINS:
            return p.value in v
    except TypeError:
        return False
    return False


def eval_expr(expr: Any, ctx: dict) -> bool:
    if isinstance(expr, Predicate):
        return eval_predicate(expr, ctx)
    if isinstance(expr, All):
        return all(eval_expr(e, ctx) for e in expr.all)
    if isinstance(expr, Any_):
        return any(eval_expr(e, ctx) for e in expr.any)
    return False


def referenced_vars(expr: Any) -> set[str]:
    if isinstance(expr, Predicate):
        return {expr.var}
    if isinstance(expr, All):
        out: set[str] = set()
        for e in expr.all:
            out |= referenced_vars(e)
        return out
    if isinstance(expr, Any_):
        out = set()
        for e in expr.any:
            out |= referenced_vars(e)
        return out
    return set()


def evaluate_rule(rule: DecisionRule, ctx: dict) -> tuple[Outcome, Optional[int]]:
    """Return (chosen outcome, matched branch index or None for default)."""
    for i, b in enumerate(rule.branches):
        if eval_expr(b.when, ctx):
            return b.then, i
    if rule.default is not None:
        return rule.default, None
    raise ValueError("decision rule produced no outcome and defines no default")

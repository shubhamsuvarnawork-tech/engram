"""Connector / tool registry for the agent runtime.

A Skill references tools by id (``billing.get_subscription``). In production
these map to real connectors (Salesforce, Zendesk, internal APIs). Here we ship
deterministic mocks plus a sample customer dataset so a generated skill runs
end-to-end with no external systems. Action tools are mocked side-effects that
return a receipt.
"""
from __future__ import annotations

from typing import Any, Callable

# Sample tenant data covering the three interesting refund paths.
DEFAULT_CUSTOMERS: dict[str, dict[str, Any]] = {
    "cust_loyal": {  # long tenure, high LTV, small refund -> AUTO-APPROVE
        "name": "Loyal Inc.",
        "months_active": 24,
        "lifetime_value": 15000,
        "risk_flags": [],
        "refund_amount": 1200,
    },
    "cust_fraud": {  # fraud flag -> ESCALATE (human)
        "name": "Risky LLC",
        "months_active": 24,
        "lifetime_value": 15000,
        "risk_flags": ["chargeback_fraud"],
        "refund_amount": 1200,
    },
    "cust_highvalue": {  # qualifies to auto-approve BUT $8k trips the guard -> approval
        "name": "BigSpend Co.",
        "months_active": 30,
        "lifetime_value": 40000,
        "risk_flags": [],
        "refund_amount": 8000,
    },
    "cust_new": {  # short tenure -> MANUAL REVIEW
        "name": "Newbie Ltd.",
        "months_active": 3,
        "lifetime_value": 500,
        "risk_flags": [],
        "refund_amount": 300,
    },
}


class ToolNotFound(Exception):
    pass


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Callable[[dict], dict]] = {}

    def register(self, name: str, fn: Callable[[dict], dict]) -> None:
        self._tools[name] = fn

    def has(self, name: str) -> bool:
        return name in self._tools

    def call(self, name: str, params: dict) -> dict:
        if name not in self._tools:
            raise ToolNotFound(name)
        return self._tools[name](params)


def default_registry(dataset: dict | None = None) -> ToolRegistry:
    data = dataset if dataset is not None else DEFAULT_CUSTOMERS
    reg = ToolRegistry()

    def _customer(p: dict) -> dict:
        cid = p.get("customer_id")
        if cid not in data:
            raise ToolNotFound(f"unknown customer_id '{cid}'")
        return data[cid]

    reg.register("billing.get_subscription", lambda p: {"months_active": _customer(p)["months_active"]})
    reg.register("crm.get_customer", lambda p: {"lifetime_value": _customer(p)["lifetime_value"], "name": _customer(p)["name"]})
    reg.register("support.get_history", lambda p: {"risk_flags": _customer(p).get("risk_flags", [])})
    reg.register("billing.get_open_refund", lambda p: {"amount": _customer(p).get("refund_amount", 0)})

    # Action tools: mocked side-effects. Each returns an auditable receipt.
    for action in ("approve_refund", "escalate_to_finance", "manual_review", "deny_refund"):
        reg.register(f"action.{action}", _make_action(action))
    return reg


def _make_action(action: str) -> Callable[[dict], dict]:
    def _fn(params: dict) -> dict:
        return {"action": action, "status": "done", "params": params}

    return _fn

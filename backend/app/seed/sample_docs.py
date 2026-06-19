"""A bundled sample so the entire pipeline runs with zero external services.

``SAMPLE_REFUND_DOC`` is the raw prose a company might keep in Notion/Confluence.
``REFUND_EXTRACTION`` is the structured graph the extraction LLM is expected to
return for it (the ``MockLLMClient`` returns this verbatim, which is what lets
tests and the demo run fully offline). It models the exact refund example from
the product spec, plus a realistic high-value exception and an approver.
"""
from __future__ import annotations

SAMPLE_REFUND_DOC = """\
Refund Policy  -  Customer Success Wiki (last reviewed 20 days ago)

Customers on a paid plan may request a refund. Support evaluates each request:

- If the subscription has been active for at least 12 months AND the customer's
  lifetime value is at least $10,000, support may AUTO-APPROVE the refund.
- If the account has a chargeback or fraud flag, the request must be ESCALATED
  to the Finance team and must never be auto-approved.
- Anything else goes to MANUAL REVIEW by a support lead.

Exception: refunds of $5,000 or more always require explicit Finance approval,
even when the auto-approve conditions are met.

The Refund Policy is owned and approved by the Finance team.
"""

# The structured knowledge an extraction LLM should produce from the prose above.
# Edges reference nodes by their stable "key".
REFUND_EXTRACTION = {
    "policies": [
        {
            "key": "refund_policy",
            "name": "Refund Policy",
            "goal": "refund_customer",
            "description": "How customer refund requests are evaluated and approved.",
            "confidence": 0.9,
            "freshness_days": 20,
            "source": "notion://wiki/refund-policy",
        }
    ],
    "decisions": [
        {
            "key": "refund_decision",
            "name": "Refund Decision",
            "goal": "refund_customer",
            "description": "Decide how to handle an incoming refund request.",
            "confidence": 0.86,
            "freshness_days": 20,
            "source": "notion://wiki/refund-policy",
            "rule": {
                "variables": [
                    {
                        "name": "subscription_months",
                        "tool": "billing.get_subscription",
                        "params": {"customer_id": "{{customer_id}}"},
                        "output_field": "months_active",
                        "type": "number",
                        "description": "How long the customer has been subscribed.",
                    },
                    {
                        "name": "ltv",
                        "tool": "crm.get_customer",
                        "params": {"customer_id": "{{customer_id}}"},
                        "output_field": "lifetime_value",
                        "type": "number",
                        "description": "Customer lifetime value in USD.",
                    },
                    {
                        "name": "risk_flags",
                        "tool": "support.get_history",
                        "params": {"customer_id": "{{customer_id}}"},
                        "output_field": "risk_flags",
                        "type": "list",
                        "description": "Risk / fraud flags from support history.",
                    },
                    {
                        "name": "refund_amount",
                        "tool": "billing.get_open_refund",
                        "params": {"customer_id": "{{customer_id}}"},
                        "output_field": "amount",
                        "type": "number",
                        "description": "Dollar amount of the requested refund.",
                    },
                ],
                "branches": [
                    {
                        "when": {
                            "kind": "any",
                            "any": [
                                {
                                    "kind": "predicate",
                                    "var": "risk_flags",
                                    "op": "contains",
                                    "value": "chargeback_fraud",
                                }
                            ],
                        },
                        "then": {
                            "action": "escalate_to_finance",
                            "requires_approval": True,
                            "label": "Fraud / chargeback flag present - escalate to Finance.",
                        },
                    },
                    {
                        "when": {
                            "kind": "all",
                            "all": [
                                {
                                    "kind": "predicate",
                                    "var": "subscription_months",
                                    "op": "gte",
                                    "value": 12,
                                },
                                {
                                    "kind": "predicate",
                                    "var": "ltv",
                                    "op": "gte",
                                    "value": 10000,
                                },
                            ],
                        },
                        "then": {
                            "action": "approve_refund",
                            "requires_approval": False,
                            "label": "Loyal, high-value customer - auto-approve.",
                        },
                    },
                ],
                "default": {
                    "action": "manual_review",
                    "requires_approval": True,
                    "label": "Send to a support lead for manual review.",
                },
            },
        }
    ],
    "exceptions": [
        {
            "key": "high_value_refund",
            "name": "High-value refund hold",
            "requires_approval": True,
            "action": "approve_refund",
            "condition": {
                "kind": "predicate",
                "var": "refund_amount",
                "op": "gte",
                "value": 5000,
            },
            "description": (
                "Refunds of $5,000 or more require explicit Finance approval, even "
                "when auto-approve conditions are met."
            ),
            "confidence": 0.8,
            "freshness_days": 20,
            "source": "notion://wiki/refund-policy",
        }
    ],
    "stakeholders": [
        {
            "key": "finance_team",
            "name": "Finance Team",
            "confidence": 0.95,
            "freshness_days": 20,
            "source": "notion://wiki/refund-policy",
        }
    ],
    "edges": [
        {"type": "GOVERNS", "src": "refund_policy", "dst": "refund_decision"},
        {"type": "GOVERNS", "src": "high_value_refund", "dst": "refund_decision"},
        {"type": "APPROVED_BY", "src": "refund_policy", "dst": "finance_team"},
    ],
}

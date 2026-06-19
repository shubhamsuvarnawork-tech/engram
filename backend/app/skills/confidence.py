"""Confidence & freshness scoring for generated skills.

A skill is only as trustworthy as the knowledge it was compiled from. We combine
each source node's ``confidence`` with an exponential decay on its
``freshness_days`` so that stale or low-confidence knowledge drags the skill's
score down — which is exactly what the runtime uses to decide auto-execute vs.
human review.
"""
from __future__ import annotations

from typing import Iterable

from app.graph.schema import GraphNode

FRESHNESS_HALF_LIFE_DAYS = 180.0


def freshness_decay(days: float, half_life: float = FRESHNESS_HALF_LIFE_DAYS) -> float:
    if days <= 0:
        return 1.0
    return 0.5 ** (days / half_life)


def freshness_score(nodes: Iterable[GraphNode]) -> float:
    nodes = list(nodes)
    if not nodes:
        return 0.0
    return round(sum(freshness_decay(n.freshness_days) for n in nodes) / len(nodes), 4)


def confidence_score(nodes: Iterable[GraphNode]) -> float:
    nodes = list(nodes)
    if not nodes:
        return 0.0
    vals = [n.confidence * freshness_decay(n.freshness_days) for n in nodes]
    return round(sum(vals) / len(vals), 4)

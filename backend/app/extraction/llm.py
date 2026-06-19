"""LLM client abstraction for knowledge extraction.

The LLM's job is narrow and upstream: turn messy prose (a wiki page, a Slack
thread, a ticket) into the structured decision graph the rest of the platform
compiles deterministically. Keeping it behind an interface means:

* tests/demos use ``MockLLMClient`` and run fully offline, and
* production swaps in ``AnthropicLLMClient`` (or any other) with no code change.
"""
from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from typing import Optional

EXTRACTION_CONTRACT = """\
Return ONLY JSON with these optional top-level arrays: facts, policies,
processes, decisions, exceptions, stakeholders, systems, entities, edges.
Every node has a stable "key", a "name", optional "confidence" (0..1),
"freshness_days", and "source". A decision additionally has a "rule" with
"variables" (name, tool, params, output_field), ordered "branches"
(when -> then) and a "default" outcome. Edges are {type, src, dst} referencing
node keys; type is one of GOVERNS, APPROVED_BY, HAS, USES, NEXT, ESCALATES_TO.
"""


class LLMClient(ABC):
    @abstractmethod
    def extract(self, text: str) -> dict:
        """Extract structured knowledge from raw text (see EXTRACTION_CONTRACT)."""


class MockLLMClient(LLMClient):
    """Deterministic, offline extractor. Recognises bundled samples by keyword."""

    def extract(self, text: str) -> dict:
        t = text.lower()
        if "refund" in t:
            from app.seed.sample_docs import REFUND_EXTRACTION

            return REFUND_EXTRACTION
        return {}


class AnthropicLLMClient(LLMClient):
    """Real extractor backed by Claude. Guarded so the platform runs offline."""

    SYSTEM = (
        "You are the knowledge extraction engine for Company Brain. You convert "
        "company documents into a structured decision graph. " + EXTRACTION_CONTRACT
    )

    def __init__(self, model: str = "claude-sonnet-4-6", api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")

    def extract(self, text: str) -> dict:
        if not self.api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set; use MockLLMClient for offline runs."
            )
        import httpx

        resp = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": self.model,
                "max_tokens": 4096,
                "system": self.SYSTEM,
                "messages": [
                    {"role": "user", "content": f"Extract the decision graph:\n\n{text}"}
                ],
            },
            timeout=60,
        )
        resp.raise_for_status()
        return json.loads(_strip_fences(resp.json()["content"][0]["text"]))


def _strip_fences(s: str) -> str:
    s = s.strip()
    if s.startswith("```"):
        s = s.split("\n", 1)[1] if "\n" in s else s
        s = s.rsplit("```", 1)[0]
    return s.strip()


def get_llm_client() -> LLMClient:
    """Pick a client from the environment: real if a key is present, else mock."""
    if os.environ.get("ANTHROPIC_API_KEY"):
        return AnthropicLLMClient()
    return MockLLMClient()

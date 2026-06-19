import os
import tempfile

# Bind a clean, file-based sqlite DB before importing any app module so that
# config -> engine -> Base -> models all agree on one database for the session.
_TEST_DB = os.path.join(tempfile.gettempdir(), "companybrain_test.db")
if os.path.exists(_TEST_DB):
    os.remove(_TEST_DB)
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB}"
os.environ["GRAPH_BACKEND"] = "memory"

import pytest

from app.extraction.extractor import KnowledgeExtractor
from app.extraction.llm import MockLLMClient
from app.graph.store import InMemoryGraphStore
from app.runtime.tools import default_registry
from app.seed.sample_docs import SAMPLE_REFUND_DOC
from app.skills.generator import SkillGenerator

COMPANY = "acme"


@pytest.fixture
def store():
    s = InMemoryGraphStore()
    KnowledgeExtractor(s, MockLLMClient()).ingest_document(SAMPLE_REFUND_DOC, COMPANY)
    return s


@pytest.fixture
def skill(store):
    return SkillGenerator(store).generate("refund_customer", COMPANY)


@pytest.fixture
def registry():
    return default_registry()

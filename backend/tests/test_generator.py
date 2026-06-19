import pytest

from app.skills.generator import SkillGenerationError, SkillGenerator
from app.skills.models import StepType


def test_inputs_discovered_from_graph(skill):
    assert [i.name for i in skill.inputs] == ["customer_id"]


def test_fetch_before_decide_before_act(skill):
    phases = {StepType.DATA_FETCH: 0, StepType.DECISION: 1, StepType.ACTION: 2}
    seq = [phases[s.type] for s in skill.steps]
    assert seq == sorted(seq), "steps must be ordered fetch -> decide -> act"


def test_every_consumed_var_is_produced(skill):
    produced = {s.produces for s in skill.steps if s.type == StepType.DATA_FETCH}
    for s in skill.steps:
        if s.type == StepType.DECISION:
            assert set(s.consumes) <= produced


def test_all_outcome_actions_present(skill):
    actions = {s.action for s in skill.steps if s.type == StepType.ACTION}
    assert actions == {"approve_refund", "escalate_to_finance", "manual_review"}


def test_auto_approve_path_needs_no_step_approval(skill):
    approve = next(s for s in skill.steps if s.action == "approve_refund")
    escalate = next(s for s in skill.steps if s.action == "escalate_to_finance")
    assert approve.requires_approval is False
    assert escalate.requires_approval is True


def test_guard_extracted_from_exception(skill):
    assert len(skill.guards) == 1
    g = skill.guards[0]
    assert g.action == "approve_refund"
    assert g.requires_approval is True
    assert g.condition is not None  # conditional on refund_amount


def test_confidence_scored_and_bounded(skill):
    assert 0.0 < skill.confidence <= 1.0
    assert 0.0 < skill.freshness <= 1.0


def test_provenance_links_back_to_sources(skill):
    assert len(skill.provenance.node_ids) >= 4
    assert "notion://wiki/refund-policy" in skill.provenance.sources


def test_unknown_goal_raises(store):
    with pytest.raises(SkillGenerationError):
        SkillGenerator(store).generate("provision_server", "acme")

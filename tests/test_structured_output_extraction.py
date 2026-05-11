import pytest
import json
from gamma_runtime.structured_output import StructuredOutputExtractor

def test_extract_clean_json():
    content = '{"study_question": "test?", "claim_type": "proposal_value"}'
    result = StructuredOutputExtractor.extract_json(content)
    assert result is not None
    assert result["study_question"] == "test?"

def test_extract_fenced_json():
    content = 'Here is the result:\n```json\n{"study_question": "fenced?", "claim_type": "proposal_value"}\n```\nHope it helps.'
    result = StructuredOutputExtractor.extract_json(content)
    assert result is not None
    assert result["study_question"] == "fenced?"

def test_extract_channel_contamination():
    content = '{"study_question": "part1"}<channel|>{"study_question": "part2", "claim_type": "proposal_value", "intended_action": "propose_only", "python_or_analysis_requirement": "none", "parameters_with_units": {}, "expected_artifacts": [], "validation_gates": [], "next_handoff": "slot_02"}'
    result = StructuredOutputExtractor.extract_json(content)
    assert result is not None
    assert result["study_question"] == "part2" # Should pick the one with better rubric score

def test_extract_concatenated_json_no_channel():
    content = '{"q": 1}{"study_question": "q2", "claim_type": "proposal_value"}'
    result = StructuredOutputExtractor.extract_json(content)
    assert result is not None
    # Depending on implementation, it might pick the first one or second one.
    # Our _find_json_candidates (stack-based) will find both.
    # q2 has better rubric score.
    assert result["study_question"] == "q2"

def test_validate_rubric_missing_fields():
    data = {"study_question": "only one"}
    errors = StructuredOutputExtractor.validate_work_unit(data)
    assert len(errors) > 0
    assert any("Missing required field" in e for e in errors)

def test_validate_toy_empirical_forbidden():
    data = {
        "study_question": "q",
        "claim_type": "empirical_observation",
        "intended_action": "a",
        "python_or_analysis_requirement": "r",
        "parameters_with_units": {},
        "expected_artifacts": [],
        "validation_gates": [],
        "next_handoff": "h"
    }
    errors = StructuredOutputExtractor.validate_work_unit(data, is_toy=True)
    assert any("Forbidden claim_type 'empirical_observation'" in e for e in errors)

def test_validate_invalid_claim_type():
    data = {"claim_type": "invalid_type"}
    errors = StructuredOutputExtractor.validate_work_unit(data)
    assert any("Invalid claim_type" in e for e in errors)

import json
import re
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger("StructuredOutput")

REQUIRED_RUBRIC_FIELDS = [
    "study_question",
    "claim_type",
    "intended_action",
    "python_or_analysis_requirement",
    "parameters_with_units",
    "expected_artifacts",
    "validation_gates",
    "next_handoff"
]

ALLOWED_CLAIM_TYPES = [
    "proposal_value",
    "simulation_result",
    "empirical_observation",
    "truth_value",
    "rejected_invalid"
]

class StructuredOutputExtractor:
    @staticmethod
    def extract_json(content: str) -> Optional[Dict[str, Any]]:
        """
        Extracts a valid JSON object from content, handling fences and <channel|> contamination.
        """
        if not content:
            return None

        # 1. Handle <channel|> contamination by splitting
        segments = content.split("<channel|>")
        
        candidates = []
        for segment in segments:
            # Try to find JSON in this segment
            candidates.extend(StructuredOutputExtractor._find_json_candidates(segment))

        if not candidates:
            return None

        # 2. Score candidates based on rubric fulfillment
        scored_candidates = []
        for cand in candidates:
            try:
                data = json.loads(cand)
                if isinstance(data, dict):
                    score = StructuredOutputExtractor._score_rubric(data)
                    scored_candidates.append((score, data))
            except json.JSONDecodeError:
                continue

        if not scored_candidates:
            return None

        # 3. Sort by score (descending) and return the best one if it's unambiguous enough
        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        
        best_score, best_data = scored_candidates[0]
        
        if best_score == 0:
            # If even the best one has 0 score, check if it's just a simple JSON object
            # that might be valid for other reasons, but we prefer rubric-aligned ones.
            return best_data

        return best_data

    @staticmethod
    def _find_json_candidates(text: str) -> List[str]:
        """
        Locates potential JSON strings in a single text segment.
        """
        candidates = []
        
        # 1. Check for markdown blocks first
        fences = re.findall(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if fences:
            candidates.extend(fences)

        # 2. If no fences, or even if there are, try brace matching
        # We use a more careful approach than find/rfind to avoid greedy spans across multiple objects
        # However, nested braces make regex hard. We'll use a simple balance-based scanner.
        
        stack = []
        start_idx = -1
        for i, char in enumerate(text):
            if char == '{':
                if not stack:
                    start_idx = i
                stack.append('{')
            elif char == '}':
                if stack:
                    stack.pop()
                    if not stack:
                        candidates.append(text[start_idx:i+1])
        
        return candidates

    @staticmethod
    def _score_rubric(data: Dict[str, Any]) -> int:
        """
        Scores how many required rubric fields are present.
        """
        score = 0
        for field in REQUIRED_RUBRIC_FIELDS:
            if field in data:
                score += 1
        return score

    @staticmethod
    def validate_work_unit(data: Dict[str, Any], is_toy: bool = False) -> List[str]:
        """
        Validates the extracted JSON against the scientific work-unit requirements.
        Returns a list of error messages.
        """
        errors = []
        for field in REQUIRED_RUBRIC_FIELDS:
            if field not in data:
                errors.append(f"Missing required field: {field}")

        claim_type = data.get("claim_type")
        if claim_type and claim_type not in ALLOWED_CLAIM_TYPES:
            errors.append(f"Invalid claim_type: {claim_type}. Must be one of {ALLOWED_CLAIM_TYPES}")

        if is_toy:
            if claim_type == "empirical_observation":
                errors.append("Forbidden claim_type 'empirical_observation' for toy simulation.")
            if claim_type == "truth_value":
                errors.append("Forbidden claim_type 'truth_value' for toy simulation.")

        return errors

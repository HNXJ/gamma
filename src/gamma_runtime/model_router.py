import logging

logger = logging.getLogger("ModelRouter")

LMS_ROLE_MAPPING = {
    "biological_plausibility_01": "G03-analyst",
    "consensus_judge_01": "J01-judge",
    "e4b_critic": "G03-analyst",
    "e4b_macro": "G01-builder",
    "e4b_meso": "G02-tuner",
    "e4b_micro": "G01-builder",
    "hypothesis_builder_01": "G01-builder",
    "methods_skeptic_01": "G03-analyst",
    "v1_gamma_adversary": "G03-analyst",
    "v1_gamma_consensus": "J01-judge",
    "v1_gamma_proponent": "G01-builder",
    "G01": "G01-builder",
    "G02": "G02-tuner",
    "G03": "G03-analyst",
    "J01": "J01-judge",
    "M01": "M01-monitor"
}

def resolve_lms_identifier(agent_id: str, original_model_key: str) -> str:
    """
    Resolves a logical model key (e.g. 'gemma4-parallel') into a physical LMS
    identifier (e.g. 'G01-builder') based on the agent_id requesting it.
    If the original_model_key is already a resolved physical identifier, it passes through.
    """
    if original_model_key in ["G01-builder", "G02-tuner", "G03-analyst", "J01-judge", "M01-monitor"]:
        return original_model_key
        
    resolved = LMS_ROLE_MAPPING.get(agent_id, "G01-builder") # Default fallback
    logger.debug(f"Routed agent '{agent_id}' from logical key '{original_model_key}' to LMS identifier '{resolved}'")
    return resolved

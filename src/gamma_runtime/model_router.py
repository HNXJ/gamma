import logging
import json
import os

logger = logging.getLogger("ModelRouter")

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "context", "configs", "lms_routing.json")

class RoutingError(Exception):
    pass

def load_routing_config() -> dict:
    if not os.path.exists(CONFIG_PATH):
        logger.warning(f"Routing config not found at {CONFIG_PATH}")
        return {}
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def resolve_lms_identifier(agent_id: str, original_model_key: str, allow_fallback: bool = False) -> str:
    """
    Resolves a logical model key (e.g. 'gemma4-parallel') into a physical LMS
    identifier (e.g. 'G01-builder') based on the agent_id requesting it.
    If the original_model_key is already a resolved physical identifier, it passes through.
    """
    if original_model_key in ["G01-builder", "G02-tuner", "G03-analyst", "J01-judge", "M01-monitor"]:
        return original_model_key
        
    mapping = load_routing_config()
    
    if agent_id in mapping:
        resolved = mapping[agent_id]
        logger.debug(f"Routed agent '{agent_id}' from logical key '{original_model_key}' to LMS identifier '{resolved}'")
        return resolved
        
    if allow_fallback:
        logger.warning(f"Using degraded-mode fallback to 'G01-builder' for unmapped agent '{agent_id}'")
        return "G01-builder"
        
    raise RoutingError(f"No explicit LMS routing mapping found for agent '{agent_id}'. Original logical key was '{original_model_key}'.")

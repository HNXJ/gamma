import logging
import json
import os

logger = logging.getLogger("ModelRouter")

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "context", "configs", "lms_routing.json")

class RoutingError(Exception):
    pass

def load_routing_config() -> dict:
    if not os.path.exists(CONFIG_PATH):
        logger.error(f"CRITICAL: Routing config not found at {CONFIG_PATH}")
        return {}
    with open(CONFIG_PATH, "r") as f:
        data = json.load(f)
        if "__WARNING__" in data: del data["__WARNING__"]
        return data

def resolve_lms_identifier(agent_id: str, original_model_key: str, allow_fallback: bool = False) -> str:
    """
    Resolves a logical model key into a physical LMS identifier.
    STRICT MODE: No silent fallback allowed unless explicitly overridden.
    """
    # 1. Direct pass-through for known physical identifiers
    PHYSICAL_IDS = ["G01-builder", "G02-tuner", "G03-analyst", "J01-judge", "M01-monitor"]
    if original_model_key in PHYSICAL_IDS:
        return original_model_key
        
    mapping = load_routing_config()
    
    # 2. Check explicit agent mapping
    if agent_id in mapping:
        resolved = mapping[agent_id]
        logger.info(f"ROUTING: Agent '{agent_id}' -> '{resolved}' (via explicit map)")
        return resolved
        
    # 3. Check explicit logical model mapping
    if original_model_key in mapping:
        resolved = mapping[original_model_key]
        logger.info(f"ROUTING: Logical Key '{original_model_key}' -> '{resolved}'")
        return resolved

    # 4. Fallback is PROHIBITED in production hardening
    if allow_fallback:
        logger.warning(f"ROUTING FALLBACK: Agent '{agent_id}' using 'G01-builder' (NOT RECOMMENDED)")
        return "G01-builder"
        
    raise RoutingError(
        f"HARDENING FAILURE: No explicit LMS routing mapping found for agent '{agent_id}'. "
        f"Divergence detected from office-dev doctrine. Mapping target: {original_model_key}"
    )

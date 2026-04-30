from typing import List, Set, Dict
from .types import AgentSpec, ModelSpec

def resolve_runtime_name(model: ModelSpec, agent_id: str) -> str:
    """
    Enforces the naming rule: {model_key}-{quant}-{backend}-{agent_id}
    """
    quant = model.quantization or "unknown"
    backend = model.provider
    return f"{model.key}-{quant}-{backend}-{agent_id}"

def validate_identity_uniqueness(agents: List[AgentSpec], model_map: Dict[str, ModelSpec]) -> bool:
    """
    Verifies that all agents in a team have unique resolved runtime names.
    """
    names: Set[str] = set()
    
    for agent in agents:
        model = model_map.get(agent.model_key)
        if not model:
            # If model is missing, it's an orchestration failure, but here we focus on collision
            continue
        name = resolve_runtime_name(model, agent.agent_id)
        if name in names:
            return False
        names.add(name)
    return True

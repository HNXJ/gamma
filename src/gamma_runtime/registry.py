import json
from pathlib import Path
from .types import AgentSpec, ModelSpec

class RuntimeRegistry:
    """
    Central registry for loading declarative configurations.
    Pivoted to JSON to ensure zero-dependency execution in restricted environments.
    """
    def __init__(self, config_root: str):
        self.root = Path(config_root).expanduser().resolve()

    def load_model(self, key: str) -> ModelSpec:
        path = self.root / "models" / f"{key}.json"
        with open(path, "r") as f:
            data = json.load(f)
        return ModelSpec(**data)

    def load_agent(self, agent_id: str) -> AgentSpec:
        path = self.root / "agents" / f"{agent_id}.json"
        with open(path, "r") as f:
            data = json.load(f)
        return AgentSpec(**data)

    def load_team(self, team_id: str) -> dict:
        path = self.root / "teams" / f"{team_id}.json"
        with open(path, "r") as f:
            return json.load(f)

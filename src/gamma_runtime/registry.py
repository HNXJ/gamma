import json
from pathlib import Path
from .structs import ModelSpec, AgentSpec

class RuntimeRegistry:
    def __init__(self, root: str):
        self.root = Path(root).expanduser().resolve()

    def load_model(self, model_key: str) -> ModelSpec:
        path = self.root / "models" / f"{model_key}.json"
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

    # Backward-compatible aliases
    def get_model(self, model_key: str):
        return self.load_model(model_key)

    def get_agent(self, agent_id: str):
        return self.load_agent(agent_id)

    def get_team(self, team_id: str):
        return self.load_team(team_id)

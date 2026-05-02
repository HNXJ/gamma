import json
from pathlib import Path
from .runtime_types import AgentSpec, ModelSpec
from . import config
from .player_identity import PlayerIdentityManager

class RuntimeRegistry:
    """
    Central registry for loading declarative configurations.
    Pivoted to JSON to ensure zero-dependency execution in restricted environments.
    """
    def __init__(self, config_root: str):
        self.root = Path(config_root).expanduser().resolve()
        # Initialize player manager relative to the registry root
        self.player_manager = PlayerIdentityManager(self.root.parent.parent)

    def load_model(self, key: str) -> ModelSpec:
        if config.DEVELOPER_GUEST_MODE and key.startswith("dev-"):
            username = key[4:-6] # extract username from dev-{username}-model
            accounts = {a['username']: a for a in self.player_manager.list_accounts()}
            if username in accounts:
                account_id = accounts[username]['account_id']
                bindings = self.player_manager.get_bindings(account_id)
                if bindings:
                    binding = bindings[0] # Take first active binding for dev shim
                    return ModelSpec(
                        key=key,
                        provider="lmstudio" if binding['provider_kind'] == 'lmstudio' else "mlx",
                        name=binding['model_id'],
                        path=binding['provider_url']
                    )

        path = self.root / "models" / f"{key}.json"
        with open(path, "r") as f:
            data = json.load(f)
        import inspect
        fields = inspect.signature(ModelSpec).parameters
        filtered = {k: v for k, v in data.items() if k in fields}
        return ModelSpec(**filtered)

    def load_agent(self, agent_id: str) -> AgentSpec:
        if config.DEVELOPER_GUEST_MODE:
            accounts = {a['username']: a for a in self.player_manager.list_accounts()}
            if agent_id in accounts:
                account = accounts[agent_id]
                return AgentSpec(
                    agent_id=agent_id,
                    role=account.get('display_name', 'DevGuest'),
                    model_key=f"dev-{agent_id}-model",
                    system_prompt=f"You are a developer guest acting as {agent_id}."
                )

        path = self.root / "agents" / f"{agent_id}.json"
        with open(path, "r") as f:
            data = json.load(f)
        import inspect
        fields = inspect.signature(AgentSpec).parameters
        filtered = {k: v for k, v in data.items() if k in fields}
        return AgentSpec(**filtered)

    def load_team(self, team_id: str) -> dict:
        path = self.root / "teams" / f"{team_id}.json"
        with open(path, "r") as f:
            return json.load(f)

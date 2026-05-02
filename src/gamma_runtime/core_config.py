import os
import json
from pathlib import Path
from typing import Any, Dict, Optional

class CoreConfig:
    """
    Canonical configuration loader for Gamma Arena / Gamma runtime.
    Supports primary config file and local overrides.
    """
    def __init__(self, root_dir: Optional[str] = None):
        if root_dir:
            self.root = Path(root_dir).resolve()
        else:
            # Heuristic: CWD or parent of src/
            self.root = Path(os.getcwd()).resolve()
            if not (self.root / "context").exists() and (self.root.parent / "context").exists():
                self.root = self.root.parent

        self.primary_config_path = self.root / "context" / "configs" / "core" / "runtime_core.json"
        self.override_path = self.root / "local" / "runtime_overrides.json"
        
        self._data: Dict[str, Any] = {}
        self.load()

    def load(self):
        """Loads primary config and applies overrides."""
        # 1. Load primary
        if self.primary_config_path.exists():
            with open(self.primary_config_path, "r") as f:
                self._data = json.load(f)
        else:
            print(f"Warning: Primary config not found at {self.primary_config_path}")
            self._data = {}

        # 2. Apply local overrides
        if self.override_path.exists():
            try:
                with open(self.override_path, "r") as f:
                    overrides = json.load(f)
                    self._deep_update(self._data, overrides)
            except Exception as e:
                print(f"Warning: Failed to load overrides from {self.override_path}: {e}")

        # 3. Apply Environment variables (prefixed with GAMMA_)
        self._apply_env_overrides()

    def _deep_update(self, base: dict, overrides: dict):
        for k, v in overrides.items():
            if isinstance(v, dict) and k in base and isinstance(base[k], dict):
                self._deep_update(base[k], v)
            else:
                base[k] = v

    def _apply_env_overrides(self):
        """
        Supports GAMMA_SECTION__KEY=value (e.g. GAMMA_TIMING__HEARTBEAT_INTERVAL_SECONDS=10.5)
        Double underscore __ separates sections from keys or sub-sections.
        """
        for env_key, value in os.environ.items():
            if env_key.startswith("GAMMA_"):
                # Use __ as section separator
                parts = env_key[6:].lower().split("__")
                if not parts: continue
                
                curr = self._data
                for i, part in enumerate(parts[:-1]):
                    if part not in curr: curr[part] = {}
                    curr = curr[part]
                
                # Cast value if possible
                target_key = parts[-1]
                try:
                    if value.lower() in ("true", "false"):
                        curr[target_key] = value.lower() == "true"
                    elif "." in value:
                        curr[target_key] = float(value)
                    else:
                        curr[target_key] = int(value)
                except ValueError:
                    curr[target_key] = value

    def get(self, path: str, default: Any = None) -> Any:
        """Helper to get nested values using dot notation (e.g. 'network.hub_port')"""
        parts = path.split(".")
        curr = self._data
        for part in parts:
            if isinstance(curr, dict) and part in curr:
                curr = curr[part]
            else:
                return default
        return curr

# Singleton instance for runtime access
config = CoreConfig()

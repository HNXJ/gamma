import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables from .env if present
load_dotenv()

class Config(BaseModel):
    base_url: str = Field(default="http://127.0.0.1:1234/v1", alias="GUARD_BASE_URL")
    api_key: str = Field(default="lm-studio", alias="GUARD_API_KEY")
    model: str = Field(default="gemma-4-e4b-it-mxfp8", alias="GUARD_MODEL")
    
    sandbox_dir: Path = Field(default=Path("./sandbox"), alias="GUARD_SANDBOX_DIR")
    repo_root: Path = Field(default=Path("."), alias="GUARD_REPO_ROOT")
    
    poll_interval_sec: int = Field(default=5, alias="GUARD_POLL_INTERVAL_SEC")
    max_iterations: int = Field(default=10, alias="GUARD_MAX_ITERATIONS")
    max_memory_chars: int = Field(default=10000, alias="GUARD_MAX_MEMORY_CHARS")
    command_timeout_sec: int = Field(default=120, alias="GUARD_COMMAND_TIMEOUT_SEC")
    
    audit_log: Path = Field(default=Path("state/guard-audit.jsonl"), alias="GUARD_AUDIT_LOG")
    memory_log: Path = Field(default=Path("state/guard-state.md"), alias="GUARD_MEMORY_LOG")

    class Config:
        populate_by_name = True

def get_config() -> Config:
    config_dict = {
        "GUARD_BASE_URL": os.getenv("GUARD_BASE_URL", "http://127.0.0.1:1234/v1"),
        "GUARD_API_KEY": os.getenv("GUARD_API_KEY", "lm-studio"),
        "GUARD_MODEL": os.getenv("GUARD_MODEL", "gemma-4-e4b-it-mxfp8"),
        "GUARD_SANDBOX_DIR": os.getenv("GUARD_SANDBOX_DIR", "./sandbox"),
        "GUARD_REPO_ROOT": os.getenv("GUARD_REPO_ROOT", "."),
        "GUARD_POLL_INTERVAL_SEC": int(os.getenv("GUARD_POLL_INTERVAL_SEC", "5")),
        "GUARD_MAX_ITERATIONS": int(os.getenv("GUARD_MAX_ITERATIONS", "10")),
        "GUARD_MAX_MEMORY_CHARS": int(os.getenv("GUARD_MAX_MEMORY_CHARS", "10000")),
        "GUARD_COMMAND_TIMEOUT_SEC": int(os.getenv("GUARD_COMMAND_TIMEOUT_SEC", "30")),
        "GUARD_AUDIT_LOG": os.getenv("GUARD_AUDIT_LOG", "state/guard-audit.jsonl"),
        "GUARD_MEMORY_LOG": os.getenv("GUARD_MEMORY_LOG", "state/guard-state.md"),
    }
    return Config(**config_dict)

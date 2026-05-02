import os
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional
from .core_config import config

ROLE_CONTENT_ADMIN = "content_admin"
ROLE_WORLD_OPERATOR = "world_operator"
ROLE_TRUTH_ADMIN = "truth_admin"

class ContentAuthorizationError(Exception):
    """Raised when a user lacks content mutation privileges."""
    pass

class TruthAuthorizationError(Exception):
    """Raised when a user attempts truth mutation without privileges."""
    pass

def can_edit_content(account: Optional[Dict[str, Any]]) -> bool:
    """Check if the account has content administration privileges."""
    if not account:
        return False
    roles = account.get("roles", [])
    # In a full RBAC, truth_admin might imply content_admin, but we keep it explicit.
    return ROLE_CONTENT_ADMIN in roles or ROLE_TRUTH_ADMIN in roles

def can_edit_truth(account: Optional[Dict[str, Any]]) -> bool:
    """Check if the account has truth mutation privileges."""
    if not account:
        return False
    roles = account.get("roles", [])
    return ROLE_TRUTH_ADMIN in roles

def can_control_runtime(account: Optional[Dict[str, Any]]) -> bool:
    """Check if the account has runtime/world operator privileges."""
    if not account:
        return False
    roles = account.get("roles", [])
    return ROLE_WORLD_OPERATOR in roles or ROLE_TRUTH_ADMIN in roles

class ContentAuditLogger:
    """
    Append-only audit log for content mutations (blog, wiki, docs).
    Non-truth-bearing.
    """
    def __init__(self, root_dir: Optional[str] = None):
        self.root = Path(root_dir) if root_dir else config.root
        self.log_path = self._resolve_path(config.get("paths.audit_logs", "local/logs/audit"))
        self.log_path.mkdir(parents=True, exist_ok=True)
        self.content_log_file = self.log_path / "content_mutations.jsonl"

    def _resolve_path(self, path_str: str) -> Path:
        p = Path(path_str)
        if p.is_absolute():
            return p
        return self.root / p

    def log_action(self, account_id: str, action: str, target: str, metadata: Optional[Dict[str, Any]] = None):
        entry = {
            "timestamp": time.time(),
            "account_id": account_id,
            "action": action,
            "target": target,
            "metadata": metadata or {}
        }
        with open(self.content_log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

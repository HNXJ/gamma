import os
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from .core_config import config
from .content_admin import can_edit_content, ContentAuthorizationError, ContentAuditLogger

class ContentService:
    """
    Manages content surfaces (Roadmap, Wiki, Docs) with RBAC.
    """
    def __init__(self, root_dir: Optional[str] = None):
        self.root = Path(root_dir) if root_dir else config.root
        self.content_path = self._resolve_path(config.get("paths.content_root", "local/content"))
        self.content_path.mkdir(parents=True, exist_ok=True)
        self.audit_logger = ContentAuditLogger(root_dir)

    def _resolve_path(self, path_str: str) -> Path:
        p = Path(path_str)
        if p.is_absolute():
            return p
        return self.root / p

    def _get_surface_path(self, surface: str) -> Path:
        p = self.content_path / surface
        p.mkdir(parents=True, exist_ok=True)
        return p

    def list_pages(self, surface: str) -> List[str]:
        p = self._get_surface_path(surface)
        return [f.name for f in p.glob("*.md")]

    def read_page(self, surface: str, page_id: str) -> Optional[str]:
        p = self._get_surface_path(surface) / f"{page_id}.md"
        if not p.exists():
            return None
        with open(p, "r") as f:
            return f.read()

    def write_page(self, account: Dict[str, Any], surface: str, page_id: str, content: str, metadata: Optional[Dict] = None):
        if not can_edit_content(account):
            raise ContentAuthorizationError("Account lacks content_admin privileges.")

        p = self._get_surface_path(surface) / f"{page_id}.md"
        
        # Write content
        with open(p, "w") as f:
            f.write(content)

        # Audit log
        self.audit_logger.log_action(
            account_id=account["account_id"],
            action="EDIT",
            target=f"{surface}/{page_id}",
            metadata=metadata
        )
        return True

    def publish_page(self, account: Dict[str, Any], surface: str, page_id: str, metadata: Optional[Dict] = None):
        if not can_edit_content(account):
            raise ContentAuthorizationError("Account lacks content_admin privileges.")
            
        # For this pass, 'publish' just means marking it as published in the audit log
        # or moving it to a 'published' subdirectory. Let's just log it.
        self.audit_logger.log_action(
            account_id=account["account_id"],
            action="PUBLISH",
            target=f"{surface}/{page_id}",
            metadata=metadata
        )
        return True

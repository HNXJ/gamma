import os
import json
import hashlib
import time
import uuid
import secrets
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import List, Optional, Dict, Any
from .core_config import config

@dataclass
class PlayerAccount:
    account_id: str
    username: str
    password_hash: str # Format: salt:hash
    display_name: str
    enabled: bool = True
    dev_only: bool = True
    created_at: float = field(default_factory=time.time)
    last_login_at: Optional[float] = None

@dataclass
class ProviderBinding:
    binding_id: str
    account_id: str
    provider_kind: str
    provider_url: str
    model_id: str
    api_key_ref: str
    active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SessionLease:
    session_id: str
    account_id: str
    binding_id: str
    attached_at: float = field(default_factory=time.time)
    detached_at: Optional[float] = None
    active: bool = True

class PlayerIdentityManager:
    """
    Minimal provider-agnostic player account foundation.
    Salted PBKDF2-HMAC hashing, non-truth-bearing.
    """
    def __init__(self, root_dir: Optional[str] = None):
        self.root = Path(root_dir) if root_dir else config.root
        
        # Resolve paths from config with root-relative fallback
        self.accounts_path = self._resolve_path(config.get("paths.player_accounts", "local/player_accounts"))
        self.sessions_path = self._resolve_path(config.get("paths.player_sessions", "local/player_sessions"))
        self.inventory_path = self._resolve_path(config.get("paths.inventory_root", "local/player_inventory"))
        self.mail_path = self._resolve_path(config.get("paths.mail_root", "local/player_mail"))
        
        for p in [self.accounts_path, self.sessions_path, self.inventory_path, self.mail_path]:
            p.mkdir(parents=True, exist_ok=True)

    def _resolve_path(self, path_str: str) -> Path:
        p = Path(path_str)
        if p.is_absolute():
            return p
        return self.root / p

    def _hash_password(self, password: str, salt: Optional[bytes] = None) -> str:
        if salt is None:
            salt = secrets.token_bytes(16)
        iterations = 100_000
        dk = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, iterations)
        return f"{salt.hex()}:{dk.hex()}"

    def _verify_password(self, password: str, stored_hash: str) -> bool:
        try:
            salt_hex, hash_hex = stored_hash.split(':')
            salt = bytes.fromhex(salt_hex)
            new_hash = self._hash_password(password, salt)
            return secrets.compare_digest(new_hash, stored_hash)
        except:
            return False

    def _load_json(self, path: Path) -> dict:
        if not path.exists(): return {}
        try:
            with open(path, "r") as f: return json.load(f)
        except: return {}

    def _save_json(self, path: Path, data: dict):
        with open(path, "w") as f: json.dump(data, f, indent=2)

    def sign_up(self, username, password, display_name=None) -> Optional[Dict]:
        accounts = self._load_json(self.accounts_path / "registry.json")
        if username in accounts: return None
        
        account_id = str(uuid.uuid4())
        account = PlayerAccount(
            account_id=account_id,
            username=username,
            password_hash=self._hash_password(password),
            display_name=display_name or username
        )
        accounts[username] = asdict(account)
        self._save_json(self.accounts_path / "registry.json", accounts)
        
        # Initialize persistent inventory
        self._save_json(self.inventory_path / f"{account_id}.json", {
            "account_id": account_id,
            "items": []
        })
        
        # Initialize persistent mailbox
        self._save_json(self.mail_path / f"{account_id}.json", {
            "account_id": account_id,
            "mailbox": [{"sender": "SYSTEM", "content": f"Welcome to Gamma Arena, {username}!"}]
        })
        
        return accounts[username]

    def sign_in(self, username, password) -> Optional[Dict]:
        accounts = self._load_json(self.accounts_path / "registry.json")
        acc = accounts.get(username)
        if acc and self._verify_password(password, acc['password_hash']):
            acc['last_login_at'] = time.time()
            accounts[username] = acc
            self._save_json(self.accounts_path / "registry.json", accounts)
            return acc
        return None

    def create_binding(self, account_id, provider_kind, provider_url, model_id, api_key_ref) -> Dict:
        bindings = self._load_json(self.accounts_path / "bindings.json")
        if account_id not in bindings: bindings[account_id] = []
        
        binding_id = str(uuid.uuid4())
        binding = ProviderBinding(
            binding_id=binding_id,
            account_id=account_id,
            provider_kind=provider_kind,
            provider_url=provider_url,
            model_id=model_id,
            api_key_ref=api_key_ref
        )
        bindings[account_id].append(asdict(binding))
        self._save_json(self.accounts_path / "bindings.json", bindings)
        return asdict(binding)

    def create_session(self, account_id, binding_id) -> Dict:
        sessions = self._load_json(self.sessions_path / "active.json")
        session_id = str(uuid.uuid4())
        lease = SessionLease(session_id=session_id, account_id=account_id, binding_id=binding_id)
        sessions[session_id] = asdict(lease)
        self._save_json(self.sessions_path / "active.json", sessions)
        return sessions[session_id]

    def sign_off(self, session_id):
        sessions = self._load_json(self.sessions_path / "active.json")
        if session_id in sessions:
            sessions[session_id]['active'] = False
            sessions[session_id]['detached_at'] = time.time()
            self._save_json(self.sessions_path / "active.json", sessions)
            return True
        return False

    def get_inventory(self, account_id) -> Dict:
        # Reattach persistent inventory and mail
        inventory = self._load_json(self.inventory_path / f"{account_id}.json")
        mail = self._load_json(self.mail_path / f"{account_id}.json")
        
        # Migration logic: if mail is missing but exists in legacy inventory file
        if not mail and "mailbox" in inventory:
            mail = {"account_id": account_id, "mailbox": inventory.get("mailbox", [])}
            # Optional: Clean up legacy mailbox from inventory object in memory
            # inventory.pop("mailbox", None) 
            
        return {
            "inventory": inventory,
            "mail": mail
        }

    def update_inventory(self, account_id, inventory_data):
        inventory_data["account_id"] = account_id # Enforce ownership
        self._save_json(self.inventory_path / f"{account_id}.json", inventory_data)

    def update_mail(self, account_id, mail_data):
        mail_data["account_id"] = account_id
        self._save_json(self.mail_path / f"{account_id}.json", mail_data)


    def get_bindings(self, account_id) -> List[Dict]:
        return self._load_json(self.accounts_path / "bindings.json").get(account_id, [])

    def list_accounts(self) -> List[dict]:
        return list(self._load_json(self.accounts_path / "registry.json").values())

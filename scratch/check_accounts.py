import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(os.path.abspath("src"))

from gamma_runtime.player_identity import PlayerIdentityManager
from gamma_runtime.core_config import config

def check():
    print(f"Config root: {config.root}")
    manager = PlayerIdentityManager()
    print(f"Accounts path: {manager.accounts_path}")
    accounts = manager.list_accounts()
    print(f"Accounts: {accounts}")
    
    for acc in accounts:
        bindings = manager.get_bindings(acc['account_id'])
        print(f"Bindings for {acc['username']}: {bindings}")

if __name__ == "__main__":
    check()

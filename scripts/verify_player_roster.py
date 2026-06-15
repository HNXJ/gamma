import os
import json
import sys
from pathlib import Path

# Setup paths
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(ROOT_DIR, 'src'))

from gamma_runtime.player_identity import PlayerIdentityManager

def verify():
    print("=== GAMMA ARENA: PLAYER ROSTER VERIFICATION ===")
    print(f"Root: {ROOT_DIR}")
    
    manager = PlayerIdentityManager(root_dir=ROOT_DIR)
    accounts = manager.list_accounts()
    
    print(f"Found {len(accounts)} registered players.\n")
    
    for username, acc in accounts.items():
        print(f"PLAYER: {username}")
        print(f"  Account ID: {acc.account_id}")
        print(f"  Display Name: {acc.display_name}")
        
        # Check Binding
        bindings = manager.list_bindings(acc.account_id)
        if bindings:
            print(f"  [PROVEN] Binding exists ({len(bindings)} found)")
        else:
            print(f"  [MISSING] No bindings found.")
            
        # Check Session
        session = manager.get_active_session(acc.account_id)
        if session:
            print(f"  [PROVEN] Active session exists: {session['session_id']}")
        else:
            print(f"  [STANDBY] No active session.")
            
        # Check Filesystem artifacts (Inventory/Mailbox)
        # Using a simplified check for now
        inv_path = Path(ROOT_DIR) / f"local/player_inventories/{acc.account_id}.json"
        mail_path = Path(ROOT_DIR) / f"local/player_mailboxes/{acc.account_id}.json"
        
        if inv_path.exists():
            print(f"  [PROVEN] Inventory persisted.")
        if mail_path.exists():
            print(f"  [PROVEN] Mailbox persisted.")
            
        print("-" * 40)

    print("\nVerification Complete.")

if __name__ == "__main__":
    verify()

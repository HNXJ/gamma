import sys
import os
import argparse
from pathlib import Path

# Add src to sys.path to allow importing gamma_runtime
ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR / "src"))

from gamma_runtime.player_identity import PlayerIdentityManager

def main():
    parser = argparse.ArgumentParser(description="Canonical Guest Onboarding Script")
    parser.add_argument("--username", required=True, help="Username for the new guest")
    parser.add_argument("--password", default="gamma2026", help="Password (default: gamma2026)")
    parser.add_argument("--display-name", help="Display name (defaults to username)")
    parser.add_argument("--model", default="qwen-2.5-7b-instruct", help="Model ID for binding")
    
    args = parser.parse_args()
    
    manager = PlayerIdentityManager(root_dir=str(ROOT_DIR))
    
    print(f"[*] Attempting to onboard: {args.username}")
    
    # 1. Sign Up
    account = manager.sign_up(
        username=args.username, 
        password=args.password, 
        display_name=args.display_name or args.username
    )
    
    if not account:
        print(f"[!] Account {args.username} already exists or failed to create.")
        # Try to retrieve it anyway to continue binding
        accounts = manager._load_json(manager.accounts_path / "registry.json")
        account = accounts.get(args.username)
        if not account:
            sys.exit(1)
    
    account_id = account["account_id"]
    print(f"[+] Account Created/Verified: {account_id}")
    
    # 2. Create Binding
    binding = manager.create_binding(
        account_id=account_id,
        provider_kind="lmstudio",
        provider_url="http://localhost:1234/v1",
        model_id=args.model,
        api_key_ref="LMS_LOCAL"
    )
    print(f"[+] Binding Created: {binding['binding_id']}")
    
    # 3. Create Session
    session = manager.create_session(
        account_id=account_id,
        binding_id=binding["binding_id"]
    )
    print(f"[+] Session Created: {session['session_id']}")
    
    print(f"\n[SUCCESS] {args.username} is now a canonical inhabitant of Gamma Arena.")

if __name__ == "__main__":
    main()

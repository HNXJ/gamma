import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(os.path.abspath("src"))

from gamma_runtime.player_identity import PlayerIdentityManager
from gamma_runtime.core_config import config

def onboard():
    print(f"Config root: {config.root}")
    manager = PlayerIdentityManager()
    
    # Ensure directories exist (though sign_up should do this)
    os.makedirs(manager.accounts_path, exist_ok=True)
    os.makedirs(manager.sessions_path, exist_ok=True)
    os.makedirs(manager.inventory_path, exist_ok=True)
    os.makedirs(manager.mail_path, exist_ok=True)
    
    username = "lite_guest_02"
    password = "password123"
    display_name = "Lite Guest 02"
    
    print(f"Attempting to sign up {username}...")
    account = manager.sign_up(username, password, display_name)
    if account:
        print(f"Successfully signed up {username}. Account ID: {account['account_id']}")
        
        # Create binding
        provider_kind = "lmstudio"
        provider_url = "http://localhost:1234/v1"
        model_id = "qwen-2.5-7b-instruct"
        
        print(f"Creating binding for {username}...")
        binding = manager.create_binding(account['account_id'], provider_kind, provider_url, model_id)
        if binding:
            print(f"Successfully created binding for {username}.")
        else:
            print(f"Failed to create binding for {username}.")
    else:
        print(f"Failed to sign up {username}. It might already exist.")

if __name__ == "__main__":
    onboard()

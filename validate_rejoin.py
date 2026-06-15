import os
import sys
import shutil
import time
from pathlib import Path

# Add src to path
sys.path.append(os.path.abspath("src"))

from gamma_runtime.player_identity import PlayerIdentityManager
from gamma_runtime.registry import RuntimeRegistry
import gamma_runtime.config as config

def test_rejoin_foundation():
    print("--- Starting Player Identity & Rejoin Validation ---")
    
    # Setup test env
    root_dir = Path("./test_gamma_rejoin_root")
    if root_dir.exists(): shutil.rmtree(root_dir)
    root_dir.mkdir(parents=True)
    (root_dir / "context" / "configs" / "agents").mkdir(parents=True)
    (root_dir / "context" / "configs" / "models").mkdir(parents=True)
    
    manager = PlayerIdentityManager(root_dir)
    
    # 1. Sign up two accounts
    print("1. Signing up accounts...")
    a1 = manager.sign_up("colleague_jane", "password123", "Jane Doe")
    a2 = manager.sign_up("colleague_bob", "password456", "Bob Smith")
    
    assert a1 is not None
    assert a2 is not None
    assert a1['username'] == "colleague_jane"
    assert ":" in a1['password_hash'] # Salted hash
    print("   [PASS] Sign up successful with salted hashing.")
    
    # 2. Sign in successfully
    print("2. Testing sign in...")
    login1 = manager.sign_in("colleague_jane", "password123")
    assert login1 is not None
    assert login1['account_id'] == a1['account_id']
    print("   [PASS] Sign in successful.")
    
    # 3. Wrong password rejected
    print("3. Testing wrong password rejection...")
    failed_login = manager.sign_in("colleague_jane", "wrongpass")
    assert failed_login is None
    print("   [PASS] Wrong password rejected.")
    
    # 4. Create provider binding
    print("4. Creating provider binding...")
    binding = manager.create_binding(a1['account_id'], "claude", "https://api.anthropic.com", "claude-3-opus", "CLAUDE_KEY_REF")
    assert binding['model_id'] == "claude-3-opus"
    print("   [PASS] Provider binding created.")
    
    # 5. Create session and simulate inventory/mailbox
    print("5. Creating session and inventory...")
    session = manager.create_session(a1['account_id'], binding['binding_id'])
    inventory = manager.get_inventory(a1['account_id'])
    inventory['items'].append({"id": "probe_01", "name": "Bio-Probe"})
    inventory['mailbox'].append({"sender": "M01", "content": "Initial audit complete."})
    manager.update_inventory(a1['account_id'], inventory)
    print("   [PASS] Session created and inventory updated.")
    
    # 6. Sign off
    print("6. Signing off...")
    success = manager.sign_off(session['session_id'])
    assert success is True
    print("   [PASS] Sign off successful.")
    
    # 7. Rejoin and verify persistence
    print("7. Testing rejoin (sign in again)...")
    rejoin_acc = manager.sign_in("colleague_jane", "password123")
    assert rejoin_acc['account_id'] == a1['account_id']
    
    rejoined_inventory = manager.get_inventory(rejoin_acc['account_id'])
    assert len(rejoined_inventory['items']) == 1
    assert rejoined_inventory['items'][0]['id'] == "probe_01"
    assert any(m['sender'] == "M01" for m in rejoined_inventory['mailbox'])
    print("   [PASS] Rejoin successful: same account_id and inventory restored.")
    
    # 8. Provider switch preserves identity
    print("8. Testing provider switch...")
    new_binding = manager.create_binding(a1['account_id'], "lmstudio", "http://localhost:1234", "local-model", "LMS_KEY_REF")
    new_session = manager.create_session(a1['account_id'], new_binding['binding_id'])
    
    final_inventory = manager.get_inventory(a1['account_id'])
    assert final_inventory['account_id'] == a1['account_id']
    assert len(final_inventory['items']) == 1
    print("   [PASS] Provider switch preserves account identity and inventory.")
    
    # Cleanup
    shutil.rmtree(root_dir)
    print("--- All Foundation Validation Steps Passed ---")
    return True

if __name__ == "__main__":
    if test_rejoin_foundation():
        sys.exit(0)
    else:
        sys.exit(1)

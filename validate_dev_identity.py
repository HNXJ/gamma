import os
import sys
import shutil
from pathlib import Path

# Add src to path
sys.path.append(os.path.abspath("src"))

from gamma_runtime.dev_identity import DevIdentityManager
from gamma_runtime.registry import RuntimeRegistry
import gamma_runtime.config as config

def test_dev_identity():
    print("--- Starting Dev Identity Validation ---")
    
    # Setup test env
    root_dir = Path("./test_gamma_root")
    if root_dir.exists(): shutil.rmtree(root_dir)
    root_dir.mkdir(parents=True)
    (root_dir / "context" / "configs" / "agents").mkdir(parents=True)
    (root_dir / "context" / "configs" / "models").mkdir(parents=True)
    
    # Create a dummy agent and model for backward compatibility check
    with open(root_dir / "context" / "configs" / "agents" / "standard_agent.json", "w") as f:
        f.write('{"agent_id": "standard_agent", "role": "Standard", "model_key": "standard_model", "system_prompt": "Standard prompt"}')
    with open(root_dir / "context" / "configs" / "models" / "standard_model.json", "w") as f:
        f.write('{"key": "standard_model", "provider": "lmstudio", "name": "standard-model"}')
    
    manager = DevIdentityManager(root_dir)
    
    # 1. Sign up two identities
    print("1. Signing up identities...")
    u1 = manager.sign_up("flash_builder", "secret123", "Flash Builder", ["builder"])
    u2 = manager.sign_up("lite_judge", "judge456", "Lite Judge", ["judge"])
    
    assert u1 is not None
    assert u2 is not None
    assert u1['username'] == "flash_builder"
    assert u1['password_hash'] != "secret123" # Must be hashed
    print("   [PASS] Sign up successful and passwords hashed.")
    
    # 2. Sign in successfully
    print("2. Testing sign in...")
    login1 = manager.sign_in("flash_builder", "secret123")
    assert login1 is not None
    assert login1['display_name'] == "Flash Builder"
    print("   [PASS] Sign in successful.")
    
    # 3. Rejected login fails
    print("3. Testing wrong password rejection...")
    failed_login = manager.sign_in("flash_builder", "wrongpass")
    assert failed_login is None
    print("   [PASS] Wrong password rejected.")
    
    # 4. Bind provider
    print("4. Binding provider...")
    binding = manager.bind_provider("flash_builder", "http://localhost:4474", "qwen-35b", "LMS_KEY", "lmstudio")
    assert binding['model_id'] == "qwen-35b"
    print("   [PASS] Provider binding successful.")
    
    # 5. Registry integration
    print("5. Testing registry integration (DEVELOPER_GUEST_MODE=True)...")
    config.DEVELOPER_GUEST_MODE = True
    registry = RuntimeRegistry(str(root_dir / "context" / "configs"))
    
    dev_agent = registry.load_agent("flash_builder")
    assert dev_agent.agent_id == "flash_builder"
    assert dev_agent.model_key == "dev-flash_builder-model"
    
    dev_model = registry.load_model(dev_agent.model_key)
    assert dev_model.name == "qwen-35b"
    assert dev_model.path == "http://localhost:4474"
    print("   [PASS] Registry recognized dev identity and model.")
    
    # 6. Backward compatibility
    print("6. Testing backward compatibility (DEVELOPER_GUEST_MODE=False)...")
    config.DEVELOPER_GUEST_MODE = False
    
    # Should still load standard agent
    std_agent = registry.load_agent("standard_agent")
    assert std_agent.role == "Standard"
    
    # Should FAIL to load dev agent (or load from file if exists, but here it doesn't)
    try:
        registry.load_agent("flash_builder")
        print("   [FAIL] Loaded dev agent while guest mode is OFF.")
        return False
    except FileNotFoundError:
        print("   [PASS] Dev agent not found when guest mode is OFF.")
    
    # Cleanup
    shutil.rmtree(root_dir)
    print("--- All Validation Steps Passed ---")
    return True

if __name__ == "__main__":
    if test_dev_identity():
        sys.exit(0)
    else:
        sys.exit(1)

import os
import sys
import json
from pathlib import Path

# Add src to path
sys.path.append(os.path.abspath("src"))

from gamma_runtime.core_config import CoreConfig

def test_config_resolution():
    print("--- Starting Core Config Resolution Test ---")
    
    # 1. Base resolution
    root_dir = Path("./test_config_root")
    if root_dir.exists():
        import shutil
        shutil.rmtree(root_dir)
    
    config_dir = root_dir / "context" / "configs" / "core"
    config_dir.mkdir(parents=True)
    
    base_config = {
        "network": {"hub_port": 8001},
        "timing": {"heartbeat_interval_seconds": 5.0}
    }
    with open(config_dir / "runtime_core.json", "w") as f:
        json.dump(base_config, f)
        
    cfg = CoreConfig(root_dir=str(root_dir))
    
    assert cfg.get("network.hub_port") == 8001
    assert cfg.get("timing.heartbeat_interval_seconds") == 5.0
    print("   [PASS] Base config loaded.")
    
    # 2. Local override
    local_dir = root_dir / "local"
    local_dir.mkdir(parents=True)
    with open(local_dir / "runtime_overrides.json", "w") as f:
        json.dump({"network": {"hub_port": 9001}}, f)
        
    cfg.load()
    assert cfg.get("network.hub_port") == 9001
    assert cfg.get("timing.heartbeat_interval_seconds") == 5.0
    print("   [PASS] Local override applied.")
    
    # 3. Env override
    os.environ["GAMMA_TIMING__HEARTBEAT_INTERVAL_SECONDS"] = "10.5"
    cfg.load()
    assert cfg.get("timing.heartbeat_interval_seconds") == 10.5
    print("   [PASS] Env override applied (typed).")
    
    # 4. Dot notation fallback
    assert cfg.get("non.existent.key", "fallback") == "fallback"
    print("   [PASS] Dot notation fallback works.")

    # Cleanup
    import shutil
    shutil.rmtree(root_dir)
    print("--- Core Config Validation Passed ---")
    return True

if __name__ == "__main__":
    if test_config_resolution():
        sys.exit(0)
    else:
        sys.exit(1)

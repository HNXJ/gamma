import os
from gamma.got.engine.persistence import ArenaPersistence

def test_isolation():
    # Simulate a non-truth worker environment
    os.environ.pop("AUTHORITY_TOKEN", None)
    os.environ["TRUTH_GATE_ENABLED"] = "1"
    
    p = ArenaPersistence(game_id="game001", root_dir="/Users/hamednejat/workspace/computational/gamma")
    try:
        p.save_state({"test": "value"})
        print("FAIL: Write succeeded without token")
    except PermissionError:
        print("SUCCESS: Write rejected without token")

if __name__ == "__main__":
    test_isolation()

import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(os.path.abspath("src"))

from gamma_runtime.registry import RuntimeRegistry
from gamma_runtime.core_config import config

def verify():
    print(f"Config root: {config.root}")
    # Initialize registry pointing to the correct config root
    registry = RuntimeRegistry(os.path.join(config.root, "context/configs"))
    
    print("Testing visibility for lite_guest_01...")
    try:
        agent1 = registry.load_agent("lite_guest_01")
        print(f"SUCCESS: lite_guest_01 visible. Spec: {agent1}")
    except Exception as e:
        print(f"FAILED: lite_guest_01 not visible. Error: {e}")

    print("\nTesting visibility for lite_guest_02...")
    try:
        agent2 = registry.load_agent("lite_guest_02")
        print(f"SUCCESS: lite_guest_02 visible. Spec: {agent2}")
    except Exception as e:
        print(f"FAILED: lite_guest_02 not visible. Error: {e}")

    # Test model loading too
    print("\nTesting model loading for lite_guest_02...")
    try:
        model2 = registry.load_model("dev-lite_guest_02-model")
        print(f"SUCCESS: lite_guest_02 model visible. Spec: {model2}")
    except Exception as e:
        print(f"FAILED: lite_guest_02 model not visible. Error: {e}")

if __name__ == "__main__":
    verify()

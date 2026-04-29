import sys
import os
import json
import asyncio

# Set up paths
ROOT = "/Users/HN/MLLM/gamma"
sys.path.append(ROOT)
sys.path.append(os.path.join(ROOT, "src"))

from gamma_runtime.bridge.v1_gamma_bridge import V1GammaBridge

class MockBlackboard:
    def __init__(self):
        self.entries = []
    async def add_entry(self, sender, content, metadata=None):
        self.entries.append({"sender": sender, "content": content, "metadata": metadata})
        print(f"BLACKBOARD UPDATE from {sender}: {content}")

async def main():
    bb = MockBlackboard()
    bridge = V1GammaBridge(bb, enabled=True)
    
    mock_proposal = """
    I suggest we test the following configuration:
    ```json
    {
        "seed_pair": 101,
        "healthy_params": {"pv_gain": 1.2},
        "schiz_params": {"pv_gain": 0.9},
        "rationale": "Testing gain reduction."
    }
    ```
    """
    
    print("--- Test 1: Valid Proposal ---")
    await bridge.process_proposal("agent_alpha", mock_proposal, 1)
    
    print("\n--- Test 2: Invalid Proposal ---")
    await bridge.process_proposal("agent_beta", "Just some text without JSON.", 2)
    
    print("\n--- Test 3: Stability Failure Proposal ---")
    fail_proposal = """
    ```json
    {
        "healthy_params": {}, "schiz_params": {},
        "rationale": "This will fail stability check."
    }
    ```
    """
    await bridge.process_proposal("agent_gamma", fail_proposal, 3)

if __name__ == "__main__":
    asyncio.run(main())

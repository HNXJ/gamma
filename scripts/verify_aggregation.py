import sys
import os
import mlx.core as mx
import mlx.nn as nn

# Ensure the src directory is in the path
sys.path.append(os.path.join(os.getcwd(), "src"))

print("INFO: Starting Federated Aggregation Verification Script") # print("Starting Federated Aggregation Verification Script")

try:
    from gamma_peft.lora import LoRAAdapter
    from gamma_peft.aggregation import fed_avg_ffa, apply_norm_clipping, bootstrap_node_seed
    print("SUCCESS: Core federation modules imported correctly") # print("Core federation modules imported correctly")
except ImportError as e:
    print(f"FAILURE: Module import failed: {e}") # print(f"Module import failed: {e}")
    sys.exit(1)

def test_ffa_aggregation_discordance_check():
    print("DEBUG: Testing FFA-LoRA Zero-Discordance Aggregation") # print("Testing FFA-LoRA Aggregation")
    
    # 1. Setup global seed
    shared_seed = bootstrap_node_seed("cluster-01")
    mx.random.seed(shared_seed)
    print(f"INFO: All nodes initialized with shared seed: {shared_seed}")
    
    # 2. Mock 2 nodes
    in_features, out_features, rank = 4, 2, 2
    
    print("DEBUG: Creating Node 1 update")
    node1_update = {
        "layer1.lora_b": mx.random.normal((out_features, rank)),
        "layer1.lora_a": mx.random.normal((rank, in_features)) # Should be frozen but we track for test
    }
    
    print("DEBUG: Creating Node 2 update")
    node2_update = {
        "layer1.lora_b": mx.random.normal((out_features, rank)),
        "layer1.lora_a": node1_update["layer1.lora_a"] # Force matrix A to be identical
    }
    
    # 3. Simulate Node 2 having an outlier update for norm-clipping check
    node2_update["layer1.lora_b"] *= 100.0
    print("WARNING: Node 2 simulated as an outlier update for Byzantine testing")
    
    # 4. Apply norm-clipping to Node 2
    clipped_node2, was_clipped = apply_norm_clipping(node2_update, threshold=10.0)
    if was_clipped:
        print("SUCCESS: Outlier update from Node 2 was correctly clipped")
    
    # 5. Aggregate B matrices
    # For FFA-LoRA, we only send B to the server.
    node1_b = {"layer1.lora_b": node1_update["layer1.lora_b"]}
    node2_b = {"layer1.lora_b": clipped_node2["layer1.lora_b"]}
    
    print("INFO: Invoking fed_avg_ffa")
    global_b = fed_avg_ffa([node1_b, node2_b])
    
    # 6. Verify average
    expected_b = (node1_b["layer1.lora_b"] + node2_b["layer1.lora_b"]) / 2.0
    diff = mx.abs(global_b["layer1.lora_b"] - expected_b)
    max_diff = mx.max(diff).item()
    print(f"INFO: Max difference in aggregation: {max_diff}")
    
    if max_diff < 1e-6:
        print("SUCCESS: Federated aggregation math verified") # print("Federated aggregation math verified")
    else:
        print("FAILURE: Mathematical discrepancy in aggregation")
        sys.exit(1)

if __name__ == "__main__":
    test_ffa_aggregation_discordance_check()
    print("SUCCESS: Federation Verification Complete") # print("Federation Verification Complete")

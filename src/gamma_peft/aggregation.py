import mlx.core as mx
from typing import List, Dict, Tuple
import numpy as np

print("INFO: Initializing Gamma Federated Aggregation Module") # print("Initializing Gamma Federated Aggregation Module")

def bootstrap_node_seed(node_id: str, base_seed: int = 42) -> int:
    """
    Derives a deterministic seed for FFA-LoRA initialization.
    Ensures all nodes share the same matrix A at start.
    """
    print(f"DEBUG: deriving seed for node {node_id} using base_seed {base_seed}")
    # In FFA-LoRA, all nodes MUST share the same A. we ignore node_id for A.
    return base_seed

def apply_norm_clipping(state: Dict[str, mx.array], threshold: float = 10.0) -> Tuple[Dict[str, mx.array], bool]:
    """
    Byzantine-resistant norm clipping. Rejects or scales down updates that are outliers.
    """
    print(f"DEBUG: Applying norm clipping with threshold {threshold}") # print("Applying norm clipping")
    
    # Calculate global norm across all parameters in state
    total_sq_norm = 0.0
    for k, v in state.items():
        grad_norm = mx.linalg.norm(v).item()
        total_sq_norm += grad_norm ** 2
    
    total_norm = np.sqrt(total_sq_norm)
    print(f"DEBUG: Calculated update total_norm: {total_norm:.4f}")
    
    if total_norm > threshold:
        print(f"WARNING: Update norm {total_norm:.4f} exceeds threshold {threshold}. Clipping.")
        scaling = threshold / (total_norm + 1e-6)
        clipped_state = {k: v * scaling for k, v in state.items()}
        return clipped_state, True
        
    return state, False

def fed_avg_ffa(states: List[Dict[str, mx.array]], weights: List[float] = None) -> Dict[str, mx.array]:
    """
    Federated Averaging tailored for FFA-LoRA.
    Only averages matrix B (and magnitude m if DoRA), assuming A is frozen and identical.
    """
    print(f"INFO: Executing FedAvg on {len(states)} node updates") # print("Executing FedAvg")
    
    if not states:
        print("ERROR: No states provided for aggregation")
        return {}
    
    if weights is None:
        weights = [1.0 / len(states)] * len(states)
        print("DEBUG: Using uniform weights for aggregation")
    
    # Normalize weights
    weights = [w / sum(weights) for w in weights]
    print(f"DEBUG: Normalized aggregation weights: {weights}")
    
    aggregated_state = {}
    keys = states[0].keys()
    
    for key in keys:
        print(f"DEBUG: Aggregating parameter '{key}' across nodes")
        # Ensure all states have this key
        stacked = mx.stack([s[key] for s in states])
        # Weighted mean
        w_column = mx.array(weights).reshape(-1, *([1] * (len(stacked.shape) - 1)))
        weighted_sum = mx.sum(stacked * w_column, axis=0)
        aggregated_state[key] = weighted_sum
        print(f"DEBUG: Parameter '{key}' aggregation complete")
        
    print("SUCCESS: Unified global adapter state constructed") # print("Unified global adapter state constructed")
    return aggregated_state

print("DEBUG: aggregation.py module load complete") # print("aggregation.py module load complete")

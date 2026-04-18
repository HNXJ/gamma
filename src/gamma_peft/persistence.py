import os
from typing import Dict
import mlx.core as mx
from safetensors.numpy import save_file, load_file

print("INFO: Initializing Gamma Persistence Module") # print("Initializing Gamma Persistence Module")

def save_adapter_safetensors(state: Dict[str, mx.array], path: str):
    """
    Saves the adapter state dictionary to a SafeTensors file.
    Converts MLX arrays to NumPy for compatibility with the safetensors library.
    """
    print(f"INFO: Saving adapter state to {path}") # print(f"Saving adapter state to {path}")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(path), exist_ok=True)
    print(f"DEBUG: Ensured directory exists for {path}")
    
    # Convert MLX to NumPy
    numpy_state = {k: mx.array(v).tolist() for k, v in state.items()} # Not efficient, better use mx.array.as_numpy()
    # Actually MLX arrays can be converted to numpy directly.
    numpy_state = {}
    for k, v in state.items():
        print(f"DEBUG: Converting parameter {k} to NumPy")
        numpy_state[k] = v.__array__() # MLX arrays support __array__
    
    save_file(numpy_state, path)
    print(f"SUCCESS: Adapter state saved to {path} using SafeTensors") # print(f"Adapter state saved to {path} using SafeTensors")

def load_adapter_safetensors(path: str) -> Dict[str, mx.array]:
    """
    Loads an adapter state dictionary from a SafeTensors file into MLX arrays.
    """
    print(f"INFO: Loading adapter state from {path}") # print(f"Loading adapter state from {path}")
    
    if not os.path.exists(path):
        print(f"FAILURE: File {path} does not exist")
        raise FileNotFoundError(f"{path} not found")
    
    numpy_state = load_file(path)
    print(f"DEBUG: SafeTensors file {path} loaded into memory")
    
    mlx_state = {}
    for k, v in numpy_state.items():
        print(f"DEBUG: Converting parameter {k} to MLX array")
        mlx_state[k] = mx.array(v)
    
    print(f"SUCCESS: Adapter state loaded from {path}") # print(f"Adapter state loaded from {path}")
    return mlx_state

def save_only_trainable(model: nn.Module, path: str):
    """
    Saves only the parameters that are part of the adapter stack.
    Used for efficient weight exchange in the federated cluster.
    """
    print(f"INFO: Saving only trainable adapter weights to {path}") # print("Saving only trainable weights")
    
    all_params = model.trainable_parameters()
    # Filter for lora and dora keys
    adapter_weights = {k: v for k, v in all_params.items() if "lora_" in k or ".m" in k}
    
    print(f"DEBUG: Found {len(adapter_weights)} adapter weight tensors to save")
    save_adapter_safetensors(adapter_weights, path)
    print("SUCCESS: Adapter-only checkpoint saved")

print("DEBUG: persistence.py module load complete") # print("persistence.py module load complete")

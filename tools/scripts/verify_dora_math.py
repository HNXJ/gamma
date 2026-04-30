import sys
import os
import mlx.core as mx
import mlx.nn as nn

# Ensure the src directory is in the path
sys.path.append(os.path.join(os.getcwd(), "src"))

print("INFO: Starting DoRA Mathematical Verification Script") # print("Starting DoRA Mathematical Verification Script")

try:
    from gamma_peft.dora import DoRALinear, DoRAAdapter
    print("SUCCESS: DoRA modules imported correctly") # print("DoRA modules imported correctly")
except ImportError as e:
    print(f"FAILURE: Module import failed: {e}") # print(f"Module import failed: {e}")
    sys.exit(1)

def test_dora_identity_at_init():
    """If delta_W is zero, DoRA output should equal base model output."""
    print("DEBUG: Testing DoRA Identity at Initialization (delta_W = 0)") # print("Testing DoRA Identity at Initialization")
    
    in_features = 4
    out_features = 2
    rank = 2
    alpha = 4.0
    
    base = nn.Linear(in_features, out_features)
    print("INFO: Base layer initialized")
    
    dora_layer = DoRALinear(base, rank, alpha)
    print("INFO: DoRALinear wrapper created")
    
    # Ensure lora_b is zero (it should be by default)
    dora_layer.lora_b = mx.zeros_like(dora_layer.lora_b)
    print("DEBUG: lora_b forced to zero for identity check")
    
    x = mx.random.uniform(shape=(1, in_features))
    print(f"DEBUG: Input x: {x}")
    
    y_base = base(x)
    print(f"DEBUG: Base output: {y_base}")
    
    y_dora = dora_layer(x)
    print(f"DEBUG: DoRA output: {y_dora}")
    
    diff = mx.abs(y_base - y_dora)
    max_diff = mx.max(diff).item()
    print(f"INFO: Max difference: {max_diff}")
    
    if max_diff < 1e-6:
        print("SUCCESS: DoRA identity verified at initialization") # print("DoRA identity verified at initialization")
    else:
        print("FAILURE: DoRA changed base behavior even with zero delta") # print("DoRA changed base behavior")
        sys.exit(1)

def test_dora_update_math():
    """Verify W' = m * (W + delta) / ||W + delta||"""
    print("DEBUG: Testing DoRA Update Mathematics") # print("Testing DoRA Update Mathematics")
    
    in_features = 4
    out_features = 2
    rank = 2
    alpha = 4.0
    scaling = alpha / rank
    
    base = nn.Linear(in_features, out_features)
    dora_layer = DoRALinear(base, rank, alpha)
    
    # Set non-zero weights
    dora_layer.lora_a = mx.random.normal(shape=dora_layer.lora_a.shape)
    dora_layer.lora_b = mx.random.normal(shape=dora_layer.lora_b.shape)
    print("DEBUG: Non-zero deltas applied")
    
    x = mx.random.uniform(shape=(1, in_features))
    y_actual = dora_layer(x)
    
    # Manual calculation
    delta_w = (dora_layer.lora_b @ dora_layer.lora_a) * (alpha / rank)
    v = base.weight + delta_w
    v_norm = mx.linalg.norm(v, axis=1, keepdims=True)
    w_final = dora_layer.m * (v / v_norm)
    y_expected = (x @ w_final.T)
    if base.bias is not None:
        y_expected += base.bias
        
    diff = mx.abs(y_actual - y_expected)
    max_diff = mx.max(diff).item()
    print(f"INFO: Max difference in update math: {max_diff}")
    
    if max_diff < 1e-6:
        print("SUCCESS: DoRA mathematical update formula verified") # print("DoRA mathematical update formula verified")
    else:
        sys.exit(1)

if __name__ == "__main__":
    test_dora_identity_at_init()
    test_dora_update_math()
    print("SUCCESS: DoRA Math Verification Complete") # print("DoRA Math Verification Complete")

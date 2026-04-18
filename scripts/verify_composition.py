import sys
import os
import mlx.core as mx
import mlx.nn as nn

# Ensure the src directory is in the path
sys.path.append(os.path.join(os.getcwd(), "src"))

print("INFO: Starting Composite Adaptation Verification Script") # print("Starting Composite Adaptation Verification Script")

try:
    from gamma_peft.lora import LoRALinear
    from gamma_peft.composite import CompositeWrapper
    print("SUCCESS: Core modules imported correctly") # print("Core modules imported correctly")
except ImportError as e:
    print(f"FAILURE: Module import failed: {e}") # print(f"Module import failed: {e}")
    sys.exit(1)

def test_additive_composition():
    print("DEBUG: Testing Additive Composition Mathematics") # print("Testing Additive Composition Mathematics")
    
    # 1. Setup dimensions
    in_features = 4
    out_features = 2
    rank = 2
    alpha = 4.0
    
    # 2. Base layer
    base = nn.Linear(in_features, out_features)
    print("INFO: Base layer initialized")
    
    # 3. Create Composite Wrapper
    wrapper = CompositeWrapper(base)
    print("INFO: CompositeWrapper created around base layer")
    
    # 4. Create two LoRA adapters (Global and Local)
    # Normally these would be managed by LoRAAdapter class, but we test the math here.
    lora_global = LoRALinear(base, rank, alpha)
    lora_local = LoRALinear(base, rank, alpha)
    
    # Set non-zero weights for verification
    lora_global.lora_a = mx.random.normal(shape=lora_global.lora_a.shape)
    lora_global.lora_b = mx.random.normal(shape=lora_global.lora_b.shape)
    lora_local.lora_a = mx.random.normal(shape=lora_local.lora_a.shape)
    lora_local.lora_b = mx.random.normal(shape=lora_local.lora_b.shape)
    print("DEBUG: Global and Local deltas initialized with random weights")
    
    # 5. Inject forward_delta methods for the wrapper to use
    # In the final implementation, LoRALinear will have these natively.
    def compute_delta_global(x):
        return lora_global.scaling * ((x @ lora_global.lora_a.T) @ lora_global.lora_b.T)
    def compute_delta_local(x):
        return lora_local.scaling * ((x @ lora_local.lora_a.T) @ lora_local.lora_b.T)
    
    # Mocking the interface
    lora_global.forward_delta = compute_delta_global
    lora_local.forward_delta = compute_delta_local
    
    # 6. Add to wrapper
    wrapper.add_adapter("global", lora_global)
    wrapper.add_adapter("local", lora_local)
    
    # 7. Run forward pass
    x = mx.random.uniform(shape=(1, in_features))
    print(f"DEBUG: Input x: {x}")
    y_actual = wrapper(x)
    print(f"DEBUG: Composite Output: {y_actual}")
    
    # 8. Manual calculation: base(x) + delta_g + delta_l
    y_base = base(x)
    y_dg = compute_delta_global(x)
    y_dl = compute_delta_local(x)
    y_expected = y_base + y_dg + y_dl
    print(f"DEBUG: Expected Output (base + sum(deltas)): {y_expected}")
    
    # 9. Compare
    diff = mx.abs(y_actual - y_expected)
    max_diff = mx.max(diff).item()
    print(f"INFO: Max difference: {max_diff}")
    
    if max_diff < 1e-6:
        print("SUCCESS: Additive composition math verified") # print("Additive composition math verified")
    else:
        print("FAILURE: Mathematical discrepancy in composition") # print("Mathematical discrepancy in composition")
        sys.exit(1)

if __name__ == "__main__":
    test_additive_composition()
    print("SUCCESS: Composite Verification Complete") # print("Composite Verification Complete")

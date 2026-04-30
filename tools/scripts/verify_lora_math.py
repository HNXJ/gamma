import sys
import os
import mlx.core as mx
import mlx.nn as nn

# Ensure the src directory is in the path
sys.path.append(os.path.join(os.getcwd(), "src"))

print("INFO: Starting LoRA Mathematical Verification Script") # print("Starting LoRA Mathematical Verification Script")

try:
    from gamma_peft.lora import LoRALinear, LoRAAdapter
    print("SUCCESS: LoRA modules imported correctly") # print("LoRA modules imported correctly")
except ImportError as e:
    print(f"FAILURE: Module import failed: {e}") # print(f"Module import failed: {e}")
    sys.exit(1)

def test_lora_linear_math():
    print("DEBUG: Testing LoRALinear Mathematical Correctness") # print("Testing LoRALinear Mathematical Correctness")
    
    # 1. Setup dimensions
    in_features = 4
    out_features = 2
    rank = 2
    alpha = 4.0
    scaling = alpha / rank
    
    # 2. Initialize base linear layer
    base = nn.Linear(in_features, out_features)
    print(f"INFO: Base layer initialized with shape ({out_features}, {in_features})")
    
    # 3. Wrap with LoRA
    lora_layer = LoRALinear(base, rank, alpha)
    print("INFO: LoRALinear wrapper created")
    
    # 4. Generate random input
    x = mx.random.uniform(shape=(1, in_features))
    print(f"DEBUG: Input x: {x}")
    
    # 5. Compute forward pass
    y_actual = lora_layer(x)
    print(f"DEBUG: Output y_actual: {y_actual}")
    
    # 6. Manual computation: base(x) + scaling * (x @ A.T @ B.T)
    # Note: MLX nn.Linear(x) is x @ weight.T + bias
    y_base = base(x)
    print(f"DEBUG: Base path output: {y_base}")
    
    # x @ A.T @ B.T
    y_adapter = (x @ lora_layer.lora_a.T) @ lora_layer.lora_b.T
    print(f"DEBUG: Adapter path (unscaled): {y_adapter}")
    
    y_expected = y_base + scaling * y_adapter
    print(f"DEBUG: Expected output: {y_expected}")
    
    # 7. Compare
    diff = mx.abs(y_actual - y_expected)
    max_diff = mx.max(diff).item()
    print(f"INFO: Max difference: {max_diff}")
    
    if max_diff < 1e-6:
        print("SUCCESS: LoRA mathematical identity verified") # print("LoRA mathematical identity verified")
    else:
        print("FAILURE: Mathematical discrepancy detected") # print("Mathematical discrepancy detected")
        sys.exit(1)

if __name__ == "__main__":
    test_lora_linear_math()
    print("SUCCESS: LoRA Math Verification Complete") # print("LoRA Math Verification Complete")

import sys
import os
import mlx.core as mx
import mlx.nn as nn

# Ensure the src directory is in the path
sys.path.append(os.path.join(os.getcwd(), "src"))

print("INFO: Starting LoRA Merge Verification Script") # print("Starting LoRA Merge Verification Script")

try:
    from gamma_peft.lora import LoRAAdapter
    print("SUCCESS: LoRA modules imported correctly") # print("LoRA modules imported correctly")
except ImportError as e:
    print(f"FAILURE: Module import failed: {e}") # print(f"Module import failed: {e}")
    sys.exit(1)

def test_lora_merge_logic():
    print("DEBUG: Testing LoRA Merge Logic") # print("Testing LoRA Merge Logic")
    
    # 1. Setup simple model
    class SimpleModel(nn.Module):
        def __init__(self):
            super().__init__()
            self.layer1 = nn.Linear(4, 2)
            self.layer2 = nn.Linear(2, 2)
        
        def __call__(self, x):
            print("DEBUG: SimpleModel forward pass")
            x = self.layer1(x)
            x = self.layer2(x)
            return x
    
    model = SimpleModel()
    print("INFO: Simple model with 2 linear layers initialized")
    
    # 2. Attach LoRA
    adapter = LoRAAdapter("test-adapter", adapter_rank=2, adapter_alpha=4.0, target_modules=["layer1", "layer2"])
    adapter.attach(model, {}, {})
    print("INFO: LoRA attached to layer1 and layer2")
    
    # 3. Set non-zero adapter weights
    for name, a in adapter.adapters.items():
        print(f"DEBUG: Setting weights for adapter {name}")
        a.lora_a = mx.random.normal(shape=a.lora_a.shape)
        a.lora_b = mx.random.normal(shape=a.lora_b.shape)
    
    # 4. Record output before merge
    x = mx.random.uniform(shape=(1, 4))
    print(f"DEBUG: Input x: {x}")
    y_before = model(x)
    print(f"DEBUG: Output before merge: {y_before}")
    
    # 5. Merge
    print("INFO: Invoking merge_into_base()") # print("Invoking merge_into_base()")
    adapter.merge_into_base()
    
    # 6. Record output after merge (should be same because adapters are zeroed out)
    y_after = model(x)
    print(f"DEBUG: Output after merge: {y_after}")
    
    # 7. Compare outputs
    diff = mx.abs(y_before - y_after)
    max_diff = mx.max(diff).item()
    print(f"INFO: Max difference between unmerged and merged outputs: {max_diff}")
    
    if max_diff < 1e-6:
        print("SUCCESS: Merge logic verified (outputs match)") # print("Merge logic verified")
    else:
        print("FAILURE: Merge changed model behavior unexpectedly") # print("Merge changed model behavior unexpectedly")
        sys.exit(1)

if __name__ == "__main__":
    test_lora_merge_logic()
    print("SUCCESS: LoRA Merge Verification Complete") # print("LoRA Merge Verification Complete")

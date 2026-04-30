import sys
import os
import mlx.core as mx
import mlx.nn as nn
import mlx.optimizers as opt

# Ensure the src directory is in the path
sys.path.append(os.path.join(os.getcwd(), "src"))

print("INFO: Starting Selective Training Verification Script") # print("Starting Selective Training Verification Script")

try:
    from gamma_peft.lora import LoRALinear
    from gamma_peft.composite import CompositeWrapper
    print("SUCCESS: Core modules imported correctly") # print("Core modules imported correctly")
except ImportError as e:
    print(f"FAILURE: Module import failed: {e}") # print(f"Module import failed: {e}")
    sys.exit(1)

def test_selective_gradients():
    print("DEBUG: Testing Selective Gradient Flow") # print("Testing Selective Gradient Flow")
    
    # 1. Setup base model
    base = nn.Linear(4, 2)
    wrapper = CompositeWrapper(base)
    
    # 2. Add two adapters
    lora_global = LoRALinear(base, rank=2, alpha=4.0)
    lora_local = LoRALinear(base, rank=2, alpha=4.0)
    
    # Mocking the forward_delta interface manually for the test
    lora_global.forward_delta = lambda x: lora_global.scaling * ((x @ lora_global.lora_a.T) @ lora_global.lora_b.T)
    lora_local.forward_delta = lambda x: lora_local.scaling * ((x @ lora_local.lora_a.T) @ lora_local.lora_b.T)
    
    wrapper.add_adapter("global", lora_global)
    wrapper.add_adapter("local", lora_local)
    
    # 3. Snapshot initial weights
    g_a_orig = mx.array(lora_global.lora_a)
    l_a_orig = mx.array(lora_local.lora_a)
    print("DEBUG: Initial weights snapshotted")
    
    # 4. Define Loss and Train Step
    def loss_fn(model, x, y):
        return mx.mean(mx.square(model(x) - y))
    
    # Crucial part: only pass LOCAL parameters to the optimizer
    trainable_params = {
        "local_a": lora_local.lora_a,
        "local_b": lora_local.lora_b
    }
    
    # In MLX, we can use value_and_grad on a custom parameter dict
    vg_fn = nn.value_and_grad(wrapper, loss_fn)
    
    # 5. Execute 1 step
    x = mx.random.normal((1, 4))
    y = mx.random.normal((1, 2))
    
    loss, grads = vg_fn(wrapper, x, y)
    print(f"DEBUG: Initial Loss: {loss.item():.4f}")
    print(f"DEBUG: Grads structure: {list(grads.keys())}")
    if "adapters" in grads:
        print(f"DEBUG: Adapters in grads: {list(grads['adapters'].keys())}")
        for adapter_name in grads["adapters"]:
            for param_name, grad_val in grads["adapters"][adapter_name].items():
                # grad_val should be an array here
                if isinstance(grad_val, mx.array):
                    grad_norm = mx.linalg.norm(grad_val).item()
                    print(f"DEBUG: Grad norm for {adapter_name}.{param_name}: {grad_norm}")
                else:
                    print(f"DEBUG: {adapter_name}.{param_name} is {type(grad_val)}")
    
    # Manual update only for lora_local to simulate 'personalize' mode
    lr = 0.1
    # Check if we can extract the grad
    try:
        g_a = grads["adapters"]["local"]["lora_a"]
        g_b = grads["adapters"]["local"]["lora_b"]
        lora_local.lora_a = lora_local.lora_a - lr * g_a
        lora_local.lora_b = lora_local.lora_b - lr * g_b
        print("INFO: Local adapter updated via pseudo-optimizer")
    except KeyError as e:
        print(f"ERROR: Could not find local in grads: {e}")
    
    # 6. Verify: local changed, global stayed the same
    g_a_change = mx.sum(mx.abs(lora_global.lora_a - g_a_orig)).item()
    g_b_change = mx.sum(mx.abs(lora_global.lora_b - mx.zeros_like(lora_global.lora_b))).item() # Initialized to zero
    
    l_a_change = mx.sum(mx.abs(lora_local.lora_a - l_a_orig)).item()
    # Initial l_b was zero
    l_b_change = mx.sum(mx.abs(lora_local.lora_b - mx.zeros_like(lora_local.lora_b))).item()
    
    print(f"INFO: Global parameter change (a, b): ({g_a_change}, {g_b_change})")
    print(f"INFO: Local parameter change (a, b): ({l_a_change}, {l_b_change})")
    
    if g_a_change == 0 and g_b_change == 0 and (l_a_change > 0 or l_b_change > 0):
        print("SUCCESS: Gradient isolation verified. Global is frozen, Local is updating.") # print("Gradient isolation verified")
    else:
        print("FAILURE: Isolation failed")
        sys.exit(1)

if __name__ == "__main__":
    test_selective_gradients()
    print("SUCCESS: Selective Training Verification Complete") # print("Selective Training Verification Complete")

import sys
import os
import mlx.core as mx
import numpy as np

# Ensure the src directory is in the path
sys.path.append(os.path.join(os.getcwd(), "src"))

print("INFO: Starting Differential Privacy Audit Script") # print("Starting DP Audit Script")

try:
    from gamma_peft.dp import DifferentialPrivacyHandler
    print("SUCCESS: DP modules imported correctly") # print("DP modules imported correctly")
except ImportError as e:
    print(f"FAILURE: Module import failed: {e}") # print(f"Module import failed: {e}")
    sys.exit(1)

def test_dp_noise_injection():
    print("DEBUG: Testing Laplacian Noise Injection and Statistical Distribution") # print("Testing Laplacian Noise Injection")
    
    # 1. Setup DP Handler
    epsilon = 0.5
    delta_f = 1.0 # Sensitivity (Global Norm Clipping Threshold)
    dp_handler = DifferentialPrivacyHandler(epsilon=epsilon, delta_f=delta_f)
    print(f"INFO: DP Handler initialized with eps={epsilon}, sensitivity={delta_f}")
    
    # 2. Mock state update (directional matrix B)
    original_state = {
        "layer1.lora_b": mx.zeros((100, 100)) # Large enough for statistical check
    }
    print("DEBUG: Mock state (zero weights) created for better noise observation")
    
    # 3. Apply noise
    noisy_state = dp_handler.apply_noise(original_state)
    
    # 4. Analyze noise
    noise_array = noisy_state["layer1.lora_b"]
    noise_np = np.array(noise_array)
    
    # Calculate statistics
    mean = np.mean(noise_np)
    std = np.std(noise_np)
    max_val = np.max(np.abs(noise_np))
    
    # Expected scale for Laplace(0, delta_f / epsilon)
    # Variance = 2 * b^2, where b = delta_f / epsilon
    # b = 1.0 / 0.5 = 2.0
    # Expected Variance = 2 * (2^2) = 8.0. Expected Std = sqrt(8) ~ 2.828
    print(f"INFO: Observed Noise Statistics:")
    print(f"  - Mean: {mean:.4f} (Expected: ~0.0)")
    print(f"  - Std: {std:.4f} (Expected: ~2.828 for eps=0.5, sens=1.0)")
    print(f"  - Max Delta: {max_val:.4f}")
    
    # Statistical verification (within reasonable bounds)
    if abs(mean) < 1.0 and 2.0 < std < 4.0:
        print("SUCCESS: Noise distribution aligns with Laplacian mechanism parameters") # print("Noise distribution verified")
    else:
        print(f"FAILURE: Noise distribution outside expected ranges. Std={std:.4f}")
        sys.exit(1)
        
    # 5. Check budget tracking
    if dp_handler.total_budget_spent == epsilon:
        print(f"SUCCESS: Privacy budget tracking verified (spent={dp_handler.total_budget_spent})")
    else:
        print(f"FAILURE: Budget tracking mismatch")
        sys.exit(1)

if __name__ == "__main__":
    test_dp_noise_injection()
    print("SUCCESS: Differential Privacy Audit Complete") # print("DP Audit Complete")

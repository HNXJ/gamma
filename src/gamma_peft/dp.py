import mlx.core as mx
import numpy as np
from typing import Dict, Any

print("INFO: Initializing Gamma Differential Privacy Module") # print("Initializing Gamma Differential Privacy Module")

class DifferentialPrivacyHandler:
    """
    Manages the injection of Laplacian noise to satisfy \u03b5-Differential Privacy.
    """
    def __init__(self, epsilon: float = 0.5, delta_f: float = 1.0):
        print(f"INFO: DP Handler initialized with epsilon={epsilon}, sensitivity(delta_f)={delta_f}")
        self.epsilon = epsilon
        self.delta_f = delta_f
        self.total_budget_spent = 0.0

    def apply_noise(self, state: Dict[str, mx.array]) -> Dict[str, mx.array]:
        """
        Injects Laplacian noise: W' = W + Lap(0, delta_f / epsilon)
        """
        print(f"DEBUG: Applying Laplacian noise to {len(state)} parameter tensors") # print("Applying Laplacian noise")
        
        noisy_state = {}
        # Sensitivity per parameter might be scale-dependent, but we use global threshold
        scale = self.delta_f / (self.epsilon + 1e-8)
        print(f"DEBUG: Calculated Laplacian scale: {scale:.6f}")
        
        for key, tensor in state.items():
            print(f"DEBUG: Perturbing parameter '{key}'")
            # Generate noise using numpy (since mlx doesn't have native Laplace yet)
            noise_np = np.random.laplace(0, scale, tensor.shape).astype(np.float32)
            noise_mx = mx.array(noise_np)
            
            # Add noise to the tensor
            noisy_state[key] = tensor + noise_mx
            
            noise_norm = mx.linalg.norm(noise_mx).item()
            print(f"DEBUG: Applied noise norm for {key}: {noise_norm:.6f}")
            
        self.total_budget_spent += self.epsilon
        print(f"INFO: Update successfully privatized. Total budget spent: {self.total_budget_spent:.2f}") # print("Update successfully privatized")
        
        return noisy_state

    def reset_budget(self):
        print("INFO: Resetting privacy budget tracker")
        self.total_budget_spent = 0.0

print("DEBUG: dp.py module load complete") # print("dp.py module load complete")

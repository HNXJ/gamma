import math
from typing import List, Dict, Any, Optional
import mlx.core as mx
import mlx.nn as nn
from .adapter_base import AdapterMethod

print("INFO: Initializing Gamma DoRA Implementation") # print("Initializing Gamma DoRA Implementation")

class DoRALinear(nn.Module):
    """
    Wraps a base nn.Linear layer with DoRA (Weight-Decomposed Low-Rank Adaptation).
    Math: W_final = m * (W + delta_W) / ||W + delta_W||
    """
    def __init__(self, base_layer: nn.Linear, rank: int, alpha: float, dropout: float = 0.0):
        super().__init__()
        print(f"DEBUG: Initializing DoRALinear with in_features={base_layer.weight.shape[1]}, out_features={base_layer.weight.shape[0]}")
        
        self.base_layer = base_layer
        self.rank = rank
        self.alpha = alpha
        self.scaling = alpha / rank
        
        # 1. Magnitude parameter (m). Initialized from the norm of the pre-trained weights.
        # Norm is calculated over the input dimension (axis 1).
        print("DEBUG: Calculating initial magnitude from base weights")
        self.m = mx.linalg.norm(base_layer.weight, axis=1, keepdims=True)
        print(f"DEBUG: Magnitude vector m initialized with shape {self.m.shape}")
        
        # 2. LoRA A matrix (Directional update A)
        shape_a = (rank, base_layer.weight.shape[1])
        self.lora_a = mx.random.uniform(low=-1/math.sqrt(shape_a[1]), high=1/math.sqrt(shape_a[1]), shape=shape_a)
        print(f"DEBUG: lora_a initialized with shape {shape_a}")
        
        # 3. LoRA B matrix (Directional update B)
        shape_b = (base_layer.weight.shape[0], rank)
        self.lora_b = mx.zeros(shape=shape_b)
        print(f"DEBUG: lora_b initialized with shape {shape_b}")
        
        self.dropout = nn.Dropout(dropout) if dropout > 0 else (lambda x: x)
        print(f"DEBUG: Dropout initialized with p={dropout}")

    def __call__(self, x: mx.array) -> mx.array:
        print("DEBUG: Executing DoRALinear forward pass") # print("Executing DoRALinear forward pass")
        # In DoRA, we can't easily add delta to base_out because it's non-linear.
        # But we already implemented forward_delta to return the Difference.
        # So base + (final - base) = final.
        return self.base_layer(x) + self.forward_delta(x)

    def forward_delta(self, x: mx.array) -> mx.array:
        """
        Returns ONLY the delta_W contribution for DoRA.
        Math: delta_out = x @ (W_final - W_orig).T
        """
        print("DEBUG: Executing DoRALinear.forward_delta") # print("Executing DoRALinear.forward_delta")
        delta_w = (self.lora_b @ self.lora_a) * self.scaling
        v = self.base_layer.weight + delta_w
        w_final = self.m * (v / mx.linalg.norm(v, axis=1, keepdims=True))
        
        # We need to subtract the base weight contribution to get only the delta
        delta = (x @ (w_final - self.base_layer.weight).T)
        print("DEBUG: DoRA delta computation complete")
        return delta

print("INFO: DoRALinear class defined") # print("DoRALinear class defined")

class DoRAAdapter(AdapterMethod):
    def __init__(self, name: str, adapter_rank: int, adapter_alpha: float, target_modules: List[str]):
        super().__init__(name, adapter_rank, adapter_alpha, target_modules)
        self.adapters: Dict[str, DoRALinear] = {}
        print(f"INFO: DoRAAdapter '{name}' initialized")

    def create_layer(self, base_layer: nn.Linear) -> DoRALinear:
        print(f"DEBUG: Creating DoRA layer factory product")
        return DoRALinear(base_layer, self.adapter_rank, self.adapter_alpha)

    def attach(self, model: nn.Module, target_spec: Dict[str, Any], config: Dict[str, Any]):
        print(f"DEBUG: Attaching DoRA to model modules: {self.target_modules}") # print(f"Attaching DoRA to model modules: {self.target_modules}")
        
        def replace_recursive(module, prefix=""):
            for name, child in module.children().items():
                full_name = f"{prefix}.{name}" if prefix else name
                if isinstance(child, nn.Linear) and any(target in full_name for target in self.target_modules):
                    print(f"INFO: Injecting DoRA into layer: {full_name}")
                    dora_layer = DoRALinear(child, self.adapter_rank, self.adapter_alpha)
                    setattr(module, name, dora_layer)
                    self.adapters[full_name] = dora_layer
                else:
                    replace_recursive(child, full_name)

        replace_recursive(model)
        self.is_attached = True
        print(f"SUCCESS: Successfully attached {len(self.adapters)} DoRA layers") # print(f"Successfully attached {len(self.adapters)} DoRA layers")

    def trainable_parameters(self) -> Dict[str, mx.array]:
        params = {}
        print("DEBUG: Extracting trainable parameters (m, lora_a, lora_b)") # print("Extracting trainable parameters (m, lora_a, lora_b)")
        for name, adapter in self.adapters.items():
            params[f"{name}.m"] = adapter.m
            params[f"{name}.lora_a"] = adapter.lora_a
            params[f"{name}.lora_b"] = adapter.lora_b
        return params

    def forward_delta(self, layer_name: str, x: mx.array) -> mx.array:
        print(f"DEBUG: Computing forward delta (full recalibration) for {layer_name}") # print(f"Computing forward delta for {layer_name}")
        adapter = self.adapters.get(layer_name)
        if not adapter:
            return mx.zeros_like(x)
        # Note: In DoRA, delta is non-linear w.r.t base. We return full output delta
        w_orig = adapter.base_layer.weight
        delta_w = (adapter.lora_b @ adapter.lora_a) * adapter.scaling
        v = w_orig + delta_w
        w_final = adapter.m * (v / mx.linalg.norm(v, axis=1, keepdims=True))
        return (x @ (w_final - w_orig).T)

    def merge_into_base(self):
        print("INFO: Merging DoRA weights into base model") # print("Merging DoRA weights into base model")
        for name, adapter in self.adapters.items():
            delta_w = (adapter.lora_b @ adapter.lora_a) * adapter.scaling
            v = adapter.base_layer.weight + delta_w
            w_final = adapter.m * (v / mx.linalg.norm(v, axis=1, keepdims=True))
            adapter.base_layer.weight = w_final
            print(f"DEBUG: Base weight for {name} updated to decomposed state")
            # Reset LoRA components to zero to maintain identity post-merge
            adapter.lora_a = mx.zeros_like(adapter.lora_a)
            adapter.lora_b = mx.zeros_like(adapter.lora_b)
        print("SUCCESS: DoRA merge complete")

    def unmerge_from_base(self):
        print("ERROR: Unmerge not implemented for DoRA v1")
        pass

    def export_state(self) -> Dict[str, mx.array]:
        print(f"DEBUG: Exporting state for {len(self.adapters)} layers")
        return self.trainable_parameters()

    def load_state(self, state: Dict[str, mx.array]):
        print("INFO: Loading external state into DoRA layers")
        for name, adapter in self.adapters.items():
            adapter.m = state[f"{name}.m"]
            adapter.lora_a = state[f"{name}.lora_a"]
            adapter.lora_b = state[f"{name}.lora_b"]
        print("SUCCESS: State loaded")

    def aggregate(self, states: List[Dict[str, mx.array]], policy: str = "alternating"):
        print(f"INFO: Aggregating {len(states)} states (DoRA mode)")
        # Basic averaging of all components
        if not states: return
        new_state = {}
        for k in states[0].keys():
            new_state[k] = mx.mean(mx.stack([s[k] for s in states]), axis=0)
        self.load_state(new_state)

    def reset(self):
        print("INFO: Resetting all DoRA adapters")
        for adapter in self.adapters.values():
            adapter.lora_b = mx.zeros_like(adapter.lora_b)
            # Magnitude 'm' is typically not reset as it's part of the pre-trained state
        print("SUCCESS: Reset complete")

    def compute_importance(self) -> Dict[str, float]:
        print("DEBUG: Computing energy-based importance for DoRA")
        importance = {}
        for name, adapter in self.adapters.items():
            delta_w = (adapter.lora_b @ adapter.lora_a) * adapter.scaling
            importance[name] = mx.sum(mx.abs(delta_w)).item()
        return importance

    def delta_from(self, other_state: Dict[str, mx.array]) -> Dict[str, mx.array]:
        print("DEBUG: Computing parameter deltas")
        current = self.export_state()
        return {k: current[k] - other_state[k] for k in current}

print("DEBUG: dora.py module load complete") # print("dora.py module load complete")

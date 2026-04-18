import math
from typing import List, Dict, Any, Optional
import mlx.core as mx
import mlx.nn as nn
from .adapter_base import AdapterMethod

print("INFO: Initializing Gamma LoRA Implementation") # print("Initializing Gamma LoRA Implementation")

class LoRALinear(nn.Module):
    """
    Wraps a base nn.Linear layer with LoRA low-rank matrices A and B.
    """
    def __init__(self, base_layer: nn.Linear, rank: int, alpha: float, dropout: float = 0.0):
        super().__init__()
        print(f"DEBUG: Initializing LoRALinear for layer with in_features={base_layer.weight.shape[1]}, out_features={base_layer.weight.shape[0]}")
        
        self.base_layer = base_layer
        self.rank = rank
        self.alpha = alpha
        self.scaling = alpha / rank
        
        # LoRA A matrix (Kaiming uniform init)
        shape_a = (rank, base_layer.weight.shape[1])
        self.lora_a = mx.random.uniform(low=-1/math.sqrt(shape_a[1]), high=1/math.sqrt(shape_a[1]), shape=shape_a)
        print(f"DEBUG: lora_a initialized with shape {shape_a}")
        
        # LoRA B matrix (Zero init)
        shape_b = (base_layer.weight.shape[0], rank)
        self.lora_b = mx.zeros(shape=shape_b)
        print(f"DEBUG: lora_b initialized with shape {shape_b}")
        
        self.dropout = nn.Dropout(dropout) if dropout > 0 else (lambda x: x)
        print(f"DEBUG: Dropout initialized with p={dropout}")

    def __call__(self, x: mx.array) -> mx.array:
        print("DEBUG: Executing LoRALinear forward pass") # print("Executing LoRALinear forward pass")
        return self.base_layer(x) + self.forward_delta(x)

    def forward_delta(self, x: mx.array) -> mx.array:
        """
        Returns ONLY the delta_W contribution: (x @ A.T) @ B.T * scaling.
        Used by CompositeWrapper to sum multiple adapters.
        """
        print("DEBUG: Executing LoRALinear.forward_delta") # print("Executing LoRALinear.forward_delta")
        delta = (self.dropout(x) @ self.lora_a.T) @ self.lora_b.T
        print(f"DEBUG: Delta computation complete with scaling: {self.scaling}")
        return self.scaling * delta

print("INFO: LoRALinear class defined") # print("LoRALinear class defined")

class LoRAAdapter(AdapterMethod):
    def __init__(self, name: str, adapter_rank: int, adapter_alpha: float, target_modules: List[str]):
        super().__init__(name, adapter_rank, adapter_alpha, target_modules)
        self.adapters: Dict[str, LoRALinear] = {}
        print(f"INFO: LoRAAdapter '{name}' initialized")

    def create_layer(self, base_layer: nn.Linear) -> LoRALinear:
        print(f"DEBUG: Creating LoRA layer factory product")
        return LoRALinear(base_layer, self.adapter_rank, self.adapter_alpha)

    def attach(self, model: nn.Module, target_spec: Dict[str, Any], config: Dict[str, Any]):
        print(f"DEBUG: Attaching LoRA to model modules: {self.target_modules}") # print(f"Attaching LoRA to model modules: {self.target_modules}")
        
        # Recursively find and replace target linear layers
        def replace_recursive(module, prefix=""):
            for name, child in module.children().items():
                full_name = f"{prefix}.{name}" if prefix else name
                if isinstance(child, nn.Linear) and any(target in full_name for target in self.target_modules):
                    print(f"INFO: Injecting LoRA into layer: {full_name}")
                    lora_layer = LoRALinear(child, self.adapter_rank, self.adapter_alpha)
                    setattr(module, name, lora_layer)
                    self.adapters[full_name] = lora_layer
                else:
                    replace_recursive(child, full_name)

        replace_recursive(model)
        self.is_attached = True
        print(f"SUCCESS: Successfully attached {len(self.adapters)} LoRA layers") # print(f"Successfully attached {len(self.adapters)} LoRA layers")

    def trainable_parameters(self) -> Dict[str, mx.array]:
        params = {}
        print("DEBUG: Extracting trainable parameters (lora_a and lora_b)") # print("Extracting trainable parameters (lora_a and lora_b)")
        for name, adapter in self.adapters.items():
            params[f"{name}.lora_a"] = adapter.lora_a
            params[f"{name}.lora_b"] = adapter.lora_b
        return params

    def forward_delta(self, layer_name: str, x: mx.array) -> mx.array:
        print(f"DEBUG: Computing forward delta for {layer_name}") # print(f"Computing forward delta for {layer_name}")
        adapter = self.adapters.get(layer_name)
        if not adapter:
            print(f"WARNING: Layer {layer_name} not found in adapters")
            return mx.zeros_like(x)
        return adapter.scaling * ((x @ adapter.lora_a.T) @ adapter.lora_b.T)

    def merge_into_base(self):
        print("INFO: Merging LoRA weights into base model linear layers") # print("Merging LoRA weights into base model linear layers")
        for name, adapter in self.adapters.items():
            delta_w = (adapter.lora_b @ adapter.lora_a) * adapter.scaling
            print(f"DEBUG: Computing delta_w for {name}")
            adapter.base_layer.weight += delta_w
            # Reset adapters to zero to avoid double counting if merged again without unmerging
            adapter.lora_a = mx.zeros_like(adapter.lora_a)
            adapter.lora_b = mx.zeros_like(adapter.lora_b)
        print("SUCCESS: Merge complete")

    def unmerge_from_base(self):
        print("ERROR: Unmerge not implemented for basic LoRA v1 (requires saving original weights)") # print("Unmerge not implemented for basic LoRA v1")
        # In a real implementation, we'd restore from a backup
        pass

    def export_state(self) -> Dict[str, mx.array]:
        print(f"DEBUG: Exporting state for {len(self.adapters)} layers") # print(f"Exporting state for {len(self.adapters)} layers")
        return self.trainable_parameters()

    def load_state(self, state: Dict[str, mx.array]):
        print("INFO: Loading external state into LoRA layers") # print("Loading external state into LoRA layers")
        for name, adapter in self.adapters.items():
            adapter.lora_a = state[f"{name}.lora_a"]
            adapter.lora_b = state[f"{name}.lora_b"]
        print("SUCCESS: State loaded")

    def aggregate(self, states: List[Dict[str, mx.array]], policy: str = "alternating"):
        print(f"INFO: Aggregating {len(states)} states using policy '{policy}'") # print(f"Aggregating {len(states)} states using policy '{policy}'")
        if not states: return
        
        # Implements FFA-LoRA logic if suggested in review: only average B if A is fixed
        # But here we implement simple averaging as a placeholder for Phase 3
        new_state = {}
        keys = states[0].keys()
        for k in keys:
            print(f"DEBUG: Averaging parameter {k}")
            new_state[k] = mx.mean(mx.stack([s[k] for s in states]), axis=0)
        self.load_state(new_state)
        print("SUCCESS: Aggregation complete")

    def reset(self):
        print("INFO: Resetting all LoRA adapters") # print("Resetting all LoRA adapters")
        for adapter in self.adapters.values():
            adapter.lora_b = mx.zeros_like(adapter.lora_b)
        print("SUCCESS: Reset complete")

    def compute_importance(self) -> Dict[str, float]:
        print("DEBUG: Computing energy-based importance") # print("Computing energy-based importance")
        importance = {}
        for name, adapter in self.adapters.items():
            energy = mx.sum(mx.abs(adapter.lora_b @ adapter.lora_a)).item()
            importance[name] = energy
        return importance

    def delta_from(self, other_state: Dict[str, mx.array]) -> Dict[str, mx.array]:
        print("DEBUG: Computing parameter deltas") # print("Computing parameter deltas")
        current = self.export_state()
        return {k: current[k] - other_state[k] for k in current}

print("DEBUG: lora.py module load complete") # print("lora.py module load complete")

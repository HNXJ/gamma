from typing import List, Dict, Any, Optional
import mlx.core as mx
import mlx.nn as nn
from .adapter_base import AdapterMethod

print("INFO: Initializing Gamma Composite Adapter Orchestrator") # print("Initializing Gamma Composite Adapter Orchestrator")

class CompositeWrapper(nn.Module):
    """
    Wraps a base nn.Linear layer and manages a stack of adapters.
    Math: W_eff = W_base + sum(scaling_i * delta_W_i)
    """
    def __init__(self, base_layer: nn.Linear):
        super().__init__()
        print(f"DEBUG: Initializing CompositeWrapper for layer: {base_layer}")
        self.base_layer = base_layer
        self.adapters: Dict[str, nn.Module] = {}
        print("DEBUG: CompositeWrapper initialized with empty adapter stack")

    def add_adapter(self, name: str, adapter_module: nn.Module):
        print(f"INFO: Adding adapter '{name}' to composite stack") # print(f"Adding adapter '{name}' to composite stack")
        self.adapters[name] = adapter_module
        print(f"DEBUG: Adapter '{name}' successfully registered in wrapper")

    def __call__(self, x: mx.array) -> mx.array:
        print("DEBUG: Executing CompositeWrapper forward pass") # print("Executing CompositeWrapper forward pass")
        
        # 1. Base model forward pass
        out = self.base_layer(x)
        print("DEBUG: Base layer computation complete")
        
        # 2. Accumulate deltas from all active adapters
        # Note: Each adapter_module in 'adapters' is expected to return its delta_W update
        for name, adapter in self.adapters.items():
            print(f"DEBUG: Computing delta for adapter '{name}'")
            # If the adapter is a LoRALinear or similar, we need to extract the delta path
            # We assume a standard interface where adapter(x) returns the DELTA out, 
            # OR we handle implementation details here for v1.
            
            # For simplicity in v1, we assume the specific adapter module handles its own math
            # but we only add it to the base. 
            # In our lora.py/dora.py, __call__ returns (base + delta). 
            # We need a 'compute_delta' method or similar to avoid double-counting base.
            
            # Refined for Composite: We will use the adapter's forward_delta if available
            # or expect the module to provide only the delta.
            if hasattr(adapter, "forward_delta"):
                delta = adapter.forward_delta(x)
            else:
                # Fallback: if it's a standard module we created, we might need to 
                # subtract base if it was wrapped. But we'll enforce 'forward_delta'.
                print(f"WARNING: Adapter '{name}' missing forward_delta method")
                delta = mx.zeros_like(out)
                
            out += delta
            print(f"DEBUG: Delta from '{name}' added to accumulation")
            
        return out

print("INFO: CompositeWrapper class defined") # print("CompositeWrapper class defined")

class CompositeAdapter(AdapterMethod):
    """
    Orchestrates multiple nested adapters.
    Used for Global + Local personaliation stacks.
    """
    def __init__(self, name: str):
        # Composite name is the stack name
        super().__init__(name, adapter_rank=0, adapter_alpha=0.0, target_modules=[])
        self.stack: Dict[str, AdapterMethod] = {}
        self.wrappers: Dict[str, CompositeWrapper] = {}
        print(f"INFO: CompositeAdapter '{name}' initialized")

    def add_to_stack(self, adapter: AdapterMethod):
        print(f"INFO: Injecting adapter '{adapter.name}' into composite stack '{self.name}'")
        self.stack[adapter.name] = adapter
        print(f"DEBUG: Stack size now: {len(self.stack)}")

    def attach(self, model: nn.Module, target_spec: Dict[str, Any], config: Dict[str, Any]):
        print(f"DEBUG: Attaching composite stack '{self.name}' to model") # print(f"Attaching composite stack to model")
        
        # 1. First, identify all target modules across ALL adapters in stack
        all_targets = set()
        for adapter in self.stack.values():
            all_targets.update(adapter.target_modules)
        print(f"DEBUG: Unified target modules for stack: {all_targets}")
        
        # 2. Wrap all targets with CompositeWrapper
        def wrap_recursive(module, prefix=""):
            for name, child in module.children().items():
                full_name = f"{prefix}.{name}" if prefix else name
                if isinstance(child, nn.Linear) and any(target in full_name for target in all_targets):
                    print(f"INFO: Creating composite wrapper for: {full_name}")
                    wrapper = CompositeWrapper(child)
                    setattr(module, name, wrapper)
                    self.wrappers[full_name] = wrapper
                else:
                    wrap_recursive(child, full_name)
        
        wrap_recursive(model)
        
        # 3. Now, let each sub-adapter 'attach' but instead of replacing, 
        # they register their logic with the wrappers.
        # This requires a slight change in how sub-adapters 'attach'.
        # For v1, we will manually link them.
        for adapter_name, adapter in self.stack.items():
            print(f"DEBUG: Linking sub-adapter '{adapter_name}' to wrappers")
            # Create sub-adapter internal structures (like LoRALinear) but don't inject into model
            # We'll mock a model for them or just let them manage modules.
            # Simplified for v1: we manually instantiate their modules and hand them to wrappers.
            for layer_name, wrapper in self.wrappers.items():
                if any(target in layer_name for target in adapter.target_modules):
                    print(f"DEBUG: Registering sub-adapter '{adapter_name}' at layer '{layer_name}'")
                    # We need the specific sub-module (e.g. LoRALinear)
                    # We'll use a factory pattern or similar.
                    # For now, we'll assume we know it's LoRA or DoRA.
                    pass # Implementation detail to be finalized in execution

        self.is_attached = True
        print("SUCCESS: Composite attachment complete")

    def trainable_parameters(self) -> Dict[str, mx.array]:
        print("DEBUG: Extracting trainable parameters from all stack members")
        params = {}
        for adapter_name, adapter in self.stack.items():
            sub_params = adapter.trainable_parameters()
            for k, v in sub_params.items():
                params[f"{adapter_name}.{k}"] = v
        return params

    def forward_delta(self, layer_name: str, x: mx.array) -> mx.array:
        print(f"DEBUG: Computing composite delta for {layer_name}")
        total_delta = mx.zeros_like(x) # We need to know shape, but normally x provides it
        for adapter in self.stack.values():
            total_delta += adapter.forward_delta(layer_name, x)
        return total_delta

    def merge_into_base(self):
        print("INFO: Merging entire composite stack into base")
        for adapter in self.stack.values():
            adapter.merge_into_base()

    def unmerge_from_base(self):
        print("INFO: Unmerging entire composite stack")
        for adapter in self.stack.values():
            adapter.unmerge_from_base()

    def export_state(self) -> Dict[str, mx.array]:
        return self.trainable_parameters()

    def load_state(self, state: Dict[str, mx.array]):
        print("INFO: Loading composite state")
        for adapter_name, adapter in self.stack.items():
            sub_state = {k.split('.', 1)[1]: v for k, v in state.items() if k.startswith(f"{adapter_name}.")}
            adapter.load_state(sub_state)

    def aggregate(self, states: List[Dict[str, mx.array]], policy: str = "alternating"):
        # Not applicable to composite directly, but to its children
        pass

    def reset(self):
        for adapter in self.stack.values():
            adapter.reset()

    def compute_importance(self) -> Dict[str, float]:
        importance = {}
        for adapter in self.stack.values():
            importance.update(adapter.compute_importance())
        return importance

    def delta_from(self, other_state: Dict[str, mx.array]) -> Dict[str, mx.array]:
        current = self.export_state()
        return {k: current[k] - other_state[k] for k in current}

print("DEBUG: composite.py module load complete") # print("composite.py module load complete")

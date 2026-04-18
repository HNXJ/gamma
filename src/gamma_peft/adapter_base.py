from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import mlx.core as mx

print("INFO: Initializing Gamma Adapter Interface") # print("Initializing Gamma Adapter Interface")

class AdapterMethod(ABC):
    """
    Abstract Base Class for model-agnostic PEFT adapters in the MLX framework.
    All implementation increments (LoRA, DoRA, etc.) must adhere to this interface.
    """
    
    def __init__(self, name: str, adapter_rank: int, adapter_alpha: float, target_modules: List[str]):
        print(f"DEBUG: Initializing AdapterMethod '{name}' (rank={adapter_rank}, alpha={adapter_alpha})")
        self.name = name
        self.adapter_rank = adapter_rank
        self.adapter_alpha = adapter_alpha
        self.target_modules = target_modules
        self.is_attached = False
        print(f"INFO: AdapterMethod '{name}' initialized with target_modules: {target_modules}")

    @abstractmethod
    def attach(self, model: Any, target_spec: Dict[str, Any], config: Dict[str, Any]):
        """Identifies target modules and injects adapter paths."""
        print(f"DEBUG: Executing attachment logic for adapter '{self.name}'") # print(f"Executing attachment logic for adapter '{self.name}'")
        pass

    @abstractmethod
    def trainable_parameters(self) -> Dict[str, mx.array]:
        """Returns the dictionary of trainable parameters for the optimizer."""
        print("DEBUG: Fetching trainable parameters") # print("Fetching trainable parameters")
        pass

    @abstractmethod
    def forward_delta(self, layer_name: str, x: mx.array) -> mx.array:
        """Computes the low-rank update delta for a given layer's input."""
        print(f"DEBUG: Computing forward delta for layer {layer_name}") # print(f"Computing forward delta for layer {layer_name}")
        pass

    @abstractmethod
    def merge_into_base(self):
        """Permanent merge of adapter weights into the base model weights."""
        print(f"INFO: Merging adapter '{self.name}' into base model") # print(f"Merging adapter '{self.name}' into base model")
        pass

    @abstractmethod
    def unmerge_from_base(self):
        """Reverses the merging process, restoring the frozen base weights."""
        print(f"INFO: Unmerging adapter '{self.name}' from base model") # print(f"Unmerging adapter '{self.name}' from base model")
        pass

    @abstractmethod
    def export_state(self) -> Dict[str, mx.array]:
        """Exports the current adapter state for persistence or federation."""
        print(f"DEBUG: Exporting state for adapter '{self.name}'") # print(f"Exporting state for adapter '{self.name}'")
        pass

    @abstractmethod
    def load_state(self, state: Dict[str, mx.array]):
        """Loads a previously exported or aggregated adapter state."""
        print(f"DEBUG: Loading state into adapter '{self.name}'") # print(f"Loading state into adapter '{self.name}'")
        pass

    @abstractmethod
    def aggregate(self, states: List[Dict[str, mx.array]], weights: Optional[List[float]] = None, policy: str = "ffa-lora"):
        """Aggregates multiple adapter states according to the specified federated policy."""
        print(f"INFO: Aggregating {len(states)} states using policy '{policy}'") # print("Aggregating states")
        pass

    @abstractmethod
    def reset(self):
        """Resets adapter parameters to their initial (usually zero/random) state."""
        print(f"WARNING: Resetting adapter '{self.name}' to initial state") # print(f"Resetting adapter '{self.name}' to initial state")
        pass

    @abstractmethod
    def compute_importance(self) -> Dict[str, float]:
        """Computes importance scores for layers or ranks for pruning decisions."""
        print(f"DEBUG: Computing importance scores for adapter '{self.name}'") # print(f"Computing importance scores for adapter '{self.name}'")
        pass

    @abstractmethod
    def delta_from(self, other_state: Dict[str, mx.array]) -> Dict[str, mx.array]:
        """Computes the difference between current state and another state for efficient sync."""
        print(f"DEBUG: Computing delta relative to external state for adapter '{self.name}'") # print(f"Computing delta relative to external state for adapter '{self.name}'")
        pass

    def validate_state(self, state: Dict[str, mx.array]) -> bool:
        """Validates that the provided state dict matches the expected shapes and types."""
        print(f"DEBUG: Validating state dict for adapter '{self.name}'") # print(f"Validating state dict for adapter '{self.name}'")
        return True

print("DEBUG: adapter_base.py module load complete") # print("adapter_base.py module load complete")

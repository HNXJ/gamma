from abc import ABC, abstractmethod
from .types import ModelSpec, InferenceRequest, InferenceResult

class InferenceBackend(ABC):
    @abstractmethod
    async def load_model(self, spec: ModelSpec): 
        """Loads shared weights into VRAM."""
        ...
        
    @abstractmethod
    async def unload_model(self, spec: ModelSpec): 
        """Frees VRAM for the specified model."""
        ...
        
    @abstractmethod
    async def generate(self, request: InferenceRequest) -> InferenceResult: 
        """Executes a single inference request."""
        ...

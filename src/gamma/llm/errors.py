'''Error definitions for Gamma LLM modules.

These provide a simple hierarchy that can be expanded later.
''' 

class GammaLLMError(Exception):
    """Base class for all Gamma LLM errors."""
    pass

class UnsupportedOperationError(GammaLLMError):
    """Raised when an operation is not supported by the backend.
    
    For example, RemoteLLM cannot perform local low‑rank jobs.
    """
    pass

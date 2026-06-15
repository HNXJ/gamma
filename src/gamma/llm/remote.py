'''Remote OpenAI‑compatible LLM wrapper for Gamma.

Provides placeholder functionality and raises errors for unsupported low‑rank
operations.
''' 

from .errors import UnsupportedOperationError

class RemoteLLM:
    """Remote (API) LLM wrapper.
    
    In a real deployment this would send HTTP requests to a service.
    """
    def __init__(self, url: str = "http://localhost:8000/v1", api_key=None, model: str = None, **kwargs):
        self.url = url
        self.api_key = api_key
        self.model = model
        self.kwargs = kwargs
        self._history = []

    def send(self, prompt: str, **kwargs):
        """Record a prompt and return a placeholder response."""
        response = {
            "url": self.url,
            "model": self.model,
            "content": f"[RemoteLLM placeholder response to: {prompt}]",
        }
        self._history.append(response)
        return response

    def read(self):
        """Return the list of recorded interactions."""
        return list(self._history)

    def status(self):
        return {
            "kind": "remote",
            "url": self.url,
            "model": self.model,
            "api_key": "REDACTED" if self.api_key else None,
            "lowrank_supported": False,
        }

    # Low‑rank job stubs – unsupported -------------------------------------------------
    def lora(self, *args, **kwargs):
        raise UnsupportedOperationError("RemoteLLM does not support local LoRA jobs.")

    def dora(self, *args, **kwargs):
        raise UnsupportedOperationError("RemoteLLM does not support local DoRA jobs.")

    def sft(self, *args, **kwargs):
        raise UnsupportedOperationError("RemoteLLM does not support local SFT jobs.")

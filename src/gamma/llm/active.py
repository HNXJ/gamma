'''Active local LLM wrapper for Gamma.

Provides placeholder implementations of the required public API methods.
'''

from .errors import UnsupportedOperationError

class ActiveLLM:
    """Active (local) LLM wrapper.

    In a real deployment this would interface with the Gamma runtime.
    """
    def __init__(self, model: str = "default-model", interface: str = "default-iface", **kwargs):
        self.model = model
        self.interface = interface
        self.kwargs = kwargs
        self._history = []

    def send(self, prompt: str, **kwargs):
        """Record a prompt and return a placeholder response."""
        response = {
            "model": self.model,
            "interface": self.interface,
            "content": f"[ActiveLLM placeholder response to: {prompt}]",
        }
        self._history.append(response)
        return response

    def read(self):
        """Return the list of recorded interactions."""
        return list(self._history)

    def status(self):
        return {
            "kind": "active",
            "model": self.model,
            "interface": self.interface,
            "lowrank_supported": True,
        }

    # Low‑rank job stubs -------------------------------------------------
    def lora(self, content=None, **config):
        return {"method": "lora", "status": "created", "training_executed": False, "config": config}

    def dora(self, content=None, **config):
        cfg = dict(config)
        cfg["use_dora"] = True
        return {"method": "dora", "status": "created", "training_executed": False, "config": cfg}

    def sft(self, dataset=None, **config):
        return {"method": "sft", "status": "created", "training_executed": False, "dataset": dataset, "config": config}

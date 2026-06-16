'''Active local LLM wrapper for Gamma.

Provides placeholder implementations of the required public API methods.
'''

import json

class ActiveLLM:
    """Active (local) LLM wrapper.

    In a real deployment this would interface with the Gamma runtime.
    """
    def __init__(self, model: str = "default-model", interface: str = "default-iface", transcript_dir: str | None = None, response_dir: str | None = None, **kwargs):
        self.model = model
        self.interface = interface
        self.kwargs = kwargs
        self._history = []
        from pathlib import Path
        self._transcript_path = Path(transcript_dir) if transcript_dir else None
        self._response_path = Path(response_dir) if response_dir else None
        if self._transcript_path:
            self._transcript_path.mkdir(parents=True, exist_ok=True)
        if self._response_path:
            self._response_path.mkdir(parents=True, exist_ok=True)

    def send(self, prompt: str, **kwargs):
        """Record a prompt and return a placeholder response."""
        response = {
            "model": self.model,
            "interface": self.interface,
            "content": f"[ActiveLLM placeholder response to: {prompt}]",
        }
        self._history.append(response)
        # Write transcript (request/response) if enabled
        if getattr(self, "_transcript_path", None):
            idx = len(self._history) - 1
            transcript_file = self._transcript_path / f"transcript_{idx}.json"
            request = {"model": self.model, "prompt": prompt, "interface": self.interface}
            transcript_file.write_text(json.dumps({"request": request, "response": response}, indent=2), encoding="utf-8")
        # Write response artifact if enabled
        if getattr(self, "_response_path", None):
            idx = len(self._history) - 1
            response_file = self._response_path / f"response_{idx}.json"
            response_file.write_text(json.dumps(response, indent=2), encoding="utf-8")
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

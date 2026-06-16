'''Remote OpenAI‑compatible LLM wrapper for Gamma.

Provides placeholder functionality and raises errors for unsupported low‑rank
operations.
'''

from .backends.openai_compatible import OpenAICompatibleClient
from .errors import UnsupportedOperationError

class RemoteLLM:
    """Remote (API) LLM wrapper using OpenAICompatibleClient.

    Mirrors the previous stub API while performing real HTTP calls.
    """

    def __init__(self, url: str = "http://localhost:8000/v1", api_key=None, api_key_env: str | None = None,
                 model: str | None = None, timeout: float = 120.0, transcript_dir: str | None = None, response_dir: str | None = None, **kwargs):
        # Initialise the underlying client; kwargs are accepted for compatibility
        self._client = OpenAICompatibleClient(
            url=url,
            api_key=api_key,
            api_key_env=api_key_env,
            model=model,
            timeout=timeout,
            transcript_dir=transcript_dir,
            response_dir=response_dir,
        )
        self.url = url
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def send(self, prompt: str, **kwargs):
        """Send a prompt via the OpenAI‑compatible client."""
        response = self._client.send(prompt, **kwargs)
        return response

    def read(self):
        """Return the client's recorded interactions."""
        return self._client.read()

    def status(self):
        """Combine client status with remote‑specific metadata."""
        status = self._client.status()
        status.update({
            "kind": "remote",
            "url": self.url,
            "model": self.model,
            "lowrank_supported": False,
        })
        return status

    # Low‑rank stubs – unsupported
    def lora(self, *args, **kwargs):
        raise UnsupportedOperationError("RemoteLLM does not support local LoRA jobs.")

    def dora(self, *args, **kwargs):
        raise UnsupportedOperationError("RemoteLLM does not support local DoRA jobs.")

    def sft(self, *args, **kwargs):
        raise UnsupportedOperationError("RemoteLLM does not support local SFT jobs.")

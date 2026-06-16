"""OpenAI compatible mocked LLM client.

This client pretends to talk to an OpenAI‑compatible endpoint but does not make any network
calls. It stores prompts in memory and returns a deterministic placeholder response.

All low‑rank operations (lora, dora, sft) are unsupported and raise
:class:`gamma.llm.errors.UnsupportedOperationError`.
"""

from ..remote import RemoteLLM
from ..errors import UnsupportedOperationError


class OpenAIMockLLM(RemoteLLM):
    """A lightweight mock of an OpenAI‑compatible remote LLM.

    Parameters
    ----------
    url: str
        Base URL of the mocked service (e.g. ``"http://mock-openai"``).
    api_key: str
        API key – stored internally but redacted in :meth:`status`.
    """

    def __init__(self, url: str, api_key: str):
        super().__init__(url=url, api_key=api_key)
        self._history: list[str] = []
        # Ensure the base class does not perform any network calls.
        # RemoteLLM only stores the arguments; no side effects.

    def send(self, prompt: str):
        """Record *prompt* and return a mock response dict.

        The response mimics the shape of an OpenAI ``/v1/completions`` payload
        but contains only placeholder data.
        """
        self._history.append(prompt)
        return {"id": "mock-id", "object": "completion", "choices": [{"text": "mocked response"}]}

    def read(self):
        """Return the most recent prompt's placeholder response.

        If no prompt has been sent yet, returns an empty dict.
        """
        if not self._history:
            return {}
        # Return deterministic placeholder for the latest prompt.
        return {"response": "mocked response for: " + self._history[-1]}

    def status(self):
        """Return minimal status with redacted API key."""
        return {"url": self.url, "api_key": "REDACTED"}

    # Low‑rank methods deliberately raise the unsupported error defined in the base.
    def lora(self, *_, **__):  # pragma: no cover – exercised via inheritance test
        raise UnsupportedOperationError("Low‑rank Lora not supported by OpenAI mock client")

    def dora(self, *_, **__):  # pragma: no cover
        raise UnsupportedOperationError("Low‑rank Dora not supported by OpenAI mock client")

    def sft(self, *_, **__):  # pragma: no cover
        raise UnsupportedOperationError("SFT not supported by OpenAI mock client")

'''Public API entry points for Gamma.

Provides the user‑facing ``allm`` and ``llm`` factory functions that return
instances of the active and remote LLM classes respectively.
'''

from .api import allm, llm

__all__ = ["allm", "llm"]

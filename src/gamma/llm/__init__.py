'''LLM interfaces for Gamma.

Exports ActiveLLM and RemoteLLM for package-level imports.
''' 

from .active import ActiveLLM
from .remote import RemoteLLM

__all__ = ["ActiveLLM", "RemoteLLM"]

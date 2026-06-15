'''Public API entry points for Gamma.

Provides the user‑facing ``allm`` and ``llm`` factory functions that return
instances of the active and remote LLM classes respectively.
'''

from .llm.active import ActiveLLM
from .llm.remote import RemoteLLM

def allm(*args, **kwargs) -> ActiveLLM:
    """Create and return an ActiveLLM instance.

    Parameters are passed through to :class:`ActiveLLM` constructor.
    """
    return ActiveLLM(*args, **kwargs)

def llm(*args, **kwargs) -> RemoteLLM:
    """Create and return a RemoteLLM instance.

    Parameters are passed through to :class:`RemoteLLM` constructor.
    """
    return RemoteLLM(*args, **kwargs)

'''LLM base classes and simple implementations.

This module provides minimal ActiveLLM and RemoteLLM classes that satisfy the
public API. They are deliberately lightweight; advanced functionality is
implemented elsewhere in the Gamma runtime.
'''\n\nclass ActiveLLM:\n    """Active (local) LLM wrapper.
    \n    For demonstration purposes this class merely echoes the prompt. In the real
    Gamma system it would interface with the local runtime.
    """
    def __init__(self, *args, **kwargs):\n        self.args = args\n        self.kwargs = kwargs\n\n    def generate(self, prompt: str) -> str:\n        """Return a placeholder response.
        \n        In a production environment this would call the underlying local LLM.
        """
        return f"[ActiveLLM response to: {prompt}]"\n\n    __call__ = generate\n\nclass RemoteLLM:\n    """Remote (API) LLM wrapper.
    \n    This stub pretends to call a remote service and returns a formatted string.
    """
    def __init__(self, *args, **kwargs):\n        self.args = args\n        self.kwargs = kwargs\n\n    def generate(self, prompt: str) -> str:\n        return f"[RemoteLLM response to: {prompt}]"\n\n    __call__ = generate\n

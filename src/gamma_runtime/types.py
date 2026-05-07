"""
Compatibility boundary for legacy gamma_runtime imports; 
canonical definitions live in runtime_types.py.
"""
from .runtime_types import (
    AgentId,
    SessionId,
    AgentSpec,
    ModelSpec,
    InferenceRequest,
    InferenceResult,
    AgentMessage,
    MissionContext,
)

__all__ = [
    "AgentId",
    "SessionId",
    "AgentSpec",
    "ModelSpec",
    "InferenceRequest",
    "InferenceResult",
    "AgentMessage",
    "MissionContext",
]

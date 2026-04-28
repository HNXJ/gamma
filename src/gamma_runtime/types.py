from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Literal

RoleName = str
ModelKey = str
AdapterKey = str
SessionId = str
AgentId = str

@dataclass(frozen=True)
class ModelSpec:
    key: ModelKey
    provider: Literal["lmstudio", "mlx"]
    name: str | None = None
    path: str | None = None
    context_length: int = 4096
    quantization: str | None = None
    max_parallel_slots: int = 1
    device: str | None = None
    config: dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class AdapterRef:
    key: AdapterKey
    path: str
    adapter_type: Literal["lora", "dora", "composite"]
    shared: bool = True

@dataclass(frozen=True)
class AgentSpec:
    agent_id: AgentId
    role: RoleName
    model_key: ModelKey
    system_prompt: str
    adapter_stack: list[AdapterKey] = field(default_factory=list)
    tool_policy: dict[str, Any] = field(default_factory=dict)
    generation: dict[str, Any] = field(default_factory=dict)
    routing_tags: list[str] = field(default_factory=list)

@dataclass
class InferenceRequest:
    session_id: SessionId
    agent_id: AgentId
    model_key: ModelKey
    messages: list[dict[str, str]]
    generation: dict[str, Any]
    adapter_stack: list[AdapterKey]

@dataclass
class InferenceResult:
    text: str
    raw: dict[str, Any]
    usage: dict[str, Any]
    latency_s: float

@dataclass
class AgentMessage:
    sender: AgentId
    recipient: AgentId | None
    kind: str
    content: dict[str, Any]

@dataclass
class PoolStats:
    active_requests: int = 0
    total_requests: int = 0
    total_tokens: int = 0

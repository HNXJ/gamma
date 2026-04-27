from .types import InferenceRequest, InferenceResult
from .model_pool import SharedModelPool

class InferenceScheduler:
    """The operational heart of parallel execution. Enforces budgets and routes requests."""
    
    def __init__(self, pool: SharedModelPool):
        self.pool = pool
        self._active_kv_tokens = 0
        self.MAX_KV_BUDGET = 128000 # Strict hardware constraint (Apple Silicon VRAM target)

    async def execute(self, request: InferenceRequest) -> InferenceResult:
        # Structured concurrency slot acquisition
        await self.pool.acquire_slot(request.model_key)
        
        # Simple heuristic for token estimation: 1 word ~ 1.3 tokens
        estimated_tokens = sum(int(len(m["content"].split()) * 1.3) for m in request.messages)
        
        try:
            if self._active_kv_tokens + estimated_tokens > self.MAX_KV_BUDGET:
                # Backpressure logic: in a full implementation, we'd wait or reject
                raise MemoryError(f"KV Cache budget exceeded ({self._active_kv_tokens + estimated_tokens} > {self.MAX_KV_BUDGET}). Backpressure applied.")
            
            self._active_kv_tokens += estimated_tokens
            print(f"DEBUG: Session {request.session_id} acquired KV budget. Pool utilization: {self._active_kv_tokens}/{self.MAX_KV_BUDGET}")
            
            # --- Yield to provider backend (MLX/LM Studio) here ---
            # result = await backend.generate(request)
            
            # Placeholder for actual generation
            result = InferenceResult(
                content=f"Agent {request.session_id} executing logically against {request.model_key}.",
                prompt_tokens=estimated_tokens,
                completion_tokens=50
            )
            return result
            
        finally:
            # Deterministic cleanup
            self._active_kv_tokens -= estimated_tokens
            self.pool.release_slot(request.model_key)
            print(f"DEBUG: Session {request.session_id} released KV budget. Pool utilization: {self._active_kv_tokens}/{self.MAX_KV_BUDGET}")

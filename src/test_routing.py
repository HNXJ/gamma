import asyncio
from gamma_runtime.backend_lmstudio import LMStudioBackend
from gamma_runtime.types import InferenceRequest, ModelSpec

async def main():
    backend = LMStudioBackend()
    
    request = InferenceRequest(
        session_id="test_session",
        agent_id="consensus_judge_01",
        model_key="gemma4-parallel",
        messages=[{"role": "user", "content": "ping"}],
        generation={"temperature": 0.8, "top_p": 0.9, "min_p": 0.1, "max_tokens": 10},
        adapter_stack=[]
    )
    
    print("Sending request through LMStudioBackend...")
    print(f"Original Logical Key: {request.model_key}")
    print(f"Agent ID: {request.agent_id}")
    
    try:
        result = await backend.generate(request)
        print(f"SUCCESS!")
        print(f"Resolved to Model in payload? (Check logs on server, but request succeeded against LMS port 1234)")
        print(f"Latency: {result.latency_s:.2f}s")
        print(f"Usage: {result.usage}")
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(main())

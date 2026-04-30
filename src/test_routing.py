import asyncio
from gamma_runtime.backend_lmstudio import LMStudioBackend
from gamma_runtime.types import InferenceRequest, ModelSpec
import sys

async def test_agent(backend, agent_id, expected_model):
    request = InferenceRequest(
        session_id="test_session",
        agent_id=agent_id,
        model_key="gemma4-parallel",
        messages=[{"role": "user", "content": "ping"}],
        generation={"temperature": 0.8, "top_p": 0.9, "min_p": 0.1, "max_tokens": 5},
        adapter_stack=[]
    )
    print(f"Testing Agent: {agent_id} (Expect: {expected_model})")
    try:
        result = await backend.generate(request)
        resolved_model = result.raw.get("model")
        print(f"  -> SUCCESS! Resolved LMS ID: {resolved_model}")
        if resolved_model != expected_model:
            print(f"  -> ERROR: Mismatch. Expected {expected_model}, got {resolved_model}")
            return False
        return True
    except Exception as e:
        print(f"  -> FAILED: {e}")
        return False

async def main():
    backend = LMStudioBackend(base_url="http://127.0.0.1:1234")
    
    success = True
    success &= await test_agent(backend, "v1_gamma_proponent", "G01-builder")
    success &= await test_agent(backend, "v1_gamma_adversary", "G03-analyst")
    success &= await test_agent(backend, "v1_gamma_consensus", "J01-judge")
    
    print("\nTesting Unmapped Agent without fallback:")
    request = InferenceRequest(
        session_id="test_session",
        agent_id="unknown_agent_99",
        model_key="gemma4-parallel",
        messages=[{"role": "user", "content": "ping"}],
        generation={"max_tokens": 5},
        adapter_stack=[]
    )
    try:
        await backend.generate(request)
        print("  -> ERROR: Unmapped agent succeeded silently!")
        success = False
    except Exception as e:
        print(f"  -> SUCCESS: Raised error as expected: {e}")
        
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

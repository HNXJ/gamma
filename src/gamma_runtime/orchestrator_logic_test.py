import asyncio
import sys
from pathlib import Path

# Add src and root to path
sys.path.append(str(Path(__file__).parent.parent / "src"))
sys.path.append(str(Path(__file__).parent.parent))

from gamma_runtime.orchestrator import UnifiedOrchestrator
from gamma_runtime.scheduler import InferenceScheduler
from gamma_runtime.registry import RuntimeRegistry

async def test_orchestrator_logic():
    print("🚀 Testing UnifiedOrchestrator Logic...")
    
    scheduler = InferenceScheduler()
    # Mocking the registry root to avoid actual file reads if needed, 
    # but let's use the real one since it exists
    registry = RuntimeRegistry(str(Path(__file__).parent.parent / "configs"))
    orchestrator = UnifiedOrchestrator(scheduler, registry)
    
    # Launch a council run (this will start a background task)
    session_id = await orchestrator.launch_run(
        run_type="council",
        topic="Testing the orchestrator handshake.",
        rounds=1
    )
    
    print(f"Session launched: {session_id}")
    assert "session-council-" in session_id
    
    # Check session state (initial)
    state = orchestrator.get_session_state(session_id)
    print(f"Initial state topic: {state['topic']}")
    assert state['topic'] == "Testing the orchestrator handshake."
    
    print("\nOrchestrator Logic Verification: SUCCESS")

if __name__ == "__main__":
    asyncio.run(test_orchestrator_logic())

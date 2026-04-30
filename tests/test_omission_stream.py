import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from src.sde_engine.omission_pipeline import OmissionPipeline
from src.gamma_runtime.orchestrator import UnifiedOrchestrator
from src.gamma_runtime.types import InferenceResult

@pytest.mark.anyio
async def test_omission_pipeline_fedlora_trigger():
    """
    Mock a 150-neuron session and verify the FedLoRA trigger fires at the end of the epoch.
    """
    # 1. Setup Mocks
    mock_orchestrator = MagicMock(spec=UnifiedOrchestrator)
    mock_orchestrator.scheduler = MagicMock()
    mock_orchestrator.scheduler.schedule = AsyncMock(return_value=InferenceResult(
        text="Mock Proposal/Critique",
        raw={},
        usage={"total_tokens": 100},
        latency_s=0.5
    ))
    mock_orchestrator.registry = MagicMock()
    mock_orchestrator.registry.load_agent = MagicMock(return_value=MagicMock(
        agent_id="mock_agent",
        model_key="mock_model",
        system_prompt="Static Ego",
        generation={},
        adapter_stack=[]
    ))
    
    mock_orchestrator.consolidation = MagicMock()
    mock_orchestrator.consolidation.extract_validated_traces = MagicMock(return_value="/path/to/payload.json")
    mock_orchestrator.consolidation.trigger_training = AsyncMock()

    # 2. Initialize Pipeline with 150 neurons (3 batches of 50)
    pipeline = OmissionPipeline(mock_orchestrator)
    
    # Override sessions to just one for the test
    pipeline.sessions = ["test_session_1"]
    
    # Patch laminar_batch_iterator to return a fixed number of neurons
    def mock_iterator(session_id):
        # 150 neurons -> 3 batches of 50
        for i in range(3):
            yield [{"id": f"unit_{j}", "depth": "superficial"} for j in range(50)]
            
    with patch.object(OmissionPipeline, 'laminar_batch_iterator', side_effect=mock_iterator):
        # 3. Execute
        await pipeline.execute_full_pipeline()

    # 4. Assertions
    # Ensure extract_validated_traces was called exactly once (at the end of the session)
    mock_orchestrator.consolidation.extract_validated_traces.assert_called_once()
    
    # Ensure trigger_training was called exactly once
    mock_orchestrator.consolidation.trigger_training.assert_called_once_with(
        "/path/to/payload.json", 
        model_key="gemma-9b-schiz"
    )
    
    # Ensure SDE iterations happened (3 batches * 2 calls [prop/adv] = 6 schedule calls)
    # Actually SDESolver makes 2 calls per run_optimization_cycle
    assert mock_orchestrator.scheduler.schedule.call_count == 6

if __name__ == "__main__":
    import sys
    import pytest
    sys.exit(pytest.main([__file__]))

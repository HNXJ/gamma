import pytest
import os
import json
from pathlib import Path
from gamma_runtime.auto_continue import AutoContinueDaemon
from gamma_runtime.registry import RuntimeRegistry
from gamma_runtime.scheduler import InferenceScheduler

def test_auto_continue_dry_run(tmp_path):
    # Setup mock config
    config_root = tmp_path / "context" / "configs"
    (config_root / "agents").mkdir(parents=True)
    (config_root / "models").mkdir(parents=True)
    (config_root / "teams").mkdir(parents=True)

    # Mock Model
    model_data = {
        "key": "test-model",
        "provider": "lmstudio",
        "name": "test",
        "context_length": 4096
    }
    with open(config_root / "models" / "test-model.json", "w") as f:
        json.dump(model_data, f)

    # Mock Agent
    agent_data = {
        "agent_id": "T01",
        "role": "tester",
        "model_key": "test-model",
        "system_prompt": "test"
    }
    with open(config_root / "agents" / "T01.json", "w") as f:
        json.dump(agent_data, f)

    # Mock Team
    team_data = {
        "team_id": "test-team",
        "agents": ["T01"]
    }
    with open(config_root / "teams" / "test-team.json", "w") as f:
        json.dump(team_data, f)

    registry = RuntimeRegistry(str(config_root))
    scheduler = InferenceScheduler()
    
    daemon = AutoContinueDaemon(
        registry=registry,
        scheduler=scheduler,
        interval_sec=1,
        max_turns=1,
        dry_run=True
    )
    
    # We need to ensure ProfileRegistry returns T01 as route-ready or mock it
    # For Stage 3, we'll just test that execute_tick works in dry-run
    from gamma_runtime.runtime_types import AgentSpec
    agents = [AgentSpec(**agent_data)]
    
    import asyncio
    results = asyncio.run(daemon.execute_tick(agents))
    
    assert len(results) == 1
    assert results[0][0] == "T01"
    assert "DRY-RUN" in results[0][1].text
    
    # Check persistence
    run_dir = daemon.output_dir
    assert run_dir.exists()
    manifests = list(run_dir.glob("manifest_*.json"))
    assert len(manifests) == 1
    
    with open(manifests[0], "r") as f:
        data = json.load(f)
        assert data["dry_run"] is True
        assert data["truth_mode"] == "truth_safe_unverified"

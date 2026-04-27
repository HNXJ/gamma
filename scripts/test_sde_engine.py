import asyncio
import pytest
import re
from typing import Dict, Any, List, Tuple

# Import the core engine from the main script
from sde_game_server import (
    SDEGameServer, PlayerAgent, PlayerProposal, GameState, TurnResult,
    DummyMathPolicy, MockExecutionBridge, GamePolicy
)

# ==========================================
# 1. CHAOS AGENTS & BRIDGES
# ==========================================

class ErraticAgent(PlayerAgent):
    """An agent that ignores feedback for N turns to test persistence."""
    def __init__(self, agent_id, role, stubborn_until=2):
        super().__init__(agent_id, role, "http://localhost:1234")
        self.stubborn_until = stubborn_until

    async def get_proposal(self, prompt: str) -> PlayerProposal:
        epoch = int(re.search(r'Epoch: (\d+)', prompt).group(1))
        # Be stubborn (propose 1000) until epoch > stubborn_until
        val = 1000 if epoch <= self.stubborn_until else 60
        return PlayerProposal(self.agent_id, self.role, f"I propose {val}", parsed_payload={"value": val}, valid=True)

class FailingBridge(MockExecutionBridge):
    """A bridge that fails on boot or win execution."""
    def __init__(self, fail_on_boot=False, fail_on_win=False):
        self.fail_on_boot = fail_on_boot
        self.fail_on_win = fail_on_win

    async def boot_environment(self) -> bool:
        if self.fail_on_boot: return False
        return await super().boot_environment()

    async def execute_win_state(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if self.fail_on_win: raise RuntimeError("REMOTE SSH TIMEOUT")
        return await super().execute_win_state(payload)

# ==========================================
# 2. PYTEST SUITE
# ==========================================

@pytest.mark.asyncio
async def test_standard_convergence():
    """Verify that a normal game loop reaches a win-state."""
    bridge = MockExecutionBridge()
    server = SDEGameServer(bridge)
    server.load_policy(DummyMathPolicy())
    
    g1 = PlayerAgent("G1", "Excitatory", "http://localhost:1234")
    g2 = PlayerAgent("G2", "Inhibitory", "http://localhost:1234")
    
    # Linear convergence mocks
    g1.get_proposal = lambda prompt: asyncio.sleep(0.1, result=PlayerProposal("G1", "Excitatory", "I propose 60", parsed_payload={"value": 60}, valid=True))
    g2.get_proposal = lambda prompt: asyncio.sleep(0.1, result=PlayerProposal("G2", "Inhibitory", "I propose 40", parsed_payload={"value": 40}, valid=True))
    
    server.add_player(g1)
    server.add_player(g2)
    
    result = await server.start_game_loop(max_epochs=1)
    assert result.accepted is True
    assert result.winning_payload == {"g1": 60, "g2": 40}
    assert result.council_loss == 0.0

@pytest.mark.asyncio
async def test_stubborn_agent_recovery():
    """Verify the server survives an agent that initially fails to cooperate."""
    bridge = MockExecutionBridge()
    server = SDEGameServer(bridge)
    server.load_policy(DummyMathPolicy())
    
    # G1 is stubborn until epoch 2
    g1 = ErraticAgent("G1", "Excitatory", stubborn_until=2)
    g2 = PlayerAgent("G2", "Inhibitory", "http://localhost:1234")
    g2.get_proposal = lambda prompt: asyncio.sleep(0, result=PlayerProposal("G2", "Inhibitory", "I propose 40", parsed_payload={"value": 40}, valid=True))
    
    server.add_player(g1)
    server.add_player(g2)
    
    # Should take at least 3 epochs to converge
    result = await server.start_game_loop(max_epochs=5)
    assert result.accepted is True
    assert result.epoch >= 3
    assert result.council_loss == 0.0

@pytest.mark.asyncio
async def test_boot_failure_handling():
    """Verify server raises an error if the execution bridge fails to boot."""
    bridge = FailingBridge(fail_on_boot=True)
    server = SDEGameServer(bridge)
    server.load_policy(DummyMathPolicy())
    
    with pytest.raises(RuntimeError, match="Failed to boot remote environment"):
        await server.start_game_loop(max_epochs=1)

@pytest.mark.asyncio
async def test_win_state_failure_cleanup():
    """Verify that a win-state failure triggers an emergency state."""
    bridge = FailingBridge(fail_on_win=True)
    server = SDEGameServer(bridge)
    server.load_policy(DummyMathPolicy())
    
    g1 = PlayerAgent("G1", "Excitatory", "http://localhost:1234")
    g1.get_proposal = lambda p: asyncio.sleep(0, result=PlayerProposal("G1", "Excitatory", "60", {"value": 60}, True))
    g2 = PlayerAgent("G2", "Inhibitory", "http://localhost:1234")
    g2.get_proposal = lambda p: asyncio.sleep(0, result=PlayerProposal("G2", "Inhibitory", "40", {"value": 40}, True))
    
    server.add_player(g1)
    server.add_player(g2)
    
    # The win detection happens in run_epoch and calls the bridge
    with pytest.raises(RuntimeError, match="REMOTE SSH TIMEOUT"):
        await server.start_game_loop(max_epochs=1)

@pytest.mark.asyncio
async def test_schema_validation_failure():
    """Verify that malformed agent output is penalized and feedback is applied."""
    bridge = MockExecutionBridge()
    server = SDEGameServer(bridge)
    server.load_policy(DummyMathPolicy())
    
    g1 = PlayerAgent("G1", "Excitatory", "http://localhost:1234")
    # Agent sends text with no numbers
    g1.get_proposal = lambda p: asyncio.sleep(0, result=PlayerProposal("G1", "Excitatory", "No number here!", valid=False))
    
    server.add_player(g1)
    
    # We just run one epoch to check feedback
    result = await server.run_epoch()
    assert result.accepted is False
    assert "FEEDBACK" in g1.history[-1]["content"]
    assert "Could not find an integer" in g1.history[-1]["content"]

@pytest.mark.asyncio
async def test_emergency_kill_trigger():
    """Verify that emergency_kill propagates to the bridge."""
    bridge = MockExecutionBridge()
    server = SDEGameServer(bridge)
    # This just checks if calling it hits the bridge log
    await server.emergency_kill()
    # (Checking log/state if we had tracking)

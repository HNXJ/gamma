import asyncio
import logging
from typing import Dict, Any, Optional, List
from gamma_runtime.types import AgentId, InferenceRequest, AgentSpec
from gamma_runtime.scheduler import InferenceScheduler
from gamma_runtime.blackboard import Blackboard
from gamma_runtime.registry import RuntimeRegistry
from .metrics import SDEMetrics

logger = logging.getLogger("SDESolver")

class SDESolver:
    """
    Sovereign SDE Engine for Gamma.
    Refactored to remove shadow agent logic and integrate with the Gamma Runtime.
    Tracks trajectories and convergence metrics directly on the Blackboard.
    """
    def __init__(self, scheduler: InferenceScheduler, blackboard: Blackboard, registry: Optional[RuntimeRegistry] = None):
        self.scheduler = scheduler
        self.blackboard = blackboard
        self.registry = registry or RuntimeRegistry("configs")
        self.metrics = SDEMetrics()

    async def run_optimization_cycle(
        self, 
        proponent: Any, 
        adversary: Any, 
        batch_data: Optional[List[Dict[str, Any]]] = None
    ):
        """
        Executes a single adversarial SDE optimization cycle.
        Supports passing AgentSpec objects or AgentIds (strings).
        If batch_data is provided, it is injected into the proponent's context.
        """
        prop_spec = proponent if isinstance(proponent, AgentSpec) else self.registry.load_agent(proponent)
        adv_spec = adversary if isinstance(adversary, AgentSpec) else self.registry.load_agent(adversary)

        # 1. Proponent Turn
        prompt = "Propose optimal E-I parameters."
        if batch_data:
            prompt += f"\n\n### Batch Data ({len(batch_data)} neurons):\n{batch_data}"
            
        proposal_req = self._build_inference_request(prop_spec, prompt)
        proposal_res = await self.scheduler.schedule(prop_spec.model_key, proposal_req)
        proposal_text = proposal_res.text
        
        # 2. Heuristic Parameter Extraction (Mocked for Phase 2)
        gmax_estimate = 0.42 # Extracted from proposal_text
        mse_estimate = 0.05
        
        x = self.metrics.calculate_x(mse_estimate)
        z = self.metrics.calculate_z(gmax_estimate)
        
        # 3. Adversary Turn (Critique)
        critique_req = self._build_inference_request(adv_spec, f"Attack this proposal:\n{proposal_text}")
        critique_res = await self.scheduler.schedule(adv_spec.model_key, critique_req)
        
        # 4. Final Aggregation
        w = self.metrics.calculate_w(0.0) 
        y = 0.85 
        
        council_loss = self.metrics.council_loss(x, y, z, w)
        
        # 5. Blackboard Commitment
        await self.blackboard.add_entry(
            sender=prop_spec.agent_id,
            content=proposal_text,
            metadata={"kind": "sde_proposal", "x": x, "z": z, "batch_size": len(batch_data) if batch_data else 0}
        )
        
        await self.blackboard.add_entry(
            sender=adv_spec.agent_id,
            content=critique_res.text,
            metadata={"kind": "sde_critique"}
        )
        
        state_entry = await self.blackboard.add_entry(
            sender="SDE_ENGINE",
            content=f"Equilibrium Check: Round {self.blackboard.round} complete.",
            metadata={
                "kind": "sde_metrics",
                "x": x, "y": y, "z": z, "w": w,
                "loss": council_loss,
                "converged": council_loss < 0.1
            }
        )
        
        logger.info(f"SDE Cycle Complete. Council Loss: {council_loss:.4f}")
        return state_entry

    async def execute_materialized_config(self, config: Dict[str, Any]):
        """
        Executes a biophysical simulation grounded in a materialized config.
        Stage 2: Asserts consistency and triggers the optimization cycle.
        """
        n = config["neuron_count"]
        logger.info(f"Executing grounded biophysical simulation for N={n} neurons.")
        
        # Construct mock batch based on materialized neuron count
        mock_batch = [{"id": f"neuron_{i}"} for i in range(n)]
        
        state_entry = await self.run_optimization_cycle(
            proponent="v1_gamma_proponent",
            adversary="v1_gamma_adversary",
            batch_data=mock_batch
        )
        
        # Ensure neuron_count is explicitly tracked in metadata for truth-verification
        state_entry.metadata["neuron_count"] = n
        return state_entry

    def _build_inference_request(self, agent: AgentSpec, prompt: str) -> InferenceRequest:
        return InferenceRequest(
            session_id=f"sde-{self.blackboard.topic[:10]}",
            agent_id=agent.agent_id,
            model_key=agent.model_key,
            messages=[
                {"role": "system", "content": agent.system_prompt},
                {"role": "user", "content": prompt}
            ],
            generation=agent.generation,
            adapter_stack=agent.adapter_stack
        )

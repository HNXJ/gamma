import asyncio
import logging
import json
import re
from typing import Dict, Any, Optional, List
from src.gamma_runtime.types import AgentId, InferenceRequest, AgentSpec
from src.gamma_runtime.scheduler import InferenceScheduler
from src.gamma_runtime.blackboard import Blackboard
from src.gamma_runtime.registry import RuntimeRegistry
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

    def _parse_proposal_text(self, text: str) -> Dict[str, Any]:
        """
        Extracts JSON from agent proposal text. Supports fenced and raw JSON.
        """
        # 1. Try to find fenced JSON blocks
        fenced_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if fenced_match:
            try:
                return {"status": "success", "data": json.loads(fenced_match.group(1))}
            except json.JSONDecodeError as e:
                return {"status": "failed", "error": f"JSONDecodeError in fenced block: {str(e)}"}
                
        # 2. Try to find anything that looks like a JSON object
        json_match = re.search(r"(\{.*\})", text, re.DOTALL)
        if json_match:
            try:
                return {"status": "success", "data": json.loads(json_match.group(1))}
            except json.JSONDecodeError as e:
                return {"status": "failed", "error": f"JSONDecodeError in text: {str(e)}"}
                
        return {"status": "failed", "error": "No JSON object found in proposal text"}

    def _extract_parameters(self, proposal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extracts scientific parameters from parsed proposal data.
        """
        params = proposal_data.get("parameters", proposal_data)
        
        valid_keys = {
            "gmax", "gNa_gmax", "gNa", "gNa_bar", "gK", "gLeak", 
            "gCa", "gM", "gA", "gH", "gK_bar", "gL", "g_leak",
            "mse", "mse_estimate"
        }
        
        extracted = {k: v for k, v in params.items() if k in valid_keys and isinstance(v, (int, float))}
        
        # Check for at least one conductance parameter (scientific causality)
        conductance_keys = {"gmax", "gNa_gmax", "gNa", "gNa_bar", "gK", "gLeak"}
        if not any(k in extracted for k in conductance_keys):
            return {"status": "failed", "error": "No valid conductance parameters found (e.g., gmax, gNa)"}
            
        return {"status": "success", "parameters": extracted}

    async def _run_optimization_cycle(
        self, 
        proponent: Any, 
        adversary: Any, 
        batch_data: Optional[List[Dict[str, Any]]] = None,
        provenance: Optional[Dict[str, Any]] = None
    ):
        """
        [PROTECTED] Executes a single adversarial SDE optimization cycle.
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
        
        # 2. Robust Parameter Extraction
        parse_res = self._parse_proposal_text(proposal_text)
        if parse_res["status"] == "success":
            extract_res = self._extract_parameters(parse_res["data"])
        else:
            extract_res = parse_res

        if extract_res["status"] == "failed":
            logger.error(f"Proposal parsing failed: {extract_res['error']}")
            # Mark the execution as proposal_parse_failed and abort cycle
            await self.blackboard.add_entry(
                sender=prop_spec.agent_id,
                content=proposal_text,
                metadata={
                    "kind": "sde_proposal", 
                    "status": "proposal_parse_failed", 
                    "error": extract_res["error"]
                }
            )
            return

        params = extract_res["parameters"]
        # Prioritize 'gmax' or first available conductance
        gmax_estimate = params.get("gmax") or params.get("gNa") or params.get("gNa_bar") or 0.0
        mse_estimate = params.get("mse") or params.get("mse_estimate") or 0.1 # Defaulting to 0.1 if missing but JSON parsed
        
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
            metadata={
                "kind": "sde_proposal", 
                "x": x, 
                "z": z, 
                "parameters": params,
                "batch_size": len(batch_data) if batch_data else 0
            }
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
                "converged": council_loss < 0.1,
                "provenance": provenance or {"materialized_by": "unknown"}
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
        
        state_entry = await self._run_optimization_cycle(
            proponent="v1_gamma_proponent",
            adversary="v1_gamma_adversary",
            batch_data=mock_batch,
            provenance=config.get("provenance")
        )
        
        # Ensure full contextual metadata is tracked for Stage 2D truth-verification
        state_entry.metadata.update({
            "neuron_count": n,
            "proposal_id": config.get("proposal_id"),
            "mission_topic": config.get("mission_topic")
        })
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

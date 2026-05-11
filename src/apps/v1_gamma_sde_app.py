import asyncio
import json
import logging
import os
import time
from typing import Optional
from gamma_runtime.scheduler import InferenceScheduler
from gamma_runtime.registry import RuntimeRegistry
from gamma_runtime.blackboard import Blackboard
from gamma_runtime.runtime_types import MissionContext
from apps.council_app import CouncilOrchestrator

logger = logging.getLogger("V1GammaSDEApp")

class V1GammaSDEOrchestrator(CouncilOrchestrator):
    """
    Thin wrapper around the CouncilOrchestrator specifically designed for the V1 Gamma SDE Game.
    It intercepts the Proponent's output, structures it into a JSON payload, and writes it
    out for the jbiophysic-main repository to consume and simulate.
    """
    def __init__(self, scheduler: InferenceScheduler, registry: RuntimeRegistry, mission_context: MissionContext, blackboard: Optional[Blackboard] = None):
        super().__init__(scheduler, registry, blackboard)
        self.mission_context = mission_context
        self.proposals_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "sde_proposals")
        os.makedirs(self.proposals_dir, exist_ok=True)

    async def run_deliberation(self, team_id: str, topic: str, rounds: int = 2):
        if not self.blackboard:
            self.blackboard = Blackboard(topic)

        team_config = self.registry.load_team(team_id)
        agents = [self.registry.load_agent(aid) for aid in team_config["agents"]]

        logger.info(f"🚀 INITIATING V1 GAMMA SDE DELIBERATION: '{topic}'")

        for r in range(rounds):
            self.blackboard.round = r + 1
            logger.info(f"--- SDE Epoch {self.blackboard.round} ---")

            # Managed Parallel Execution via Scheduler
            requests = []
            for agent in agents:
                req = self._build_request(agent)
                requests.append((agent.model_key, req))

            results = await self.scheduler.batch_run(requests)

            for i, result in enumerate(results):
                agent_id = agents[i].agent_id
                await self.blackboard.add_entry(agent_id, result.text)
                logger.info(f"[{agent_id}] Entry committed to blackboard.")

                # If the Proponent proposed something, we extract and serialize it.
                if agent_id == "v1_gamma_proponent":
                    await self._emit_proposal(self.blackboard.round, result.text)

        logger.info("✅ V1 GAMMA SDE DELIBERATION COMPLETE.")
        return self.blackboard

    async def _emit_proposal(self, epoch: int, content: str):
        """
        Parses the proponent's text for a JSON block and writes it to disk
        if and only if it satisfies the active mission target and rubric.
        """
        try:
            # 1. Extract JSON block
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            else:
                start = content.find('{')
                end = content.rfind('}') + 1
                if start != -1 and end > start:
                    json_str = content[start:end]
                else:
                    json_str = ""

            # 2. Rubric Drift Check
            is_prose_only = "intended_action" not in content or "propose_only" in content
            if not json_str and is_prose_only:
                logger.warning("⚠️ PROSE-ONLY DRIFT: No structured scientific action detected.")
                await self.blackboard.add_entry(
                    sender="SYSTEM_VALIDATOR",
                    content="DRIFT DETECTED: Prose-only output without executable artifact intent.",
                    metadata={"kind": "drift_warning", "reason": "prose_only_yapping"}
                )
                return

            if not json_str:
                logger.error("💥 Failed to locate JSON block in proponent output.")
                return

            # 3. Parse JSON
            proposal = json.loads(json_str)

            # 4. Schema & Mission Alignment Validation
            rejection_reason = None
            meta = proposal.get("meta")

            # Check for rubric fields in JSON if possible
            work_unit = {
                "study_question": proposal.get("study_question"),
                "intended_action": proposal.get("intended_action"),
                "claim_type": proposal.get("claim_type")
            }

            if not meta or not isinstance(meta, dict):
                rejection_reason = "Missing or malformed 'meta' block."
            elif "neuron_count" not in meta:
                rejection_reason = "Missing 'meta.neuron_count' field."
            elif not isinstance(meta["neuron_count"], int):
                rejection_reason = f"Non-integer 'meta.neuron_count': {type(meta['neuron_count']).__name__}"
            elif meta["neuron_count"] != self.mission_context.target_neuron_count:
                rejection_reason = f"Mission Mismatch: Proposal N={meta['neuron_count']} != Target N={self.mission_context.target_neuron_count}"
            elif work_unit["intended_action"] == "propose_only" and work_unit["claim_type"] != "proposal_value":
                rejection_reason = "Rubric Violation: intended_action 'propose_only' requires claim_type 'proposal_value'."

            if rejection_reason:
                logger.warning(f"❌ PROPOSAL REJECTED: {rejection_reason}")
                # Structured rejection log for monitor ingestion
                await self.blackboard.add_entry(
                    sender="SYSTEM_VALIDATOR",
                    content=f"REJECTED PROPOSAL [Target N={self.mission_context.target_neuron_count}]: {rejection_reason}",
                    metadata={"kind": "proposal_rejection", "reason": rejection_reason, "target": self.mission_context.target_neuron_count}
                )
                return

            # 5. Successful Emission
            if "proposal_id" not in proposal:
                proposal["proposal_id"] = f"epoch_{epoch:02d}_candidate_{int(time.time())}"

            filename = os.path.join(self.proposals_dir, f"{proposal['proposal_id']}.json")
            with open(filename, 'w') as f:
                json.dump(proposal, f, indent=2)

            logger.info(f"✅ Emitted mission-aligned proposal: {filename}")
            await self.blackboard.add_entry(
                sender="SYSTEM_VALIDATOR",
                content=f"ACCEPTED PROPOSAL [Target N={self.mission_context.target_neuron_count}]: {proposal['proposal_id']}",
                metadata={
                    "kind": "proposal_acceptance",
                    "proposal_id": proposal['proposal_id'],
                    "intended_action": work_unit["intended_action"]
                }
            )
        except Exception as e:
            logger.error(f"💥 Failed to parse/emit proposal JSON: {e}")

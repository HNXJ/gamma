import logging
import json
import os
import time
from pathlib import Path
from .proposal_normalizer import ProposalNormalizer
from .bridge_contract import STATUS_INVALID, STATUS_PENDING
from .path_topology import GameLogTopology

class V1GammaBridge:
    def __init__(self, blackboard, enabled: bool = False, game_id: str = 'game001'):
        self.blackboard = blackboard
        self.enabled = enabled
        self.root = Path('/Users/HN/MLLM/gamma')
        self.topology = GameLogTopology(self.root, game_id)
        
        # Setup bridge-specific logger
        self.logger = logging.getLogger('GammaBridge')
        self.logger.setLevel(logging.INFO)
        # Clear existing handlers to avoid duplication if re-init
        self.logger.handlers = []
        fh = logging.FileHandler(self.topology.get_log_path('bridge'))
        fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(fh)

    async def process_proposal(self, agent_id: str, proposal_text: str, round_idx: int):
        if not self.enabled:
            return
            
        proposal_id = f'R{round_idx}_{agent_id}'
        self.logger.info('Received proposal for normalization: %s', proposal_id)
        
        # 1. Normalize & Validate Schema
        payload = ProposalNormalizer.normalize(proposal_text, proposal_id)
        if not payload:
            self.logger.warning('Proposal %s schema is invalid', proposal_id)
            await self.blackboard.add_entry(
                sender='bridge',
                content=f'INVALID PROPOSAL: {proposal_id} - Schema validation failed.',
                metadata={'status': STATUS_INVALID}
            )
            # Write invalid proposal to ledger for visibility
            self._write_to_ledger(proposal_id, STATUS_INVALID, agent_id, round_idx)
            return
            
        # 2. Enqueue in Durable Registry
        proposal_entry = {
            'proposal_id': proposal_id,
            'agent_id': agent_id,
            'round': round_idx,
            'status': STATUS_PENDING,
            'payload': payload.__dict__,
            'timestamp': time.time()
        }
        
        with open(self.topology.proposals_file, 'a') as f:
            f.write(json.dumps(proposal_entry) + '\n')
            
        await self.blackboard.add_entry(
            sender='bridge',
            content=f'PROPOSAL ENQUEUED: {proposal_id}. Awaiting scientific simulation...',
            metadata={'status': STATUS_PENDING, 'proposal_id': proposal_id}
        )
        self.logger.info('Proposal %s enqueued for execution.', proposal_id)

    def _write_to_ledger(self, proposal_id, status, agent_id, round_idx):
        entry = {
            'proposal_id': proposal_id,
            'agent_id': agent_id,
            'round': round_idx,
            'status': status,
            'timestamp': time.time()
        }
        with open(self.topology.proposals_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')


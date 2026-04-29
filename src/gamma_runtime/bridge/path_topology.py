import os
from pathlib import Path

class GameLogTopology:
    def __init__(self, root: Path, game_id: str = 'game001'):
        self.root = root
        self.game_id = game_id
        self.game_root = root / 'local' / game_id
        self.logs_dir = self.game_root / 'logs'
        self.proposals_dir = self.game_root / 'proposals'
        self.results_dir = self.game_root / 'results'
        self.provenance_dir = self.game_root / 'provenance'
        self.notes_dir = self.game_root / 'notes'
        self.heartbeat_dir = self.notes_dir / 'heartbeat'
        self.heartbeat_inputs = self.heartbeat_dir / 'inputs'
        self.heartbeat_outputs = self.heartbeat_dir / 'outputs'
        
        # Ensure directory structure
        for d in [self.logs_dir, self.proposals_dir, self.results_dir, self.provenance_dir, 
                  self.heartbeat_dir, self.heartbeat_inputs, self.heartbeat_outputs]:
            d.mkdir(parents=True, exist_ok=True)

    def get_log_path(self, subsystem: str) -> Path:
        return self.logs_dir / f'{subsystem}.log'

    @property
    def proposals_file(self) -> Path:
        return self.game_root / 'proposals.jsonl'

    @property
    def ledger_file(self) -> Path:
        return self.game_root / 'ledger.json'

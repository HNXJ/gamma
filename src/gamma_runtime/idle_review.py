import os
import json
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from .structs import InferenceRequest, ToolLoopResult
from .bridge.path_topology import GameLogTopology
from .tool_loop import execute_tool_loop

logger = logging.getLogger('IdleReview')

class IdleReviewManager:
    def __init__(self, scheduler, registry, heartbeat, game_id: str, root: Path):
        self.scheduler = scheduler
        self.registry = registry
        self.heartbeat = heartbeat
        self.game_id = game_id
        self.topology = GameLogTopology(root, game_id)
        self.last_idle_review_time = 0
        self.is_running = False

    async def run_heartbeat(self, idle_duration: float):
        if self.is_running:
            return
        
        self.is_running = True
        try:
            now_dt = datetime.now()
            timestamp_sortable = now_dt.strftime('%Y%m%d-%H%M%S')
            heartbeat_id = f'{self.game_id}-{timestamp_sortable}'
            logger.info(f'Starting Tool-Enabled Idle-Review: {heartbeat_id}')
            
            max_chars = 40000
            logs_metadata, logs_content = self._gather_recent_logs_with_metadata(max_chars=max_chars)
            
            input_artifact = {
                'timestamp': now_dt.isoformat(),
                'game_id': self.game_id,
                'heartbeat_id': heartbeat_id,
                'idle_duration_seconds': idle_duration,
                'trigger_reason': 'idle_threshold_met',
                'reviewed_sources': logs_metadata,
                'concatenated_input_text': logs_content,
                'reviewer_agent': 'v1_gamma_judge'
            }
            
            input_path = self.topology.heartbeat_inputs / f'{timestamp_sortable}.json'
            with open(input_path, 'w') as f:
                json.dump(input_artifact, f, indent=2)
            
            agent_id = 'v1_gamma_judge'
            agent = self.registry.get_agent(agent_id)
            if not agent:
                agent_id = 'v1_gamma_proponent'
                agent = self.registry.get_agent(agent_id)

            messages = [
                {"role": "system", "content": agent.system_prompt + "\n\nMANDATE: You MUST use code (programming) for log analysis and state verification. Do not perform token-to-token summaries."},
                {"role": "user", "content": f"IDLE-REVIEW HEARTBEAT PROTOCOL\nHeartbeat ID: {heartbeat_id}\nIdle Duration: {idle_duration:.1f}s\n\nRECENT LOGS:\n{logs_content}"}
            ]
            
            result: ToolLoopResult = await execute_tool_loop(
                self.scheduler, agent, messages, heartbeat_id, logger
            )
            
            # Update Heartbeat State
            self.heartbeat.update_agent(agent_id, {
                "input_chars": result.input_chars,
                "output_chars": result.output_chars,
                "usage_tokens": result.usage_tokens,
                "last_tool_name": result.last_tool_name,
                "is_idle_review": True
            })

            output_artifact = {
                'timestamp': datetime.now().isoformat(),
                'game_id': self.game_id,
                'heartbeat_id': heartbeat_id,
                'idle_duration_seconds': idle_duration,
                'input_ref': str(input_path.name),
                'summary': result.final_text,
                'metrics': {
                    "input_chars": result.input_chars,
                    "output_chars": result.output_chars,
                    "usage_tokens": result.usage_tokens
                },
                'confidence': 'observed/inferred'
            }
            
            output_path = self.topology.heartbeat_outputs / f'{timestamp_sortable}.json'
            with open(output_path, 'w') as f:
                json.dump(output_artifact, f, indent=2)
                
            md_path = self.topology.heartbeat_dir / f'heartbeat-{timestamp_sortable}.md'
            with open(md_path, 'w') as f:
                f.write(f'# TOOL-ENABLED HEARTBEAT: {heartbeat_id}\n\n{result.final_text}')
            
            logger.info(f'Heartbeat artifacts saved: {heartbeat_id}')
            self.last_idle_review_time = time.time()
            
        finally:
            self.is_running = False

    def _gather_recent_logs_with_metadata(self, max_chars: int) -> tuple[List[Dict], str]:
        subsystems = ['orchestrator', 'board', 'bridge', 'worker', 'errors']
        all_text = []
        metadata = []
        chars_per_log = max_chars // len(subsystems)
        
        for sub in subsystems:
            log_path = self.topology.get_log_path(sub)
            meta = {'subsystem': sub, 'path': str(log_path), 'status': 'missing'}
            if log_path.exists():
                with open(log_path, 'r') as f:
                    f.seek(0, 2)
                    size = f.tell()
                    start_pos = max(0, size - chars_per_log)
                    f.seek(start_pos)
                    content = f.read()
                    all_text.append(f'--- {sub}.log ---\n{content}')
                    meta.update({
                        'status': 'read',
                        'byte_range': [start_pos, size],
                        'chars_read': len(content)
                    })
            else:
                all_text.append(f'--- {sub}.log ---\n(File missing)')
            metadata.append(meta)
                
        return metadata, '\n\n'.join(all_text)

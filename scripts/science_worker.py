import os
import json
import time
import logging
import sys
import argparse
from pathlib import Path

# Add src to path
ROOT = Path('/Users/HN/MLLM/gamma')
sys.path.append(str(ROOT))
sys.path.append(str(ROOT / 'src'))

from gamma_runtime.bridge.scientific_adapter import run_v1_gamma_bridge_payload
from gamma_runtime.bridge.path_topology import GameLogTopology
from gamma_runtime.bridge.bridge_contract import STATUS_PENDING, STATUS_RUNNING, STATUS_COMPLETED, STATUS_ERROR, ScientificResult

def setup_worker_logging(topology):
    logger = logging.getLogger('ScienceWorker')
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(topology.get_log_path('worker'))
    fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(fh)
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(sh)
    return logger

def process_pending_proposals(topology, logger):
    if not topology.proposals_file.exists():
        return

    with open(topology.proposals_file, 'r') as f:
        lines = f.readlines()

    updated_lines = []
    changed = False
    for line in lines:
        try:
            data = json.loads(line)
            if data.get('status') == STATUS_PENDING:
                logger.info(f"Processing proposal: {data['proposal_id']}")
                data['status'] = STATUS_RUNNING
                data['worker_start_time'] = time.time()
                
                try:
                    result = run_v1_gamma_bridge_payload(data['payload'])
                    
                    # LOG SPECIFIC STABILITY CHECKS FOR DEBUGGING
                    if hasattr(result, 'rejection_reason') and result.rejection_reason == 'Stability gate failed':
                        logger.warning(f"Proposal {data['proposal_id']} rejected. Rejection: {result.rejection_reason}")

                    result_file = topology.results_dir / f"{data['proposal_id']}.json"
                    with open(result_file, 'w') as rf:
                        result_dict = result.__dict__
                        result_dict['worker_finish_time'] = time.time()
                        json.dump(result_dict, rf, indent=2, default=str)
                    
                    data['status'] = STATUS_COMPLETED
                    data['result_path'] = str(result_file)
                    data['worker_finish_time'] = time.time()
                    logger.info(f"Completed proposal: {data['proposal_id']} -> Status: {result.status}")
                except Exception as ex:
                    logger.error(f"Execution failed for {data['proposal_id']}: {ex}")
                    data['status'] = STATUS_ERROR
                    data['error'] = str(ex)
                
                changed = True
            
            updated_lines.append(json.dumps(data) + '\n')
        except Exception as e:
            logger.error(f"Error processing line: {e}")
            updated_lines.append(line)

    if changed:
        temp_file = topology.proposals_file.with_suffix('.tmp')
        with open(temp_file, 'w') as f:
            f.writelines(updated_lines)
        os.replace(temp_file, topology.proposals_file)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--game_id', default='game001')
    args = parser.parse_args()

    topology = GameLogTopology(ROOT, args.game_id)
    logger = setup_worker_logging(topology)

    logger.info(f"Science Worker started for {args.game_id}")
    while True:
        process_pending_proposals(topology, logger)
        time.sleep(5)

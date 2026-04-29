import logging
import importlib
import sys
import os
from .bridge_contract import ScientificResult, STATUS_ACCEPTED, STATUS_REJECTED, STATUS_ERROR

logger = logging.getLogger('ScientificAdapter')
JBIOPHYSIC_SRC = '/Users/HN/MLLM/jbiophysic/src'

def run_v1_gamma_bridge_payload(payload_dict: dict) -> ScientificResult:
    proposal_id = payload_dict.get('proposal_id', 'unknown')
    
    if JBIOPHYSIC_SRC not in sys.path:
        sys.path.append(JBIOPHYSIC_SRC)
        
    try:
        v1_mod = importlib.import_module('jbiophysic.models.pipelines.v1_gamma_sde_pipeline')
        raw_result = v1_mod.run_v1_gamma_bridge_payload(payload_dict)
        
        status = STATUS_ACCEPTED if raw_result['is_stable'] else STATUS_REJECTED
        rejection_reason = None if raw_result['is_stable'] else 'Stability gate failed'
        
        return ScientificResult(
            proposal_id=proposal_id,
            status=status,
            healthy=raw_result['results']['healthy'],
            schiz=raw_result['results']['schiz'],
            delta={},
            rejection_reason=rejection_reason,
            metadata=raw_result.get('metadata', {}),
            artifacts={'engine': 'jaxley-v0.13.0'}
        )
    except Exception as e:
        logger.error('Simulation dispatch error: %s', str(e))
        return ScientificResult(
            proposal_id=proposal_id,
            status=STATUS_ERROR,
            rejection_reason=f'Simulation error: {str(e)}'
        )

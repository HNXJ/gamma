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
        
        metadata = raw_result.get('metadata', {})
        h_stab = metadata.get('healthy_stability', {})
        
        # Populate mandatory metrics block
        metrics = {
            "firing_rate": h_stab.get('firing_rate'),
            "v_min": h_stab.get('v_min'),
            "v_max": h_stab.get('v_max'),
            "has_nan": not h_stab.get('checks', {}).get('nan_inf', True),
            "has_inf": not h_stab.get('checks', {}).get('nan_inf', True),
            "stability_score": 1.0 if raw_result['is_stable'] else 0.0
        }
        
        return ScientificResult(
            proposal_id=proposal_id,
            status=status,
            healthy=raw_result['results']['healthy'],
            schiz=raw_result['results']['schiz'],
            delta={},
            rejection_reason=rejection_reason,
            metadata=metadata,
            metrics=metrics,
            artifacts={'engine': 'jaxley-v0.13.0'}
        )
    except Exception as e:
        logger.error('Simulation dispatch error: %s', str(e))
        return ScientificResult(
            proposal_id=proposal_id,
            status=STATUS_ERROR,
            rejection_reason=f'Simulation error: {str(e)}',
            metrics={
                "firing_rate": None,
                "v_min": None,
                "v_max": None,
                "has_nan": False,
                "has_inf": False,
                "stability_score": 0.0
            }
        )

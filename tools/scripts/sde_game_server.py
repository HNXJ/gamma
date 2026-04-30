import os
import pdfplumber
import logging
import re
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Any

# Setup logger for the SDE_GameServer
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SDE_GameServer")

class PlayerAgent:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
    def query(self, prompt: str) -> str:
        # Mocking the query method
        return f"Critique of proposal by {self.agent_id}"

class SDE_GameServer:
    def __init__(self):
        self.documents = {}

    def triage_workspace(self, directory_path: str, chunk_size_chars: int = 25000):
        """
        Task 2: PDF Ingestion Pipeline.
        Iterates through the target directory, extracting text and chunking it 
        to protect the models' optimal context window.
        """
        logger.info(f"Initiating workspace triage in: {directory_path}")
        documents = {}
        
        for filename in os.listdir(directory_path):
            if filename.endswith(".pdf"):
                filepath = os.path.join(directory_path, filename)
                full_text = ""
                with pdfplumber.open(filepath) as pdf:
                    for page in pdf.pages:
                        extracted = page.extract_text()
                        if extracted:
                            full_text += extracted + "\n"
                
                # Simple chunking with a 10% overlap to preserve context across boundaries
                overlap = int(chunk_size_chars * 0.1)
                chunks = []
                for i in range(0, len(full_text), chunk_size_chars - overlap):
                    chunks.append(full_text[i:i + chunk_size_chars])
                
                documents[filename] = chunks
                logger.debug(f"Triaged {filename} into {len(chunks)} chunks.")
        
        self.documents = documents
        return documents

    def evaluate_turn(self, proposal: str, proponent: PlayerAgent, adversary: PlayerAgent):
        """
        Task 3: The Adversarial Peer Review Loop.
        Routes the proponent's hypothesis to the adversary with a ruthless constraint.
        """
        logger.info(f"Routing proposal from {proponent.agent_id} to {adversary.agent_id} for peer review.")
        
        adversarial_prompt = (
            "SYSTEM DIRECTIVE: Act as a highly critical, adversarial peer reviewer. "
            "Your objective is to tear down the assumptions in the following proposed methodology. "
            "Find the logical leaps, expose where the math or physics fails, and explicitly deny "
            "any claims not supported by empirical evidence. Be ruthless and precise.\n\n"
            f"PROPOSAL TO ATTACK:\n{proposal}"
        )
        
        # Query the adversary endpoint
        critique = adversary.query(prompt=adversarial_prompt)
        
        # Log the interaction for the trace
        interaction_trace = {
            "proponent_id": proponent.agent_id,
            "proposal": proposal,
            "adversary_id": adversary.agent_id,
            "critique": critique
        }
        
        return interaction_trace

    def execute_win_state(self, winning_trace: Dict[str, Any]):
        """
        Task 5: Federated Aggregation.
        Packages the optimized, DOI-verified trace to staging/ for the FedLoRA pipeline.
        """
        staging_dir = "staging/fedlora_payloads"
        os.makedirs(staging_dir, exist_ok=True)
        
        # Generate a unique hash for the proposal to prevent duplicate training data
        proposal_text = winning_trace.get("proposal", "")
        trace_hash = hashlib.sha256(proposal_text.encode('utf-8')).hexdigest()[:12]
        
        # Structure the payload for the MLX fine-tuning loop
        payload = {
            "timestamp": datetime.utcnow().isoformat(),
            "trace_hash": trace_hash,
            "loss_achieved": winning_trace.get("final_loss", 0.0),
            "epistemic_gain_x": winning_trace.get("x", 0.0),
            "methodological_rigor_y": winning_trace.get("y", 0.0),
            "ground_truth_z": winning_trace.get("z", 0.0),
            "algorithmic_coherence_w": winning_trace.get("w", 0.0),
            "interaction_history": winning_trace.get("interaction_history", [])
        }
        
        file_path = os.path.join(staging_dir, f"trace_{trace_hash}.json")
        with open(file_path, 'w') as f:
            json.dump(payload, f, indent=2)
            
        logger.info(f"🏆 Equilibrium reached. Trace {trace_hash} staged for FedLoRA.")
        return file_path

class LiteratureDiscoveryPolicy:
    def evaluate_y(self, trace: Dict[str, Any]) -> float:
        """
        Task 4: DOI Grounding Request.
        Scans the proposed hypothesis for valid DOI strings. Penalizes the 
        Methodological Rigor (y) score heavily if claims lack verifiable grounding.
        """
        # Standard DOI Regex pattern (Crossref / DataCite compliant)
        doi_pattern = re.compile(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+")
        
        proposal = trace.get("proposal", "")
        
        # Simple proxy for claims: paragraphs or distinct bullet points
        claims_count = max(1, len(proposal.split('\n\n'))) 
        
        found_dois = doi_pattern.findall(proposal)
        unique_dois = set(found_dois)
        
        if not unique_dois:
            logger.warning(f"Agent {trace.get('proponent_id', 'Unknown')} provided zero valid DOIs. Slashing rigor.")
            return -1.0
        
        # Rigor scales with the ratio of unique DOIs to claims, capped at 1.0
        rigor_score = min(1.0, len(unique_dois) / claims_count)
        
        logger.debug(f"Validated {len(unique_dois)} DOIs. Rigor score: {rigor_score}")
        return rigor_score

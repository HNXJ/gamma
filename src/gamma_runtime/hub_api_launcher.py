import os
import sys
import logging

# Anchor to project root for module imports
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(ROOT)
sys.path.append(os.path.join(ROOT, "src"))

from src.gamma_runtime.hub_api import HubAPIServer
from src.gamma_runtime.config import HUB_PORT

# Mock orchestrator for a "Minimal Hub" if the main orchestrator is down
class MockOrchestrator:
    def get_all_sessions(self):
        return []
    def get_session_state(self, sid):
        return None

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("HubLauncher")
    
    logger.info(f"Starting Hub API on port {HUB_PORT}...")
    
    # In a real setup, this would eventually connect to the active orchestrator worker.
    # For now, it provides the endpoint for events and heartbeat pulse.
    mock = MockOrchestrator()
    server = HubAPIServer(mock, port=HUB_PORT)
    server.start()
    
    import time
    while True:
        time.sleep(3600)

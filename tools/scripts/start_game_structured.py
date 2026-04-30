import os
import sys
import json
import asyncio
import logging
import socket
from urllib.parse import urlparse
from datetime import datetime

# Anchor to project root for module imports
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(ROOT)
sys.path.append(os.path.join(ROOT, "src"))

# Setup Logging
os.makedirs(os.path.join(ROOT, "local"), exist_ok=True)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GammaStarter")

def emit_failure(reason: str, details: str):
    failure = {
        "event_type": "preflight_failure",
        "timestamp": datetime.now().isoformat(),
        "failure_reason": reason,
        "details": details
    }
    print(json.dumps(failure))
    sys.exit(1)

def run_preflight_checks():
    logger.info("Running preflight checks...")
    
    # 1. Check interpreter (Only enforce if .venv exists in ROOT)
    venv_path = os.path.join(ROOT, ".venv")
    if os.path.exists(venv_path) and not sys.executable.startswith(venv_path):
        emit_failure("wrong_interpreter", f"Expected inside {venv_path}, got {sys.executable}")
        
    # 2. Check required imports
    try:
        import pydantic
        import httpx
    except ImportError as e:
        emit_failure("missing_dependency", str(e))

    from src.gamma_runtime.config import get_lms_url
    
    # 3. Check LMS Port Reachability
    lms_url = get_lms_url()
    try:
        parsed = urlparse(lms_url)
        host = parsed.hostname
        port = parsed.port
        with socket.create_connection((host, port), timeout=3):
            pass
    except Exception as e:
        emit_failure("lms_unreachable", f"LMS Model server not reachable at {lms_url}. Error: {e}")

    # 4. Check inventory directories
    agents = ["G01", "G02", "G03", "J01", "M01"]
    for agent in agents:
        agent_dir = os.path.join(ROOT, f"local/inventory/{agent}")
        if not os.path.exists(agent_dir):
            os.makedirs(agent_dir, exist_ok=True)
            
    logger.info("✅ Preflight checks passed.")

async def main():
    logger.info("🚀 Starting Gamma Structured Runtime...")
    run_preflight_checks()
    
    from src.gamma_runtime.scheduler import InferenceScheduler
    from src.gamma_runtime.registry import RuntimeRegistry
    from src.gamma_runtime.orchestrator import UnifiedOrchestrator
    from src.gamma_runtime.hub_api import HubAPIServer
    from src.gamma_runtime.events import EventEmitter
    from src.gamma_runtime.config import HUB_PORT
    from src.gamma_runtime.tool_harness import ToolRouter, ContextHydrator
    
    # 1. Initialize Registry and Scheduler
    registry = RuntimeRegistry(os.path.join(ROOT, "context/configs"))
    scheduler = InferenceScheduler()
    
    # 2. Initialize Tool Harness (Context + Tooling)
    hydrator = ContextHydrator(ROOT)
    routers = {}
    agents = ["G01", "G02", "G03", "J01", "M01"]
    for agent_id in agents:
        # Strict Player Sandbox Mapping
        sandbox_path = os.path.join(ROOT, f"local/inventory/{agent_id}")
        routers[agent_id] = ToolRouter(agent_id, sandbox_path)
    
    # 3. Initialize Event Emitter
    events_path = os.path.join(ROOT, "local/events.jsonl")
    emitter = EventEmitter(events_path)
    
    # 4. Initialize Orchestrator with Tool Harness
    orchestrator = UnifiedOrchestrator(
        scheduler, 
        registry, 
        emitter=emitter,
        tool_routers=routers,
        context_hydrator=hydrator
    )
    
    # 5. Initialize Hub API Server
    hub_server = HubAPIServer(orchestrator, port=HUB_PORT)
    hub_server.start()
    
    # 6. Launch a real task to prove orchestration and tool harness are active
    logger.info("Triggering real orchestrator run...")
    await orchestrator.launch_run(
        run_type="council",
        topic="Initial Substrate Review: 11 Neurons Target",
        team_id="gamma_structured_team",
        rounds=1,
        auto_consolidate=False
    )
    
    logger.info("✅ Gamma Game is now RUNNING with Tool Harness active.")
    logger.info(f"Hub API: http://localhost:{HUB_PORT}")
    
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutdown requested.")

import asyncio
import json
import http.client
import time
from pathlib import Path
from gamma_runtime.orchestrator import UnifiedOrchestrator
from gamma_runtime.scheduler import InferenceScheduler
from gamma_runtime.registry import RuntimeRegistry
from gamma_runtime.hub_api import HubAPIServer

async def main():
    print("🚀 Initializing Hub API Smoke Test...")
    
    # Setup Runtime Components
    scheduler = InferenceScheduler()
    registry = RuntimeRegistry(str(Path(__file__).parent.parent.parent / "configs"))
    orchestrator = UnifiedOrchestrator(scheduler, registry)
    
    # Start API Server
    server = HubAPIServer(orchestrator, port=8002)
    server.start()
    
    # Give the server a moment to boot
    time.sleep(1)
    
    # Test POST /api/launch
    print("Testing /api/launch...")
    conn = http.client.HTTPConnection("127.0.0.1", 8002)
    payload = json.dumps({
        "type": "council",
        "topic": "The stability of JAX-based biophysical solvers.",
        "rounds": 1
    })
    conn.request("POST", "/api/launch", body=payload, headers={"Content-Type": "application/json"})
    response = conn.getresponse()
    data = json.loads(response.read().decode())
    session_id = data.get("session_id")
    
    print(f"Response: {response.status}, Session ID: {session_id}")
    assert response.status == 201
    assert "session-" in session_id

    # Test GET /api/session/<id>
    print(f"Testing /api/session/{session_id}...")
    conn.request("GET", f"/api/session/{session_id}")
    response = conn.getresponse()
    data = json.loads(response.read().decode())
    
    print(f"Response: {response.status}, Topic: {data.get('topic')}")
    assert response.status == 200
    assert data.get("topic") == "The stability of JAX-based biophysical solvers."
    
    print("\nHub API Verification: SUCCESS")
    # server.shutdown() # socketserver.TCPServer doesn't have shutdown() easily reachable here but it's a daemon thread

if __name__ == "__main__":
    asyncio.run(main())

import pytest
import time
import json
from unittest.mock import MagicMock
from src.gamma_runtime.hub_api import HubAPIHandler
from io import BytesIO

class MockRequest:
    def __init__(self, path):
        self.path = path
        self.rfile = BytesIO()
        self.wfile = BytesIO()
        self.makefile = lambda mode, bufsize: self.rfile

def test_status_no_orchestrator():
    request = MockRequest("/api/status")
    # Initialize without socketserver overhead
    handler = HubAPIHandler.__new__(HubAPIHandler)
    handler.request = request
    handler.client_address = ("127.0.0.1", 8000)
    handler.server = MagicMock()
    handler.orchestrator = None
    
    # Initialize attributes expected by do_GET
    handler.path = request.path
    
    # Mock _set_headers
    handler._set_headers = MagicMock()
    handler.wfile = request.wfile
    
    handler.do_GET()
    
    response = json.loads(handler.wfile.getvalue().decode())
    assert response["source"] == "mock_fallback"
    assert response["freshness"] == "fallback"
    assert response["truth_mode"] == "truth_safe_unverified"
    assert response["truth_bearing_run"] is False
    assert response["system"]["backend_status"] == "unavailable"

def test_status_orchestrator_live():
    request = MockRequest("/api/status")
    handler = HubAPIHandler.__new__(HubAPIHandler)
    handler.request = request
    handler.client_address = ("127.0.0.1", 8000)
    handler.server = MagicMock()
    
    # Initialize attributes expected by do_GET
    handler.path = request.path
    
    now = time.time()
    mock_orchestrator = MagicMock()
    mock_orchestrator.get_all_sessions.return_value = [
        {"id": "ses1", "topic": "test", "round": 1, "last_active": time.ctime(now)}
    ]
    handler.orchestrator = mock_orchestrator
    handler._set_headers = MagicMock()
    handler.wfile = request.wfile
    
    handler.do_GET()
    
    response = json.loads(handler.wfile.getvalue().decode())
    assert response["source"] == "orchestrator_state"
    assert response["freshness"] == "live"
    assert len(response["players"]) == 1
    assert response["players"][0]["id"] == "ses1"
    assert response["players"][0]["liveness"] == "active"

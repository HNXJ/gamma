import json
import http.server
import socketserver
import logging
import asyncio
import os
import time
from typing import Optional
from urllib.parse import urlparse, parse_qs
from .orchestrator import UnifiedOrchestrator
from .player_identity import PlayerIdentityManager
from .content_service import ContentService
from .content_admin import ContentAuthorizationError

logger = logging.getLogger("HubAPI")

class HubAPIHandler(http.server.BaseHTTPRequestHandler):
    """
    Standard Library implementation of the Gamma Hub API.
    Provides zero-dependency REST endpoints for the Dashboard.
    """
    orchestrator: Optional[UnifiedOrchestrator] = None
    identity_manager: Optional[PlayerIdentityManager] = None
    content_service: Optional[ContentService] = None

    def _set_headers(self, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*') # Enable CORS for the local dashboard
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers()

    def _get_authenticated_account(self) -> Optional[dict]:
        auth_header = self.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
        session_id = auth_header.split(' ')[1]
        
        sessions = self.identity_manager._load_json(self.identity_manager.sessions_path / "active.json")
        session = sessions.get(session_id)
        if not session or not session.get('active'):
            return None
        
        account_id = session.get('account_id')
        accounts = self.identity_manager._load_json(self.identity_manager.accounts_path / "registry.json")
        for acc in accounts.values():
            if acc['account_id'] == account_id:
                return acc
        return None

    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query = parse_qs(parsed_path.query)
        
        if path.startswith("/api/session/"):
            session_id = path.split("/")[-1]
            state = self.orchestrator.get_session_state(session_id)
            if state:
                self._set_headers()
                self.wfile.write(json.dumps(state).encode())
            else:
                self._set_headers(404)
                self.wfile.write(json.dumps({"error": "Session not found"}).encode())
        elif path == "/api/status":
            # Returns the runtime state for internal bridge consumption
            state = {
                "system": {
                    "id": "GAMMA-M3MAX-01",
                    "status": "RUNNING",
                    "heartbeat": time.time()
                },
                "sessions": self.orchestrator.get_all_sessions() if self.orchestrator else []
            }
            self._set_headers()
            self.wfile.write(json.dumps(state).encode())
        elif path == "/api/events":
            # Safely appended: return structured events for front
            log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "local/events.jsonl")
            events = []
            if os.path.exists(log_path):
                with open(log_path, "r") as f:
                    for line in f:
                        if line.strip():
                            try:
                                events.append(json.loads(line))
                            except: pass
            self._set_headers()
            self.wfile.write(json.dumps(events[-100:]).encode()) # Return last 100 events
        elif path == "/api/content/list":
            surface = query.get("surface", ["blog"])[0]
            pages = self.content_service.list_pages(surface)
            self._set_headers()
            self.wfile.write(json.dumps({"surface": surface, "pages": pages}).encode())
        elif path == "/api/content/read":
            surface = query.get("surface", ["blog"])[0]
            page_id = query.get("page_id", [""])[0]
            content = self.content_service.read_page(surface, page_id)
            if content is not None:
                self._set_headers()
                self.wfile.write(json.dumps({"surface": surface, "page_id": page_id, "content": content}).encode())
            else:
                self._set_headers(404)
                self.wfile.write(json.dumps({"error": "Page not found"}).encode())
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode())

    def do_POST(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        params = json.loads(post_data)

        if path == "/api/launch":
            account = self._get_authenticated_account()
            if not account:
                self._set_headers(401)
                return
            
            from .content_admin import can_control_runtime
            if not can_control_runtime(account):
                self._set_headers(403)
                self.wfile.write(json.dumps({"error": "Account lacks world_operator privileges."}).encode())
                return

            # Use a wrapper to run the async launch in the current event loop
            # Note: This requires the server to be running in an async context or thread
            session_id = self._launch_sync(params)
            self._set_headers(201)
            self.wfile.write(json.dumps({"session_id": session_id}).encode())
        elif path == "/api/auth/login":
            username = params.get("username")
            password = params.get("password")
            account = self.identity_manager.sign_in(username, password)
            if account:
                # We need a binding for session creation, but for content-admin we can skip or use dummy
                session = self.identity_manager.create_session(account['account_id'], "internal")
                self._set_headers()
                self.wfile.write(json.dumps({
                    "session_id": session['session_id'],
                    "account_id": account['account_id'],
                    "username": account['username'],
                    "display_name": account['display_name'],
                    "roles": account.get('roles', [])
                }).encode())
            else:
                self._set_headers(401)
                self.wfile.write(json.dumps({"error": "Invalid credentials"}).encode())
        elif path == "/api/content/write":
            account = self._get_authenticated_account()
            if not account:
                self._set_headers(401)
                return
            
            try:
                self.content_service.write_page(
                    account=account,
                    surface=params.get("surface"),
                    page_id=params.get("page_id"),
                    content=params.get("content"),
                    metadata=params.get("metadata")
                )
                self._set_headers()
                self.wfile.write(json.dumps({"status": "success"}).encode())
            except ContentAuthorizationError as e:
                self._set_headers(403)
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        elif path == "/api/content/publish":
            account = self._get_authenticated_account()
            if not account:
                self._set_headers(401)
                return
            
            try:
                self.content_service.publish_page(
                    account=account,
                    surface=params.get("surface"),
                    page_id=params.get("page_id"),
                    metadata=params.get("metadata")
                )
                self._set_headers()
                self.wfile.write(json.dumps({"status": "success"}).encode())
            except ContentAuthorizationError as e:
                self._set_headers(403)
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        else:
            self._set_headers(404)

    def _launch_sync(self, params):
        if not self.orchestrator:
            return "mock-session-id"
        # This is a bit tricky with http.server. 
        # In a real async server (FastAPI), this would be clean.
        # Here we assume the orchestrator has an async loop running.
        loop = asyncio.get_event_loop()
        future = asyncio.run_coroutine_threadsafe(
            self.orchestrator.launch_run(
                run_type=params.get("type", "council"),
                topic=params.get("topic", "General Inquiry"),
                **params
            ),
            loop
        )
        return future.result()

class HubAPIServer:
    def __init__(self, orchestrator: Optional[UnifiedOrchestrator], port: int = None):
        if port is None:
            from .config import HUB_PORT
            port = HUB_PORT
        self.orchestrator = orchestrator
        self.port = port
        self.identity_manager = PlayerIdentityManager()
        self.content_service = ContentService()
        
        HubAPIHandler.orchestrator = orchestrator
        HubAPIHandler.identity_manager = self.identity_manager
        HubAPIHandler.content_service = self.content_service

    def start(self):
        # We run the TCPServer in a separate thread to not block the main loop
        import threading
        # Try to bind to localhost, which is usually permitted even in restricted environments
        try:
            server = socketserver.TCPServer(("localhost", self.port), HubAPIHandler)
        except Exception:
            # Fallback to 127.0.0.1 if localhost fails
            server = socketserver.TCPServer(("127.0.0.1", self.port), HubAPIHandler)
        
        thread = threading.Thread(target=server.serve_forever)
        thread.daemon = True
        thread.start()
        logger.info(f"Hub API listening on http://localhost:{self.port}")
        return server

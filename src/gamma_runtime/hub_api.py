import json
import http.server
import socketserver
import logging
import asyncio
import os
import subprocess
import time
from typing import Optional, Dict, Any
from urllib.parse import urlparse, parse_qs
from pathlib import Path
from .orchestrator import UnifiedOrchestrator
from .bridge.path_topology import GameLogTopology

logger = logging.getLogger('HubAPI')

class HubAPIHandler(http.server.BaseHTTPRequestHandler):
    orchestrator: Optional[UnifiedOrchestrator] = None
    root_dir = Path('/Users/HN/MLLM/gamma')

    def _set_headers(self, status=200, content_type='application/json'):
        self.send_response(status)
        self.send_header('Content-type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers()

    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path == '/':
            self._serve_file(self.root_dir / 'dashboard/templates/index.html', 'text/html')
        elif path.startswith('/api/session/'):
            session_id = path.split('/')[-1]
            state = self.orchestrator.get_session_state(session_id)
            if state:
                self._set_headers()
                self.wfile.write(json.dumps(state).encode())
            else:
                self._set_headers(404)
        elif path.startswith('/api/logs/'):
            parts = path.split('/')
            if len(parts) >= 5:
                game_id = parts[3]
                subsystem = parts[4]
                self._serve_log(game_id, subsystem)
            else:
                self._set_headers(400)
        elif path.startswith('/api/proposals/'):
            game_id = path.split('/')[-1]
            self._serve_proposals(game_id)
        elif path.startswith('/api/status/'):
            game_id = path.split('/')[-1]
            self._serve_scientific_status(game_id)
        elif path.startswith('/api/heartbeat/'):
            game_id = path.split('/')[-1]
            self._serve_heartbeat_status(game_id)
        elif path.startswith('/api/notes/heartbeat/'):
            game_id = path.split('/')[-1]
            self._serve_heartbeat_notes(game_id)
        elif path == '/api/terminal/lms':
            self._serve_lms_status()
        else:
            self._set_headers(404)

    def _serve_file(self, file_path, content_type):
        if file_path.exists():
            self._set_headers(200, content_type)
            with open(file_path, 'rb') as f:
                self.wfile.write(f.read())
        else:
            self._set_headers(404)

    def _serve_log(self, game_id, subsystem):
        topology = GameLogTopology(self.root_dir, game_id)
        log_path = topology.get_log_path(subsystem)
        if log_path.exists():
            self._set_headers(200, 'text/plain')
            with open(log_path, 'r') as f:
                lines = f.readlines()
                self.wfile.write(''.join(lines[-200:]).encode())
        else:
            self._set_headers(404)

    def _serve_proposals(self, game_id):
        topology = GameLogTopology(self.root_dir, game_id)
        if topology.proposals_file.exists():
            self._set_headers(200)
            with open(topology.proposals_file, 'r') as f:
                self.wfile.write(f.read().encode())
        else:
            self._set_headers(404)

    def _serve_scientific_status(self, game_id):
        topology = GameLogTopology(self.root_dir, game_id)
        results = []
        if topology.results_dir.exists():
            for f in topology.results_dir.glob('*.json'):
                with open(f, 'r') as rf:
                    try:
                        res = json.load(rf)
                        if res.get('status') == 'accepted':
                            results.append(res)
                    except: continue
        
        session_state = self.orchestrator.get_session_state(game_id)
        system_status = session_state.get('system_status', 'UNKNOWN') if session_state else 'UNKNOWN'
        idle_duration = session_state.get('idle_duration', 0) if session_state else 0

        status = {
            'game_id': game_id,
            'system_status': system_status,
            'idle_duration': idle_duration,
            'scientific_execution_evidenced': len(results) > 0,
            'results_count': len(results),
            'latest_results': results[-5:] if results else []
        }
        self._set_headers()
        self.wfile.write(json.dumps(status).encode())

    def _serve_heartbeat_status(self, game_id):
        # 1. Get stats from HeartbeatManager (Source of Truth)
        hb_state = self.orchestrator.heartbeat.get_state()
        
        # 2. Check if council is currently in memory
        session = self.orchestrator._active_sessions.get(game_id)
        
        # 3. Skills count
        skills_path = self.root_dir / 'skills/SKILLS.md'
        skills_count = 0
        if skills_path.exists():
            with open(skills_path, 'r') as f:
                skills_text = f.read()
                skills_count = skills_text.count('### ')

        status = {
            'game_id': game_id,
            'council_alive': session is not None,
            'skills_count': skills_count,
            'agents': hb_state.get('agents', {}),
            'last_real_task_time': hb_state.get('last_real_task_time', 0)
        }
        self._set_headers()
        self.wfile.write(json.dumps(status).encode())

    def _serve_heartbeat_notes(self, game_id):
        topology = GameLogTopology(self.root_dir, game_id)
        notes = []
        if topology.heartbeat_outputs.exists():
            for f in sorted(topology.heartbeat_outputs.glob('*.json'), reverse=True):
                with open(f, 'r') as nf:
                    try:
                        note_data = json.load(nf)
                        md_file = topology.heartbeat_dir / f'heartbeat-{f.stem}.md'
                        if md_file.exists():
                            with open(md_file, 'r') as mf:
                                note_data['content'] = mf.read()
                        else:
                            note_data['content'] = note_data.get('summary', 'No summary available.')
                        notes.append(note_data)
                    except: continue
        self._set_headers()
        self.wfile.write(json.dumps(notes).encode())

    def _serve_lms_status(self):
        try:
            res = subprocess.run(['/Users/HN/.lmstudio/bin/lms', 'ps'], capture_output=True, text=True)
            self._set_headers(200, 'text/plain')
            self.wfile.write(res.stdout.encode())
        except Exception as e:
            self._set_headers(500)
            self.wfile.write(str(e).encode())

class HubAPIServer:
    def __init__(self, orchestrator: UnifiedOrchestrator, port: int = 8001):
        self.orchestrator = orchestrator
        self.port = port
        HubAPIHandler.orchestrator = orchestrator

    def start(self):
        import threading
        socketserver.TCPServer.allow_reuse_address = True
        server = socketserver.TCPServer(('0.0.0.0', self.port), HubAPIHandler)
        thread = threading.Thread(target=server.serve_forever)
        thread.daemon = True
        thread.start()
        logger.info(f'Hub API listening on http://0.0.0.0:{self.port}')
        return server

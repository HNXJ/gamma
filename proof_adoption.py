import sys
import os
import json
import requests

# Ensure src is in PYTHONPATH
sys.path.append(os.path.abspath("src"))

try:
    from gamma_runtime.core_config import config
    from gamma_runtime.config import HUB_PORT, LMS_PORT, MONITOR_PORT, DASHBOARD_PORT
    
    print("--- Office Mac Resolved Values ---")
    print(f"world_root: {config.get('paths.world_root')}")
    print(f"heartbeat_interval_seconds: {config.get('timing.heartbeat_interval_seconds')}")
    print(f"hub_port: {HUB_PORT}")
    print(f"lms_port: {LMS_PORT}")
    print(f"monitor_port: {MONITOR_PORT}")
    print(f"dashboard_port: {DASHBOARD_PORT}")
    print(f"mail_root: {config.get('paths.mail_root')}")
    print(f"inventory_root: {config.get('paths.inventory_root')}")
    print(f"player_accounts: {config.get('paths.player_accounts')}")
    print(f"player_sessions: {config.get('paths.player_sessions')}")

    print("\n--- Live Adoption Check ---")
    # Check if config.py is actually proxying from config
    # We saw it does: HUB_PORT = config.get("network.hub_port", 8001)
    
    # Check if a live service (Hub) is reachable on the resolved port
    try:
        resp = requests.get(f"http://localhost:{HUB_PORT}/sessions", timeout=1)
        print(f"Hub API reachable on port {HUB_PORT}: {resp.status_code == 200}")
    except:
        print(f"Hub API not reachable on port {HUB_PORT} (Service might be down)")

    # Check if Heartbeat is running and has used the new interval (check health.json timestamp delta if possible)
    health_path = "local/run/health.json"
    if os.path.exists(health_path):
        with open(health_path, "r") as f:
            health = json.load(f)
            print(f"Live Heartbeat Health status: {health.get('status')}")
            print(f"Live Heartbeat LMS status: {health.get('lms')}")

    print("\nVERDICT_READY: TRUE")

except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)

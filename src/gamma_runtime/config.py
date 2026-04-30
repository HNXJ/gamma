import os
import socket
from enum import Enum

class LMSConnectivityMode(Enum):
    UNAVAILABLE = "UNAVAILABLE"
    TUNNELED = "TUNNELED"
    LOCAL = "LOCAL"
    PUBLIC = "PUBLIC"

# Role-Aware Service Discovery Surface Definitions
# -----------------------------------------------
# BIND_HOST: Internal network bind interface.
# LOCAL_URL: Surface for co-located workers and infrastructure (e.g., via tunnel).
# PUBLIC_URL: Surface for remote players, dashboard users, and external observers.

PUBLIC_HOST = os.environ.get("OFFICE_MAC_PUBLIC_IP", "100.69.184.42")

# 1. LMS Inference Server
LMS_PORT = int(os.environ.get("LMS_PORT", 1234))
LMS_BIND_HOST = "0.0.0.0"

def get_lms_local_url() -> str: return f"http://localhost:{LMS_PORT}"
def get_lms_public_url() -> str: return f"http://{PUBLIC_HOST}:{LMS_PORT}"

def detect_lms_connectivity_mode() -> LMSConnectivityMode:
    # 1. Check if public surface is reachable
    try:
        with socket.create_connection((PUBLIC_HOST, LMS_PORT), timeout=1):
            return LMSConnectivityMode.PUBLIC
    except:
        pass
        
    # 2. Check if localhost is reachable
    try:
        with socket.create_connection(("localhost", LMS_PORT), timeout=1):
            # To distinguish LOCAL vs TUNNELED, we'd need to know if we are on the Office Mac.
            # For now, if we are on the M1 Max and see localhost:1234, it's likely a tunnel.
            # If we are on the Office Mac, it's LOCAL.
            # Simplified heuristic:
            hostname = socket.gethostname()
            if "MacBook-Pro" in hostname or "100.69.184.42" in hostname:
                return LMSConnectivityMode.LOCAL
            return LMSConnectivityMode.TUNNELED
    except:
        pass
        
    return LMSConnectivityMode.UNAVAILABLE

# 2. Hub API (Orchestrator/Events)
HUB_PORT = int(os.environ.get("HUB_PORT", 8001))
HUB_BIND_HOST = "0.0.0.0"
def get_hub_local_url() -> str: return f"http://localhost:{HUB_PORT}"
def get_hub_public_url() -> str: return f"http://{PUBLIC_HOST}:{HUB_PORT}"

# 3. Dashboard UI
DASHBOARD_PORT = int(os.environ.get("DASHBOARD_PORT", 3012))
DASHBOARD_BIND_HOST = "0.0.0.0"
def get_dashboard_local_url() -> str: return f"http://localhost:{DASHBOARD_PORT}"
def get_dashboard_public_url() -> str: return f"http://{PUBLIC_HOST}:{DASHBOARD_PORT}"

# Backward Compatibility (Deprecate immediately in favor of LOCAL/PUBLIC)
def get_lms_url() -> str: return get_lms_local_url()
def get_hub_url() -> str: return get_hub_local_url()

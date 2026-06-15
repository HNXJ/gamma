# PILLAR : WARNING
# CRITICAL: DEFINES SERVICE SURFACES
# DO NOT ADD ARBITRARY PORTS. 
# VALIDATE ALL ADDITIONS AGAINST CANONICAL CONFIG.

import os
import socket
from enum import Enum
from .core_config import config

# Role-Aware Service Discovery Surface Definitions
# -----------------------------------------------

# 1. Environment and Identity
PUBLIC_HOST = os.environ.get("OFFICE_MAC_PUBLIC_IP", "100.69.184.42")
DEVELOPER_GUEST_MODE = config.get("features.developer_guest_mode", False)

# 2. LMS Inference Server
LMS_PORT = config.get("network.lms_port", 1234)
LMS_BIND_HOST = config.get("network.bind_host", "0.0.0.0")

def get_lms_local_url() -> str: return f"http://localhost:{LMS_PORT}"
def get_lms_public_url() -> str: return f"http://{PUBLIC_HOST}:{LMS_PORT}"

class LMSConnectivityMode(Enum):
    UNAVAILABLE = "UNAVAILABLE"
    TUNNELED = "TUNNELED"
    LOCAL = "LOCAL"
    PUBLIC = "PUBLIC"

def detect_lms_connectivity_mode() -> LMSConnectivityMode:
    # 1. Check if public surface is reachable
    try:
        with socket.create_connection((PUBLIC_HOST, LMS_PORT), timeout=1):
            return LMSConnectivityMode.PUBLIC
    except:
        pass
        
    # 2. Check if localhost is reachable
    try:
        with socket.create_connection(("localhost", LMS_PORT), timeout=1) as s:
            hostname = socket.gethostname()
            is_office_mac = "100.69.184.42" in hostname or "HN" in hostname
            
            if is_office_mac:
                return LMSConnectivityMode.LOCAL
            else:
                return LMSConnectivityMode.TUNNELED
    except:
        pass
        
    return LMSConnectivityMode.UNAVAILABLE

# 3. Hub API (Orchestrator/Events - Internal Bridge)
HUB_PORT = config.get("network.hub_port", 8001)
HUB_BIND_HOST = config.get("network.bind_host", "0.0.0.0")
def get_hub_local_url() -> str: return f"http://localhost:{HUB_PORT}"
def get_hub_public_url() -> str: return f"http://{PUBLIC_HOST}:{HUB_PORT}"

# 4. Monitor API (Canonical External API)
MONITOR_PORT = config.get("network.monitor_port", 3013)
def get_monitor_local_url() -> str: return f"http://localhost:{MONITOR_PORT}"

# 5. Dashboard UI
DASHBOARD_PORT = config.get("network.ui_port", 3012)
DASHBOARD_BIND_HOST = config.get("network.bind_host", "0.0.0.0")
def get_dashboard_local_url() -> str: return f"http://localhost:{DASHBOARD_PORT}"
def get_dashboard_public_url() -> str: return f"http://{PUBLIC_HOST}:{DASHBOARD_PORT}"

# 6. Supabase Observer Infrastructure (Truth Plane Writer)
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://pedkrfxnicxdsacflvbj.supabase.co")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

def get_supabase_config() -> dict:
    if not SUPABASE_SERVICE_KEY:
        return {}
    return {
        "url": SUPABASE_URL,
        "headers": {
            "apikey": SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }
    }

# Backward Compatibility (Deprecate immediately in favor of LOCAL/PUBLIC)
def get_lms_url() -> str: return get_lms_local_url()
def get_hub_url() -> str: return get_hub_local_url()

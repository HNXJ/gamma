# PILLAR : WARNING
# CRITICAL: DEFINES SERVICE SURFACES
# DO NOT ADD ARBITRARY PORTS. 
# VALIDATE ALL ADDITIONS AGAINST CANONICAL CONFIG.

import os
import socket
from enum import Enum

# ANTI-REGRESSION VALIDATION
ALLOWED_PORTS = {1234, 3012, 3013}

def _validate_port(port: int, name: str):
    if port not in ALLOWED_PORTS:
        raise ValueError(f"CRITICAL PORT ERROR: {name} attempted to use non-canonical port {port}. Allowed: {ALLOWED_PORTS}")

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
_validate_port(LMS_PORT, "LMS")
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

# 2. Hub API (Orchestrator/Events)
HUB_PORT = int(os.environ.get("HUB_PORT", 3013))
_validate_port(HUB_PORT, "HUB")
HUB_BIND_HOST = "0.0.0.0"
def get_hub_local_url() -> str: return f"http://localhost:{HUB_PORT}"
def get_hub_public_url() -> str: return f"http://{PUBLIC_HOST}:{HUB_PORT}"

# 3. Dashboard UI
DASHBOARD_PORT = int(os.environ.get("DASHBOARD_PORT", 3012))
_validate_port(DASHBOARD_PORT, "DASHBOARD")
DASHBOARD_BIND_HOST = "0.0.0.0"
def get_dashboard_local_url() -> str: return f"http://localhost:{DASHBOARD_PORT}"
def get_dashboard_public_url() -> str: return f"http://{PUBLIC_HOST}:{DASHBOARD_PORT}"

# Backward Compatibility (Deprecate immediately in favor of LOCAL/PUBLIC)
def get_lms_url() -> str: return get_lms_local_url()
def get_hub_url() -> str: return get_hub_local_url()

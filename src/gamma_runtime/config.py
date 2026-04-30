import os

# Centralized Role-Aware Service Discovery for Gamma Arena
# Separation of surfaces: BIND (internal), LOCAL (infra), PUBLIC (world)

OFFICE_MAC_PUBLIC_IP = os.environ.get("OFFICE_MAC_PUBLIC_IP", "100.69.184.42")

# 1. Inference Server (LMS/Model)
LMS_PORT = int(os.environ.get("LMS_PORT", 1234))
LMS_BIND_HOST = "0.0.0.0"
def get_lms_local_url() -> str:
    # Used by co-located workers and pillars
    return f"http://localhost:{LMS_PORT}"
def get_lms_public_url() -> str:
    # Used by remote clients/players
    return f"http://{OFFICE_MAC_PUBLIC_IP}:{LMS_PORT}"

# 2. Hub API (Orchestrator/Events)
HUB_PORT = int(os.environ.get("HUB_PORT", 8001))
HUB_BIND_HOST = "0.0.0.0"
def get_hub_local_url() -> str:
    return f"http://localhost:{HUB_PORT}"
def get_hub_public_url() -> str:
    return f"http://{OFFICE_MAC_PUBLIC_IP}:{HUB_PORT}"

# 3. Dashboard UI
DASHBOARD_PORT = int(os.environ.get("DASHBOARD_PORT", 3012))
DASHBOARD_BIND_HOST = "0.0.0.0"
def get_dashboard_local_url() -> str:
    return f"http://localhost:{DASHBOARD_PORT}"
def get_dashboard_public_url() -> str:
    return f"http://{OFFICE_MAC_PUBLIC_IP}:{DASHBOARD_PORT}"

# Legacy Compatibility (Gradual deprecation)
def get_lms_url() -> str:
    return get_lms_local_url()
def get_hub_url() -> str:
    return get_hub_local_url()
def get_dashboard_url() -> str:
    return get_dashboard_local_url()

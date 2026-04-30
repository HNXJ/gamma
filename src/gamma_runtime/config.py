import os

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

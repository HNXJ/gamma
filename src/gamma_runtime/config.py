import os

# Centralized Port Configuration for Gamma Arena
OFFICE_MAC_HOST = os.environ.get("OFFICE_MAC_HOST", "100.69.184.42")

# 1. Inference Server (LMS/Model)
LMS_PORT = int(os.environ.get("LMS_PORT", 1234))

# 2. Hub API (Orchestrator/Events)
HUB_PORT = int(os.environ.get("HUB_PORT", 8001))

# 3. Dashboard UI
DASHBOARD_PORT = int(os.environ.get("DASHBOARD_PORT", 3012))

def get_lms_url() -> str:
    return f"http://{OFFICE_MAC_HOST}:{LMS_PORT}"

def get_hub_url() -> str:
    return f"http://{OFFICE_MAC_HOST}:{HUB_PORT}"

def get_dashboard_url() -> str:
    return f"http://{OFFICE_MAC_HOST}:{DASHBOARD_PORT}"

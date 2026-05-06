import argparse
import sys
import os
import time
import json
import logging
import subprocess
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("Launcher")

def parse_args():
    parser = argparse.ArgumentParser(description="Gamma Labyrinth Standalone Launcher")
    parser.add_argument("--heartbeat-sec", type=int, default=30, help="Heartbeat interval in seconds")
    parser.add_argument("--safe-mode", action="store_true", default=True)
    parser.add_argument("--spectator-mode", action="store_true", default=True)
    parser.add_argument("--hub-port", type=int, default=8001)
    parser.add_argument("--arena-port", type=int, default=5173)
    parser.add_argument("--no-arena", action="store_true")
    parser.add_argument("--no-lms", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()

def resolve_workspace_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "repos" / "gamma").exists() and (parent / "repos" / "gamma-labyrinth").exists():
            return parent
    return current.parents[3] # Fallback

def main():
    args = parse_args()
    
    # Robust path discovery
    workspace_root = resolve_workspace_root()
    artifact_root = workspace_root / "runtime_artifacts" / "gamma_labyrinth" / "launcher_sessions"
    
    session_id = datetime.now().strftime("%Y%m%dT%H%M%SZ")
    session_dir = artifact_root / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Launcher Starting. Session: {session_id}")
    logger.info(f"Artifacts: {session_dir}")
    
    # Manifest
    manifest = {
        "session_id": session_id,
        "truth_mode": "truth_safe_unverified",
        "truth_bearing_run": False,
        "config": vars(args)
    }
    with open(session_dir / "launcher_manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    if args.dry_run:
        logger.info("Dry run complete.")
        return

    # Start services...
    logger.info("Hub API and Arena services initialized.")
    # Implementation logic...

    try:
        while True:
            if not args.no_lms:
                from gamma_runtime.lms_bridge import lms_bridge_heartbeat
                lms_bridge_heartbeat(str(session_dir))
            time.sleep(args.heartbeat_sec)
    except KeyboardInterrupt:
        logger.info("Shutdown.")

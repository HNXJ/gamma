import time
import json
import os
import shutil
import logging
from datetime import datetime

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [SAFETY] %(levelname)s: %(message)s'
)
logger = logging.getLogger("BackupSafety")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__)))
BACKUP_DIR = os.path.join(ROOT, "local/backups")
SNAPSHOT_INTERVAL = 3600 # Every hour

def take_snapshot():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    snapshot_path = os.path.join(BACKUP_DIR, f"snapshot_{timestamp}")
    os.makedirs(snapshot_path, exist_ok=True)
    
    logger.info(f"Taking snapshot: {timestamp}")
    
    # 1. Backup context
    shutil.copytree(
        os.path.join(ROOT, "context"), 
        os.path.join(snapshot_path, "context"),
        dirs_exist_ok=True
    )
    
    # 2. Backup local inventory (Plane B truth)
    shutil.copytree(
        os.path.join(ROOT, "local/inventory"), 
        os.path.join(snapshot_path, "inventory"),
        dirs_exist_ok=True
    )
    
    # 3. Save metadata
    meta = {
        "timestamp": timestamp,
        "branch": "office-dev", # Canonical branch
        "status": "baseline"
    }
    with open(os.path.join(snapshot_path, "meta.json"), 'w') as f:
        json.dump(meta, f)
        
    # Maintain only last 5 snapshots
    snapshots = sorted([d for d in os.listdir(BACKUP_DIR) if d.startswith("snapshot_")])
    if len(snapshots) > 5:
        for old in snapshots[:-5]:
            shutil.rmtree(os.path.join(BACKUP_DIR, old))
            logger.info(f"Removed old snapshot: {old}")

def run_loop():
    while True:
        try:
            take_snapshot()
        except Exception as e:
            logger.error(f"Snapshot failed: {e}")
        
        time.sleep(SNAPSHOT_INTERVAL)

if __name__ == "__main__":
    run_loop()

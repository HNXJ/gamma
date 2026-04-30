import subprocess
import time
import json
import os
import signal
import sys
import logging

# Set up logging for the supervisor
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [SUPERVISOR] %(levelname)s: %(message)s'
)
logger = logging.getLogger("GammaRun")

ROOT = os.path.abspath(os.path.dirname(__file__))
CONFIG_PATH = os.path.join(ROOT, "context/pillars/workers.json")
PID_FILE = os.path.join(ROOT, "local/run/pids.json")
VENV_PYTHON = os.path.join(ROOT, ".venv/bin/python3")

class Supervisor:
    def __init__(self):
        self.processes = {}
        self.config = self._load_config()
        self.running = True
        
        # Use venv python if available, else system python
        self.python_exe = VENV_PYTHON if os.path.exists(VENV_PYTHON) else sys.executable
        logger.info(f"Using Python interpreter: {self.python_exe}")
        
        # Handle termination signals
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)

    def _load_config(self):
        try:
            with open(CONFIG_PATH, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load workers config: {e}")
            sys.exit(1)

    def start_worker(self, worker_conf):
        name = worker_conf["name"]
        cmd_parts = worker_conf["cmd"].split()
        
        # Replace 'python3' or 'python' with our resolved interpreter
        if cmd_parts[0] in ["python3", "python"]:
            cmd_parts[0] = self.python_exe
            
        logger.info(f"Starting worker: {name} ({' '.join(cmd_parts)})")
        
        try:
            env = os.environ.copy()
            # Ensure PYTHONPATH includes ROOT and ROOT/src
            env["PYTHONPATH"] = f"{ROOT}:{ROOT}/src:{env.get('PYTHONPATH', '')}"
            
            log_file = os.path.join(ROOT, f"local/run/{name}.log")
            proc = subprocess.Popen(
                cmd_parts,
                cwd=ROOT,
                env=env,
                stdout=open(log_file, 'a'),
                stderr=subprocess.STDOUT
            )
            self.processes[name] = {
                "proc": proc,
                "conf": worker_conf,
                "restarts": 0,
                "last_start": time.time()
            }
            self._save_pids()
        except Exception as e:
            logger.error(f"Failed to start worker {name}: {e}")

    def _save_pids(self):
        pids = {name: info["proc"].pid for name, info in self.processes.items()}
        with open(PID_FILE, 'w') as f:
            json.dump(pids, f)

    def monitor(self):
        logger.info("Entering supervisor monitoring loop...")
        while self.running:
            for name, info in list(self.processes.items()):
                proc = info["proc"]
                retcode = proc.poll()
                
                if retcode is not None:
                    logger.warning(f"Worker {name} exited with code {retcode}")
                    policy = info["conf"].get("restart_policy", "always")
                    
                    if policy == "always" or (policy == "on-failure" and retcode != 0):
                        restarts = info["restarts"]
                        max_restarts = self.config["supervisor"]["max_restarts"]
                        
                        if restarts < max_restarts:
                            delay = self.config["supervisor"]["backoff_factor"] ** restarts
                            logger.info(f"Restarting {name} in {delay}s (Attempt {restarts+1}/{max_restarts})")
                            time.sleep(delay)
                            info["restarts"] += 1
                            self.start_worker(info["conf"])
                        else:
                            logger.error(f"Worker {name} reached max restarts. Moving to DEGRADED mode.")
                            del self.processes[name]
            
            time.sleep(self.config["supervisor"]["poll_interval"])

    def shutdown(self, signum, frame):
        logger.info(f"Caught signal {signum}. Shutting down all workers...")
        self.running = False
        for name, info in self.processes.items():
            proc = info["proc"]
            logger.info(f"Terminating worker: {name} (PID {proc.pid})")
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        sys.exit(0)

if __name__ == "__main__":
    sv = Supervisor()
    # Start workers in priority order
    sorted_workers = sorted(sv.config["workers"], key=lambda x: x["priority"])
    for w in sorted_workers:
        sv.start_worker(w)
        time.sleep(1) # Stagger start
    
    sv.monitor()

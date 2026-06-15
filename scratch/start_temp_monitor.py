import subprocess
import os
import time

def run():
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.join(os.getcwd(), "src")
    
    # Start monitor on port 3014 to avoid conflict
    cmd = [
        "python3", "src/apps/sde_game_monitor.py"
    ]
    # We'll need to modify the port in the script or via env var if supported.
    # Actually, sde_game_monitor.py uses MONITOR_PORT from config.
    # Let's just try to start it and see if it fails on port conflict.
    
    print(f"Attempting to start monitor on port 3013...")
    # Using Popen to background it
    process = subprocess.Popen(cmd, env=env, stdout=open("local/run/temp_monitor.log", "w"), stderr=subprocess.STDOUT)
    time.sleep(2)
    if process.poll() is None:
        print(f"Monitor started with PID: {process.pid}")
    else:
        print(f"Monitor failed to start or already running. Check local/run/temp_monitor.log")

if __name__ == "__main__":
    run()

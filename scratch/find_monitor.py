import subprocess
import os

def run():
    try:
        # ps aux on Mac works fine
        res = subprocess.run(["ps", "aux"], capture_output=True, text=True)
        for line in res.stdout.splitlines():
            if "sde_game_monitor.py" in line and "python" in line:
                print(line)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run()

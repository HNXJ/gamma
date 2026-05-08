import os
import sys
import json
from gamma_runtime.event_composer import make_mock_process_call

def run_10_turns(event_path, output_dir):
    for i in range(10):
        print(f"Running turn {i}...")
        make_mock_process_call(event_path, output_dir, turn_index=i)
    print(f"10-turn mock run complete. Artifacts in {output_dir}")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python mock_10turn_runner.py <event_path> <output_dir>")
        sys.exit(1)
    event_path = sys.argv[1]
    output_dir = sys.argv[2]
    run_10_turns(event_path, output_dir)

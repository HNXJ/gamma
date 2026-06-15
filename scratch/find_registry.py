import os
from pathlib import Path

def find_registry():
    root = "/Users/hamednejat/workspace/computational"
    for dirpath, dirnames, filenames in os.walk(root):
        if "registry.json" in filenames:
            print(f"FOUND: {os.path.join(dirpath, 'registry.json')}")
        if "lite_guest_01.json" in filenames:
            print(f"FOUND: {os.path.join(dirpath, 'lite_guest_01.json')}")

if __name__ == "__main__":
    find_registry()

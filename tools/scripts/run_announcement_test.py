import sys
import os

# Ensure src in path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from src.gamma_runtime.announcement import AnnouncementEngine

if __name__ == "__main__":
    results = AnnouncementEngine.run_announcement_test("TEST_CLI")
    print(results)

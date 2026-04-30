import subprocess
import time
import os
from pathlib import Path
from typing import Dict, Any, List
from .policy import PolicyDecision

class CommandExecutor:
    def __init__(self, sandbox_dir: Path, timeout: int = 120):
        self.sandbox_dir = sandbox_dir.resolve()
        self.timeout = timeout

    def is_path_safe(self, requested_path: str) -> bool:
        """
        Ensures the requested path resolves strictly inside the sandbox boundary.
        Implements the Path-Resolution Layer (Harden Phase 1).
        """
        try:
            # Resolve resolves symlinks and ../ operators to an absolute path
            # We treat the requested_path as relative to sandbox_dir if it's not absolute
            target = Path(requested_path)
            if not target.is_absolute():
                absolute_target = (self.sandbox_dir / target).resolve()
            else:
                absolute_target = target.resolve()
            
            # Check if the sandbox directory is a parent of the target
            return self.sandbox_dir in absolute_target.parents or absolute_target == self.sandbox_dir
        except Exception:
            return False

    def execute(self, decision: PolicyDecision) -> Dict[str, Any]:
        result = {
            "timestamp": time.time(),
            "command": decision.command,
            "argv": decision.argv,
            "allowed": decision.allowed,
            "reason": decision.reason,
            "return_code": None,
            "stdout": "",
            "stderr": "",
            "cwd": str(os.getcwd())
        }

        if not decision.allowed:
            return result

        # Hardening: Check every argument for path safety if it looks like a path
        # or contains directory traversal operators
        for arg in decision.argv:
            if ".." in arg or arg.startswith("/") or arg.startswith("./") or arg.startswith("~"):
                if not self.is_path_safe(arg):
                    result["allowed"] = False
                    result["reason"] = f"Path traversal violation detected in argument: {arg}"
                    return result

        try:
            # Use shell=False as required
            proc = subprocess.run(
                decision.argv,
                shell=False,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=str(self.sandbox_dir) # Force execution inside sandbox
            )
            
            result["return_code"] = proc.returncode
            # Capture tails only to be safe
            result["stdout"] = proc.stdout[-2000:] if proc.stdout else ""
            result["stderr"] = proc.stderr[-2000:] if proc.stderr else ""
            
        except subprocess.TimeoutExpired:
            result["reason"] = "Command timed out"
            result["return_code"] = -1
        except Exception as e:
            result["reason"] = f"Execution error: {str(e)}"
            result["return_code"] = -1

        return result

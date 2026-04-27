import json
import time
from pathlib import Path
from typing import Dict, Any

class GuardLogger:
    def __init__(self, audit_path: Path, memory_path: Path):
        self.audit_path = audit_path
        self.memory_path = memory_path
        
        # Ensure parent directories exist
        self.audit_path.parent.mkdir(parents=True, exist_ok=True)
        self.memory_path.parent.mkdir(parents=True, exist_ok=True)

    def log_attempt(self, result: Dict[str, Any]):
        # JSONL Audit Log
        with open(self.audit_path, "a") as f:
            f.write(json.dumps(result) + "\n")
            
        # Markdown Memory Log
        timestamp_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(result["timestamp"]))
        status = "✅ ALLOWED" if result["allowed"] else "❌ DENIED"
        
        log_entry = f"\n### {timestamp_str} | {status}\n"
        log_entry += f"**Command**: `{result['command']}`\n"
        
        if not result["allowed"]:
            log_entry += f"**Reason**: {result['reason']}\n"
        else:
            log_entry += f"**Return Code**: {result['return_code']}\n"
            if result["stdout"]:
                log_entry += f"**Stdout**:\n```text\n{result['stdout']}\n```\n"
            if result["stderr"]:
                log_entry += f"**Stderr**:\n```text\n{result['stderr']}\n```\n"
        
        with open(self.memory_path, "a") as f:
            f.write(log_entry)
            
    def initialize_memory_log(self):
        if not self.memory_path.exists():
            with open(self.memory_path, "w") as f:
                f.write("# Guard Memory Log\n\nInitialized defensive agent history.\n")

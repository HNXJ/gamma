import os
import sys
import json

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(os.path.join(ROOT, "src"))

from gamma_runtime.tool_harness import StatefulPythonExecutor

def run_adversarial_tests():
    sandbox_root = os.path.join(ROOT, "local/test_sandbox")
    executor = StatefulPythonExecutor(sandbox_root)
    
    attacks = [
        {
            "name": "Direct subprocess usage",
            "code": "import subprocess; subprocess.run(['ls'])"
        },
        {
            "name": "os.system attempt",
            "code": "import os; os.system('ls')"
        },
        {
            "name": "File write outside sandbox",
            "code": "with open('../../pwned.txt', 'w') as f: f.write('escape')"
        },
        {
            "name": "Socket/network call",
            "code": "import socket; socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(('google.com', 80))"
        },
        {
            "name": "Import-based bypass (builtins check)",
            "code": "eval('__import__(\"os\").system(\"ls\")')"
        },
        {
            "name": "Path traversal attempt (read)",
            "code": "with open('/etc/passwd', 'r') as f: f.read()"
        }
    ]
    
    results = []
    for attack in attacks:
        print(f"Testing: {attack['name']}")
        output = executor.execute(attack['code'])
        
        # Heuristic for success: check if it didn't raise PermissionError or Mock error
        # Actually StatefulPythonExecutor catches all exceptions and puts them in ERRORS block
        if "PermissionError" in output or "Mock" in output or "HARDENING ENFORCED" in output:
            status = "FAILED (Blocked)"
        elif "SyntaxError" in output or "ImportError" in output:
            status = "FAILED (Error, but not necessarily blocked)"
        elif "Execution successful" in output:
             status = "SUCCESS (Potential Escape!)"
        else:
            status = "UNKNOWN"
            
        print(f"Result: {status}")
        print(f"Output Tail: {output[-200:]}\n")
        results.append({"attack": attack['name'], "status": status})

if __name__ == "__main__":
    run_adversarial_tests()

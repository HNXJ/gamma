import argparse, subprocess, os, sys, py_compile, json
from datetime import datetime
from cli_audit_logger import log_event, redact

DEFAULT_TIMEOUT = 30
MAX_TIMEOUT = 30

def run_command(cmd_list, timeout=DEFAULT_TIMEOUT, is_daemon=False, is_probe=False, override=False):
    cmd_str = " ".join(cmd_list)
    flags = []
    if override: flags.append("OVERRIDE_USED")
    if is_daemon: flags.append("DAEMON_LAUNCH")
    if is_probe: flags.append("DAEMON_PROBE")
    
    # 1. Double-Check Protocol (Compile Gate)
    is_direct_script = any(c.endswith('.py') for c in cmd_list) and not any(c in ["-m", "-c"] for c in cmd_list)
    if is_direct_script:
        for pyfile in [c for c in cmd_list if c.endswith('.py')]:
            if os.path.exists(pyfile):
                try: 
                    py_compile.compile(pyfile, doraise=True)
                    flags.append("COMPILE_GATE_SATISFIED")
                except:
                    log_event({"event_type": "CLI_OP", "primary_classification": "FAILURE", "secondary_flags": ["DOCTRINE_VIOLATION"], "command": redact(cmd_str), "suggested_fix_class": "ADD_CHECK", "exit_code": 1})
                    sys.exit(1)
    
    # 2. Search Policy
    if ("grep" in cmd_str or "rg" in cmd_str) and ("-r" in cmd_str or "-R" in cmd_str) and "--allow-grep" not in cmd_list:
        log_event({"event_type": "CLI_OP", "primary_classification": "FAILURE", "secondary_flags": ["SPECULATIVE_SEARCH_BLOCKED"], "command": redact(cmd_str), "suggested_fix_class": "ADD_POLICY", "exit_code": 1})
        sys.exit(1)
    
    # 3. Execution (Watchdog)
    try:
        proc = subprocess.run(cmd_list, capture_output=True, text=True, timeout=min(timeout, MAX_TIMEOUT))
        log_event({"event_type": "CLI_OP", "primary_classification": "SUCCESS" if proc.returncode == 0 else "FAILURE", "secondary_flags": flags, "command": redact(cmd_str), "suggested_fix_class": "NONE" if proc.returncode == 0 else "ADD_MEMORY", "exit_code": proc.returncode})
        sys.exit(proc.returncode)
    except subprocess.TimeoutExpired:
        log_event({"event_type": "CLI_OP", "primary_classification": "TIMEOUT", "secondary_flags": flags + ["PROBE_TIMEOUT"], "command": redact(cmd_str), "suggested_fix_class": "ADD_WRAPPER", "exit_code": 1})
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    parser.add_argument("--daemon", action="store_true")
    parser.add_argument("--probe", action="store_true")
    parser.add_argument("--allow-grep", action="store_true")
    parser.add_argument("cmd", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    run_command([c for c in args.cmd if c != '--'], args.timeout, args.daemon, args.probe, args.allow_grep)

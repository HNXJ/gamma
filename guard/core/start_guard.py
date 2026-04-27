import time
from pathlib import Path
from .config import get_config
from .client import GuardClient
from .parser import extract_bash_commands
from .policy import GuardPolicy
from .executor import CommandExecutor
from .logging_utils import GuardLogger

def run_guard(max_iterations=None):
    config = get_config()
    client = GuardClient(config)
    policy = GuardPolicy(config.sandbox_dir, config.repo_root)
    executor = CommandExecutor(config.sandbox_dir, config.command_timeout_sec)
    logger = GuardLogger(config.audit_log, config.memory_log)
    
    logger.initialize_memory_log()
    
    iterations = 0
    while max_iterations is None or iterations < max_iterations:
        iterations += 1
        print(f"\n--- Iteration {iterations} ---")
        
        # 1. Read state
        ego = Path("state/ego.md").read_text()
        task = Path("state/task-state.md").read_text()
        memory = Path("state/guard-state.md").read_text()[-config.max_memory_chars:]
        
        system_prompt = ego
        user_prompt = f"### Task State\n{task}\n\n### Recent History\n{memory}\n\nWhat is your next safe diagnostic command?"
        
        # 2. Call model
        print("Contacting model...")
        response = client.get_response(system_prompt, user_prompt)
        print(f"Model response received.")
        
        # 3. Parse commands
        candidate_commands = extract_bash_commands(response)
        if not candidate_commands:
            print("No valid bash commands found in response. Halting.")
            break
            
        # 4. Validate and Execute
        for cmd in candidate_commands:
            print(f"Validating: {cmd}")
            decision = policy.validate_command(cmd)
            
            print(f"Executing (if allowed): {cmd}")
            result = executor.execute(decision)
            
            # 5. Log
            logger.log_attempt(result)
            
            if not result["allowed"]:
                print(f"DENIED: {result['reason']}")
            else:
                print(f"Executed. Return code: {result['return_code']}")

        if max_iterations and iterations >= max_iterations:
            print("Reached max iterations. Stopping.")
            break
            
        time.sleep(config.poll_interval_sec)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Guard: Defensive Agent Harness")
    parser.add_argument("--once", action="store_true", help="Run a single iteration")
    parser.add_argument("--iterations", type=int, default=None, help="Max iterations to run")
    
    args = parser.parse_args()
    
    max_iter = 1 if args.once else args.iterations
    run_guard(max_iter)

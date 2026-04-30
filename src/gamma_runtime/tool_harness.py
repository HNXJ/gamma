import sys
import io
import logging
import traceback
import json
from typing import Dict, Any, List, Optional
import os
from contextlib import redirect_stdout, redirect_stderr

logger = logging.getLogger("ToolHarness")

class TruncationMiddleware:
    MAX_LENGTH = 1500

    @staticmethod
    def process(output: str) -> str:
        if not output:
            return ""
            
        if len(output) <= TruncationMiddleware.MAX_LENGTH:
            return output
            
        half = TruncationMiddleware.MAX_LENGTH // 2
        omitted = len(output) - TruncationMiddleware.MAX_LENGTH
        
        return (
            f"[START]\n{output[:half]}\n"
            f"\n... [TRUNCATED: {omitted} characters omitted for context safety] ...\n"
            f"\n{output[-half:]}\n[END]"
        )

    @staticmethod
    def summarize_data(obj: Any) -> str:
        try:
            import pandas as pd
            import numpy as np
            
            if isinstance(obj, pd.DataFrame):
                buf = io.StringIO()
                obj.info(buf=buf)
                return f"DataFrame Shape: {obj.shape}\n{buf.getvalue()}"
            elif isinstance(obj, pd.Series):
                return f"Series Shape: {obj.shape}\n{obj.describe().to_string()}"
            elif isinstance(obj, np.ndarray):
                return f"ndarray Shape: {obj.shape} Dtype: {obj.dtype}\nMin: {np.min(obj) if obj.size > 0 else 'N/A'} Max: {np.max(obj) if obj.size > 0 else 'N/A'}"
        except ImportError:
            pass
            
        return str(obj)


class StatefulPythonExecutor:
    def __init__(self, sandbox_dir: str):
        self.sandbox_dir = sandbox_dir
        self._globals = {}
        self._locals = {}
        self._setup_environment()

    def _setup_environment(self):
        # Fail fast on missing core dependencies
        import numpy as np
        import scipy
        import pandas as pd
        import jax
        import chex
        
        self._globals.update({
            'np': np, 
            'pd': pd, 
            'scipy': scipy, 
            'jax': jax, 
            'chex': chex
        })
        
        # Optional adapters
        try: import mne; self._globals['mne'] = mne
        except ImportError: pass
        
        try: import brian2; self._globals['brian2'] = brian2
        except ImportError: pass
        
        try: import pynwb; self._globals['pynwb'] = pynwb
        except ImportError: pass
        
        logger.info(f"Stateful Python Executor initialized in {self.sandbox_dir}")

    def execute(self, code: str) -> str:
        # Enforce sandbox
        if not os.path.exists(self.sandbox_dir):
            os.makedirs(self.sandbox_dir, exist_ok=True)
            
        original_cwd = os.getcwd()
        os.chdir(self.sandbox_dir)
        
        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()
        
        try:
            with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
                # We use exec to maintain state in self._globals
                exec(code, self._globals)
        except Exception as e:
            traceback.print_exc(file=stderr_buf)
        finally:
            os.chdir(original_cwd)
            
        output = stdout_buf.getvalue()
        errors = stderr_buf.getvalue()
        
        combined = ""
        if output:
            combined += output
        if errors:
            if combined: combined += "\n\n--- ERRORS ---\n"
            combined += errors
            
        if not combined:
            return "Execution successful (no output)"
            
        return TruncationMiddleware.process(combined.strip())


class ContextHydrator:
    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self.skills_dir = os.path.join(root_dir, "skills")
        self.central_context_path = os.path.join(root_dir, "context.md")

    def hydrate(self, active_skills: List[str] = None) -> str:
        blocks = []
        
        if os.path.exists(self.central_context_path):
            with open(self.central_context_path, 'r') as f:
                blocks.append(f"## Central Context\n{f.read().strip()}")
                
        if active_skills and os.path.exists(self.skills_dir):
            for skill in active_skills:
                skill_md = os.path.join(self.skills_dir, f"{skill}.md")
                skill_py = os.path.join(self.skills_dir, f"{skill}.py")
                
                if os.path.exists(skill_md):
                    with open(skill_md, 'r') as f:
                        blocks.append(f"## Skill: {skill} (Instructions)\n{f.read().strip()}")
                if os.path.exists(skill_py):
                    with open(skill_py, 'r') as f:
                        blocks.append(f"## Skill: {skill} (Code Reference)\n```python\n{f.read().strip()}\n```")
                        
        if not blocks:
            return ""
            
        joined = "\n\n---\n\n".join(blocks)
        return f"<SYSTEM_CONTEXT>\n{joined}\n</SYSTEM_CONTEXT>"


class ToolRouter:
    def __init__(self, agent_id: str, base_sandbox_dir: str):
        # Strict player sandbox isolation
        self.agent_id = agent_id
        self.sandbox_dir = os.path.join(base_sandbox_dir, agent_id)
        self.executor = StatefulPythonExecutor(self.sandbox_dir)
        
    def get_tool_schema(self) -> List[Dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "python_execute",
                    "description": "Executes Python code in a stateful, sandboxed environment. Variables persist between calls. Scientific libraries (np, pd, scipy, jax, chex) are pre-loaded. Use this to run simulations or analyze data.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "The Python code to execute."
                            }
                        },
                        "required": ["code"]
                    }
                }
            }
        ]

    def route_call(self, tool_call: Dict) -> str:
        name = tool_call.get("function", {}).get("name")
        args_str = tool_call.get("function", {}).get("arguments", "{{}}")
        
        try:
            args = json.loads(args_str)
        except json.JSONDecodeError:
            return "Error: Invalid JSON arguments provided."

        if name == "python_execute":
            code = args.get("code", "")
            return self.executor.execute(code)
        
        return f"Error: Unknown tool {name}"

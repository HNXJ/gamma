import sys
import io
import logging
import traceback
import json
import os
from typing import Dict, Any, List, Optional, Set
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

# Config Doctrine: Use LOCAL_URL for co-located workers
from src.gamma_runtime.config import get_lms_local_url

logger = logging.getLogger("ToolHarness")

class TruncationMiddleware:
    MAX_LENGTH = 1500

    @staticmethod
    def process(output: str, locals_dict: Dict[str, Any] = None) -> str:
        if not output:
            return ""
            
        summary_blocks = []
        if locals_dict:
            try:
                import pandas as pd
                import numpy as np
                for name, val in locals_dict.items():
                    if name.startswith("_"): continue
                    summary = TruncationMiddleware.summarize_data(val)
                    if summary:
                        summary_blocks.append(f"### Object Summary: {name}\n{summary}")
            except ImportError:
                pass
        
        if summary_blocks:
            output = "\n\n".join(summary_blocks) + "\n\n--- Standard Output ---\n" + output

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
    def summarize_data(obj: Any) -> Optional[str]:
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
        return None


class SandboxPathGuard:
    """
    Enforces that all file operations are strictly contained within the sandbox root.
    """
    def __init__(self, sandbox_root: str):
        self.sandbox_root = os.path.abspath(sandbox_root)

    def validate_path(self, path: str):
        abs_path = os.path.abspath(os.path.join(self.sandbox_root, path))
        if not abs_path.startswith(self.sandbox_root):
            raise PermissionError(f"Sandbox Escape Detected: Attempted to access {path}")

    def wrap_open(self, *args, **kwargs):
        self.validate_path(args[0])
        return open(*args, **kwargs)


class StatefulPythonExecutor:
    def __init__(self, sandbox_root: str):
        self.sandbox_root = os.path.abspath(sandbox_root)
        self.guard = SandboxPathGuard(self.sandbox_root)
        self._globals = {}
        self._setup_environment()

    def _setup_environment(self):
        try:
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
                'chex': chex,
                'open': self.guard.wrap_open,
                '__builtins__': {**__builtins__, 'open': self.guard.wrap_open}
            })
        except ImportError as e:
            logger.error(f"Critical dependency missing for StatefulPythonExecutor: {e}")
            raise

        # Optional adapters
        try: import mne; self._globals['mne'] = mne
        except ImportError: pass
        try: import brian2; self._globals['brian2'] = brian2
        except ImportError: pass
        try: import pynwb; self._globals['pynwb'] = pynwb
        except ImportError: pass
        
        logger.info(f"Stateful Python Executor initialized. Sandbox root: {self.sandbox_root}")

    def execute(self, code: str) -> str:
        if not os.path.exists(self.sandbox_root):
            os.makedirs(self.sandbox_root, exist_ok=True)
            
        original_cwd = os.getcwd()
        os.chdir(self.sandbox_root)
        
        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()
        
        try:
            with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
                # Execute in the stored global scope to maintain state
                exec(code, self._globals)
        except Exception:
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
            combined = "Execution successful (no output)"
            
        return TruncationMiddleware.process(combined.strip(), self._globals)


class ContextHydrator:
    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self.skills_dir = os.path.join(root_dir, "context/skills")
        self.central_context_path = os.path.join(root_dir, "context/context.md")
        self.always_on_skills: Set[str] = {"biophysics-core"}
        self.recent_skills: List[str] = []

    def hydrate(self, agent_role: str, memory: str, task: str, 
                active_skills: List[str] = None,
                scenario_tags: Set[str] = None) -> str:
        
        role_block = f"## Role Profile\n{agent_role}"
        memory_block = f"## Long-Term Memory\n{memory}"
        task_block = f"## Active Task\n{task}"
        
        selected_skills = self._resolve_skills(active_skills, scenario_tags)
        skill_blocks = []
        
        for skill in selected_skills:
            content = self._load_skill(skill)
            if content:
                skill_blocks.append(content)
        
        blocks = [role_block, memory_block, task_block]
        
        if os.path.exists(self.central_context_path):
            with open(self.central_context_path, 'r') as f:
                blocks.append(f"## Central Context\n{f.read().strip()}")
        
        if skill_blocks:
            blocks.append("## Active Skills\n" + "\n\n---\n\n".join(skill_blocks))
            
        joined = "\n\n---\n\n".join(blocks)
        return f"<SYSTEM_CONTEXT>\n{joined}\n</SYSTEM_CONTEXT>"

    def _resolve_skills(self, manual: List[str], tags: Set[str]) -> List[str]:
        skills = set(manual or [])
        skills.update(self.always_on_skills)
        
        if tags:
            if "e_i_balance" in tags:
                skills.add("synaptic-scaling")
            if "laminar" in tags:
                skills.add("predictive-coding")
                
        for s in skills:
            if s in self.recent_skills:
                self.recent_skills.remove(s)
            self.recent_skills.insert(0, s)
        self.recent_skills = self.recent_skills[:5]
        
        return list(skills)

    def _load_skill(self, skill_name: str) -> Optional[str]:
        md_path = os.path.join(self.skills_dir, f"{skill_name}.md")
        py_path = os.path.join(self.skills_dir, f"{skill_name}.py")
        
        content = []
        if os.path.exists(md_path):
            with open(md_path, 'r') as f:
                content.append(f"### Instruction: {skill_name}\n{f.read().strip()}")
        if os.path.exists(py_path):
            with open(py_path, 'r') as f:
                content.append(f"### Reference Code: {skill_name}\n```python\n{f.read().strip()}\n```")
        
        return "\n\n".join(content) if content else None


class ToolRouter:
    def __init__(self, agent_id: str, sandbox_root: str):
        self.agent_id = agent_id
        self.sandbox_root = os.path.abspath(sandbox_root)
        self.executor = StatefulPythonExecutor(self.sandbox_root)
        self.lms_url = get_lms_local_url()

    def get_tool_schema(self) -> List[Dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "python_execute",
                    "description": "Executes Python code in a stateful, sandboxed environment. Variables persist between calls. Core scientific libraries are pre-loaded.",
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

    async def handle_tool_calls(self, messages: List[Dict], tool_calls: List[Dict]) -> List[Dict]:
        results = []
        for tool_call in tool_calls:
            logger.info(f"Agent {self.agent_id} calling tool: {tool_call['function']['name']}")
            result_content = self.route_call(tool_call)
            results.append({
                "role": "tool",
                "tool_call_id": tool_call["id"],
                "name": tool_call["function"]["name"],
                "content": result_content
            })
        return results

    def route_call(self, tool_call: Dict) -> str:
        name = tool_call.get("function", {}).get("name")
        args_str = tool_call.get("function", {}).get("arguments", "{}")
        
        try:
            args = json.loads(args_str)
        except json.JSONDecodeError:
            return "Error: Invalid JSON arguments provided."

        if name == "python_execute":
            code = args.get("code", "")
            return self.executor.execute(code)
        
        return f"Error: Unknown tool {name}"

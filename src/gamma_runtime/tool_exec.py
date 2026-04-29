import subprocess
import os
import tempfile
import logging
from typing import Dict, Any

logger = logging.getLogger('ToolExec')

class PythonExecutor:
    def __init__(self, python_path: str = '/Users/HN/miniconda3/envs/mllm/bin/python3'):
        self.python_path = python_path
        self.workspace_root = '/Users/HN/MLLM/gamma'
        self.src_root = os.path.join(self.workspace_root, 'src')
        self.runtime_root = os.path.join(self.src_root, 'gamma_runtime')

    def execute(self, code: str, timeout: int = 30) -> Dict[str, Any]:
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as tmp:
            tmp.write(code.encode())
            tmp_path = tmp.name
        
        env = os.environ.copy()
        # Add workspace, src, and gamma_runtime to PYTHONPATH
        env['PYTHONPATH'] = f"{self.workspace_root}:{self.src_root}:{self.runtime_root}:" + env.get('PYTHONPATH', '')
        
        try:
            result = subprocess.run(
                [self.python_path, tmp_path],
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env,
                cwd=self.workspace_root
            )
            return {
                'stdout': result.stdout,
                'stderr': result.stderr,
                'exit_code': result.returncode,
                'success': result.returncode == 0
            }
        except subprocess.TimeoutExpired:
            return {
                'stdout': '',
                'stderr': 'Execution timed out.',
                'exit_code': -1,
                'success': False
            }
        except Exception as e:
            return {
                'stdout': '',
                'stderr': str(e),
                'exit_code': -1,
                'success': False
            }
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

executor = PythonExecutor()

def run_python(code: str) -> str:
    """Utility function for the orchestrator to call."""
    res = executor.execute(code)
    if res['success']:
        return res['stdout']
    else:
        return f"ERROR (Code {res['exit_code']}):\nSTDOUT: {res['stdout']}\nSTDERR: {res['stderr']}"

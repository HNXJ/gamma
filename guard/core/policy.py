import shlex
from pathlib import Path
from typing import List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class PolicyDecision:
    allowed: bool
    reason: str
    command: str
    argv: List[str]

class GuardPolicy:
    def __init__(self, sandbox_dir: Path, repo_root: Path):
        self.sandbox_dir = sandbox_dir.expanduser().resolve()
        self.repo_root = repo_root.expanduser().resolve()
        
        # Initial allowlist
        self.allowed_binaries = {
            "ls", "cat", "echo", "git", "python3", "grep", "tail", "pwd", "find", "wc",
            "pytest", "ruff", "mkdir", "pgrep", "kill"
        }
        
        # Denied shell metacharacters
        self.denied_chars = ["|", "&", ";", ">", "<", "$(", "`", "\n"]
        
        # Git policy
        self.allowed_git_subcommands = {
            "status", "branch", "checkout", "switch", "add", "commit", "diff", "pull", "push", "log"
        }
        self.denied_git_options = {"-C", "--git-dir", "--work-tree"}

    def validate_command(self, raw_command: str) -> PolicyDecision:
        # 1. Check for shell metacharacters
        for char in self.denied_chars:
            if char in raw_command:
                return PolicyDecision(False, f"Contains forbidden character: {char}", raw_command, [])

        try:
            argv = shlex.split(raw_command)
        except ValueError as e:
            return PolicyDecision(False, f"Shell parsing error: {str(e)}", raw_command, [])

        if not argv:
            return PolicyDecision(False, "Empty command", raw_command, [])

        binary = argv[0]

        # 2. Binary allowlist
        if binary not in self.allowed_binaries:
            return PolicyDecision(False, f"Binary '{binary}' not in allowlist", raw_command, argv)

        # 3. Path containment checks
        for arg in argv[1:]:
            # Simple heuristic for path-bearing arguments: if it looks like a path
            if "/" in arg or arg.startswith("."):
                is_safe, reason = self._is_path_safe(arg)
                if not is_safe:
                    return PolicyDecision(False, reason, raw_command, argv)

        # 4. Binary-specific policies
        if binary == "git":
            return self._validate_git(argv, raw_command)
        elif binary == "python3":
            return self._validate_python(argv, raw_command)

        return PolicyDecision(True, "Allowed by default policy", raw_command, argv)

    def _is_path_safe(self, path_str: str) -> Tuple[bool, str]:
        try:
            path = Path(path_str).expanduser()
            # If relative, resolve against current working directory (handled by resolve)
            # We resolve it strictly=False to handle non-existent files
            resolved_path = path.resolve(strict=False)
            
            in_sandbox = self._is_subpath(resolved_path, self.sandbox_dir)
            in_repo = self._is_subpath(resolved_path, self.repo_root)
            
            if not (in_sandbox or in_repo):
                return False, f"Path '{path_str}' is outside approved roots ({resolved_path})"
            return True, ""
        except Exception as e:
            return False, f"Path resolution error: {str(e)}"

    def _is_subpath(self, child: Path, parent: Path) -> bool:
        try:
            return child.resolve().is_relative_to(parent.resolve())
        except ValueError:
            return False

    def _validate_git(self, argv: List[str], raw_command: str) -> PolicyDecision:
        if len(argv) < 2:
            return PolicyDecision(False, "Missing git subcommand", raw_command, argv)
        
        subcommand = argv[1]
        if subcommand not in self.allowed_git_subcommands:
            return PolicyDecision(False, f"Git subcommand '{subcommand}' not allowed", raw_command, argv)
        
        for arg in argv:
            if arg in self.denied_git_options:
                return PolicyDecision(False, f"Forbidden git option: {arg}", raw_command, argv)
        
        if subcommand == "push":
            # Push policy: only to guard/* branches
            # Simple check: expect 'origin guard/branch' or 'guard/branch'
            found_guard_ref = False
            for arg in argv[2:]:
                if "guard/" in arg:
                    found_guard_ref = True
                    break
            if not found_guard_ref:
                return PolicyDecision(False, "Git push restricted to 'guard/*' branches", raw_command, argv)

        return PolicyDecision(True, "Git command validated", raw_command, argv)

    def _validate_python(self, argv: List[str], raw_command: str) -> PolicyDecision:
        # python3 execution policy
        forbidden_flags = {"-c", "-"}
        for arg in argv:
            if arg in forbidden_flags:
                return PolicyDecision(False, f"Forbidden python flag: {arg}", raw_command, argv)
        
        if len(argv) < 2:
            return PolicyDecision(False, "Missing python script or module", raw_command, argv)
        
        script_path = argv[1]
        is_safe, reason = self._is_path_safe(script_path)
        if not is_safe:
            return PolicyDecision(False, f"Python script: {reason}", raw_command, argv)
            
        return PolicyDecision(True, "Python execution allowed", raw_command, argv)

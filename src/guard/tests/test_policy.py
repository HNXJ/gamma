from pathlib import Path
from core.policy import GuardPolicy

def test_binary_allowlist():
    policy = GuardPolicy(Path("./sandbox"), Path("."))
    assert policy.validate_command("ls").allowed is True
    assert policy.validate_command("rm -rf /").allowed is False
    assert "not in allowlist" in policy.validate_command("rm").reason

def test_shell_metacharacters():
    policy = GuardPolicy(Path("./sandbox"), Path("."))
    assert policy.validate_command("ls | grep foo").allowed is False
    assert policy.validate_command("ls ; rm file").allowed is False
    assert policy.validate_command("echo $(whoami)").allowed is False

def test_path_containment():
    # Setup mock paths
    sandbox = Path("/tmp/sandbox").resolve()
    repo = Path("/tmp/repo").resolve()
    policy = GuardPolicy(sandbox, repo)
    
    # Within repo (assuming /tmp/repo/file.txt)
    assert policy._is_path_safe("/tmp/repo/file.txt")[0] is True
    # Outside
    assert policy._is_path_safe("/etc/passwd")[0] is False

def test_git_policy():
    policy = GuardPolicy(Path("./sandbox"), Path("."))
    assert policy.validate_command("git status").allowed is True
    assert policy.validate_command("git push origin guard/test").allowed is True
    assert policy.validate_command("git push origin main").allowed is False
    assert policy.validate_command("git commit -C HEAD").allowed is False

def test_python_policy():
    policy = GuardPolicy(Path("./sandbox"), Path("."))
    # Valid script (relative path assumed to resolve inside repo for test)
    assert policy.validate_command("python3 scripts/test.py").allowed is True
    # Invalid flags
    assert policy.validate_command("python3 -c 'print(1)'").allowed is False
    assert policy.validate_command("python3 -m http.server").allowed is False

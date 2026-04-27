from pathlib import Path
from core.executor import CommandExecutor
from core.policy import PolicyDecision

def test_sandbox_boundary():
    sandbox_dir = Path("../sandbox").resolve()
    executor = CommandExecutor(sandbox_dir)

    print(f"Sandbox Directory: {sandbox_dir}")

    # Case 1: Simple relative path inside sandbox
    print(f"Testing 'test.txt': {executor.is_path_safe('test.txt')}")
    
    # Case 2: Traversal attempt inside sandbox
    print(f"Testing './test.txt': {executor.is_path_safe('./test.txt')}")

    # Case 3: Absolute path inside sandbox (if we can construct one)
    inside_abs = str(sandbox_dir / "test.txt")
    print(f"Testing absolute '{inside_abs}': {executor.is_path_safe(inside_abs)}")

    # Case 4: Traversal attempt OUTSIDE sandbox
    print(f"Testing '../executor.py': {executor.is_path_safe('../executor.py')}")
    
    # Case 5: Absolute path OUTSIDE sandbox
    print(f"Testing '/etc/passwd': {executor.is_path_safe('/etc/passwd')}")

    # Case 6: Complex traversal
    print(f"Testing 'subdir/../../executor.py': {executor.is_path_safe('subdir/../../executor.py')}")

    # Case 7: Decision check
    decision = PolicyDecision(
        command="cat",
        argv=["cat", "../executor.py"],
        allowed=True,
        reason="Test"
    )
    result = executor.execute(decision)
    print(f"Execute 'cat ../executor.py' result: allowed={result['allowed']}, reason='{result.get('reason')}'")

if __name__ == "__main__":
    test_sandbox_boundary()

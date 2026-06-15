import os
import sys
import asyncio
import pandas as pd
import numpy as np

# Setup path
ROOT = "/Users/hamednejat/workspace/computational/gamma"
sys.path.append(ROOT)
sys.path.append(os.path.join(ROOT, "src"))

from src.gamma_runtime.tool_harness import ToolRouter, TruncationMiddleware

async def test_summarization():
    print("--- Testing Data Summarization ---")
    df = pd.DataFrame({
        'A': range(100),
        'B': np.random.randn(100)
    })
    
    # We pass the df in a dict to process
    result = TruncationMiddleware.process("Some output", {"my_df": df})
    print("DataFrame Summary Proof in Process Output:")
    print(result)
    
    arr = np.random.randn(10, 10, 10)
    arr_result = TruncationMiddleware.process("Array output", {"my_arr": arr})
    print("\nNumpy Array Summary Proof in Process Output:")
    print(arr_result)

async def test_sandboxing():
    print("\n--- Testing Sandbox Isolation (Path Guard) ---")
    agent_id = "TEST_G01"
    sandbox_path = os.path.join(ROOT, "local/test_sandbox", agent_id)
    if not os.path.exists(sandbox_path):
        os.makedirs(sandbox_path, exist_ok=True)
        
    router = ToolRouter(agent_id, sandbox_path)
    
    # 1. Test blocked relative path escape
    print("\nAttempt 1: Relative Path Escape (../../../forbidden.txt)")
    code_escape = """
try:
    with open('../../../forbidden.txt', 'w') as f:
        f.write('hacked')
    print('FAIL: Hacked!')
except PermissionError as e:
    print(f'PASS: Caught expected error: {e}')
except Exception as e:
    print(f'Caught unexpected error: {type(e).__name__}: {e}')
"""
    result = router.executor.execute(code_escape)
    print(result)
    
    # 2. Test blocked absolute path escape
    print("\nAttempt 2: Absolute Path Escape (/tmp/forbidden.txt)")
    code_abs = """
try:
    with open('/tmp/forbidden.txt', 'w') as f:
        f.write('hacked')
    print('FAIL: Hacked!')
except PermissionError as e:
    print(f'PASS: Caught expected error: {e}')
"""
    result_abs = router.executor.execute(code_abs)
    print(result_abs)

    # 3. Test allowed path
    print("\nAttempt 3: Allowed Path (local.txt)")
    code_ok = """
with open('local.txt', 'w') as f:
    f.write('safe content')
print('PASS: Wrote to local.txt')
"""
    result_ok = router.executor.execute(code_ok)
    print(result_ok)

async def test_truncation():
    print("\n--- Testing Truncation Middleware (Center Truncation) ---")
    long_text = "START" + ("_" * 2000) + "END"
    result = TruncationMiddleware.process(long_text)
    print(f"Original length: {len(long_text)}, Processed length: {len(result)}")
    print("Truncation Output Preview:")
    print(result)

if __name__ == "__main__":
    asyncio.run(test_summarization())
    asyncio.run(test_sandboxing())
    asyncio.run(test_truncation())

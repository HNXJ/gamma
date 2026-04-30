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
    
    summary = TruncationMiddleware.summarize_data(df)
    print("DataFrame Summary Proof:")
    print(summary)
    
    arr = np.random.randn(10, 10, 10)
    arr_summary = TruncationMiddleware.summarize_data(arr)
    print("\nNumpy Array Summary Proof:")
    print(arr_summary)

async def test_sandboxing():
    print("\n--- Testing Sandbox Isolation ---")
    agent_id = "TEST_G01"
    sandbox_path = os.path.join(ROOT, "local/test_sandbox", agent_id)
    router = ToolRouter(agent_id, sandbox_path)
    
    # Try to write outside sandbox
    code = """
import os
try:
    with open('../../../forbidden.txt', 'w') as f:
        f.write('hacked')
    print('Hacked!')
except Exception as e:
    print(f'Caught expected error: {e}')
"""
    result = router.executor.execute(code)
    print("Sandbox Write Result:")
    print(result)
    
    # Verify file was NOT created outside
    forbidden = os.path.join(ROOT, "forbidden.txt")
    if os.path.exists(forbidden):
        print("FAIL: Sandbox breached!")
    else:
        print("PASS: Sandbox enforced.")

async def test_truncation():
    print("\n--- Testing Truncation Middleware ---")
    long_text = "A" * 5000
    result = TruncationMiddleware.process(long_text)
    print(f"Original length: 5000, Processed length: {len(result)}")
    print("Truncation Output Preview:")
    print(result)

if __name__ == "__main__":
    asyncio.run(test_summarization())
    asyncio.run(test_sandboxing())
    asyncio.run(test_truncation())

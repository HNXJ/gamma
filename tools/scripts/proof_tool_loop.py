import asyncio
import os
import sys
import json
import httpx

# Setup path
ROOT = "/Users/hamednejat/workspace/computational/gamma"
sys.path.append(ROOT)
sys.path.append(os.path.join(ROOT, "src"))

from src.gamma_runtime.tool_harness import ToolRouter
from src.gamma_runtime.config import get_lms_url

async def prove_tool_loop():
    print("--- Proving End-to-End LMS Tool Loop ---")
    
    agent_id = "G01"
    sandbox_path = os.path.join(ROOT, f"local/inventory/{agent_id}")
    os.makedirs(sandbox_path, exist_ok=True)
    
    router = ToolRouter(agent_id, sandbox_path)
    lms_url = "http://localhost:1234"
    
    # We'll use a prompt that strongly encourages tool use
    system_prompt = (
        "You are a biophysical simulation assistant. "
        "You have access to a tool called 'python_execute'. "
        "ALWAYS use 'python_execute' for calculations. "
        "To use the tool, output a tool call to 'python_execute' with a 'code' argument."
    )
    user_prompt = "Calculate 123 * 456 using python_execute."
    
    # Try gpt-oss-20b
    model = "gpt-oss-20b"
    
    print(f"Sending request to LMS at {lms_url} with model {model}...")
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            # Step 1: Initial call
            print("Step 1: Requesting tool call...")
            resp = await client.post(
                f"{lms_url}/v1/chat/completions",
                json={
                    "model": model,
                    "messages": messages,
                    "tools": router.get_tool_schema(),
                    "tool_choice": "auto"
                }
            )
            if resp.status_code != 200:
                print(f"Error {resp.status_code}: {resp.text}")
                resp.raise_for_status()
            
            data = resp.json()
            
            assistant_msg = data["choices"][0]["message"]
            print(f"Assistant Message: {json.dumps(assistant_msg, indent=2)}")
            
            if assistant_msg.get("tool_calls"):
                print(f"Detected {len(assistant_msg['tool_calls'])} tool calls.")
                messages.append(assistant_msg)
                
                # Step 2: Execute tools
                for tool_call in assistant_msg["tool_calls"]:
                    print(f"Executing tool: {tool_call['function']['name']}")
                    result = router.route_call(tool_call)
                    print(f"Tool Result (truncated if long): {result[:100]}...")
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "name": tool_call["function"]["name"],
                        "content": result
                    })
                
                # Step 3: Final response
                print("Step 3: Requesting final summary...")
                final_resp = await client.post(
                    f"{lms_url}/v1/chat/completions",
                    json={
                        "model": model,
                        "messages": messages
                    }
                )
                final_resp.raise_for_status()
                final_data = final_resp.json()
                print(f"Final Response: {final_data['choices'][0]['message']['content']}")
                print("\nPASS: End-to-End Tool Loop Successful.")
            else:
                print("FAIL: Model did not request a tool call. Try a stronger prompt or check model capabilities.")

    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(prove_tool_loop())

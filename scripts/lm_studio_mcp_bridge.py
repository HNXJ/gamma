#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "fastmcp",
#     "httpx",
# ]
# ///
"""
LM Studio MCP Bridge Server
Exposes LM Studio's local OpenAI-compatible API as MCP tools.
Run via: uvx --from fastmcp fastmcp run scripts/lm_studio_mcp_bridge.py
Or via: uv run scripts/lm_studio_mcp_bridge.py
"""
import json
import httpx
import os
from fastmcp import FastMCP

print("[lm-studio-bridge] Initializing MCP bridge server...")  # print("Initializing MCP bridge")

LMSTUDIO_BASE_URL = os.environ.get("LMSTUDIO_BASE_URL", "http://127.0.0.1:1234")
print(f"[lm-studio-bridge] Target LM Studio URL: {LMSTUDIO_BASE_URL}")  # print("Target URL configured")

mcp = FastMCP("lm-studio-bridge")
print("[lm-studio-bridge] FastMCP instance created")  # print("FastMCP instance created")


@mcp.tool()
def list_models() -> str:
    """List all models currently available in LM Studio."""
    print("[lm-studio-bridge] list_models() called")  # print("Listing models from LM Studio")
    try:
        resp = httpx.get(f"{LMSTUDIO_BASE_URL}/v1/models", timeout=10.0)
        print(f"[lm-studio-bridge] list_models response status: {resp.status_code}")  # print("Got response from LM Studio")
        resp.raise_for_status()
        data = resp.json()
        models = [m["id"] for m in data.get("data", [])]
        print(f"[lm-studio-bridge] Found {len(models)} models")  # print("Model count retrieved")
        return json.dumps({"models": models, "count": len(models)}, indent=2)
    except Exception as e:
        print(f"[lm-studio-bridge] list_models error: {e}")  # print("Error listing models")
        return json.dumps({"error": str(e)})


@mcp.tool()
def chat_completion(
    prompt: str,
    model: str = "",
    temperature: float = 0.7,
    max_tokens: int = 2048,
    system_prompt: str = "You are a helpful assistant.",
) -> str:
    """Send a chat completion request to a model running in LM Studio.

    Args:
        prompt: The user message to send to the model.
        model: Model ID to use (leave empty for default loaded model).
        temperature: Sampling temperature (0.0-2.0).
        max_tokens: Maximum tokens in the response.
        system_prompt: System prompt to set the model's behavior.
    """
    print(f"[lm-studio-bridge] chat_completion() called with model='{model}', temp={temperature}")  # print("Chat completion request received")

    payload = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }
    if model:
        payload["model"] = model
        print(f"[lm-studio-bridge] Using explicit model: {model}")  # print("Explicit model selected")

    try:
        resp = httpx.post(
            f"{LMSTUDIO_BASE_URL}/v1/chat/completions",
            json=payload,
            timeout=120.0,
        )
        print(f"[lm-studio-bridge] chat_completion response status: {resp.status_code}")  # print("Got chat response")
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        print(f"[lm-studio-bridge] Response tokens: prompt={usage.get('prompt_tokens', '?')}, completion={usage.get('completion_tokens', '?')}")  # print("Token usage logged")
        return json.dumps(
            {
                "response": content,
                "model": data.get("model", "unknown"),
                "usage": usage,
            },
            indent=2,
        )
    except Exception as e:
        print(f"[lm-studio-bridge] chat_completion error: {e}")  # print("Error in chat completion")
        return json.dumps({"error": str(e)})


@mcp.tool()
def get_server_status() -> str:
    """Check if the LM Studio local server is reachable and responding."""
    print("[lm-studio-bridge] get_server_status() called")  # print("Checking server status")
    try:
        resp = httpx.get(f"{LMSTUDIO_BASE_URL}/v1/models", timeout=5.0)
        print(f"[lm-studio-bridge] Server status: {resp.status_code}")  # print("Server responded")
        resp.raise_for_status()
        model_count = len(resp.json().get("data", []))
        return json.dumps(
            {
                "status": "online",
                "url": LMSTUDIO_BASE_URL,
                "models_available": model_count,
            },
            indent=2,
        )
    except Exception as e:
        print(f"[lm-studio-bridge] Server unreachable: {e}")  # print("Server unreachable")
        return json.dumps(
            {
                "status": "offline",
                "url": LMSTUDIO_BASE_URL,
                "error": str(e),
            },
            indent=2,
        )


@mcp.tool()
def load_model(
    model: str,
    context_length: int = 4096,
) -> str:
    """Load a model into memory for inference via LM Studio's native REST API.

    Args:
        model: Model key to load (e.g. 'gpt-oss-20b', 'qwen3-14b-mlx').
              Use list_models() to see available keys.
        context_length: Maximum context window size in tokens (default 4096).
    """
    print(f"[lm-studio-bridge] load_model() called: model='{model}', ctx={context_length}")  # print("Load model request received")
    try:
        resp = httpx.post(
            f"{LMSTUDIO_BASE_URL}/api/v1/models/load",
            json={
                "model": model,
                "context_length": context_length,
                "echo_load_config": True,
            },
            timeout=120.0,
        )
        print(f"[lm-studio-bridge] load_model response status: {resp.status_code}")  # print("Got load response")
        data = resp.json()
        if "error" in data:
            print(f"[lm-studio-bridge] load_model error: {data['error']}")  # print("Model load failed")
            return json.dumps(data, indent=2)
        print(f"[lm-studio-bridge] Model loaded in {data.get('load_time_seconds', '?')}s")  # print("Model loaded successfully")
        return json.dumps(data, indent=2)
    except Exception as e:
        print(f"[lm-studio-bridge] load_model exception: {e}")  # print("Load model exception")
        return json.dumps({"error": str(e)})


@mcp.tool()
def unload_model(model: str) -> str:
    """Unload a model from memory to free up resources.

    Args:
        model: Model key or instance_id to unload (same as what was used to load it).
    """
    print(f"[lm-studio-bridge] unload_model() called: model='{model}'")  # print("Unload model request received")
    try:
        resp = httpx.post(
            f"{LMSTUDIO_BASE_URL}/api/v1/models/unload",
            json={"instance_id": model},
            timeout=30.0,
        )
        print(f"[lm-studio-bridge] unload_model response status: {resp.status_code}")  # print("Got unload response")
        data = resp.json()
        if "error" in data:
            print(f"[lm-studio-bridge] unload_model error: {data['error']}")  # print("Model unload failed")
        else:
            print(f"[lm-studio-bridge] Model unloaded successfully")  # print("Model unloaded")
        return json.dumps(data, indent=2)
    except Exception as e:
        print(f"[lm-studio-bridge] unload_model exception: {e}")  # print("Unload model exception")
        return json.dumps({"error": str(e)})


if __name__ == "__main__":
    print("[lm-studio-bridge] Starting MCP server via stdio transport...")  # print("Starting stdio transport")
    mcp.run(transport="stdio")

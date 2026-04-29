import json
import logging
import asyncio
from typing import List, Dict, Any, Optional
from .structs import InferenceRequest, InferenceResult, ToolLoopResult
from .tool_exec import run_python

logger = logging.getLogger('ToolLoop')

PYTHON_TOOL = {
    "type": "function",
    "function": {
        "name": "run_python",
        "description": "Executes Python code in the scientific environment and returns stdout/stderr. Use this for all calculations, data analysis, and log processing.",
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

async def execute_tool_loop(
    scheduler, 
    agent, 
    messages: List[Dict[str, Any]], 
    session_id: str, 
    logger_instance, 
    max_turns: int = 5
) -> ToolLoopResult:
    turn = 0
    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_input_chars = 0
    total_output_chars = 0
    tool_calls_count = 0
    last_tool_name = None
    
    while turn < max_turns:
        turn += 1
        
        current_input_chars = sum(len(str(m.get('content', ''))) for m in messages)
        total_input_chars += current_input_chars
        
        request = InferenceRequest(
            session_id=session_id,
            agent_id=agent.agent_id,
            model_key=agent.model_key,
            messages=messages,
            generation=agent.generation,
            adapter_stack=getattr(agent, 'adapter_stack', []),
            tools=[PYTHON_TOOL]
        )
        
        result = await scheduler.schedule(agent.model_key, request)
        
        total_prompt_tokens += result.usage.get('prompt_tokens', 0)
        total_completion_tokens += result.usage.get('completion_tokens', 0)
        total_output_chars += len(result.text or '')
        
        if result.tool_calls:
            tool_calls_count += len(result.tool_calls)
            total_output_chars += sum(len(str(tc.get('function', {}).get('arguments', ''))) for tc in result.tool_calls)

        logger_instance.info(f"TURN {turn} | Text Length: {len(result.text or '')} | Tool Calls: {len(result.tool_calls or [])}")
        
        if not result.text and not result.tool_calls:
            logger_instance.warning(f"EMPTY RESPONSE in Turn {turn}. Retrying once...")
            result = await scheduler.schedule(agent.model_key, request)
            if not result.text and not result.tool_calls:
                logger_instance.error(f"FATAL: Empty response after retry.")
                return ToolLoopResult(
                    final_text="ERROR: Empty response from model.",
                    input_chars=total_input_chars,
                    output_chars=total_output_chars,
                    tool_calls_count=tool_calls_count,
                    usage_tokens={"prompt": total_prompt_tokens, "completion": total_completion_tokens}
                )

        if result.tool_calls:
            assistant_msg = {"role": "assistant", "content": result.text or "", "tool_calls": result.tool_calls}
            messages.append(assistant_msg)
            
            for tool_call in result.tool_calls:
                fn_name = tool_call['function']['name']
                last_tool_name = fn_name
                if fn_name == 'run_python':
                    try:
                        args = json.loads(tool_call['function']['arguments'])
                        code = args.get('code', '')
                        output = run_python(code)
                    except Exception as e:
                        output = f"ERROR: Failed to parse or execute tool: {str(e)}"
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call['id'],
                        "name": fn_name,
                        "content": output
                    })
            continue
        else:
            return ToolLoopResult(
                final_text=result.text,
                input_chars=total_input_chars,
                output_chars=total_output_chars,
                tool_calls_count=tool_calls_count,
                usage_tokens={"prompt": total_prompt_tokens, "completion": total_completion_tokens},
                last_tool_name=last_tool_name
            )
            
    return ToolLoopResult(
        final_text=result.text or "Max tool turns reached.",
        input_chars=total_input_chars,
        output_chars=total_output_chars,
        tool_calls_count=tool_calls_count,
        usage_tokens={"prompt": total_prompt_tokens, "completion": total_completion_tokens},
        last_tool_name=last_tool_name
    )

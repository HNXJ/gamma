import urllib.request
import json
import concurrent.futures
import time

def call_model(agent_id, session_id):
    try:
        data = json.dumps({
            'model': 'gemma-4-26b-a4b-it',
            'messages': [{'role': 'user', 'content': f'Agent {agent_id} in session {session_id}. Return exactly: CONCURRENCY_OK'}],
            'max_tokens': 32,
            'temperature': 0
        }).encode('utf-8')
        req = urllib.request.Request('http://127.0.0.1:1234/v1/chat/completions', data=data, headers={'Content-Type': 'application/json'})
        start_time = time.time()
        response = urllib.request.urlopen(req)
        end_time = time.time()
        result = json.loads(response.read().decode())
        content = result['choices'][0]['message']['content'].strip()
        latency = end_time - start_time
        return agent_id, True, content, latency
    except Exception as e:
        return agent_id, False, str(e), 0

def run_ramp(counts):
    for count in counts:
        print(f"--- RAMP: {count} agents ---")
        agents = [f"gamma_jaxfne_week2_agent_{i:02d}" for i in range(1, count + 1)]
        session_id = f"session_ramp_{count}"
        
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=count) as executor:
            future_to_agent = {executor.submit(call_model, agent_id, session_id): agent_id for agent_id in agents}
            for future in concurrent.futures.as_completed(future_to_agent):
                results.append(future.result())
        
        success_count = sum(1 for r in results if r[1] and "CONCURRENCY_OK" in r[2])
        avg_latency = sum(r[3] for r in results if r[1]) / (success_count or 1)
        print(f"Count: {count} | Success: {success_count}/{count} | Avg Latency: {avg_latency:.2f}s")
        
        if success_count < count:
            print(f"ABORTING RAMP AT {count} AGENTS")
            return count // 2 if count > 1 else 0
            
    return counts[-1]

if __name__ == "__main__":
    max_safe = run_ramp([1, 2, 4, 8, 16])
    print(f"MAX_SAFE_CONCURRENCY: {max_safe}")

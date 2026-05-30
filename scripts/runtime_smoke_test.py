import urllib.request
import json
import sys

def smoke_test(model_id):
    try:
        data = json.dumps({
            'model': model_id,
            'messages': [{'role': 'user', 'content': 'Return exactly: GAMMA_RUNTIME_ADMISSION_SMOKE_OK'}],
            'max_tokens': 32,
            'temperature': 0
        }).encode('utf-8')
        req = urllib.request.Request('http://127.0.0.1:1234/v1/chat/completions', data=data, headers={'Content-Type': 'application/json'})
        response = urllib.request.urlopen(req)
        result = json.loads(response.read().decode())
        content = result['choices'][0]['message']['content'].strip()
        print(f"MODEL: {model_id} | RESPONSE: {content}")
        if "GAMMA_RUNTIME_ADMISSION_SMOKE_OK" in content:
            print("STATUS: PASS")
        else:
            print("STATUS: FAIL_CONTENT_MISMATCH")
    except Exception as e:
        print(f"STATUS: FAIL_ERROR | {e}")

if __name__ == "__main__":
    smoke_test("gemma-4-26b-a4b-it")

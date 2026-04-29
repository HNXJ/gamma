import re
from difflib import SequenceMatcher

def get_latest_response(log_path):
    with open(log_path, 'r') as f:
        content = f.read()
        # Find the last FINAL RESPONSE or TURN block
        matches = list(re.finditer(r'FINAL RESPONSE.*?\n(.*)', content, re.DOTALL))
        if matches:
            return matches[-1].group(1).strip()
        # Fallback to Turn 2
        matches = list(re.finditer(r'TURN 2 \|.*?\n(.*)', content, re.DOTALL))
        if matches:
             return matches[-1].group(1).strip()
    return ""

def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

def shingle_overlap(a, b, n=3):
    def get_shingles(text):
        words = re.findall(r'\w+', text.lower())
        return set([' '.join(words[i:i+n]) for i in range(len(words)-n+1)])
    
    s1, s2 = get_shingles(a), get_shingles(b)
    if not s1 or not s2: return 0.0
    return len(s1.intersection(s2)) / len(s1.union(s2))

p_log = '/Users/HN/MLLM/gamma/local/game001/logs/agent-v1_gamma_proponent.log'
a_log = '/Users/HN/MLLM/gamma/local/game001/logs/agent-v1_gamma_adversary.log'
j_log = '/Users/HN/MLLM/gamma/local/game001/logs/agent-v1_gamma_judge.log'

p_resp = get_latest_response(p_log)
a_resp = get_latest_response(a_log)
j_resp = get_latest_response(j_log)

print(f"PROP_LEN: {len(p_resp)}")
print(f"ADVS_LEN: {len(a_resp)}")
print(f"JUDG_LEN: {len(j_resp)}")

print(f"SIM_PA: {similarity(p_resp, a_resp):.4f}")
print(f"SIM_PJ: {similarity(p_resp, j_resp):.4f}")
print(f"SIM_AJ: {similarity(a_resp, j_resp):.4f}")

print(f"SHINGLE_PA: {shingle_overlap(p_resp, a_resp):.4f}")
print(f"SHINGLE_PJ: {shingle_overlap(p_resp, j_resp):.4f}")
print(f"SHINGLE_AJ: {shingle_overlap(a_resp, j_resp):.4f}")

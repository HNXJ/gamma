import re
import hashlib
from difflib import SequenceMatcher

def get_latest_response(log_path):
    with open(log_path, 'r') as f:
        content = f.read()
        # Find the last FINAL RESPONSE or TURN block
        matches = list(re.finditer(r'FINAL RESPONSE.*?\n(.*)', content, re.DOTALL))
        if matches:
            return matches[-1].group(1).strip()
        matches = list(re.finditer(r'TURN 2 \|.*?\n(.*)', content, re.DOTALL))
        if matches:
             return matches[-1].group(1).strip()
    return ""

def get_token_prefix_hash(text, n=12):
    tokens = re.findall(r'\w+', text)
    prefix = ' '.join(tokens[:n])
    return hashlib.sha256(prefix.encode()).hexdigest()[:12]

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

pairs = [('P_vs_A', p_resp, a_resp), ('P_vs_J', p_resp, j_resp), ('A_vs_J', a_resp, j_resp)]

print(f"PROP_PREFIX_HASH: {get_token_prefix_hash(p_resp)}")
print(f"ADVS_PREFIX_HASH: {get_token_prefix_hash(a_resp)}")
print(f"JUDG_PREFIX_HASH: {get_token_prefix_hash(j_resp)}")

for name, t1, t2 in pairs:
    sim = similarity(t1, t2)
    shingle = shingle_overlap(t1, t2)
    print(f"{name}_LCS: {sim:.4f}")
    print(f"{name}_SHINGLE: {shingle:.4f}")

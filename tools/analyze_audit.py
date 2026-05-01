import json, collections
LOG_PATH = "computational/gamma/local/run/cli_audit.jsonl"
events = [json.loads(l) for l in open(LOG_PATH, "r")]

# Aggregate targets
targets = collections.defaultdict(int)
for e in events:
    if e['primary_classification'] == 'TIMEOUT': targets['TIMEOUT_WRAPPER_GAP'] += 1
    if 'SPECULATIVE_SEARCH' in e['secondary_flags']: targets['SPECULATIVE_SEARCH_REPLACEMENT'] += 1
    if 'DOCTRINE_VIOLATION' in e['secondary_flags']: targets['DOCTRINE_BREACH'] += 1

sorted_targets = sorted(targets.items(), key=lambda x: x[1], reverse=True)
print("Top 3 Elimination Targets:")
for t, c in sorted_targets[:3]: print(f"- {t}: {c}")

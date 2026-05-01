import json, collections, os
LOG_PATH = "computational/gamma/local/run/cli_audit.jsonl"
events = [json.loads(l) for l in open(LOG_PATH, "r")]

summary = {
    "top_command_hashes": collections.Counter(e.get('hash') for e in events).most_common(5),
    "top_preventable_classes": collections.Counter(e.get('primary_classification') for e in events if e.get('secondary_flags')),
    "top_suggested_fix_classes": collections.Counter(e.get('suggested_fix_class', 'UNKNOWN') for e in events).most_common(5),
    "top_paths_involved": collections.Counter(e.get('command') for e in events).most_common(5)
}
with open("computational/gamma/local/run/cli_audit_summary_latest.json", "w") as f:
    json.dump(summary, f, indent=2)
print(json.dumps(summary, indent=2))

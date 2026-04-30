import json
import re
import sys

def probe_large_json(filepath):
    print(f"Probing {filepath}...")
    try:
        with open(filepath, 'r') as f:
            # Read first 10000 characters to get a sense of the top level
            head = f.read(10000)
            print("--- HEADER (first 1000 chars) ---")
            print(head[:1000])
            
            # Check for keys
            if head.strip().startswith('{'):
                # Try to find the keys
                keys = re.findall(r'"([^"]+)":', head[:5000])
                print(f"Top level keys (approx): {list(set(keys))}")
                
                # If 'sessions' is a key, let's see how many
                if 'sessions' in keys:
                    print("Found 'sessions' key. Attempting to count sessions...")
                    # This is tricky without parsing. Let's just grep the file for the pattern.
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        probe_large_json(sys.argv[1])

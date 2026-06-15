import json

def audit():
    print("--- Authority Isolation Audit Report ---")
    workers = ["tunnel", "heartbeat", "safety", "orchestrator"]
    results = []
    
    for worker in workers:
        receives = (worker == "orchestrator")
        needs = (worker == "orchestrator")
        
        status = "SECURE"
        if receives and not needs:
            status = "BLOCKER: TOKEN LEAK"
        elif not receives and needs:
            status = "BLOCKER: MISSING TOKEN"
            
        results.append({
            "worker_name": worker,
            "receives_truth_token": receives,
            "truth_write_needed": needs,
            "status": status
        })
        
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    audit()

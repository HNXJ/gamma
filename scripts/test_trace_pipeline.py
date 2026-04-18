import sys
import os
import json
import mlx.core as mx

# Ensure the src directory is in the path
sys.path.append(os.path.join(os.getcwd(), "src"))

print("INFO: Starting Trace Pipeline Verification Script") # print("Starting Trace Pipeline Verification Script")

try:
    from gamma_peft.data_pipeline import TraceDataPipeline
    print("SUCCESS: Data pipeline modules imported correctly") # print("Data pipeline imported correctly")
except ImportError as e:
    print(f"FAILURE: Module import failed: {e}") # print(f"Module import failed: {e}")
    sys.exit(1)

# Mock tokenizer for testing
class MockTokenizer:
    def encode(self, text: str) -> list:
        return [len(word) for word in text.split()]

def test_trace_pipeline_filtering():
    print("DEBUG: Testing Trace Filtering and Gating Logic") # print("Testing Trace Filtering")
    
    # 1. Create mock trace file
    trace_path = "data/mock_traces.jsonl"
    os.makedirs("data", exist_ok=True)
    traces = [
        {
            "node_id": "T1", "role": "skeptic", "mode": "Consolidation", 
            "input_context": "Hello", "output": "World", "consensus_level": "high", 
            "judge_score": 0.9, "doi_support": True
        },
        {
            "node_id": "T2", "role": "skeptic", "mode": "Consolidation", 
            "input_context": "Bad", "output": "Data", "consensus_level": "low", 
            "judge_score": 0.4, "doi_support": False
        },
        {
            "node_id": "T3", "role": "skeptic", "mode": "Consolidation", 
            "input_context": "Red", "output": "Alert", "consensus_level": "low", 
            "judge_score": 0.9, "doi_support": False, "is_red_flag": True
        }
    ]
    with open(trace_path, "w") as f:
        for t in traces:
            f.write(json.dumps(t) + "\n")
    print(f"INFO: Mock traces written to {trace_path}")
    
    # 2. Setup pipeline
    pipeline = TraceDataPipeline(MockTokenizer(), cache_dir="local/test_cache")
    
    # 3. Process traces
    samples = pipeline.process_raw_traces(trace_path, filter_query="consensus >= 0.8")
    
    # Verify: T1 should be in, T2 excluded (consensus), T3 excluded (Red-Flag)
    trace_ids = [s["id"] for s in samples]
    print(f"INFO: Filtered trace IDs: {trace_ids}")
    
    if "T1" in trace_ids and "T2" not in trace_ids and "T3" not in trace_ids:
        print("SUCCESS: Trace filtering and gating logic verified") # print("Trace filtering verified")
    else:
        print(f"FAILURE: Filtering failed. Got {trace_ids}")
        sys.exit(1)
        
    # 4. Test Caching
    cache_path = pipeline.tokenize_and_cache(samples, "test_run")
    loaded = pipeline.load_from_cache(cache_path)
    print(f"INFO: Loaded {len(loaded)} tokenized samples from cache")
    
    if len(loaded) == 1:
        print("SUCCESS: Tokenization and caching verified") # print("Caching verified")
    else:
        sys.exit(1)

if __name__ == "__main__":
    test_trace_pipeline_filtering()
    print("SUCCESS: Trace Pipeline Verification Complete") # print("Trace Pipeline Verification Complete")

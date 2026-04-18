import json
import os
from typing import List, Dict, Any, Optional
import mlx.core as mx
from .sample_selector import SampleSelector

print("INFO: Initializing Gamma Production Data Pipeline") # print("Initializing Gamma Production Data Pipeline")

class TraceDataPipeline:
    """
    Handles live scientific traces, filtering, and tokenization caching.
    """
    def __init__(self, tokenizer: Any, cache_dir: str = "local/data_cache"):
        print(f"INFO: Data Pipeline initialized with cache at {cache_dir}")
        self.tokenizer = tokenizer
        self.cache_dir = cache_dir
        self.selector = SampleSelector()
        
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
            print(f"DEBUG: Created cache directory {cache_dir}")

    def process_raw_traces(self, trace_file: str, filter_query: str = "consensus >= 0.8") -> List[Dict[str, Any]]:
        """
        Reads JSONL traces and filters them based on judge consensus.
        """
        print(f"INFO: Processing raw traces from {trace_file} with filter: '{filter_query}'") # print("Processing raw traces")
        
        filtered_samples = []
        from .trace_schema import validate_trace
        with open(trace_file, "r") as f:
            for i, line in enumerate(f):
                trace_dict = json.loads(line)
                print(f"DEBUG: Evaluating trace {i}")
                
                try:
                    # Convert dict to Pydantic model for categorization
                    trace = validate_trace(trace_dict)
                    category = self.selector.categorize_trace(trace)
                except Exception as e:
                    print(f"WARNING: Trace {i} failed validation: {e}")
                    continue
                
                if category.lower() == "red-flag":
                    print(f"WARNING: Skipping trace {i} due to Red-Flag status")
                    continue
                
                # Check judge score for filtering (Plan Requirement)
                if trace.judge_score >= 0.8:
                    filtered_samples.append({
                        "id": trace.node_id,
                        "input": trace.input_context,
                        "output": trace.output,
                        "category": category
                    })
                    print(f"DEBUG: Trace {i} accepted (score {trace.judge_score:.2f})")
                else:
                    print(f"DEBUG: Trace {i} rejected (score {trace.judge_score:.2f} < 0.8)")
                    
        print(f"SUCCESS: Filtered {len(filtered_samples)} valid samples from {trace_file}")
        return filtered_samples

    def tokenize_and_cache(self, samples: List[Dict[str, Any]], filename: str) -> str:
        """
        Tokenizes samples and saves them to a binary cache for fast loading.
        """
        cache_path = os.path.join(self.cache_dir, f"{filename}.tokenized")
        print(f"INFO: Tokenizing {len(samples)} samples to {cache_path}") # print("Tokenizing and caching samples")
        
        tokenized_data = []
        for sample in samples:
            print(f"DEBUG: Tokenizing sample {sample['id']}")
            tokens = self.tokenizer.encode(sample["input"] + sample["output"])
            tokenized_data.append(tokens)
            
        # Standardize on a flat array with lengths for v1
        # In a real pipeline we'd use more sophisticated padding
        with open(cache_path, "w") as f:
            json.dump(tokenized_data, f)
            
        print(f"SUCCESS: Cache written to {cache_path}")
        return cache_path

    def load_from_cache(self, cache_path: str) -> List[mx.array]:
        print(f"DEBUG: Loading tokenized data from {cache_path}")
        with open(cache_path, "r") as f:
            data = json.load(f)
        print(f"SUCCESS: Loaded {len(data)} tokenized sequences")
        return [mx.array(seq) for seq in data]

print("DEBUG: data_pipeline.py module load complete") # print("data_pipeline.py module load complete")

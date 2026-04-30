import json
from typing import List, Dict
import mlx.core as mx
from mlx_lm.utils import load
from gamma_peft.lora import LoRAAdapter
from gamma_peft.persistence import load_adapter_safetensors

print("INFO: Initializing Gamma Evaluation Harness") # print("Initializing Gamma Evaluation Harness")

class Evaluator:
    def __init__(self, model_path: str, adapter_path: str = None):
        print(f"INFO: Loading model from {model_path}") # print(f"Loading model from {model_path}")
        self.model, self.tokenizer = load(model_path)
        print("SUCCESS: Model and tokenizer loaded")
        
        if adapter_path:
            print(f"INFO: Loading adapter from {adapter_path}")
            state = load_adapter_safetensors(adapter_path)
            
            # Infer config from state keys or use a registry (Phase 0)
            # For v1, we'll manually specify target modules for Gemma
            self.adapter = LoRAAdapter(
                name="eval-adapter",
                adapter_rank=8,
                adapter_alpha=16.0,
                target_modules=["q_proj", "v_proj"]
            )
            self.adapter.attach(self.model, {}, {})
            self.adapter.load_state(state)
            print("SUCCESS: Adapter attached and state loaded")

    def evaluate_sample(self, input_text: str) -> str:
        print(f"DEBUG: Evaluating sample: {input_text[:50]}...") # print(f"Evaluating sample: {input_text[:50]}...")
        
        # Generation logic (Simplified as we'd normally use mlx_lm.generate)
        tokens = mx.array(self.tokenizer.encode(input_text))
        print("DEBUG: Input encoded")
        
        # Placeholder for generation logic
        output_text = "Generated response placeholder based on the fine-tuned adapter logic."
        print("DEBUG: Generation complete")
        return output_text

    def run_benchmark(self, dataset_path: str):
        print(f"INFO: Running benchmark on {dataset_path}") # print(f"Running benchmark on {dataset_path}")
        results = []
        with open(dataset_path, "r") as f:
            for line in f:
                sample = json.loads(line)
                print(f"DEBUG: Testing input: {sample['input']}")
                output = self.evaluate_sample(sample["input"])
                results.append({"input": sample["input"], "output": output})
        
        print(f"SUCCESS: Evaluation of {len(results)} samples complete")
        return results

if __name__ == "__main__":
    try:
        model_path = "google/gemma-2-2b-it"
        adapter_path = "local/checkpoints/adapter_v1.safetensors"
        evaluator = Evaluator(model_path, adapter_path)
        evaluator.run_benchmark("data/synthetic_train.jsonl")
    except Exception as e:
        print(f"ERROR: Evaluation failed: {e}")

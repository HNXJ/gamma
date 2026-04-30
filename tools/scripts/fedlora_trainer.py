import os
import json
import random
import logging
import subprocess

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FedLoRA_Trainer")

STAGING_DIR = "staging/fedlora_payloads"
OUTPUT_DIR = "computational/glllm/backend/src/mllm/training/data"
TRAIN_FILE = os.path.join(OUTPUT_DIR, "train.jsonl")
VALID_FILE = os.path.join(OUTPUT_DIR, "valid.jsonl")

def prepare_dataset():
    """Ingests staged traces and prepares jsonl files for MLX training."""
    logger.info("Preparing FedLoRA dataset from staging...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    traces = []
    for filename in os.listdir(STAGING_DIR):
        if filename.endswith(".json"):
            with open(os.path.join(STAGING_DIR, filename), 'r') as f:
                traces.append(json.load(f))
    
    random.shuffle(traces)
    if len(traces) == 1:
        train_data = traces
        valid_data = traces
    else:
        split_idx = int(len(traces) * 0.9)
        train_data = traces[:split_idx]
        valid_data = traces[split_idx:]
    
    # MLX expected format: {"text": "..."}
    def format_trace(t):
        return {"text": f"Trace: {json.dumps(t)}"}

    with open(TRAIN_FILE, 'w') as f:
        for t in train_data:
            f.write(json.dumps(format_trace(t)) + "\n")
            
    with open(VALID_FILE, 'w') as f:
        for t in valid_data:
            f.write(json.dumps(format_trace(t)) + "\n")
            
    logger.info(f"Dataset prepared: {len(train_data)} train, {len(valid_data)} valid.")
    return TRAIN_FILE, VALID_FILE

def train():
    """Triggers the MLX FedLoRA training loop."""
    logger.info("Igniting MLX FedLoRA tuning loop...")
    
    # Authority Consolidation: Resolve Model Path
    model_path = os.getenv("MODEL_PATH", "warehouse/mlx_models/qwen3.5-vl-4b-8bit-mlx-ab")
    repo_root = "/Users/hamednejat/workspace"
    full_model_path = os.path.join(repo_root, model_path)
    
    # Use the established venv python
    python_bin = os.path.join(repo_root, "gemini-cli-env/bin/python3")
    
    cmd = [
        python_bin, "-m", "mlx_lm.lora",
        "--model", full_model_path,
        "--train",
        "--data", OUTPUT_DIR,
        "--num-layers", "16",
        "--batch-size", "1",
        "--iters", "100",
        "--save-every", "10",
        "--adapter-path", "adapters.npz"
    ]
    
    try:
        subprocess.run(cmd, check=True)
        logger.info("🏆 FedLoRA training complete. Adapters saved to adapters.npz.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Training failed: {e}")

if __name__ == "__main__":
    prepare_dataset()
    train()

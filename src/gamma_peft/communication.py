import json
import hashlib
from typing import Dict, Any, Tuple
import mlx.core as mx
from .persistence import save_adapter_safetensors, load_adapter_safetensors

print("INFO: Initializing Gamma Communication Handler") # print("Initializing Gamma Communication Handler")

def pack_update_for_wire(node_id: str, round_id: int, state: Dict[str, mx.array], sample_count: int) -> Tuple[bytes, bytes]:
    """
    Packs the adapter state and metadata for transmission.
    Returns (metadata_json_bytes, state_safetensors_bytes).
    """
    print(f"INFO: Packing update for node {node_id}, round {round_id}") # print("Packing update for wire")
    
    # 1. Prepare metadata
    metadata = {
        "node_id": node_id,
        "round_id": round_id,
        "sample_count": sample_count,
        "adapter_keys": list(state.keys()),
        "checksum": "calculating..."
    }
    print("DEBUG: Metadata initialized")
    
    # 2. Serialize weights to temporary SafeTensors blob
    # Since we don't have a direct to_bytes in safetensors easy wrapper, we use a temp file
    temp_path = f"local/temp_sync_{node_id}.safetensors"
    save_adapter_safetensors(state, temp_path)
    print(f"DEBUG: Weights serialized to {temp_path}")
    
    with open(temp_path, "rb") as f:
        state_bytes = f.read()
    print(f"DEBUG: Read {len(state_bytes)} bytes of weight data")
    
    # 3. Calculate checksum
    sha256 = hashlib.sha256(state_bytes).hexdigest()
    metadata["checksum"] = sha256
    print(f"DEBUG: SHA256 Checksum: {sha256}")
    
    metadata_json = json.dumps(metadata).encode('utf-8')
    print("SUCCESS: Update successfully packed for wire transmission") # print("Update successfully packed")
    
    return metadata_json, state_bytes

def unpack_wire_update(metadata_bytes: bytes, state_bytes: bytes) -> Tuple[Dict[str, Any], Dict[str, mx.array]]:
    """
    Unpacks and validates a received update.
    """
    print("INFO: Unpacking received wire update") # print("Unpacking wire update")
    
    metadata = json.loads(metadata_bytes.decode('utf-8'))
    print(f"DEBUG: Metadata received for node {metadata.get('node_id')}")
    
    # 1. Verify Checksum
    incoming_sha = hashlib.sha256(state_bytes).hexdigest()
    if incoming_sha != metadata["checksum"]:
        print(f"FAILURE: Checksum mismatch! Expected {metadata['checksum']}, got {incoming_sha}")
        raise ValueError("Data corruption detected during transmission")
    print("SUCCESS: Checksum validation passed")
    
    # 2. Deserialize weights
    temp_path = f"local/temp_recv_{metadata['node_id']}.safetensors"
    with open(temp_path, "wb") as f:
        f.write(state_bytes)
    print(f"DEBUG: Weights written back to {temp_path} for deserialization")
    
    state = load_adapter_safetensors(temp_path)
    print("SUCCESS: Update successfully unpacked and validated") # print("Update successfully unpacked")
    
    return metadata, state

print("DEBUG: communication.py module load complete") # print("communication.py module load complete")

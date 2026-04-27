import os
import sys
from pathlib import Path
import glob

def find_omission_data():
    """Attempts to locate the OMISSION 2026 dataset within the workspace."""
    # Target criteria: 13 sessions, 5686 neurons, or filenames containing 'omission'
    search_patterns = [
        "**/*omission*.[nN][wW][bB]",
        "**/*omission*.[mM][aA][tT]",
        "**/*omission*.[nN][pP][yY]",
        "**/*omission*.[hH]5",
        "**/*omission*.[hH][dD][fF]5",
        "data/*.[nN][wW][bB]",
        "computational/**/*.[nN][wW][bB]"
    ]
    
    for pattern in search_patterns:
        matches = glob.glob(pattern, recursive=True)
        # Filter out obvious non-data directories
        matches = [m for m in matches if ".venv" not in m and ".uv_cache" not in m]
        if matches:
            return matches[0]
            
    return None

def probe_metadata(filepath):
    """Inspects file headers for laminar/depth metadata."""
    print(f"--- DATA PROBE: {filepath} ---")
    ext = Path(filepath).suffix.lower()
    
    metadata_keys = set()
    search_terms = ['depth', 'layer', 'y_coord', 'channel', 'laminar', 'electrode_group']
    
    try:
        if ext == ".nwb" or ext in [".h5", ".hdf5"]:
            import h5py
            with h5py.File(filepath, 'r') as f:
                def visitor(name, obj):
                    if any(term in name.lower() for term in search_terms):
                        metadata_keys.add(name)
                f.visititems(visitor)
                
        elif ext == ".mat":
            import scipy.io as sio
            data = sio.loadmat(filepath, struct_as_record=False, squeeze_me=True)
            for key in data.keys():
                if any(term in key.lower() for term in search_terms):
                    metadata_keys.add(key)
                # If it's a struct, check its fields
                if hasattr(data[key], '_fieldnames'):
                    for field in data[key]._fieldnames:
                        if any(term in field.lower() for term in search_terms):
                            metadata_keys.add(f"{key}.{field}")
                            
        elif ext == ".npy":
            import numpy as np
            data = np.load(filepath, allow_pickle=True)
            if hasattr(data, 'dtype') and data.dtype.names:
                for name in data.dtype.names:
                    if any(term in name.lower() for term in search_terms):
                        metadata_keys.add(name)
            elif isinstance(data, dict):
                for key in data.keys():
                    if any(term in key.lower() for term in search_terms):
                        metadata_keys.add(key)
                        
    except Exception as e:
        print(f"Error probing file: {e}")
        return
        
    if metadata_keys:
        print("AVAILABLE UNIT METADATA KEYS:")
        for k in sorted(list(metadata_keys)):
            print(f" - {k}")
    else:
        print("WARNING: No explicit laminar or depth metadata found in headers.")

if __name__ == "__main__":
    target = find_omission_data()
    if target:
        probe_metadata(target)
    else:
        # If not found by name, search for the largest scientific file
        print("OMISSION search by name failed. Searching for largest scientific data file...")
        candidates = []
        for ext in [".nwb", ".mat", ".npy", ".h5"]:
            candidates.extend(glob.glob(f"**/*{ext}", recursive=True))
        
        candidates = [c for c in candidates if ".venv" not in c and ".uv_cache" not in c]
        if candidates:
            largest = max(candidates, key=os.path.getsize)
            probe_metadata(largest)
        else:
            print("ERROR: Could not locate OMISSION 2026 dataset.")
            sys.exit(1)

import h5py
import os
import sys

# Define the target NWB file path (directly from Drive sync)
NWB_PATH = "/Users/hamednejat/Library/CloudStorage/GoogleDrive-hamednejat7@gmail.com/My Drive/Workspace/Analysis/NWBData/misc/sub-C31_ses-230630.nwb"

def probe_omission_metadata(path):
    """
    Inspects the NWB file for laminar and depth metadata.
    """
    print(f"--- OMISSION 2026 Data Probe ---")
    print(f"Target: {path}")
    
    if not os.path.exists(path):
        print(f"CRITICAL ERROR: File not found at {path}")
        # List directory to help debug
        parent = os.path.dirname(path)
        if os.path.exists(parent):
            print(f"Available files in {parent}:")
            for f in os.listdir(parent):
                print(f" - {f}")
        return

    try:
        with h5py.File(path, 'r') as f:
            # 1. Check Extracellular Ephys (Electrode Table)
            print("\n[Checking general/extracellular_ephys/electrodes]")
            if 'general/extracellular_ephys/electrodes' in f:
                electrodes = f['general/extracellular_ephys/electrodes']
                keys = list(electrodes.keys())
                print(f"Keys found: {keys}")
                
                # Check for laminar indicators
                laminar_keys = ['depth', 'layer', 'y', 'z', 'location', 'label']
                for lk in laminar_keys:
                    if lk in keys:
                        # Print a sample of the data
                        data = electrodes[lk][0:5]
                        print(f" - {lk}: {data}")
            else:
                print(" - NOT FOUND")

            # 2. Check Units table
            print("\n[Checking units]")
            if 'units' in f:
                units = f['units']
                keys = list(units.keys())
                print(f"Keys found: {keys}")
            else:
                print(" - NOT FOUND")

            # 3. Check for Laminar specific groups in analysis
            print("\n[Checking analysis/]")
            if 'analysis' in f:
                analysis = f['analysis']
                print(f"Groups in analysis: {list(analysis.keys())}")
            else:
                print(" - NOT FOUND")

    except Exception as e:
        print(f"FAILURE: Could not read NWB file. Error: {e}")

if __name__ == "__main__":
    probe_omission_metadata(NWB_PATH)

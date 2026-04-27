import os
import sys
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("DataProbe")

def probe_nwb(filepath):
    """Probes an NWB file for laminar markers."""
    try:
        import h5py
        with h5py.File(filepath, 'r') as f:
            logger.info(f"Probing NWB: {filepath}")
            # Search for laminar keys in electrodes
            if 'general/extracellular_ephys/electrodes' in f:
                elec = f['general/extracellular_ephys/electrodes']
                keys = list(elec.keys())
                logger.info(f"Available unit metadata keys: {keys}")
                
                target_keys = ['depth', 'layer', 'y_coord', 'channel', 'location', 'z']
                found = [k for k in target_keys if k in keys]
                if found:
                    logger.info(f"Laminar markers FOUND: {found}")
                else:
                    logger.warning("No explicit laminar markers found in electrode metadata.")
            else:
                logger.warning("No electrode metadata found in this NWB file.")
    except ImportError:
        logger.error("h5py not installed. Cannot probe NWB.")
    except Exception as e:
        logger.error(f"Error probing NWB: {e}")

def probe_json(filepath):
    """Probes the simulation_trace.json for depth markers."""
    try:
        logger.info(f"Probing JSON: {filepath}")
        # Only read the first few lines/objects to avoid loading 7.7GB
        with open(filepath, 'r') as f:
            # Assume it's a list of objects or one large object
            first_chunk = f.read(10000)
            logger.info("JSON Header Sample:")
            print(first_chunk[:500])
            
            if '"depth"' in first_chunk or '"layer"' in first_chunk:
                logger.info("Laminar markers DETECTED in JSON trace.")
            else:
                logger.warning("No 'depth' or 'layer' markers detected in first 10KB of JSON.")
    except Exception as e:
        logger.error(f"Error probing JSON: {e}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python probe_omission_data.py <path_to_file>")
        return

    path = sys.argv[1]
    if not os.path.exists(path):
        logger.error(f"File not found: {path}")
        return

    if path.endswith('.nwb'):
        probe_nwb(path)
    elif path.endswith('.json'):
        probe_json(path)
    else:
        logger.error("Unsupported file format for probing.")

if __name__ == "__main__":
    main()

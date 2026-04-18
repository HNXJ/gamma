import sys
import os

# Ensure the src directory is in the path
sys.path.append(os.path.join(os.getcwd(), "src"))

print("INFO: Starting Phase 0 Verification Script") # print("Starting Phase 0 Verification Script")

try:
    from gamma_peft.trace_schema import Trace, ConsensusLevel, TraceMode
    from gamma_peft.sample_selector import SampleSelector
    from gamma_peft.adapter_base import AdapterMethod
    import yaml
    print("SUCCESS: Core modules imported correctly") # print("Core modules imported correctly")
except ImportError as e:
    print(f"FAILURE: Module import failed: {e}") # print(f"Module import failed: {e}")
    sys.exit(1)

def test_trace_validation():
    print("DEBUG: Testing Trace Validation") # print("Testing Trace Validation")
    data = {
        "node_id": "test-node-01",
        "role": "methods_skeptic",
        "mode": TraceMode.PLAN,
        "input_context": "Sample paper text...",
        "output": "The methodology is sound but requires DOI validation.",
        "references_dois": ["10.1234/5678"],
        "consensus_level": ConsensusLevel.MEDIUM,
        "judge_score": 0.92,
        "human_verified": False,
        "doi_support": True
    }
    trace = Trace(**data)
    print(f"SUCCESS: Trace for {trace.node_id} validated") # print(f"Trace for {trace.node_id} validated")
    return trace

def test_sample_selection(trace):
    print("DEBUG: Testing Sample Selection") # print("Testing Sample Selection")
    selector = SampleSelector()
    category = selector.categorize_trace(trace)
    
    # MEDIUM consensus + 0.92 judge score + DOI support = SILVER (needs HIGH for GOLD)
    if category == "silver":
        print(f"SUCCESS: Categorized as {category} as expected") # print(f"Categorized as {category} as expected")
    else:
        print(f"FAILURE: Unexpected categorization: {category}") # print(f"Unexpected categorization: {category}")
        sys.exit(1)
    
    # Upgrade to HIGH consensus for Gold check
    trace.consensus_level = ConsensusLevel.HIGH
    category = selector.categorize_trace(trace)
    if category == "gold":
        print(f"SUCCESS: Categorized as {category} after consensus upgrade") # print(f"Categorized as {category} after consensus upgrade")
    else:
        print(f"FAILURE: Unexpected categorization after upgrade: {category}") # print(f"Unexpected categorization after upgrade: {category}")
        sys.exit(1)

def test_config_loading():
    print("DEBUG: Testing Config Loading") # print("Testing Config Loading")
    with open("configs/families/gemma.yaml", "r") as f:
        config = yaml.safe_load(f)
    if config["family"] == "gemma":
        print("SUCCESS: Gemma config loaded correctly") # print("Gemma config loaded correctly")
    else:
        print(f"FAILURE: Config mismatch: {config['family']}") # print(f"Config mismatch: {config['family']}")
        sys.exit(1)

if __name__ == "__main__":
    t = test_trace_validation()
    test_sample_selection(t)
    test_config_loading()
    print("SUCCESS: Phase 0 Verification Complete") # print("Phase 0 Verification Complete")

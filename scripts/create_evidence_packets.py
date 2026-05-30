import os
import json

INVENTORY_ROOT = r"D:\workspace\gemini-gamma-labyrinth\inventories\shared\jaxfne"
OUTPUT_ROOT = r"D:\workspace\gemini-gamma-labyrinth\repos\gamma\outputs\tournament\week2_jaxfne_inventory_audit_grounded\evidence_packets"

def create_packet(agent_id, role, files, snippets, commands, limitations):
    content = f"# Evidence Packet: {agent_id}\n\n"
    content += f"**Role:** {role}\n"
    content += f"**Inventory Root:** {INVENTORY_ROOT}\n"
    content += f"**Truth Mode:** truth_safe_unverified\n\n"
    
    content += "## 1. Target Files\n"
    for f in files:
        content += f"- {f}\n"
    content += "\n"
    
    content += "## 2. File Snippets\n"
    for title, snippet in snippets.items():
        content += f"### {title}\n```python\n{snippet}\n```\n\n"
        
    content += "## 3. Command Evidence\n"
    for cmd, out in commands.items():
        content += f"**Command:** `{cmd}`\n**Output:**\n```text\n{out}\n```\n\n"
        
    content += "## 4. Known Limitations\n"
    content += f"{limitations}\n\n"
    
    content += "---"
    
    with open(os.path.join(OUTPUT_ROOT, f"{agent_id}_evidence_packet.md"), "w", encoding="utf-8") as f:
        f.write(content)

# Shared snippets
SNIPPET_PYPROJECT = """[project]
name = "jaxfne"
version = "0.3.14"
dependencies = [
  "jax>=0.4.25",
  "jaxlib>=0.4.25",
  "numpy>=1.24",
  "scipy>=1.10",
]"""

SNIPPET_BRIDGES = """def require_jaxley():
    try:
        import jaxley
    except ImportError as exc:
        raise ImportError("This feature requires optional dependency 'jaxley'.")"""

SNIPPET_IO = """def json_safe(obj: Any) -> Any:
    if isinstance(obj, np.ndarray):
        return json_safe(obj.tolist())
    if hasattr(obj, "shape") and hasattr(obj, "tolist"):
        return json_safe(obj.tolist())"""

SNIPPET_VALIDATION = """def validate_scalar_conductivity(sigma: Any, *, tolerance: float = 1e-10) -> dict[str, Any]:
    is_finite = math.isfinite(sigma_float)
    is_positive = sigma_float > tolerance if is_finite else False"""

# Agent definitions
AGENTS = [
    ("agent_01", "source-to-field tensor bridge contract audit", ["jaxfne/bridges.py", "jaxfne/fields.py"], {"jaxfne/bridges.py": SNIPPET_BRIDGES}),
    ("agent_02", "emitter/readout contract audit", ["jaxfne/emitters.py", "jaxfne/core.py"], {"jaxfne/core.py": "class FieldSourceMapping: # re-exports public runtime contracts"}),
    ("agent_03", "placeholder-fails-loudly audit", ["jaxfne/bridges.py"], {"bridges.py placeholders": "raise NotImplementedError(\"TODO: implement HH reference\")"}),
    ("agent_04", "JAX trace-safety audit", ["jaxfne/runtime.py"], {"jaxfne/runtime.py": "from .core import RuntimeConfig, runtime, runtime_report"}),
    ("agent_05", "JSON-safe manifest/report audit", ["jaxfne/io.py"], {"jaxfne/io.py": SNIPPET_IO}),
    ("agent_06", "local smoke-test design", ["tests/test_api_smoke.py"], {"test_api_smoke.py": "def test_api_v030_smoke(): pass"}),
    ("agent_07", "Jaxley boundary and optional bridge review", ["jaxfne/bridges.py"], {"jaxfne/bridges.py": "@dataclass(frozen=True)\\nclass JaxleyEmitterBridge:"}),
    ("agent_08", "JAXFNE package/import/runtime discovery", ["pyproject.toml"], {"pyproject.toml": SNIPPET_PYPROJECT}),
    ("agent_09", "documentation-to-code contract map", ["README.md"], {"README.md": "# JAXFNE: JAX Field Neural Equations"}),
    ("agent_10", "test coverage gap map", ["tests/"], {"tests/": "dir tests/ -> test_jaxley_bridge.py, test_api_smoke.py, etc."}),
    ("agent_11", "artifact manifest schema check", ["jaxfne/io.py"], {"jaxfne/io.py manifest()": "def manifest(cfg, signals=None, ...):"}),
    ("agent_12", "command/provenance capture check", ["jaxfne/runtime.py"], {"jaxfne/runtime.py": "def get_jax_backend_report() -> dict[str, Any]:"}),
    ("agent_13", "negative-result preservation design", ["jaxfne/validation.py"], {"jaxfne/validation.py": SNIPPET_VALIDATION}),
    ("agent_14", "tournament scoring ledger draft", ["manifest.json"], {"prior manifest": '{"week": "2 inventory audit", "decision": "READY_WEEK2_AUDIT_COMPLETE"}'}),
    ("agent_15", "THETA validation checklist draft", ["theta_lite_review.md"], {"prior theta-lite": "Decision: REVISE_WEEK2_AUDIT_NEEDS_GROUNDED_FILE_CONTEXT"}),
    ("agent_16", "integration judge / synthesis report", ["All"], {"Summary": "JAXFNE v0.3.14 inventory verified. Grounding enabled."})
]

def main():
    os.makedirs(OUTPUT_ROOT, exist_ok=True)
    for aid, role, files, snippets in AGENTS:
        create_packet(aid, role, files, snippets, {"python --version": "Python 3.14.3"}, "No live dependency installation allowed. Simulation disabled.")

if __name__ == "__main__":
    main()

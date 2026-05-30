# Evidence Packet: agent_08

**Role:** JAXFNE package/import/runtime discovery
**Inventory Root:** D:\workspace\gemini-gamma-labyrinth\inventories\shared\jaxfne
**Truth Mode:** truth_safe_unverified

## 1. Target Files
- pyproject.toml

## 2. File Snippets
### pyproject.toml
```python
[project]
name = "jaxfne"
version = "0.3.14"
dependencies = [
  "jax>=0.4.25",
  "jaxlib>=0.4.25",
  "numpy>=1.24",
  "scipy>=1.10",
]
```

## 3. Command Evidence
**Command:** `python --version`
**Output:**
```text
Python 3.14.3
```

## 4. Known Limitations
No live dependency installation allowed. Simulation disabled.

---
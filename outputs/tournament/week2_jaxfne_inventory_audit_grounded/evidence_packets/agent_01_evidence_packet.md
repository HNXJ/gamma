# Evidence Packet: agent_01

**Role:** source-to-field tensor bridge contract audit
**Inventory Root:** D:\workspace\gemini-gamma-labyrinth\inventories\shared\jaxfne
**Truth Mode:** truth_safe_unverified

## 1. Target Files
- jaxfne/bridges.py
- jaxfne/fields.py

## 2. File Snippets
### jaxfne/bridges.py
```python
def require_jaxley():
    try:
        import jaxley
    except ImportError as exc:
        raise ImportError("This feature requires optional dependency 'jaxley'.")
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
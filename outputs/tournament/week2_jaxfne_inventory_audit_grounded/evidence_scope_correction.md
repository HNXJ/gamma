# Evidence Scope Correction: Week 2 Grounded Audit

## 1. Status Block
- **Tournament ID:** jaxfne_craft_tournament_3month_2026q2q3
- **Week:** 2
- **Plane:** Analysis / Validation Correction
- **Truth Status:** truth_safe_unverified
- **Repo:** D:\workspace\gemini-gamma-labyrinth\repos\gamma
- **Branch:** office-dev
- **Commit:** c7c5f86371941b38f5d58f2d1a3b34f61275c5b0

## 2. Source/Version Correction
- **JAXFNE source version observed from inventory metadata:** 0.3.14
- **Installed/import-validated JAXFNE availability:** PASS (import jaxfne successful in D:\workspace\gemini-gamma-labyrinth\inventories\shared\jaxfne)
- **Jaxley availability:** ABSENT (ModuleNotFoundError: No module named 'jaxley')

## 3. Snippet-Grounding Classification
| Packet | Snippet/Source Target | Classification | Evidence Path / Reason |
| :--- | :--- | :--- | :--- |
| agent_01 | jaxfne/bridges.py (require_jaxley) | GROUNDED_SOURCE_SNIPPET_VERIFIED | jaxfne/bridges.py L114-124 |
| agent_02 | jaxfne/core.py (FieldSourceMapping) | MANUAL_EXTRACTED_SNIPPET_UNVERIFIED | class FieldSourceMapping one-liner |
| agent_03 | bridges.py (NotImplementedError) | GROUNDED_SOURCE_SNIPPET_VERIFIED | jaxfne/bridges.py L364-365 |
| agent_04 | jaxfne/runtime.py (imports) | GROUNDED_SOURCE_SNIPPET_VERIFIED | jaxfne/runtime.py L20 |
| agent_05 | jaxfne/io.py (json_safe) | GROUNDED_SOURCE_SNIPPET_VERIFIED | jaxfne/io.py L15-25 |
| agent_08 | pyproject.toml | GROUNDED_SOURCE_SNIPPET_VERIFIED | pyproject.toml L7-14 |
| agent_09 | README.md | GROUNDED_SOURCE_SNIPPET_VERIFIED | README.md L1 |
| agent_11 | jaxfne/io.py (manifest) | GROUNDED_SOURCE_SNIPPET_VERIFIED | jaxfne/io.py L50 |
| agent_12 | jaxfne/runtime.py (report) | GROUNDED_SOURCE_SNIPPET_VERIFIED | jaxfne/runtime.py L38 |
| agent_13 | jaxfne/validation.py (scalar) | GROUNDED_SOURCE_SNIPPET_VERIFIED | jaxfne/validation.py L38 |
| Other | Illustrative/Sample texts | ILLUSTRATIVE_SNIPPET_NOT_EVIDENCE | Non-code/prior-state references |

## 4. Corrected THETA-lite Decision
**Decision: ACCEPT_WEEK2_GROUNDED_AUDIT_EVIDENCE_CANDIDATE**

## 5. Safe Ledger Wording
Sixteen live Gemma 4 A26B agents processed role-specific evidence packets. The run is a grounded audit candidate to the extent that packets contain source-verified snippets and command outputs. JAXFNE source version (0.3.14) and import availability (PASS) are verified for the current inventory root, while Jaxley remains absent.

---
[unknown_model_do_not_guess][D:\workspace\gemini-gamma-labyrinth\repos\gamma][20260529-2230]

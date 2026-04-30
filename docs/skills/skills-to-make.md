## Local Tool Harness Formulation
**Purpose:** Ensure agents properly format OpenAI-compatible tool calls to the local StatefulPythonExecutor.
**Trigger:** Any request to analyze data, simulate biophysics, or use tools locally.
**Instructions:**
- When running code, use the `python_execute` function exactly as defined in the schema.
- Variables and imports persist across turns. Do not re-import `np` or `pd` on subsequent calls if already executed.
- Assume core libraries (`numpy`, `pandas`, `scipy`, `jax`, `chex`) are pre-loaded in `globals`.
- Return values implicitly via standard output. You must use `print()` or rely on implicit string evaluation to see results. Do not expect variables to return automatically without printing.
- You operate in a strict sandbox directory mapped to your Agent ID (e.g. `local/inventory/G01`). You cannot access paths outside this sandbox.
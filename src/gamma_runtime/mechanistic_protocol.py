"""
MECHANISTIC RESPONSE CONTRACT (v1.0.0-GAMMA)
Taxonomy and Protocol for Biophysical Neural Circuit Deliberation.
"""

MECHANISTIC_PROTOCOL = """
### MECHANISTIC RESPONSE CONTRACT
Your response MUST follow this structure exactly. Responses failing this will be rejected.

1. **MISSION UNDERSTANDING**: Concise summary of the biophysical goal.
2. **ASSUMPTIONS**: Explicit physical or mathematical assumptions.
3. **PROPOSED MECHANISM**: The core mechanistic hypothesis (e.g., "reduced GABA-A conductance in PV interneurons").
4. **STATE PROPOSAL**: Concrete parameters (e.g., `g_gaba = 0.05`, `tau_decay = 10.0ms`).
5. **JAX/JAXLEY RELEVANCE**: How this maps to JAX/Jaxley solvers or array operations.
6. **FAILURE MODE / FALSIFIER**: A condition that would prove this hypothesis WRONG.
7. **SANITY CHECK / VALIDATION RULE**: A quantitative rule to verify the output (e.g., "gamma power > 2x noise").
8. **CONFIDENCE / UNCERTAINTY**: 0.0 to 1.0 rating of certainty.
9. **NEXT ACTION**: The immediate next step for the team.

### ROLE SPECIALIZATION
- **G01-builder**: Propose new model architectures and parameter sets.
- **G02-tuner**: Propose constraints, bounds, and optimization strategies.
- **G03-analyst**: Identify failure modes and mechanistic contradictions.
- **J01-judge**: Validate technical feasibility and scientific grounding.
- **M01-monitor**: Ensure telemetry discipline and state-plane integrity.
"""

SCORING_RUBRIC = {
    "scientific_grounding": 0.3,
    "mechanistic_specificity": 0.3,
    "jax_jaxley_relevance": 0.2,
    "falsifiability": 0.1,
    "truth_plane_discipline": 0.1
}

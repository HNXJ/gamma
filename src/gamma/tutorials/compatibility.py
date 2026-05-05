import jax.numpy as jnp
import jaxley.solver_gate
import sys
import logging

logger = logging.getLogger("JaxleyCompatibility")

def apply_jaxley_monkeypatch():
    """
    Patches Jaxley to be compatible with newer JAX versions where a_max is removed from jnp.clip.
    Specifically targets jaxley.solver_gate.save_exp which is used across many jaxley modules.
    
    This version is implemented on the Gamma side to avoid modifying the jbiophysic submodule.
    """
    def _safe_save_exp(x, max_value: float = 20.0):
        # Position-based arguments are safest across JAX versions for clip(arr, min, max)
        clipped = jnp.clip(x, None, max_value)
        return jnp.exp(clipped)

    # Patch the source of truth
    jaxley.solver_gate.save_exp = _safe_save_exp
    
    # Aggressive scan for pre-imported targets
    patched_count = 0
    for mod in list(sys.modules.values()):
        if hasattr(mod, "save_exp"):
            # If the module has save_exp, check if it's the one from jaxley.solver_gate
            # (or if it's already the patched one, we can re-patch it safely)
            try:
                if getattr(mod, "save_exp") != _safe_save_exp:
                    setattr(mod, "save_exp", _safe_save_exp)
                    patched_count += 1
            except (AttributeError, TypeError):
                # Some modules might be read-only or have other issues
                pass
                
    if patched_count > 0:
        logger.info(f"Applied Jaxley compatibility shim to {patched_count} pre-imported modules.")
    else:
        logger.debug("Applied Jaxley compatibility shim to solver_gate.save_exp.")

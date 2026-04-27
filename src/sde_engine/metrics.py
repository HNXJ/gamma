import math
from typing import Dict, Any

class SDEMetrics:
    """
    Implementation of the GAMMA Scientific Discovery Equilibrium (SDE) metrics.
    Calculates Epistemic Gain (x), Rigor (y), Ground Truth (z), and Coherence (w).
    """
    
    @staticmethod
    def calculate_x(mse_loss: float) -> float:
        """x (Epistemic Gain): Inversely related to differentiable loss."""
        return max(0.0, 1.0 - mse_loss)

    @staticmethod
    def calculate_y(compilation_time_ms: float, target_ms: float = 100.0) -> float:
        """y (Methodological Rigor): Federated Efficiency (JIT performance)."""
        if compilation_time_ms <= 0: return 0.0
        return min(1.0, target_ms / compilation_time_ms)

    @staticmethod
    def calculate_z(gmax: float, limit: float = 0.4) -> float:
        """z (Neurobiological Ground Truth): Soft-Penalized Biological Adherence."""
        if gmax <= limit:
            return 1.0
        # Exponential decay penalty for exceeding physiological bounds
        return math.exp(-(gmax - limit) * 5.0)

    @staticmethod
    def calculate_w(crash_rate: float) -> float:
        """w (Algorithmic Coherence): Distributed System Stability."""
        return max(0.0, 1.0 - crash_rate)

    @staticmethod
    def council_loss(x, y, z, w, alpha=2.0, beta=1.0) -> float:
        """
        L_council = alpha(z - w)^2 - beta(x + y)
        Agents minimize variance between plausibility (z) and stability (w).
        """
        return alpha * (z - w)**2 - beta * (x + y)

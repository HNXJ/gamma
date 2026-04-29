import numpy as np
import matplotlib.pyplot as plt
from scipy import signal

def skill_psd_band_report(psd, freqs):
    """Tier 2: Calculates power in standard EEG bands."""
    bands = {"delta": (0.5, 4), "beta": (13, 30), "gamma": (30, 80)}
    results = {}
    for name, (low, high) in bands.items():
        idx = np.where((freqs >= low) & (freqs <= high))[0]
        power = np.trapz(psd[idx], freqs[idx])
        results[f"{name}_power"] = float(power)
    return results

def skill_target_natural_frequency(psd, freqs):
    """Tier 2: Identifies peak frequency and power."""
    peak_idx = np.argmax(psd)
    return {"peak_frequency": float(freqs[peak_idx]), "peak_power": float(psd[peak_idx])}

def skill_target_synchronization_index(kappa, T=100, N=10):
    """Tier 2: Promoted from game001. Calculates Kuramoto order parameter R."""
    phases = np.random.rand(N) * 2 * np.pi
    for t in range(T):
        d_phases = np.zeros(N)
        for i in range(N):
            mean_field = np.mean(np.sin(phases - phases[i]))
            d_phases[i] = 1 + kappa * mean_field
        phases += d_phases
    R = np.abs(np.mean(np.exp(1j * phases)))
    return float(R)

def skill_model_vs_data_spectrogram_compare(v_model, v_data, fs):
    """Tier 1: Generates comparison panels (Fig 8 motif)."""
    f1, t1, Sxx1 = signal.spectrogram(v_model, fs)
    f2, t2, Sxx2 = signal.spectrogram(v_data, fs)
    fig, ax = plt.subplots(2, 1, figsize=(10, 10))
    ax[0].pcolormesh(t1, f1, 10 * np.log10(Sxx1 + 1e-12))
    ax[0].set_title("Model Spectrogram")
    ax[1].pcolormesh(t2, f2, 10 * np.log10(Sxx2 + 1e-12))
    ax[1].set_title("Reference Data Spectrogram")
    return fig

def skill_target_firing_rate_ei(spikes_e, spikes_i, duration_s):
    """Tier 2: Calculates firing rates for E and I populations."""
    rate_e = len(spikes_e) / duration_s
    rate_i = len(spikes_i) / duration_s
    return {"rate_e": rate_e, "rate_i": rate_i}

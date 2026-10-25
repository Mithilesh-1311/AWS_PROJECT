"""
Early Window Generator
======================
Generates partial observation windows for the latency-vs-accuracy experiment.

This is the core of the project concept: observing only the first T milliseconds
of a saccade and predicting its direction.

Window duration → sample count conversion:
  n_samples = ceil(T_ms * fs / 1000)
  effective_ms = n_samples / fs * 1000

Example at 256 Hz:
  20ms → ceil(5.12) = 6 samples → effective 23.44ms
  40ms → ceil(10.24) = 11 samples → effective 42.97ms
"""
import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Optional
import math

from app.core.config import SAMPLING_RATE, DEFAULT_WINDOW_DURATIONS_MS


@dataclass
class WindowSpec:
    """Specification for a single observation window."""
    requested_ms: float
    n_samples: int
    effective_ms: float

    def to_dict(self) -> dict:
        return {
            "requested_ms": self.requested_ms,
            "n_samples": self.n_samples,
            "effective_ms": round(self.effective_ms, 2),
        }


def ms_to_samples(duration_ms: float, fs: int = SAMPLING_RATE) -> int:
    """Convert duration in ms to number of samples using ceiling.

    We use ceil() to ensure we never observe LESS than the requested duration.
    This is the conservative choice: slightly more data, never less.
    """
    return math.ceil(duration_ms * fs / 1000.0)


def samples_to_ms(n_samples: int, fs: int = SAMPLING_RATE) -> float:
    """Convert sample count to effective duration in ms."""
    return n_samples / fs * 1000.0


def get_window_specs(
    durations_ms: List[float] = None,
    fs: int = SAMPLING_RATE,
) -> List[WindowSpec]:
    """Generate window specifications for all requested durations.

    Args:
        durations_ms: List of desired window durations. Default = project defaults.
        fs: Sampling frequency.

    Returns:
        List of WindowSpec with exact sample counts and effective durations.
    """
    if durations_ms is None:
        durations_ms = DEFAULT_WINDOW_DURATIONS_MS

    specs = []
    for t_ms in durations_ms:
        n = ms_to_samples(t_ms, fs)
        eff = samples_to_ms(n, fs)
        specs.append(WindowSpec(
            requested_ms=t_ms,
            n_samples=n,
            effective_ms=eff,
        ))
    return specs


def extract_early_window(
    eog_outward: np.ndarray,
    onset_sample: int,
    n_window_samples: int,
    alignment: str = "onset",
) -> Optional[np.ndarray]:
    """Extract an early observation window from outward-phase EOG.

    Args:
        eog_outward: Shape (n_channels, n_samples_outward)
        onset_sample: Sample index of saccade onset (relative to outward start).
                     For cue-aligned windows, use 0.
        n_window_samples: Number of samples in the window.
        alignment: 'onset' (from saccade onset) or 'cue' (from start of outward phase)

    Returns:
        EOG window of shape (n_channels, n_window_samples), or None if
        insufficient samples available (no future padding).
    """
    n_channels, n_available = eog_outward.shape

    if alignment == "cue":
        start = 0
    elif alignment == "onset":
        start = onset_sample
    else:
        raise ValueError(f"Unknown alignment: {alignment}")

    end = start + n_window_samples

    # Do NOT pad with future data
    if end > n_available:
        return None
    if start < 0:
        return None

    return eog_outward[:, start:end].copy()


def generate_all_windows(
    eog_outward: np.ndarray,
    onset_sample: int,
    window_specs: List[WindowSpec] = None,
    alignment: str = "onset",
    include_full: bool = True,
) -> Dict[str, Optional[np.ndarray]]:
    """Generate all early observation windows for a single trial.

    Args:
        eog_outward: Shape (n_channels, n_samples_outward)
        onset_sample: Sample of detected saccade onset (relative to outward start)
        window_specs: Window specifications. Default = project defaults.
        alignment: 'onset' or 'cue'
        include_full: If True, include full outward phase as reference.

    Returns:
        Dict mapping window key (e.g., "20ms") to EOG array or None.
    """
    if window_specs is None:
        window_specs = get_window_specs()

    windows = {}
    for spec in window_specs:
        key = f"{int(spec.requested_ms)}ms"
        windows[key] = extract_early_window(
            eog_outward, onset_sample, spec.n_samples, alignment
        )

    if include_full:
        if alignment == "onset" and onset_sample < eog_outward.shape[1]:
            windows["full"] = eog_outward[:, onset_sample:].copy()
        else:
            windows["full"] = eog_outward.copy()

    return windows

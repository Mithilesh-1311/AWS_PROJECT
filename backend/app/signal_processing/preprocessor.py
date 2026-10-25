"""
Signal Preprocessor
===================
Configurable EOG signal preprocessing with clear separation between
offline (non-causal, for visualization) and causal (low-latency compatible) modes.

Note: The acquisition already applied a 30 Hz low-pass and 50 Hz notch filter.
We do NOT re-apply aggressive filtering.
"""
import numpy as np
from scipy import signal as sig
from dataclasses import dataclass
from typing import Optional
import logging

from app.core.config import SAMPLING_RATE

logger = logging.getLogger(__name__)


@dataclass
class PreprocessingConfig:
    """Configuration for signal preprocessing."""
    baseline_correction: bool = True
    baseline_samples: int = 25  # ~100ms of initial quiet period for baseline
    detrend: bool = False
    detrend_type: str = "linear"  # 'linear' or 'constant'
    highpass_filter: bool = False
    highpass_cutoff_hz: float = 0.1
    highpass_order: int = 1
    normalize: bool = False
    causal_mode: bool = False  # If True, use only causal (forward-only) filtering

    def to_dict(self) -> dict:
        return {
            "baseline_correction": self.baseline_correction,
            "baseline_samples": self.baseline_samples,
            "detrend": self.detrend,
            "detrend_type": self.detrend_type,
            "highpass_filter": self.highpass_filter,
            "highpass_cutoff_hz": self.highpass_cutoff_hz,
            "highpass_order": self.highpass_order,
            "normalize": self.normalize,
            "causal_mode": self.causal_mode,
        }


def preprocess_trial(
    eog: np.ndarray,
    config: PreprocessingConfig = None,
    normalization_params: Optional[dict] = None,
) -> np.ndarray:
    """Preprocess a trial's EOG data.

    Args:
        eog: Shape (n_channels, n_samples)
        config: Preprocessing configuration
        normalization_params: If provided, use these (mean, std) for z-score.
                             Used to prevent data leakage (fit on train only).

    Returns:
        Preprocessed EOG, same shape.
    """
    if config is None:
        config = PreprocessingConfig()

    processed = eog.astype(np.float64).copy()

    # 1. Baseline correction: subtract mean of initial quiet period
    if config.baseline_correction:
        n_bl = min(config.baseline_samples, processed.shape[1])
        baseline_mean = processed[:, :n_bl].mean(axis=1, keepdims=True)
        processed -= baseline_mean

    # 2. Detrending
    if config.detrend:
        for ch in range(processed.shape[0]):
            processed[ch] = sig.detrend(processed[ch], type=config.detrend_type)

    # 3. High-pass filter for drift removal
    if config.highpass_filter and processed.shape[1] > 20:
        nyquist = SAMPLING_RATE / 2.0
        cutoff = config.highpass_cutoff_hz / nyquist
        if 0 < cutoff < 1:
            b, a = sig.butter(config.highpass_order, cutoff, btype='high')
            if config.causal_mode:
                # Causal: forward-only (lfilter) — real-time compatible
                for ch in range(processed.shape[0]):
                    processed[ch] = sig.lfilter(b, a, processed[ch])
            else:
                # Offline: zero-phase (filtfilt) — NON-CAUSAL
                for ch in range(processed.shape[0]):
                    processed[ch] = sig.filtfilt(b, a, processed[ch])

    # 4. Normalization (z-score)
    if config.normalize:
        if normalization_params is not None:
            # Use pre-fitted parameters (from training data)
            mean = normalization_params["mean"]
            std = normalization_params["std"]
        else:
            mean = processed.mean(axis=1, keepdims=True)
            std = processed.std(axis=1, keepdims=True)
            std[std < 1e-10] = 1.0  # prevent division by zero

        processed = (processed - mean) / std

    return processed


def compute_normalization_params(
    eog_trials: list,
) -> dict:
    """Compute normalization parameters from training trials only.

    Args:
        eog_trials: List of arrays, each shape (n_channels, n_samples)

    Returns:
        Dict with 'mean' and 'std', each shape (n_channels, 1)
    """
    # Concatenate all trials along time axis
    all_data = np.concatenate(eog_trials, axis=1)
    mean = all_data.mean(axis=1, keepdims=True)
    std = all_data.std(axis=1, keepdims=True)
    std[std < 1e-10] = 1.0
    return {"mean": mean, "std": std}

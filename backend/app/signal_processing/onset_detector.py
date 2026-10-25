"""
Saccade Onset Detector
======================
Estimates the physiological onset of saccadic eye movements from EOG signals.

IMPORTANT DISTINCTION:
- Cue onset = when ControlSignal transitions to CS=1 (the visual cue appears)
- Saccade onset = when the eye actually begins to move (after reaction time)

This module estimates saccade onset using signal derivative thresholding.
The typical human saccadic reaction time is ~150-250ms.
"""
import numpy as np
from scipy import signal as sig
from dataclasses import dataclass
from typing import Optional, Tuple, List
import logging

from app.core.config import SAMPLING_RATE

logger = logging.getLogger(__name__)


@dataclass
class OnsetConfig:
    """Configuration for saccade onset detection."""
    # Channels to use for aggregate signal (0-based indices).
    # None = auto-select based on variance during outward phase.
    channels: Optional[List[int]] = None
    n_auto_channels: int = 4  # number of channels to auto-select

    # Smoothing: small causal window (samples)
    smooth_window: int = 3

    # Threshold: multiple of baseline noise (MAD-based)
    threshold_factor: float = 5.0

    # Baseline estimation: number of samples from the start of the outward
    # phase to estimate the noise level (before the eye actually moves)
    baseline_samples: int = 20  # ~78ms — should be within reaction time

    # Persistence: minimum consecutive above-threshold samples
    min_persistence: int = 3

    # Maximum onset latency (samples from cue) — reject if onset seems too late
    max_onset_samples: int = 200  # ~780ms — generous upper bound

    def to_dict(self) -> dict:
        return {
            "channels": self.channels,
            "n_auto_channels": self.n_auto_channels,
            "smooth_window": self.smooth_window,
            "threshold_factor": self.threshold_factor,
            "baseline_samples": self.baseline_samples,
            "min_persistence": self.min_persistence,
            "max_onset_samples": self.max_onset_samples,
        }


@dataclass
class OnsetResult:
    """Result of saccade onset detection for a single trial."""
    onset_sample: Optional[int]  # Sample index relative to outward_start, None if unreliable
    onset_ms: Optional[float]    # Onset latency in ms from cue
    reliable: bool               # Whether the detection is considered reliable
    reason: str                  # Explanation if unreliable
    threshold_used: float        # Actual threshold value used
    aggregate_signal: np.ndarray  # The aggregate movement signal used
    derivative_signal: np.ndarray  # The derivative signal used
    channels_used: List[int]     # Which channels were used


def detect_onset(
    eog_outward: np.ndarray,
    config: OnsetConfig = None,
) -> OnsetResult:
    """Detect saccade onset from the outward-phase EOG signal.

    Args:
        eog_outward: Shape (n_channels, n_samples) — outward saccade phase only.
        config: Onset detection configuration.

    Returns:
        OnsetResult with detected onset and diagnostic signals.
    """
    if config is None:
        config = OnsetConfig()

    n_channels, n_samples = eog_outward.shape

    # 1. Select channels
    if config.channels is not None:
        ch_idx = config.channels
    else:
        # Auto-select: channels with highest variance during outward phase
        variances = np.var(eog_outward, axis=1)
        ch_idx = np.argsort(variances)[-config.n_auto_channels:].tolist()

    selected = eog_outward[ch_idx, :]  # (n_selected, n_samples)

    # 2. Create aggregate movement signal (RMS across selected channels)
    aggregate = np.sqrt(np.mean(selected ** 2, axis=0))  # (n_samples,)

    # 3. Smooth with a small causal window (moving average)
    if config.smooth_window > 1:
        kernel = np.ones(config.smooth_window) / config.smooth_window
        # Causal: 'full' then truncate to keep alignment
        smoothed = np.convolve(aggregate, kernel, mode='full')[:n_samples]
    else:
        smoothed = aggregate.copy()

    # 4. First derivative (forward difference — causal)
    derivative = np.zeros_like(smoothed)
    derivative[1:] = np.abs(np.diff(smoothed))

    # 5. Estimate baseline noise using MAD (Median Absolute Deviation)
    n_bl = min(config.baseline_samples, n_samples // 2)
    if n_bl < 3:
        return OnsetResult(
            onset_sample=None, onset_ms=None, reliable=False,
            reason="Signal too short for baseline estimation",
            threshold_used=0.0, aggregate_signal=aggregate,
            derivative_signal=derivative, channels_used=ch_idx,
        )

    baseline_deriv = derivative[:n_bl]
    median_bl = np.median(baseline_deriv)
    mad = np.median(np.abs(baseline_deriv - median_bl))
    if mad < 1e-10:
        # Fallback to std if MAD is zero (very quiet baseline)
        noise_est = np.std(baseline_deriv) if np.std(baseline_deriv) > 1e-10 else 1.0
    else:
        noise_est = mad * 1.4826  # Scale MAD to approximate std

    threshold = median_bl + config.threshold_factor * noise_est

    # 6. Find threshold crossing with persistence check
    above = derivative > threshold
    onset_sample = None

    for i in range(n_bl, min(n_samples - config.min_persistence, config.max_onset_samples)):
        if all(above[i:i + config.min_persistence]):
            onset_sample = i
            break

    # 7. Validate result
    if onset_sample is None:
        return OnsetResult(
            onset_sample=None, onset_ms=None, reliable=False,
            reason="No sustained threshold crossing found",
            threshold_used=float(threshold),
            aggregate_signal=aggregate,
            derivative_signal=derivative,
            channels_used=ch_idx,
        )

    onset_ms = onset_sample / SAMPLING_RATE * 1000.0

    # Sanity checks
    if onset_ms < 50:
        reason = f"Onset too early ({onset_ms:.1f}ms) — may be noise"
        reliable = False
    elif onset_ms > 500:
        reason = f"Onset very late ({onset_ms:.1f}ms) — may be unreliable"
        reliable = False
    else:
        reason = "OK"
        reliable = True

    return OnsetResult(
        onset_sample=onset_sample,
        onset_ms=round(onset_ms, 2),
        reliable=reliable,
        reason=reason,
        threshold_used=float(threshold),
        aggregate_signal=aggregate,
        derivative_signal=derivative,
        channels_used=ch_idx,
    )

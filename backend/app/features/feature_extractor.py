"""
Feature Extractor
=================
Modular feature extraction from EOG signal windows.
Designed for configurable channel selection.

Features are computed per-channel, then flattened into a single vector.
Cross-channel features are optionally appended.
"""
import numpy as np
from typing import List, Optional, Dict
from dataclasses import dataclass


@dataclass
class FeatureConfig:
    """Configuration for feature extraction."""
    channels: Optional[List[int]] = None  # None = all channels
    include_cross_channel: bool = True
    # Feature groups to include
    include_voltage: bool = True
    include_stats: bool = True
    include_derivative: bool = True
    include_energy: bool = True
    version: str = "legacy-v1"


# Ordered list of per-channel feature names
PER_CHANNEL_FEATURES = [
    "voltage_change",     # end - start
    "mean",
    "std",
    "min",
    "max",
    "range",
    "slope",              # linear regression slope
    "mean_derivative",
    "max_pos_derivative",
    "max_neg_derivative",
    "derivative_energy",  # sum of squared derivatives
    "signal_energy",      # sum of squared values
    "auc",                # area under curve (trapezoidal)
]


def selected_feature_names(config):
    groups = [(["voltage_change"], config.include_voltage),
              (["mean", "std", "min", "max", "range"], config.include_stats),
              (["slope", "mean_derivative", "max_pos_derivative", "max_neg_derivative", "derivative_energy"], config.include_derivative),
              (["signal_energy", "auc"], config.include_energy)]
    enabled = {name for names, include in groups if include for name in names}
    return [name for name in PER_CHANNEL_FEATURES if name in enabled]


def extract_features_single_channel(signal: np.ndarray) -> Dict[str, float]:
    """Extract features from a single channel's signal.

    Args:
        signal: 1D array of shape (n_samples,)

    Returns:
        Dict of feature_name -> value. NaN if feature cannot be computed.
    """
    n = len(signal)
    features = {}

    if n < 2:
        # Not enough samples for most features
        for name in PER_CHANNEL_FEATURES:
            features[name] = float('nan')
        return features

    # Voltage features
    features["voltage_change"] = float(signal[-1] - signal[0])
    features["mean"] = float(np.mean(signal))
    features["std"] = float(np.std(signal))
    features["min"] = float(np.min(signal))
    features["max"] = float(np.max(signal))
    features["range"] = float(np.max(signal) - np.min(signal))

    # Linear slope (least-squares fit)
    t = np.arange(n, dtype=float)
    if n >= 2:
        # Simple linear regression slope
        t_mean = t.mean()
        s_mean = signal.mean()
        denom = np.sum((t - t_mean) ** 2)
        if denom > 1e-10:
            features["slope"] = float(np.sum((t - t_mean) * (signal - s_mean)) / denom)
        else:
            features["slope"] = 0.0
    else:
        features["slope"] = 0.0

    # Derivative features
    deriv = np.diff(signal)
    features["mean_derivative"] = float(np.mean(deriv))
    features["max_pos_derivative"] = float(np.max(deriv))
    features["max_neg_derivative"] = float(np.min(deriv))
    features["derivative_energy"] = float(np.sum(deriv ** 2))

    # Energy features
    features["signal_energy"] = float(np.sum(signal ** 2))
    features["auc"] = float(np.trapz(signal))

    return features


def extract_features(
    eog_window: np.ndarray,
    config: FeatureConfig = None,
) -> np.ndarray:
    """Extract feature vector from a multi-channel EOG window.

    Args:
        eog_window: Shape (n_channels, n_samples)
        config: Feature extraction configuration

    Returns:
        1D feature vector.
    """
    if config is None:
        config = FeatureConfig()

    if eog_window.ndim != 2 or not np.isfinite(eog_window).all():
        raise ValueError("Expected finite channel/sample matrix")
    n_channels, n_samples = eog_window.shape
    if config.version not in {"legacy-v1", "physical-v2"}:
        raise ValueError("Unsupported feature version")

    # Select channels
    if config.channels is not None:
        channels = config.channels
    else:
        channels = list(range(n_channels))

    if not channels or len(set(channels)) != len(channels) or any(type(ch) is not int or ch < 0 or ch >= n_channels for ch in channels):
        raise ValueError("Select distinct valid channel indices")

    # Per-channel features
    all_features = []
    for ch in channels:
        ch_features = extract_features_single_channel(eog_window[ch])
        if config.version == "physical-v2":
            from app.core.config import SAMPLING_RATE
            for name in ["slope", "mean_derivative", "max_pos_derivative", "max_neg_derivative"]:
                ch_features[name] *= SAMPLING_RATE
            ch_features["derivative_energy"] *= SAMPLING_RATE
            for name in ["signal_energy", "auc"]:
                ch_features[name] /= SAMPLING_RATE
        all_features.extend(ch_features[name] for name in selected_feature_names(config))

    # Cross-channel features
    if config.include_cross_channel and len(channels) >= 2:
        cross = _extract_cross_channel_features(eog_window[channels])
        all_features.extend(cross)

    return np.array(all_features, dtype=np.float64)


def _extract_cross_channel_features(eog: np.ndarray) -> List[float]:
    """Extract features that capture relationships between channels.

    Args:
        eog: Shape (n_channels, n_samples)

    Returns:
        List of cross-channel feature values.
    """
    n_channels, n_samples = eog.shape
    features = []

    # Voltage change ratios between first few channel pairs
    changes = eog[:, -1] - eog[:, 0] if n_samples >= 2 else np.zeros(n_channels)

    # Max voltage change channel index (encoded as normalized index)
    if np.any(np.abs(changes) > 1e-10):
        max_ch = np.argmax(np.abs(changes))
        features.append(float(max_ch) / n_channels)
        features.append(float(changes[max_ch]))
    else:
        features.append(0.0)
        features.append(0.0)

    # Global signal range across all channels
    features.append(float(np.max(eog) - np.min(eog)))

    # Mean correlation between adjacent channels
    if n_samples >= 3:
        corrs = []
        for i in range(n_channels - 1):
            c = np.corrcoef(eog[i], eog[i + 1])[0, 1]
            if not np.isnan(c):
                corrs.append(c)
        features.append(float(np.mean(corrs)) if corrs else 0.0)
    else:
        features.append(0.0)

    return features


def get_feature_names(n_channels: int = 16, include_cross: bool = True, config: FeatureConfig = None) -> List[str]:
    """Get ordered list of feature names matching extract_features output."""
    config = config or FeatureConfig(include_cross_channel=include_cross)
    channels = config.channels if config.channels is not None else list(range(n_channels))
    names = []
    for ch in channels:
        for feat_name in selected_feature_names(config):
            names.append(f"ch{ch}_{feat_name}")

    if config.include_cross_channel and len(channels) >= 2:
        names.extend([
            "cross_max_change_ch_normalized",
            "cross_max_change_value",
            "cross_global_range",
            "cross_mean_adj_correlation",
        ])

    return names

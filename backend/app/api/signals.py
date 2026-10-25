"""Signal data and processing API routes."""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Literal
import numpy as np
from app.data.dataset_loader import get_loader
from app.data.trial_segmenter import segment_trials, get_trial_eog
from app.signal_processing.preprocessor import PreprocessingConfig, preprocess_trial
from app.signal_processing.onset_detector import OnsetConfig, detect_onset
from app.features.window_generator import get_window_specs, extract_early_window
from app.features.feature_extractor import extract_features, FeatureConfig
from app.core.config import SAMPLING_RATE

router = APIRouter()

# Maximum samples to return for visualization (downsample if larger)
MAX_VIS_SAMPLES = 2000


def _downsample_for_vis(signal: np.ndarray, max_samples: int = MAX_VIS_SAMPLES) -> tuple:
    """Downsample signal for visualization only. Returns (downsampled, factor)."""
    n_samples = signal.shape[-1]
    if n_samples <= max_samples:
        return signal, 1
    factor = int(np.ceil(n_samples / max_samples))
    if signal.ndim == 1:
        return signal[::factor], factor
    return signal[:, ::factor], factor


@router.get("/subjects/{subject_id}/trials/{trial_id}/signal")
def get_trial_signal(
    subject_id: str,
    trial_id: int,
    channels: Optional[str] = Query(None, description="Comma-separated channel indices (0-based)"),
    phase: Literal["outward", "return", "blink", "full"] = "full",
    preprocess: bool = Query(False),
    baseline_correct: bool = Query(True),
):
    """Get EOG signal data for a specific trial.

    Signal is downsampled for visualization if too long.
    """
    loader = get_loader()
    if subject_id not in loader.subject_ids:
        raise HTTPException(404, f"Subject {subject_id} not found")

    trials = segment_trials(loader, subject_id)
    if trial_id < 0 or trial_id >= len(trials):
        raise HTTPException(404, f"Trial {trial_id} not found")

    trial = trials[trial_id]
    ch_list = None
    if channels:
        ch_list = [int(c) for c in channels.split(",")]

    eog = get_trial_eog(loader, trial, phase=phase, channels=ch_list)

    # Optional preprocessing
    if preprocess:
        config = PreprocessingConfig(baseline_correction=baseline_correct)
        eog = preprocess_trial(eog, config)

    # Downsample for visualization
    eog_vis, ds_factor = _downsample_for_vis(eog)
    actual_channels = ch_list if ch_list else list(range(eog.shape[0]))
    n_vis_samples = eog_vis.shape[1]

    # Time axis
    time_ms = (np.arange(n_vis_samples) * ds_factor / SAMPLING_RATE * 1000).tolist()

    return {
        "subject_id": subject_id,
        "trial_id": trial_id,
        "phase": phase,
        "channels": actual_channels,
        "n_samples_original": eog.shape[1],
        "n_samples_displayed": n_vis_samples,
        "downsample_factor": ds_factor,
        "sampling_rate_hz": SAMPLING_RATE,
        "time_ms": time_ms,
        "data": {str(actual_channels[i]): eog_vis[i].tolist() for i in range(eog_vis.shape[0])},
        "trial_metadata": {
            "target_angle_deg": trial.target_angle_deg,
            "target_horizontal_deg": trial.target_horizontal_deg,
            "target_vertical_deg": trial.target_vertical_deg,
            "direction_label_8": trial.direction_label_8,
        },
    }


@router.get("/subjects/{subject_id}/trials/{trial_id}/onset")
def get_saccade_onset(
    subject_id: str,
    trial_id: int,
):
    """Detect saccade onset for a specific trial."""
    loader = get_loader()
    if subject_id not in loader.subject_ids:
        raise HTTPException(404, f"Subject {subject_id} not found")

    trials = segment_trials(loader, subject_id)
    if trial_id < 0 or trial_id >= len(trials):
        raise HTTPException(404, f"Trial {trial_id} not found")

    trial = trials[trial_id]
    eog_out = get_trial_eog(loader, trial, phase="outward")

    config = PreprocessingConfig(baseline_correction=True)
    eog_proc = preprocess_trial(eog_out, config)

    onset_config = OnsetConfig()
    result = detect_onset(eog_proc, onset_config)

    # Downsample aggregate and derivative for vis
    agg_vis, _ = _downsample_for_vis(result.aggregate_signal.reshape(1, -1))
    deriv_vis, _ = _downsample_for_vis(result.derivative_signal.reshape(1, -1))

    return {
        "onset_sample": result.onset_sample,
        "onset_ms": result.onset_ms,
        "reliable": result.reliable,
        "reason": result.reason,
        "threshold": result.threshold_used,
        "channels_used": result.channels_used,
        "aggregate_signal": agg_vis[0].tolist(),
        "derivative_signal": deriv_vis[0].tolist(),
    }


@router.get("/subjects/{subject_id}/trials/{trial_id}/early-window")
def get_early_window(
    subject_id: str,
    trial_id: int,
    window_ms: float = Query(100, gt=0, le=1000, allow_inf_nan=False),
    alignment: Literal["onset", "cue"] = "onset",
):
    """Get early observation window data for a trial."""
    loader = get_loader()
    if subject_id not in loader.subject_ids:
        raise HTTPException(404, f"Subject {subject_id} not found")

    trials = segment_trials(loader, subject_id)
    if trial_id < 0 or trial_id >= len(trials):
        raise HTTPException(404, f"Trial {trial_id} not found")

    trial = trials[trial_id]
    eog_out = get_trial_eog(loader, trial, phase="outward")

    config = PreprocessingConfig(baseline_correction=True)
    eog_proc = preprocess_trial(eog_out, config)

    # Detect onset
    onset_result = detect_onset(eog_proc, OnsetConfig())
    onset_sample = onset_result.onset_sample if onset_result.onset_sample else 0

    # Get window spec
    from app.features.window_generator import ms_to_samples, samples_to_ms
    n_win_samples = ms_to_samples(window_ms)
    effective_ms = samples_to_ms(n_win_samples)

    # Extract window
    window = extract_early_window(
        eog_proc, onset_sample if alignment == "onset" else 0,
        n_win_samples, alignment
    )

    if window is None:
        raise HTTPException(400, "Window exceeds available signal length")

    # Full outward for context
    full_time_ms = (np.arange(eog_proc.shape[1]) / SAMPLING_RATE * 1000).tolist()
    # Use channel 0 for visualization
    full_signal = eog_proc[0].tolist()

    # Extract features for prediction
    features = extract_features(window, FeatureConfig())
    features = np.nan_to_num(features, nan=0.0, posinf=0.0, neginf=0.0)

    return {
        "window_ms": window_ms,
        "effective_ms": round(effective_ms, 2),
        "n_samples": n_win_samples,
        "alignment": alignment,
        "onset_sample": onset_sample,
        "onset_ms": round(onset_sample / SAMPLING_RATE * 1000, 2),
        "trial_metadata": {
            "target_angle_deg": trial.target_angle_deg,
            "direction_label_8": trial.direction_label_8,
            "target_horizontal_deg": trial.target_horizontal_deg,
            "target_vertical_deg": trial.target_vertical_deg,
        },
        "full_signal": full_signal[:MAX_VIS_SAMPLES],
        "full_time_ms": full_time_ms[:MAX_VIS_SAMPLES],
        "window_data": {str(ch): window[ch].tolist() for ch in range(min(4, window.shape[0]))},
        "n_features": len(features),
    }


@router.get("/subjects/{subject_id}/trials/{trial_id}/processing")
def get_signal_processing(
    subject_id: str,
    trial_id: int,
    baseline_correct: bool = Query(True),
    detrend: bool = Query(False),
    highpass: bool = Query(False),
    normalize: bool = Query(False),
):
    """Get raw vs processed signal comparison for a trial."""
    loader = get_loader()
    if subject_id not in loader.subject_ids:
        raise HTTPException(404, f"Subject {subject_id} not found")

    trials = segment_trials(loader, subject_id)
    if trial_id < 0 or trial_id >= len(trials):
        raise HTTPException(404, f"Trial {trial_id} not found")

    trial = trials[trial_id]
    eog_raw = get_trial_eog(loader, trial, phase="outward")

    config = PreprocessingConfig(
        baseline_correction=baseline_correct,
        detrend=detrend,
        highpass_filter=highpass,
        normalize=normalize,
    )
    eog_proc = preprocess_trial(eog_raw, config)

    # Onset detection on processed signal
    onset_result = detect_onset(eog_proc, OnsetConfig())

    # Use first 4 channels for visualization
    n_vis_ch = min(4, eog_raw.shape[0])
    time_ms = (np.arange(eog_raw.shape[1]) / SAMPLING_RATE * 1000).tolist()

    raw_data = {str(i): eog_raw[i].tolist() for i in range(n_vis_ch)}
    proc_data = {str(i): eog_proc[i].tolist() for i in range(n_vis_ch)}

    return {
        "subject_id": subject_id,
        "trial_id": trial_id,
        "n_channels_shown": n_vis_ch,
        "n_samples": eog_raw.shape[1],
        "time_ms": time_ms,
        "raw_data": raw_data,
        "processed_data": proc_data,
        "onset": {
            "onset_sample": onset_result.onset_sample,
            "onset_ms": onset_result.onset_ms,
            "reliable": onset_result.reliable,
            "reason": onset_result.reason,
            "aggregate_signal": onset_result.aggregate_signal.tolist(),
            "derivative_signal": onset_result.derivative_signal.tolist(),
            "threshold": onset_result.threshold_used,
        },
        "preprocessing_config": config.to_dict(),
    }

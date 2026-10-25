"""
Tests for Signal Preprocessor
"""
import numpy as np
import pytest
from app.signal_processing.preprocessor import (
    preprocess_trial, PreprocessingConfig, compute_normalization_params
)

def test_baseline_correction():
    # 2 channels, 100 samples with non-zero offset
    raw = np.ones((2, 100)) * 5.0
    # Add random signal
    raw += np.random.normal(0, 0.1, (2, 100))
    cfg = PreprocessingConfig(baseline_correction=True, baseline_samples=20, detrend=False, highpass_filter=False, normalize=False)
    processed = preprocess_trial(raw, cfg)
    # The mean of the first 20 samples should be approximately 0
    assert np.allclose(processed[:, :20].mean(axis=1), [0.0, 0.0], atol=1e-10)

def test_normalization_and_leakage():
    # Generate 2 simulated trials
    t1 = np.random.normal(10, 2, (2, 50))
    t2 = np.random.normal(20, 5, (2, 50))
    
    # Compute params on t1 only
    params = compute_normalization_params([t1])
    assert "mean" in params and "std" in params
    assert params["mean"].shape == (2, 1)
    
    cfg = PreprocessingConfig(baseline_correction=False, normalize=True)
    proc_t2 = preprocess_trial(t2, cfg, normalization_params=params)
    assert proc_t2.shape == t2.shape

def test_causal_vs_offline_mode():
    np.random.seed(42)
    sig_data = np.random.randn(2, 200)
    
    cfg_causal = PreprocessingConfig(highpass_filter=True, causal_mode=True)
    cfg_offline = PreprocessingConfig(highpass_filter=True, causal_mode=False)
    
    proc_causal = preprocess_trial(sig_data, cfg_causal)
    proc_offline = preprocess_trial(sig_data, cfg_offline)
    
    assert proc_causal.shape == sig_data.shape
    assert proc_offline.shape == sig_data.shape
    # Causal and offline filtering should produce slightly different results due to phase shifts
    assert not np.allclose(proc_causal, proc_offline)

"""
Tests for Saccade Onset Detector
"""
import numpy as np
from app.signal_processing.onset_detector import detect_onset, OnsetConfig

def test_detect_onset_synthetic_saccade():
    # Construct a synthetic signal: 50 samples quiet baseline, followed by sharp saccade
    n_samples = 200
    n_channels = 4
    eog = np.random.normal(0, 0.05, (n_channels, n_samples))
    
    # Inject a large step at sample 60
    eog[:, 60:] += 5.0
    
    cfg = OnsetConfig(baseline_samples=30, threshold_factor=4.0, min_persistence=3)
    res = detect_onset(eog, cfg)
    
    assert res.reliable is True
    assert res.onset_sample is not None
    # Onset should be detected close to sample 60 (between 58 and 65)
    assert 55 <= res.onset_sample <= 65
    assert res.onset_ms is not None

def test_detect_onset_no_movement():
    # Pure flat noise
    eog = np.random.normal(0, 0.01, (4, 150))
    cfg = OnsetConfig(baseline_samples=30, threshold_factor=10.0)
    res = detect_onset(eog, cfg)
    
    # Should not find a sustained crossing
    assert res.reliable is False
    assert res.onset_sample is None

def test_detect_onset_short_signal():
    eog = np.zeros((4, 4))
    res = detect_onset(eog)
    assert res.reliable is False
    assert "too short" in res.reason.lower()

"""
Tests for Window Generator
"""
import numpy as np
import pytest
from app.features.window_generator import (
    ms_to_samples, samples_to_ms, get_window_specs,
    extract_early_window, generate_all_windows
)

def test_ms_to_samples_at_256hz():
    # 20ms * 256 / 1000 = 5.12 -> ceil is 6
    assert ms_to_samples(20.0, 256) == 6
    # 40ms * 256 / 1000 = 10.24 -> ceil is 11
    assert ms_to_samples(40.0, 256) == 11
    # 100ms * 256 / 1000 = 25.6 -> ceil is 26
    assert ms_to_samples(100.0, 256) == 26

def test_samples_to_ms():
    assert pytest.approx(samples_to_ms(6, 256), 0.01) == 23.4375
    assert pytest.approx(samples_to_ms(11, 256), 0.01) == 42.96875

def test_window_specs():
    specs = get_window_specs([20, 40, 60, 80, 100])
    assert len(specs) == 5
    assert specs[0].requested_ms == 20
    assert specs[0].n_samples == 6
    assert specs[0].effective_ms > 20

def test_extract_early_window():
    data = np.arange(100).reshape(1, 100)
    
    # Extract 10 samples from onset=20
    w = extract_early_window(data, onset_sample=20, n_window_samples=10, alignment="onset")
    assert w is not None
    assert w.shape == (1, 10)
    assert w[0, 0] == 20
    assert w[0, -1] == 29

    # Insufficient samples (no padding)
    w_overflow = extract_early_window(data, onset_sample=95, n_window_samples=10, alignment="onset")
    assert w_overflow is None

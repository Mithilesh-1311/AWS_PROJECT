"""
Tests for Feature Extractor
"""
import numpy as np
from app.features.feature_extractor import (
    extract_features_single_channel, extract_features, FeatureConfig
)

def test_extract_features_single_channel():
    sig = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    feats = extract_features_single_channel(sig)
    
    assert feats["voltage_change"] == 4.0
    assert feats["mean"] == 3.0
    assert feats["min"] == 1.0
    assert feats["max"] == 5.0
    assert feats["range"] == 4.0
    assert feats["slope"] == 1.0
    assert feats["mean_derivative"] == 1.0

def test_extract_features_multi_channel():
    # 16 channels, 10 samples
    window = np.random.randn(16, 10)
    cfg = FeatureConfig()
    feat_vec = extract_features(window, cfg)
    
    assert isinstance(feat_vec, np.ndarray)
    assert feat_vec.ndim == 1
    assert len(feat_vec) > 0
    assert not np.isnan(feat_vec).any()

def test_extract_features_channel_selection():
    window = np.random.randn(16, 10)
    cfg_all = FeatureConfig(channels=None)
    cfg_subset = FeatureConfig(channels=[0, 1, 2, 3])
    
    vec_all = extract_features(window, cfg_all)
    vec_subset = extract_features(window, cfg_subset)
    
    assert len(vec_subset) < len(vec_all)

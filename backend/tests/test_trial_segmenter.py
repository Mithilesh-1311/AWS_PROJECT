"""
Tests for TrialSegmenter and Label Generation
"""
import pytest
import numpy as np
from app.data.trial_segmenter import (
    _find_segments, _angle_to_bin, get_direction_label_name,
    segment_trials, get_trial_eog
)
from app.data.dataset_loader import DatasetLoader
from app.core.config import DATASET_ROOT

def test_find_segments():
    cs = np.array([0, 1, 1, 1, 0, 2, 2, 0, 1, 1, 0])
    segs = _find_segments(cs, 1)
    assert segs == [(1, 4), (8, 10)]

def test_angle_to_bin_4_classes():
    # 4 classes: Right(0), Up(1), Left(2), Down(3)
    # Bin width 90 deg: Right is [-45, 45) -> 315-45
    assert _angle_to_bin(0.0, 4) == 0
    assert _angle_to_bin(10.0, 4) == 0
    assert _angle_to_bin(350.0, 4) == 0
    assert _angle_to_bin(90.0, 4) == 1
    assert _angle_to_bin(85.0, 4) == 1
    assert _angle_to_bin(180.0, 4) == 2
    assert _angle_to_bin(270.0, 4) == 3

def test_angle_to_bin_8_classes():
    # 8 classes: 45 deg bins
    # Right=0, Up-Right=1, Up=2, Up-Left=3, Left=4, Down-Left=5, Down=6, Down-Right=7
    assert _angle_to_bin(0.0, 8) == 0
    assert _angle_to_bin(45.0, 8) == 1
    assert _angle_to_bin(90.0, 8) == 2
    assert _angle_to_bin(135.0, 8) == 3
    assert _angle_to_bin(180.0, 8) == 4
    assert _angle_to_bin(225.0, 8) == 5
    assert _angle_to_bin(270.0, 8) == 6
    assert _angle_to_bin(315.0, 8) == 7

def test_direction_label_names():
    assert get_direction_label_name(0, 4) == "Right"
    assert get_direction_label_name(1, 4) == "Up"
    assert get_direction_label_name(0, 8) == "Right"
    assert get_direction_label_name(1, 8) == "Up-Right"
    assert get_direction_label_name(2, 8) == "Up"
    assert get_direction_label_name(4, 8) == "Left"
    assert get_direction_label_name(6, 8) == "Down"

def test_segment_trials_real():
    if not DATASET_ROOT or not DATASET_ROOT.exists():
        pytest.skip("Dataset root not found")
    loader = DatasetLoader(DATASET_ROOT)
    trials = segment_trials(loader, "S1")
    assert len(trials) == 288
    # Test trial properties
    t0 = trials[0]
    assert t0.outward_start < t0.outward_end
    assert t0.outward_end <= t0.return_start
    assert t0.return_end <= t0.blink_start
    assert t0.direction_label_8 in range(8)
    assert t0.direction_label_4 in range(4)
    assert t0.direction_label_36 in range(36)

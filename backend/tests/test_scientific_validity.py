import numpy as np
import pytest
from app.features.window_generator import ms_to_samples, extract_early_window
from app.features.feature_extractor import FeatureConfig, extract_features
from app.signal_processing.causal import CausalProcessor
from app.data.trial_segmenter import segment_trials


@pytest.mark.parametrize("value", [0, -1, float("nan"), float("inf")])
def test_invalid_durations(value):
    with pytest.raises(ValueError):
        ms_to_samples(value)


def test_feature_flags_and_physical_version():
    window = np.tile(np.arange(6), (2, 1)).astype(float)
    config = FeatureConfig(include_cross_channel=False, include_stats=False,
                           include_derivative=False, include_energy=False)
    np.testing.assert_equal(extract_features(window, config), [5, 5])
    full = extract_features(window, FeatureConfig(include_cross_channel=False))
    physical = extract_features(window, FeatureConfig(include_cross_channel=False, version="physical-v2"))
    assert physical[6] == pytest.approx(full[6] * 256)
    with pytest.raises(ValueError):
        extract_early_window(window, 0, 0)


def feed(values, chunk_size):
    p = CausalProcessor(20, n_channels=2)
    for i in range(0, values.shape[1], chunk_size):
        p.push(values[:, i:i + chunk_size], i)
    return p


def test_chunk_equivalence_and_no_future_dependence():
    rng = np.random.default_rng(42)
    values = rng.normal(0, 0.001, (2, 120))
    values[:, 40:] += np.arange(80) * 10
    a, b = feed(values, 1), feed(values, 17)
    assert a.result is not None
    np.testing.assert_allclose(a.result["window"], b.result["window"])
    assert a.result["confirmation_sample"] == a.result["crossing_sample"] + 2
    assert a.result["ready_sample"] >= a.result["confirmation_sample"]
    cutoff = a.result["ready_sample"]
    changed = values.copy()
    changed[:, cutoff + 1:] = 1e8
    c = feed(changed, 13)
    np.testing.assert_allclose(a.result["window"], c.result["window"])
    assert c.result["ready_sample"] == cutoff
    with pytest.raises(ValueError, match="Gap"):
        c.push(values[:, :1], 0)


def test_calibration_has_visible_delay():
    p = CausalProcessor(20, "cue", 2)
    p.push(np.ones((2, 6)), 0)
    assert p.status() == "calibrating" and p.result is None
    p.push(np.ones((2, 19)), 6)
    assert p.result["ready_sample"] == 24


@pytest.mark.parametrize("cs", [[1, 1, 3, 3, 2, 2], [1, 2], [1, 30, 2, 3], [1, 2, 3, 9]])
def test_malformed_phases_rejected(cs):
    class Loader:
        def get_control_signal(self, sid): return np.asarray(cs)
        def get_target_ga_stream(self, sid): return np.ones((2, len(cs)))
        def get_eog(self, sid): return np.ones((16, len(cs)))
    with pytest.raises(ValueError):
        segment_trials(Loader(), "S1")

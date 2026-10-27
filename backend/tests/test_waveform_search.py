import numpy as np
import pytest

from app.features.feature_extractor import FeatureConfig, extract_features
from scripts import tune_waveform
from scripts.verify_artifacts import verify_selection


def test_waveform_views_preserve_input_and_normalized_scale():
    rng = np.random.default_rng(7)
    window = rng.normal(size=(16, 103))
    def features(signal):
        return np.r_[extract_features(signal, FeatureConfig(version='physical-v2')), tune_waveform.time_bins(signal)][None, :]
    x = features(window)
    original = x.copy()
    for view in tune_waveform.VIEWS:
        result = tune_waveform.feature_view(x, view)
        assert result.shape == (1, 468 if view == 'hybrid' else 256)
        assert np.isfinite(tune_waveform.feature_view(np.zeros_like(x), view)).all()
        if view != 'wave':
            np.testing.assert_allclose(result, tune_waveform.feature_view(features(window * 7), view), atol=1e-10)
    np.testing.assert_array_equal(x, original)
    with pytest.raises(ValueError):
        tune_waveform.time_bins(window[:, :4])


def test_waveform_selection_preserves_subject_separation(monkeypatch):
    groups = np.repeat(['S1', 'S2', 'S3', 'S4'], 16)
    y = np.tile(np.arange(8), 8)
    x = np.random.default_rng(1).normal(size=(64, 468))
    configs = [dict(family='rbf_svm', C=1., gamma='scale', view=view) for view in tune_waveform.VIEWS[:3]]
    monkeypatch.setattr(tune_waveform, 'CANDIDATES', configs)
    selected, members, record = tune_waveform.select_candidates(x, y, groups)
    assert selected == max(record['candidates'], key=lambda item: item['macro_f1'])['config']
    assert len(members) == 3 and len({item['view'] for item in members}) == 3
    verify_selection(dict(train_subjects=sorted(set(groups)), test_subjects=['S5'], inner_selection=record))
    for config in tune_waveform.CANDIDATES:
        assert tune_waveform.create_candidate(config).fit(x, y).predict(x).shape == y.shape

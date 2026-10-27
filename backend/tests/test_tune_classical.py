import numpy as np
import pytest
from scripts.tune_classical import CANDIDATES, create_candidate, select_candidate
from scripts import tune_classical
from scripts.verify_artifacts import verify_selection
from app.features.feature_extractor import FeatureConfig, extract_features


def test_inner_selection_refits_and_records_disjoint_subjects():
    rng = np.random.default_rng(42)
    groups = np.repeat(["S1", "S2", "S3"], 32)
    y = np.tile(np.arange(8), 12)
    x = np.eye(8)[y] + rng.normal(0, .02, (96, 8))
    selected, record = select_candidate(x, y, groups)
    assert selected in CANDIDATES
    assert record["train_subjects"] == ["S1", "S2"]
    assert record["validation_subjects"] == ["S3"]
    assert len(record["candidates"]) == 9
    assert all(item["balanced_accuracy"] == 1 for item in record["candidates"])
    model = create_candidate(selected).fit(x, y)
    assert np.array_equal(model.predict(x), y)
    with pytest.raises(ValueError, match="at least two"):
        select_candidate(x[:32], y[:32], groups[:32])


def test_normalization_preserves_amplitude_invariance_and_input():
    signal = np.random.default_rng(42).normal(size=(16, 26))
    config = FeatureConfig(version="physical-v2")
    x = extract_features(signal, config)[None, :]
    scaled = extract_features(signal * 7, config)[None, :]
    original = x.copy()
    for mode, count in [("normalized_all", 212), ("normalized_spatial", 96), ("normalized_directional", 64)]:
        expected = tune_classical.transform_features(x, mode)
        assert expected.shape == (1, count)
        np.testing.assert_allclose(expected, tune_classical.transform_features(scaled, mode), atol=1e-10)
        assert np.isfinite(tune_classical.transform_features(np.zeros_like(x), mode)).all()
    assert np.array_equal(x, original)
    with pytest.raises(ValueError, match="212-feature"):
        tune_classical.transform_features(x[:, :20], "normalized_all")


def test_grouped_selection_covers_each_training_subject_and_rejects_leakage(monkeypatch):
    monkeypatch.setattr(tune_classical, "GROUPED_CANDIDATES", CANDIDATES[:2])
    groups = np.repeat(["S1", "S2", "S3", "S4"], 16)
    y = np.tile(np.arange(8), 8)
    x = np.eye(8)[y]
    selected, selection = select_candidate(x, y, groups, "grouped")
    assert selected in CANDIDATES[:2]
    assert len(selection['folds']) == 3
    assert all(set(item['subject_scores']) == set(groups) for item in selection['candidates'])
    fold = dict(train_subjects=sorted(set(groups)), test_subjects=['S5'], inner_selection=selection)
    verify_selection(fold)
    selection['folds'][0]['validation_subjects'].append('S5')
    with pytest.raises(AssertionError):
        verify_selection(fold)


def test_macro_candidates_and_subject_held_out_selection(monkeypatch):
    rng = np.random.default_rng(12)
    groups = np.repeat(["S1", "S2", "S3", "S4"], 24)
    y = np.tile(np.arange(8), 12)
    x = rng.normal(0, .01, (96, 212))
    x[:, :8] += np.eye(8)[y]
    for config in tune_classical.MACRO_CANDIDATES:
        model = create_candidate(config).fit(x, y)
        assert model.predict(x).shape == y.shape
    monkeypatch.setattr(tune_classical, "MACRO_CANDIDATES", CANDIDATES[:2])
    selected, selection = select_candidate(x, y, groups, "macro")
    assert selected in CANDIDATES[:2]
    assert "macro_f1" in selection["scoring"]
    assert all("macro_f1" in item and set(item["subject_scores"]) == set(groups) for item in selection["candidates"])
    verify_selection(dict(train_subjects=sorted(set(groups)), test_subjects=["S5"], inner_selection=selection))

from types import SimpleNamespace
import numpy as np
from app.evaluation import reproducible as evaluation
from app.features.feature_extractor import FeatureConfig, extract_features, get_feature_names


def test_matched_folds_use_same_train_and_test_trials(tmp_path, monkeypatch):
    groups = np.repeat(['S1', 'S2', 'S3'], 16)
    ids = np.array([f'{sid}:{i}' for sid in ['S1','S2','S3'] for i in range(16)])
    y = np.tile(np.arange(8), 6)
    x = np.random.default_rng(42).normal(size=(48, 3))
    row = dict(X=x, y=y, groups=groups, ids=ids, ready_ms=np.ones(48))
    reference = {name: values[1:] for name, values in row.items()}
    data = dict(windows={'20':row, '400':reference}, exclusions=[], source_counts={s:16 for s in ['S1','S2','S3']}, feature_runtime_seconds=0)
    monkeypatch.setattr(evaluation, 'EXPERIMENTS_DIR', tmp_path)
    monkeypatch.setattr(evaluation, 'get_loader', lambda: SimpleNamespace(subject_ids=['S1','S2','S3']))
    monkeypatch.setattr(evaluation, 'dataset_manifest', lambda *a: {'files':{},'fingerprint':'fixture'})
    monkeypatch.setattr(evaluation, 'prepare_data', lambda *a: data)
    result = evaluation.run_causal(models=['logistic_regression'], windows=[20,400], evaluation='loso', matched_reference=True)
    for short, long in zip(result['results'][0]['folds'], result['results'][1]['folds']):
        assert short['trial_ids'] == long['trial_ids']
        assert short['n_train'] == long['n_train']
        assert not set(short['train_subjects']) & set(short['test_subjects'])
    assert len(row['ids']) == 48  # Matching never mutates the all-eligible cache.
    assert result['results'][0]['coverage'] == 47 / 48
    c, selection = evaluation.select_logistic(row, groups != 'S3')
    assert c in [.1, 1.0]
    assert selection['validation_subjects'] == ['S2']
    assert selection['train_subjects'] == ['S1']


def test_feature_names_follow_flags_and_selected_channel_order():
    config = FeatureConfig(channels=[2,0], include_stats=False, include_energy=False, version='physical-v2')
    x = np.random.default_rng(42).normal(size=(3,26))
    names = get_feature_names(3, config=config)
    assert len(names) == len(extract_features(x, config))
    assert names[0] == 'ch2_voltage_change'
    assert 'ch0_mean' not in names

"""Nested subject-held-out 400 ms search using the observed waveform's time course."""
import argparse
import hashlib
import importlib.metadata
import json
import uuid
from datetime import datetime, timezone
from time import perf_counter

import joblib
import numpy as np
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import FunctionTransformer
from threadpoolctl import threadpool_limits

from app.core.config import CACHE_DIR, DIRECTION_LABELS_8, EXPERIMENTS_DIR
from app.data.dataset_loader import get_loader
from app.data.trial_segmenter import get_trial_eog, segment_trials
from app.evaluation.reproducible import WINDOWS, checksum, dataset_manifest, metrics, prepare_data, subject_interval, write_json
from app.signal_processing.causal import VERSION, causal_window
from scripts import tune_classical
from scripts.ensemble_selected import majority_vote

VIEWS = ['wave', 'unit_wave', 'contrast_wave', 'hybrid']
CANDIDATES = [
    *[dict(family='rbf_svm', C=c, gamma='scale', view=view) for view in VIEWS for c in [1., 10., 100.]],
    dict(family='logistic', C=.1, view='hybrid'),
    dict(family='lda', shrinkage='auto', view='hybrid'),
    *[dict(family='poly_svm', C=1., degree=2, view=view) for view in ['unit_wave', 'contrast_wave']],
]


def time_bins(window):
    if window.ndim != 2 or window.shape[0] != 16 or window.shape[1] < 16 or not np.isfinite(window).all():
        raise ValueError('Expected a finite 16-channel window with at least 16 samples')
    return np.stack([part.mean(axis=1) for part in np.array_split(window, 16, axis=1)], axis=1).ravel()


def feature_view(x, view):
    if x.ndim != 2 or x.shape[1] != 468 or not np.isfinite(x).all() or view not in VIEWS:
        raise ValueError('Expected finite 212 physical + 256 temporal features and a supported view')
    wave = x[:, 212:].reshape(-1, 16, 16).copy()
    if view == 'wave':
        return wave.reshape(-1, 256)
    if view == 'contrast_wave':
        wave -= wave.mean(axis=1, keepdims=True)
    scale = np.maximum(np.sqrt(np.mean(wave ** 2, axis=(1, 2))), 1e-12)
    wave = (wave / scale[:, None, None]).reshape(-1, 256)
    if view == 'hybrid':
        return np.concatenate([tune_classical.transform_features(x[:, :212], 'normalized_all'), wave], axis=1)
    return wave


def create_candidate(config):
    return make_pipeline(FunctionTransformer(feature_view, kw_args={'view': config['view']}),
                         tune_classical.create_candidate(config))


def prepare_waveforms(loader, dataset):
    key = hashlib.sha256((dataset['fingerprint'] + VERSION + 'timecourse-v1-400').encode()).hexdigest()
    path = CACHE_DIR / f'waveform_{key}.joblib'
    if path.exists():
        return joblib.load(path)
    original = prepare_data(loader.subject_ids, WINDOWS, dataset['fingerprint'])['windows']['400']
    physical = dict(zip(original['ids'], original['X']))
    rows, actual, groups, ids = [], [], [], []
    for sid in loader.subject_ids:
        for trial in segment_trials(loader, sid):
            tid = f'{sid}:{trial.trial_id}'
            observation = causal_window(get_trial_eog(loader, trial, 'outward'), 400)
            if observation is None:
                assert tid not in physical
                continue
            rows.append(np.concatenate([physical[tid], time_bins(observation['window'])]))
            actual.append(trial.direction_label_8)
            groups.append(sid)
            ids.append(tid)
        loader.release_subject(sid)
        print(f'Waveforms: {sid}', flush=True)
    data = dict(X=np.asarray(rows), y=np.asarray(actual), groups=np.asarray(groups), ids=np.asarray(ids))
    assert data['ids'].tolist() == original['ids'].tolist()
    np.testing.assert_array_equal(data['y'], original['y'])
    temporary = path.with_suffix('.tmp')
    joblib.dump(data, temporary)
    temporary.replace(path)
    return data


def select_candidates(x, y, groups):
    if len(set(groups)) < 3:
        raise ValueError('Three training subjects are required')
    splits = list(GroupKFold(3).split(x, y, groups))
    scores = []
    for config in CANDIDATES:
        subject_scores = {}
        for train, validation in splits:
            prediction = create_candidate(config).fit(x[train], y[train]).predict(x[validation])
            for sid in sorted(set(groups[validation])):
                mask = groups[validation] == sid
                subject_scores[sid] = metrics(y[validation][mask], prediction[mask])['macro_f1']
        scores.append(dict(config=config, macro_f1=float(np.mean(list(subject_scores.values()))), subject_scores=subject_scores))
    ranked = sorted(scores, key=lambda item: item['macro_f1'], reverse=True)
    members, seen = [], set()
    for item in ranked:
        if item['config']['view'] not in seen:
            members.append(item['config'])
            seen.add(item['config']['view'])
        if len(members) == 3:
            break
    if len(members) != 3:
        raise ValueError('Three waveform views are required for the vote')
    selection = dict(folds=[dict(train_subjects=sorted(set(groups[t])), validation_subjects=sorted(set(groups[v]))) for t, v in splits],
                     candidates=scores, selected=ranked[0]['config'], members=members,
                     scoring='mean per-subject macro_f1 over three grouped folds')
    return ranked[0]['config'], members, selection


def run(resume=None):
    loader = get_loader()
    subjects = loader.subject_ids
    if len(subjects) != 14:
        raise ValueError('Full waveform evaluation requires all 14 subjects')
    dataset = dataset_manifest(loader, subjects)
    eid = resume or uuid.uuid4().hex
    if not eid.isalnum() or len(eid) > 64:
        raise ValueError('Invalid experiment ID')
    folder = EXPERIMENTS_DIR / eid
    config = dict(subjects=subjects, windows=[400], models=['waveform_search', 'waveform_top3_vote'],
                  evaluation='loso', smoke=False, candidates=CANDIDATES, seed=42, preprocessing_version=VERSION,
                  feature_version='timecourse-v1', selection_policy='three inner grouped folds select by mean subject macro F1; outer subjects never select settings',
                  script_sha256=checksum(__file__), candidate_helper_sha256=checksum(tune_classical.__file__))
    report = dict(experiment_id=eid, config=config, dataset=dataset, class_names=DIRECTION_LABELS_8,
                  timestamp=datetime.now(timezone.utc).isoformat(), status='running',
                  versions={name: importlib.metadata.version(name) for name in ['numpy', 'scipy', 'scikit-learn', 'joblib']})
    manifest = folder / 'manifest.json'
    if manifest.exists():
        old = json.loads(manifest.read_text())
        if old['config'] != config or old['dataset'] != dataset:
            raise ValueError('Resume provenance mismatch')
        if old['status'] == 'complete':
            return old
        report = old
    write_json(manifest, report)
    print('Waveform experiment:', eid, flush=True)
    data = prepare_waveforms(loader, dataset)
    source_counts = {sid: len(segment_trials(loader, sid)) for sid in subjects}
    started = perf_counter()
    folds = []
    with threadpool_limits(limits=1):
        for index, sid in enumerate(subjects):
            path = folder / f'waveform_400_fold{index}.json'
            if path.exists():
                fold = json.loads(path.read_text())
            else:
                test = data['groups'] == sid
                train = ~test
                selected, members, selection = select_candidates(data['X'][train], data['y'][train], data['groups'][train])
                configs = [selected, *[item for item in members if item != selected]]
                fitted = [create_candidate(item).fit(data['X'][train], data['y'][train]) for item in configs]
                predictions = [model.predict(data['X'][test]) for model in fitted]
                voted = majority_vote([predictions[configs.index(item)] for item in members])
                fold = dict(test_subjects=[sid], train_subjects=sorted(set(data['groups'][train])),
                            trial_ids=data['ids'][test].tolist(), y_true=data['y'][test].tolist(),
                            y_pred=predictions[0].tolist(), vote_pred=voted.tolist(),
                            n_train=int(train.sum()), n_test=int(test.sum()), inner_selection=selection,
                            metrics=metrics(data['y'][test], predictions[0]))
                write_json(path, fold)
            folds.append(fold)
            print(f"Waveform {index+1}/14 {sid}: accuracy={fold['metrics']['accuracy']:.4f}", flush=True)
    results = []
    for name, key in [('waveform_search', 'y_pred'), ('waveform_top3_vote', 'vote_pred')]:
        output_folds = [dict(fold, y_pred=fold[key], metrics=metrics(np.asarray(fold['y_true']), np.asarray(fold[key]))) for fold in folds]
        actual = np.asarray([value for fold in output_folds for value in fold['y_true']])
        prediction = np.asarray([value for fold in output_folds for value in fold['y_pred']])
        result = dict(model_name=name, window_ms=400, n_samples=103, folds=output_folds, metrics=metrics(actual, prediction),
                      n_predictions=len(actual), eligible_trials=len(actual), source_test_trials=sum(source_counts.values()),
                      coverage=len(actual)/sum(source_counts.values()), subject_accuracy_interval=subject_interval(output_folds))
        results.append(result)
        print(f"RESULT {name}: accuracy={result['metrics']['accuracy']:.6f} F1={result['metrics']['macro_f1']:.6f}", flush=True)
    report.update(status='complete', results=results, total_source_trials=sum(source_counts.values()),
                  exclusion_count=sum(source_counts.values())-len(data['y']), runtime_seconds=perf_counter()-started,
                  serving_policy='comparison experiment; active serving model unchanged')
    write_json(manifest, report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--resume')
    run(parser.parse_args().resume)

"""Fixed three-member vote chosen from completed inner-CV scores, never outer scores."""
import argparse
from copy import deepcopy
import json
import uuid
from datetime import datetime, timezone
from time import perf_counter

import numpy as np
from threadpoolctl import threadpool_limits

from app.core.config import EXPERIMENTS_DIR
from app.data.dataset_loader import get_loader
from app.evaluation.reproducible import WINDOWS, checksum, dataset_manifest, metrics, prepare_data, subject_interval, write_json
from scripts.tune_classical import create_candidate


def select_members(candidates, scoring="balanced_accuracy"):
    members, seen = [], set()
    for item in sorted(candidates, key=lambda item: item[scoring], reverse=True):
        features = item['config'].get('features', 'all')
        if features not in seen:
            members.append(item['config'])
            seen.add(features)
        if len(members) == 3:
            return members
    raise ValueError('Three distinct feature representations are required')


def majority_vote(predictions):
    predictions = np.asarray(predictions)
    if predictions.ndim != 2 or predictions.shape[0] != 3:
        raise ValueError('Expected three ordered member prediction arrays')
    counts = (predictions[:, None, :] == predictions[None, :, :]).sum(axis=1)
    # Equal votes resolve to the highest inner-CV-ranked member, not a fixed class.
    return predictions[np.argmax(counts, axis=0), np.arange(predictions.shape[1])]


def run(source_id):
    if not source_id.isalnum() or len(source_id) > 64:
        raise ValueError('Invalid source experiment ID')
    source_path = EXPERIMENTS_DIR / source_id / 'manifest.json'
    source = json.loads(source_path.read_text())
    if source['status'] != 'complete' or source['config'].get('search') not in {'grouped', 'macro'}:
        raise ValueError('A completed grouped feature search is required')
    loader = get_loader()
    if dataset_manifest(loader, source['config']['subjects']) != source['dataset']:
        raise ValueError('Source recordings changed')
    data = prepare_data(source['config']['subjects'], source['config']['windows'] if source['config']['search'] == 'macro' else WINDOWS, source['dataset']['fingerprint'])
    report = deepcopy(source)
    eid = uuid.uuid4().hex
    folder = EXPERIMENTS_DIR / eid
    report.update(experiment_id=eid, timestamp=datetime.now(timezone.utc).isoformat(), status='running', results=[])
    report['config'].update(models=['grouped_top3_vote'], source_experiment_id=source_id,
                            source_manifest_sha256=checksum(source_path), script_sha256=checksum(__file__),
                            selection_policy='fixed majority vote of three inner-CV-ranked distinct feature representations; ties use highest-ranked member')
    write_json(folder / 'manifest.json', report)
    print('Experiment:', eid, flush=True)
    started = perf_counter()
    with threadpool_limits(limits=1):
        for original in source['results']:
            ms = original['window_ms']
            row = data['windows'][str(ms)]
            folds = []
            for index, original_fold in enumerate(original['folds']):
                fold = deepcopy(original_fold)
                test = np.isin(row['groups'], fold['test_subjects'])
                train = ~test
                if row['ids'][test].tolist() != fold['trial_ids']:
                    raise ValueError('Trial identity mismatch')
                members = select_members(fold['inner_selection']['candidates'], source['config'].get('inner_score', 'balanced_accuracy'))
                fit_started = perf_counter()
                models = [create_candidate(config).fit(row['X'][train], row['y'][train]) for config in members]
                fold['fit_seconds'] = perf_counter() - fit_started
                prediction = majority_vote([model.predict(row['X'][test]) for model in models])
                fold['inner_selection']['selected'] = members
                fold.update(y_pred=prediction.tolist(), metrics=metrics(row['y'][test], prediction))
                write_json(folder / f'grouped_top3_vote_{ms}_fold{index}.json', fold)
                folds.append(fold)
            true = np.array([value for fold in folds for value in fold['y_true']])
            prediction = np.array([value for fold in folds for value in fold['y_pred']])
            result = deepcopy(original)
            result.update(model_name='grouped_top3_vote', folds=folds, metrics=metrics(true, prediction),
                          subject_accuracy_interval=subject_interval(folds))
            report['results'].append(result)
            print(f"RESULT {ms}ms accuracy={result['metrics']['accuracy']:.6f} F1={result['metrics']['macro_f1']:.6f}", flush=True)
    report.update(status='complete', runtime_seconds=perf_counter()-started,
                  serving_policy='exploratory comparison only; active serving model unchanged')
    write_json(folder / 'exclusions.json', [item for item in data['exclusions'] if item['window_ms'] in source['config']['windows']])
    write_json(folder / 'manifest.json', report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source_id')
    run(parser.parse_args().source_id)

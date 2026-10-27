"""Check real source schema/checksums and published split/prediction invariants."""
import json
import numpy as np
from app.core.config import PUBLISHED_DIR
from app.data.dataset_loader import get_loader
from app.data.trial_segmenter import segment_trials
from app.evaluation.reproducible import dataset_manifest, metrics


def verify_result_metrics(result):
    actual, predicted = [], []
    for fold in result['folds']:
        for key, value in metrics(np.asarray(fold['y_true']), np.asarray(fold['y_pred'])).items():
            np.testing.assert_allclose(fold['metrics'][key], value, rtol=0, atol=1e-12,
                                       err_msg=f"Saved fold {key} disagrees with predictions")
        actual.extend(fold['y_true'])
        predicted.extend(fold['y_pred'])
    assert len(actual) == result['n_predictions']
    for key, value in metrics(np.asarray(actual), np.asarray(predicted)).items():
        np.testing.assert_allclose(result['metrics'][key], value, rtol=0, atol=1e-12,
                                   err_msg=f"Saved pooled {key} disagrees with predictions")


def verify_selection(fold):
    selection = fold.get('inner_selection')
    if selection:
        inner_folds = selection.get('folds', [selection])
        assert inner_folds
        for inner in inner_folds:
            training = set(inner['train_subjects'])
            validation = set(inner['validation_subjects'])
            assert training and validation and not training & validation
            assert training | validation <= set(fold['train_subjects'])
            assert not (training | validation) & set(fold['test_subjects'])
        if 'folds' in selection:
            subjects = [sid for inner in inner_folds for sid in inner['validation_subjects']]
            assert len(subjects) == len(set(subjects))
            assert set(subjects) == set(fold['train_subjects'])
    if 'inner_validation_subject' in fold:
        assert fold['inner_validation_subject'] in fold['train_subjects']
        assert fold['inner_validation_subject'] not in fold['test_subjects']


def main():
    loader = get_loader()
    counts = {sid: loader.get_subject_metadata(sid).n_trials for sid in loader.subject_ids}
    assert len(counts) == 14 and sum(counts.values()) == 4032
    dataset = dataset_manifest(loader, loader.subject_ids)
    targets = {}
    for sid in loader.subject_ids:
        targets.update({f'{sid}:{trial.trial_id}': trial.direction_label_8 for trial in segment_trials(loader, sid)})
        loader.release_subject(sid)
    reports = []
    for path in PUBLISHED_DIR.glob('*.json'):
        report = json.loads(path.read_text(encoding='utf-8'))
        assert report['dataset'] == dataset
        for result in report['results']:
            verify_result_metrics(result)
            seen = set()
            for fold in result['folds']:
                assert not set(fold['train_subjects']) & set(fold['test_subjects'])
                assert len(fold['trial_ids']) == len(fold['y_true']) == len(fold['y_pred']) == fold['n_test']
                assert [targets[tid] for tid in fold['trial_ids']] == fold['y_true']
                assert all(tid.split(':')[0] in fold['test_subjects'] for tid in fold['trial_ids'])
                assert not seen.intersection(fold['trial_ids'])
                seen.update(fold['trial_ids'])
                verify_selection(fold)
            assert result['n_predictions'] == len(seen)
        if report['config'].get('matched_reference'):
            reference = report['results'][0]['folds']
            for result in report['results'][1:]:
                for first, current in zip(reference, result['folds']):
                    assert first['trial_ids'] == current['trial_ids'] and first['n_train'] == current['n_train']
        reports.append(report['experiment_id'])
    print(json.dumps({'state':'PASS', 'subjects':len(counts), 'source_trials':sum(counts.values()),
                      'dataset_fingerprint':dataset['fingerprint'], 'verified_reports':reports}, indent=2))


if __name__ == '__main__':
    main()

"""Check real source schema/checksums and published split/prediction invariants."""
import json
from app.core.config import PUBLISHED_DIR
from app.data.dataset_loader import get_loader
from app.evaluation.reproducible import dataset_manifest


def main():
    loader = get_loader()
    counts = {sid: loader.get_subject_metadata(sid).n_trials for sid in loader.subject_ids}
    assert len(counts) == 14 and sum(counts.values()) == 4032
    dataset = dataset_manifest(loader, loader.subject_ids)
    reports = []
    for path in PUBLISHED_DIR.glob('*.json'):
        report = json.loads(path.read_text(encoding='utf-8'))
        assert report['dataset'] == dataset
        for result in report['results']:
            seen = set()
            for fold in result['folds']:
                assert not set(fold['train_subjects']) & set(fold['test_subjects'])
                assert len(fold['trial_ids']) == len(fold['y_true']) == len(fold['y_pred']) == fold['n_test']
                assert all(tid.split(':')[0] in fold['test_subjects'] for tid in fold['trial_ids'])
                assert not seen.intersection(fold['trial_ids'])
                seen.update(fold['trial_ids'])
                selection = fold.get('inner_selection')
                if selection:
                    assert not set(selection['validation_subjects']) & set(fold['test_subjects'])
                    assert not set(selection['train_subjects']) & set(selection['validation_subjects'])
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

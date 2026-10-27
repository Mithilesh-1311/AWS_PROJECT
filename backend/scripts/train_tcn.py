"""Real 100 ms LOSO TCN; train-only epoch selection, then refit outer training set."""
import argparse
import json
import uuid
from datetime import datetime, timezone
from time import perf_counter
import joblib
import numpy as np
import torch
from app.core.config import CACHE_DIR, EXPERIMENTS_DIR, DIRECTION_LABELS_8
from app.data.dataset_loader import get_loader
from app.data.trial_segmenter import segment_trials, get_trial_eog
from app.signal_processing.causal import causal_window, VERSION
from app.models.tcn import TinyTCN
from app.evaluation.reproducible import dataset_manifest, write_json, metrics, subject_interval, checksum


def sequences(loader, subjects, fingerprint):
    path = CACHE_DIR / f"sequences_{fingerprint}_100_{VERSION}.joblib"
    if path.exists():
        return joblib.load(path)
    x, y, groups, ids, exclusions = [], [], [], [], []
    counts = {}
    for sid in subjects:
        trials = segment_trials(loader, sid)
        counts[sid] = len(trials)
        for trial in trials:
            observation = causal_window(get_trial_eog(loader, trial, "outward"))
            if observation is None:
                exclusions.append(f"{sid}:{trial.trial_id}")
                continue
            x.append(observation["window"])
            y.append(trial.direction_label_8)
            groups.append(sid)
            ids.append(f"{sid}:{trial.trial_id}")
        loader.release_subject(sid)
        print(f"Sequences: {sid}", flush=True)
    data = dict(X=np.asarray(x, dtype=np.float32), y=np.asarray(y), groups=np.asarray(groups),
                ids=np.asarray(ids), exclusions=exclusions, source_counts=counts)
    joblib.dump(data, path)
    return data


def fit(x, y, epochs, validation=None, model_config=None):
    torch.manual_seed(42)
    model = TinyTCN(**(model_config or {}))
    optimizer = torch.optim.Adam(model.parameters(), lr=.002, weight_decay=1e-4)
    rng = np.random.default_rng(42)
    best, best_epoch, patience = float('inf'), 1, 0
    for epoch in range(1, epochs + 1):
        model.train()
        for indices in np.array_split(rng.permutation(len(y)), max(1, int(np.ceil(len(y) / 128)))):
            batch = x[indices]
            optimizer.zero_grad()
            loss = torch.nn.functional.cross_entropy(model(batch, torch.full((len(batch),), batch.shape[2], dtype=torch.long)), y[indices])
            loss.backward()
            optimizer.step()
        if validation is not None:
            model.eval()
            vx, vy = validation
            with torch.no_grad():
                loss = float(torch.nn.functional.cross_entropy(model(vx, torch.full((len(vx),), vx.shape[2], dtype=torch.long)), vy))
            if loss < best - 1e-5:
                best, best_epoch, patience = loss, epoch, 0
            else:
                patience += 1
            if patience >= 5:
                break
    return model.eval(), best_epoch


def normalize(train, others):
    mean = train.mean(axis=(0, 2), keepdims=True)
    scale = np.maximum(train.std(axis=(0, 2), keepdims=True), 1e-6)
    return [torch.from_numpy((item - mean) / scale) for item in [train, *others]], mean, scale


def run(resume=None, max_epochs=30, architecture="tiny"):
    if architecture not in {"tiny", "full_window"}:
        raise ValueError("Unsupported TCN architecture")
    model_config = dict(hidden=32, dilations=[1, 2, 4, 8]) if architecture == "full_window" else dict(hidden=24, dilations=[1, 2, 4])
    model_name = "full_window_tcn" if architecture == "full_window" else "tiny_tcn"
    torch.set_num_threads(2)
    torch.use_deterministic_algorithms(True)
    loader = get_loader()
    subjects = loader.subject_ids
    if len(subjects) != 14:
        raise ValueError("Full TCN benchmark requires all 14 subjects")
    dataset = dataset_manifest(loader, subjects)
    eid = resume or uuid.uuid4().hex
    if not eid.isalnum() or len(eid) > 64 or not 1 <= max_epochs <= 100:
        raise ValueError("Invalid experiment ID or epoch bound")
    folder = EXPERIMENTS_DIR / eid
    folder.mkdir(parents=True, exist_ok=True)
    config = dict(subjects=subjects, models=[model_name], windows=[100], evaluation='loso', smoke=False,
                  preprocessing_version=VERSION, feature_version='sequence-v1', seed=42,
                  selection_policy='100ms fixed; epochs selected on one inner training subject then refit all outer training subjects',
                  max_epochs=max_epochs, patience=5, hidden=model_config['hidden'], kernel=3, dilations=model_config['dilations'], learning_rate=.002)
    manifest = dict(experiment_id=eid, config=config, dataset=dataset, class_names=DIRECTION_LABELS_8,
                    timestamp=datetime.now(timezone.utc).isoformat(), status='running', torch_version=torch.__version__)
    if (folder / 'manifest.json').exists():
        old = json.loads((folder / 'manifest.json').read_text())
        if old['config'] != config or old['dataset'] != dataset:
            raise ValueError('Resume provenance mismatch')
        if old['status'] == 'complete':
            return old
        manifest = old
    write_json(folder / 'manifest.json', manifest)
    data = sequences(loader, subjects, dataset['fingerprint'])
    write_json(folder / 'exclusions.json', data['exclusions'])
    x, y, groups = data['X'], torch.from_numpy(data['y']).long(), data['groups']
    folds = []
    started = perf_counter()
    for index, sid in enumerate(subjects):
        path = folder / f'{model_name}_100_fold{index}.json'
        if path.exists():
            folds.append(json.loads(path.read_text()))
            continue
        train = groups != sid
        test = ~train
        inner_subject = subjects[(index + 1) % len(subjects)]
        inner_val = groups == inner_subject
        inner_train = train & ~inner_val
        tensors, _, _ = normalize(x[inner_train], [x[inner_val]])
        _, epochs = fit(tensors[0], y[inner_train], max_epochs, (tensors[1], y[inner_val]), model_config)
        tensors, mean, scale = normalize(x[train], [x[test]])
        fit_start = perf_counter()
        model, _ = fit(tensors[0], y[train], epochs, model_config=model_config)
        fit_seconds = perf_counter() - fit_start
        predict_start = perf_counter()
        with torch.no_grad():
            prediction = model(tensors[1], torch.full((int(test.sum()),), x.shape[2], dtype=torch.long)).argmax(1).numpy()
        prediction_ms = (perf_counter() - predict_start) * 1000 / int(test.sum())
        checkpoint = folder / f'fold{index}.pt'
        torch.save(dict(state_dict=model.state_dict(), mean=torch.from_numpy(mean), scale=torch.from_numpy(scale), config=config), checkpoint)
        fold = dict(train_subjects=sorted(set(groups[train])), test_subjects=[sid], inner_validation_subject=inner_subject,
                    selected_epochs=epochs, trial_ids=data['ids'][test].tolist(), y_true=y[test].tolist(), y_pred=prediction.tolist(),
                    metrics=metrics(y[test].numpy(), prediction), n_train=int(train.sum()), n_test=int(test.sum()),
                    fit_seconds=fit_seconds, batch_prediction_ms_per_trial=prediction_ms, checkpoint_sha256=checksum(checkpoint))
        write_json(path, fold)
        folds.append(fold)
        print(f"Fold {index + 1}/14 {sid}: accuracy={fold['metrics']['accuracy']:.4f}, epochs={epochs}", flush=True)
    true = np.array([v for f in folds for v in f['y_true']])
    pred = np.array([v for f in folds for v in f['y_pred']])
    result = dict(model_name=model_name, window_ms=100, n_samples=26, metrics=metrics(true, pred), folds=folds,
                  n_predictions=len(true), eligible_trials=len(true), coverage=len(true) / sum(data['source_counts'].values()),
                  matched_metrics=None, matched_prediction_count=0, subject_accuracy_interval=subject_interval(folds))
    manifest.update(status='complete', results=[result], total_source_trials=sum(data['source_counts'].values()),
                    exclusion_count=len(data['exclusions']), runtime_seconds=perf_counter() - started,
                    parameter_count=sum(p.numel() for p in TinyTCN(**model_config).parameters()),
                    serving_policy='comparison only; does not replace fixed logistic serving model')
    write_json(folder / 'manifest.json', manifest)
    print('Experiment:', eid, result['metrics'], flush=True)
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--resume')
    parser.add_argument('--max-epochs', type=int, default=30)
    parser.add_argument('--architecture', choices=['tiny', 'full_window'], default='tiny')
    args = parser.parse_args()
    run(args.resume, args.max_epochs, args.architecture)

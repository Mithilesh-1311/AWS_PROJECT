"""Immutable real-data causal experiments. Historical experiments are never overwritten."""
import hashlib
import importlib.metadata
import json
import platform
import uuid
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

import joblib
import numpy as np
from sklearn.metrics import balanced_accuracy_score
from threadpoolctl import threadpool_limits

from app.core.config import EXPERIMENTS_DIR, CACHE_DIR, DIRECTION_LABELS_8, RANDOM_SEED
from app.data.dataset_loader import get_loader
from app.data.trial_segmenter import segment_trials, get_trial_eog
from app.features.feature_extractor import extract_features, FeatureConfig, get_feature_names
from app.models.baseline_models import create_model
from app.signal_processing.causal import CausalProcessor, VERSION
from app.evaluation.evaluator import evaluate_predictions

WINDOWS = [20, 40, 60, 80, 100, 120, 160, 200, 400]
FAMILIES = ["logistic_regression", "linear_svm", "random_forest"]


def checksum(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, indent=2, allow_nan=False), encoding="utf-8")
    temporary.replace(path)


def dataset_manifest(loader, subjects):
    files = {f"{sid}/{name}": checksum(loader.root / sid / name)
             for sid in subjects for name in ["EOG.mat", "ControlSignal.mat", "Target_GA_stream.mat", "PD.mat", "Dist_screen.mat"]}
    return {"files": files, "fingerprint": hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()}


def prepare_data(subjects, windows, fingerprint, progress=lambda **kw: None):
    cache_key = hashlib.sha256(json.dumps([fingerprint, VERSION, "physical-v2", windows]).encode()).hexdigest()
    cache = CACHE_DIR / f"causal_{cache_key}.joblib"
    if cache.exists():
        return joblib.load(cache)
    loader = get_loader()
    rows = {str(ms): {"X": [], "y": [], "groups": [], "ids": [], "ready_ms": []} for ms in windows}
    exclusions = []
    source_counts = {sid: len(segment_trials(loader, sid)) for sid in subjects}
    total = sum(source_counts.values())
    done = 0
    started = perf_counter()
    for sid in subjects:
        trials = segment_trials(loader, sid)
        for trial in trials:
            raw = get_trial_eog(loader, trial, "outward")
            processor = CausalProcessor(max(windows))
            for start in range(0, raw.shape[1], 128):
                processor.push(raw[:, start:start + 128], start)
            crossing = processor.crossing
            signal = np.asarray(processor.filtered).T
            for ms in windows:
                n = int(np.ceil(ms * 256 / 1000))
                reason = None
                if crossing is None:
                    reason = "no_confirmed_onset"
                elif crossing + n > raw.shape[1]:
                    reason = "insufficient_window"
                if reason:
                    exclusions.append({"trial_id": f"{sid}:{trial.trial_id}", "window_ms": ms, "reason": reason})
                    continue
                features = extract_features(signal[:, crossing:crossing + n], FeatureConfig(version="physical-v2"))
                if not np.isfinite(features).all():
                    exclusions.append({"trial_id": f"{sid}:{trial.trial_id}", "window_ms": ms, "reason": "nonfinite_features"})
                    continue
                row = rows[str(ms)]
                row["X"].append(features)
                row["y"].append(trial.direction_label_8)
                row["groups"].append(sid)
                row["ids"].append(f"{sid}:{trial.trial_id}")
                row["ready_ms"].append(max(crossing + n - 1, processor.confirmation) / 256 * 1000)
            done += 1
            if done % 48 == 0:
                progress(stage="features", completed=done, total=total)
        loader.release_subject(sid)
    for row in rows.values():
        for key in row:
            row[key] = np.asarray(row[key])
    data = {"source_counts": source_counts, "windows": rows, "exclusions": exclusions, "feature_runtime_seconds": perf_counter() - started}
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    temp = cache.with_suffix(".tmp")
    joblib.dump(data, temp)
    temp.replace(cache)
    return data


def metrics(y, prediction):
    result = evaluate_predictions(y, prediction, 8)
    result["balanced_accuracy"] = float(balanced_accuracy_score(y, prediction))
    result["support"] = np.bincount(y, minlength=8).tolist()
    return result


def subject_interval(subject_results):
    values = np.array([r["metrics"]["accuracy"] for r in subject_results])
    rng = np.random.default_rng(RANDOM_SEED)
    means = rng.choice(values, (2000, len(values)), replace=True).mean(axis=1)
    return {"low": float(np.quantile(means, .025)), "high": float(np.quantile(means, .975)),
            "method": "subject bootstrap mean accuracy; only 14 subjects at most; not an external validation"}


def select_logistic(row, train_mask):
    """Bounded C selection uses one training subject; outer test never enters selection."""
    subjects = sorted(set(row["groups"][train_mask]))
    validation_subject = subjects[-1]
    inner_validation = train_mask & (row["groups"] == validation_subject)
    inner_train = train_mask & ~inner_validation
    if not inner_train.any() or not inner_validation.any():
        raise ValueError("Insufficient inner subjects")
    candidates = []
    for c in [.1, 1.0]:
        model = create_model("logistic_regression", C=c).fit(row["X"][inner_train], row["y"][inner_train])
        score = balanced_accuracy_score(row["y"][inner_validation], model.predict(row["X"][inner_validation]))
        candidates.append({"C": c, "validation_balanced_accuracy": float(score)})
    selected = max(candidates, key=lambda candidate: candidate["validation_balanced_accuracy"])["C"]
    return selected, {"train_subjects": sorted(set(row["groups"][inner_train])),
                      "validation_subjects": [validation_subject], "candidates": candidates, "selected_C": selected}


def run_causal(subjects=None, models=None, windows=None, evaluation="holdout", smoke=False,
               serve=False, experiment_id=None, matched_reference=False, progress=lambda **kw: None):
    loader = get_loader()
    subjects = subjects or loader.subject_ids
    models = models or FAMILIES
    windows = windows or WINDOWS
    if len(subjects) < 3 or len(set(subjects)) != len(subjects) or not set(subjects) <= set(loader.subject_ids):
        raise ValueError("Select at least three distinct available subjects")
    if len(set(models)) != len(models) or len(set(windows)) != len(windows) or not set(models) <= set(FAMILIES) or not windows or any(w not in WINDOWS for w in windows):
        raise ValueError("Unsupported model or observation budget")
    if evaluation not in {"holdout", "loso"}:
        raise ValueError("Unsupported evaluation")
    if serve and (smoke or models != ["logistic_regression"] or windows != [100]):
        raise ValueError("Serving policy is predeclared logistic regression / 100 ms; no smoke models")
    config = {"subjects": subjects, "models": models, "windows": windows, "evaluation": evaluation,
              "smoke": smoke, "serve": serve, "matched_reference": matched_reference,
              "sklearn_version": importlib.metadata.version("scikit-learn"), "preprocessing_version": VERSION, "feature_version": "physical-v2",
              "seed": RANDOM_SEED, "selection_policy": ("fixed logistic/100ms; train-only inner subject C selection" if serve else "fixed logistic/100ms primary; no outer-score tuning"),
              "hyperparameters": {"C": 1.0, "random_forest_trees": 80, "random_forest_max_depth": 12}}
    fingerprint = dataset_manifest(loader, subjects)
    config_hash = hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()
    experiment_id = experiment_id or uuid.uuid4().hex
    if not experiment_id.isalnum() or len(experiment_id) > 64:
        raise ValueError("Invalid experiment identifier")
    folder = EXPERIMENTS_DIR / experiment_id
    folder.mkdir(parents=True, exist_ok=True)
    manifest_path = folder / "manifest.json"
    manifest = {"experiment_id": experiment_id, "config": config, "config_hash": config_hash,
                "dataset": fingerprint, "class_names": DIRECTION_LABELS_8, "class_order": list(range(8)),
                "feature_names": get_feature_names(), "feature_units": "recorded units; derivatives per second; integrals in seconds",
                "versions": {name: importlib.metadata.version(name) for name in ["numpy", "scipy", "scikit-learn", "joblib"]},
                "python": platform.python_version(), "timestamp": datetime.now(timezone.utc).isoformat(),
                "calibration": "first 25 cue samples; 97.65625 ms budget; no early prediction",
                "mode": "causal recorded cue-triggered research", "status": "running"}
    if manifest_path.exists():
        old = json.loads(manifest_path.read_text())
        if old["config_hash"] != config_hash or old["dataset"] != fingerprint:
            raise ValueError("Resume configuration or dataset differs")
        if old.get("status") == "complete":
            return old
        manifest = old
    write_json(manifest_path, manifest)
    data = prepare_data(subjects, windows, fingerprint["fingerprint"], progress)
    source_counts = data.get("source_counts") or {sid: len(segment_trials(loader, sid)) for sid in subjects}
    if matched_reference:
        if 400 not in windows:
            raise ValueError("Matched evaluation requires the 400 ms reference")
        # Copy cached arrays: filtering must never mutate the all-eligible feature cache.
        common = set.intersection(*(set(row["ids"]) for row in data["windows"].values()))
        data = dict(data, windows={key: {name: values[np.isin(row["ids"], list(common))] for name, values in row.items()}
                                   for key, row in data["windows"].items()})
    write_json(folder / "exclusions.json", data["exclusions"])
    rng = np.random.RandomState(RANDOM_SEED)
    shuffled = np.array(sorted(subjects))
    rng.shuffle(shuffled)
    test_sets = [[s] for s in subjects] if evaluation == "loso" else [shuffled[:max(1, int(len(subjects) * .3))].tolist()]
    total = len(models) * len(windows) * len(test_sets)
    completed = 0
    results = []
    started = perf_counter()
    with threadpool_limits(limits=1):
        for family in models:
            for ms in windows:
                row = data["windows"][str(ms)]
                folds = []
                all_y, all_pred = [], []
                matched_y, matched_pred = [], []
                reference = data["windows"].get("400")
                matched_ids = set(reference["ids"]) if reference else set()
                for fold_index, test_subjects in enumerate(test_sets):
                    train = ~np.isin(row["groups"], test_subjects)
                    test = ~train
                    if not train.any() or not test.any():
                        raise ValueError("No eligible train/test windows")
                    fold_path = folder / f"{family}_{ms}_fold{fold_index}.json"
                    if fold_path.exists():
                        fold = json.loads(fold_path.read_text())
                    else:
                        c, selection = select_logistic(row, train) if serve else (1.0, None)
                        model = create_model(family, C=c, n_estimators=80, max_depth=12)
                        model.set_params(**({"classifier__n_jobs": 2} if family == "random_forest" else {}))
                        fit_start = perf_counter()
                        model.fit(row["X"][train], row["y"][train])
                        fit_seconds = perf_counter() - fit_start
                        predict_start = perf_counter()
                        prediction = model.predict(row["X"][test])
                        predict_ms = (perf_counter() - predict_start) * 1000 / int(test.sum())
                        fold = {"test_subjects": test_subjects, "train_subjects": sorted(set(row["groups"][train])),
                                "trial_ids": row["ids"][test].tolist(), "y_true": row["y"][test].tolist(),
                                "y_pred": prediction.tolist(), "metrics": metrics(row["y"][test], prediction),
                                "n_train": int(train.sum()), "n_test": int(test.sum()),
                                "fit_seconds": fit_seconds, "batch_prediction_ms_per_trial": predict_ms, "inner_selection": selection}
                        write_json(fold_path, fold)
                    folds.append(fold)
                    all_y.extend(fold["y_true"])
                    all_pred.extend(fold["y_pred"])
                    for tid, y, pred in zip(fold["trial_ids"], fold["y_true"], fold["y_pred"]):
                        if tid in matched_ids:
                            matched_y.append(y)
                            matched_pred.append(pred)
                    completed += 1
                    progress(stage="evaluation", completed=completed, total=total)
                result = {"model_name": family, "window_ms": ms, "n_samples": int(np.ceil(ms * 256 / 1000)),
                          "metrics": metrics(np.asarray(all_y), np.asarray(all_pred)), "folds": folds,
                          "n_predictions": len(all_y), "coverage": len(all_y) / sum(source_counts[sid] for fold in folds for sid in fold["test_subjects"]),
                          "source_test_trials": sum(source_counts[sid] for fold in folds for sid in fold["test_subjects"]),
                          "matched_reference_ms": 400 if reference else None,
                          "matched_metrics": metrics(np.asarray(matched_y), np.asarray(matched_pred)) if matched_y else None,
                          "matched_prediction_count": len(matched_y), "eligible_trials": len(row["y"])}
                if evaluation == "loso":
                    result["subject_accuracy_interval"] = subject_interval(folds)
                results.append(result)
    manifest.update(status="complete", results=results, runtime_seconds=perf_counter() - started,
                    feature_runtime_seconds=data["feature_runtime_seconds"], exclusion_count=len(data["exclusions"]),
                    total_source_trials=sum(source_counts.values()))
    if serve:
        row = data["windows"]["100"]
        with threadpool_limits(limits=1):
            c, final_selection = select_logistic(row, np.ones(len(row["y"]), dtype=bool))
            model = create_model("logistic_regression", C=c).fit(row["X"], row["y"])
        manifest["final_inner_selection"] = final_selection
        model_id = f"{experiment_id}_logistic_100"
        model_path = folder / "serving.joblib"
        joblib.dump(model, model_path)
        metadata = {"model_id": model_id, "experiment_id": experiment_id, "window_ms": 100, "alignment": "onset",
                    "preprocessing_version": VERSION, "feature_version": "physical-v2", "n_features": 212,
                    "class_names": DIRECTION_LABELS_8, "class_order": list(range(8)), "score_semantics": "uncalibrated_probability",
                    "model_file": "serving.joblib", "sha256": checksum(model_path), "versions": manifest["versions"],
                    "trained_subjects": subjects, "evaluation_scope": evaluation,
                    "warning": "Final model refitted on all selected subjects; evaluation describes separate fold models"}
        write_json(folder / "model.json", metadata)
        manifest["serving_model_id"] = model_id
    write_json(manifest_path, manifest)
    return manifest

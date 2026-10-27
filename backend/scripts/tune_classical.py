"""Exploratory nested LOSO comparison; outer subjects never select settings."""
import argparse
import importlib.metadata
import json
import uuid
from datetime import datetime, timezone
from time import perf_counter

import numpy as np
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import FunctionTransformer, StandardScaler
from sklearn.svm import SVC
from threadpoolctl import threadpool_limits

from app.core.config import EXPERIMENTS_DIR, DIRECTION_LABELS_8
from app.data.dataset_loader import get_loader
from app.data.trial_segmenter import segment_trials
from app.evaluation.reproducible import (
    WINDOWS, checksum, dataset_manifest, metrics, prepare_data, subject_interval, write_json,
)


CANDIDATES = [
    {"family": "logistic", "C": .1},
    {"family": "logistic", "C": 1.0},
    {"family": "lda", "shrinkage": "auto"},
    *[{"family": "rbf_svm", "C": c, "gamma": gamma}
      for c in [1.0, 10.0, 100.0] for gamma in ["scale", .001]],
]

GROUPED_CANDIDATES = [
    *[{"family": "rbf_svm", "C": c, "gamma": "scale", "features": features}
      for features in ["all", "normalized_all", "normalized_spatial", "normalized_directional"]
      for c in [.1, 1.0, 10.0]],
    {"family": "rbf_svm", "C": 1.0, "gamma": .001},
    {"family": "rbf_svm", "C": 10.0, "gamma": .001},
    {"family": "logistic", "C": .1},
    {"family": "lda", "shrinkage": "auto"},
]

MACRO_CANDIDATES = [
    *[{"family": "rbf_svm", "C": c, "gamma": "scale", "features": features}
      for features in ["all", "normalized_all", "normalized_spatial", "normalized_directional"]
      for c in [1.0, 10.0]],
    *[{"family": "rbf_svm", "C": c, "gamma": .001} for c in [1.0, 10.0]],
    *[{"family": "poly_svm", "C": 1.0, "degree": degree, "features": "normalized_spatial"}
      for degree in [2, 3]],
    *[{"family": "lda", "shrinkage": "auto", "features": features}
      for features in ["all", "normalized_spatial"]],
    *[{"family": "knn", "neighbors": k, "features": "normalized_spatial"} for k in [5, 15]],
    *[{"family": "extra_trees", "max_features": f} for f in [.5, 1.0]],
    *[{"family": "logistic", "C": .1, "features": features}
      for features in ["all", "normalized_directional"]],
]


def transform_features(x, mode):
    if mode not in {"all", "normalized_all", "normalized_spatial", "normalized_directional"}:
        raise ValueError("Unsupported feature mode")
    if x.ndim != 2 or x.shape[1] != 212 or not np.isfinite(x).all():
        raise ValueError("Expected finite 212-feature physical-v2 rows")
    if mode == "all":
        return x
    channels = x[:, :208].reshape(-1, 16, 13).copy()
    # Per-trial scale uses only the observed window, never other trials or labels.
    scale = np.maximum(np.sqrt(np.mean(channels[:, :, 5] ** 2, axis=1)), 1e-12)
    channels /= scale[:, None, None]
    channels[:, :, [10, 11]] /= scale[:, None, None]
    if mode == "normalized_spatial":
        return channels[:, :, :6].reshape(-1, 96)
    if mode == "normalized_directional":
        return channels[:, :, [0, 1, 6, 7]].reshape(-1, 64)
    cross = x[:, 208:].copy()
    cross[:, [1, 2]] /= scale[:, None]
    return np.concatenate([channels.reshape(-1, 208), cross], axis=1)


def create_candidate(config):
    if config["family"] == "logistic":
        model = LogisticRegression(C=config["C"], max_iter=2000, random_state=42)
    elif config["family"] == "lda":
        model = LinearDiscriminantAnalysis(solver="lsqr", shrinkage=config["shrinkage"])
    elif config["family"] == "rbf_svm":
        model = SVC(C=config["C"], gamma=config["gamma"], cache_size=256)
    elif config["family"] == "poly_svm":
        model = SVC(C=config["C"], kernel="poly", degree=config["degree"], coef0=1, cache_size=256)
    elif config["family"] == "knn":
        model = KNeighborsClassifier(n_neighbors=config["neighbors"], weights="distance", n_jobs=1)
    elif config["family"] == "extra_trees":
        model = ExtraTreesClassifier(n_estimators=128, max_features=config["max_features"], random_state=42, n_jobs=1)
    else:
        raise ValueError("Unsupported candidate")
    steps = []
    if "features" in config:
        steps.append(FunctionTransformer(transform_features, kw_args={"mode": config["features"]}))
    return make_pipeline(*steps, StandardScaler(), model)


def select_candidate(x, y, groups, search="single"):
    subjects = sorted(set(groups))
    if len(subjects) < 2:
        raise ValueError("Inner selection requires at least two training subjects")
    if search in {"grouped", "macro"}:
        if len(subjects) < 3:
            raise ValueError("Grouped selection requires at least three training subjects")
        splits = list(GroupKFold(3).split(x, y, groups))
        scores = []
        scoring = "macro_f1" if search == "macro" else "balanced_accuracy"
        candidates = MACRO_CANDIDATES if search == "macro" else GROUPED_CANDIDATES
        for config in candidates:
            subject_scores = {}
            for train, validation in splits:
                model = create_candidate(config).fit(x[train], y[train])
                prediction = model.predict(x[validation])
                for sid in sorted(set(groups[validation])):
                    mask = groups[validation] == sid
                    subject_scores[sid] = metrics(y[validation][mask], prediction[mask])[scoring]
            scores.append(dict(config=config, subject_scores=subject_scores,
                               **{scoring: float(np.mean(list(subject_scores.values())))}))
        selected = max(scores, key=lambda item: item[scoring])["config"]
        folds = [dict(train_subjects=sorted(set(groups[train])), validation_subjects=sorted(set(groups[val])))
                 for train, val in splits]
        return selected, dict(folds=folds, candidates=scores, selected=selected,
                              scoring=f"mean per-subject {scoring} over three grouped folds")
    if search != "single":
        raise ValueError("Unsupported search protocol")
    validation = groups == subjects[-1]
    scores = []
    for config in CANDIDATES:
        model = create_candidate(config).fit(x[~validation], y[~validation])
        prediction = model.predict(x[validation])
        scores.append(dict(config=config, balanced_accuracy=metrics(y[validation], prediction)["balanced_accuracy"]))
    selected = max(scores, key=lambda item: item["balanced_accuracy"])["config"]
    return selected, dict(train_subjects=subjects[:-1], validation_subjects=subjects[-1:],
                          candidates=scores, selected=selected)


def run(windows, resume=None, search="single"):
    allowed = [100, 200, 400, 600, 800] if search == "macro" else [100, 200, 400]
    if not windows or len(set(windows)) != len(windows) or any(ms not in allowed for ms in windows):
        raise ValueError(f"Select distinct budgets from {allowed} ms")
    if search not in {"single", "grouped", "macro"}:
        raise ValueError("Unsupported search protocol")
    candidates = MACRO_CANDIDATES if search == "macro" else GROUPED_CANDIDATES if search == "grouped" else CANDIDATES
    model_name = "macro_f1_search" if search == "macro" else "grouped_feature_search" if search == "grouped" else "nested_classical_search"
    loader = get_loader()
    subjects = loader.subject_ids
    if len(subjects) != 14:
        raise ValueError("Full comparison requires all 14 subjects")
    dataset = dataset_manifest(loader, subjects)
    eid = resume or uuid.uuid4().hex
    if not eid.isalnum() or len(eid) > 64:
        raise ValueError("Invalid experiment ID")
    folder = EXPERIMENTS_DIR / eid
    folder.mkdir(parents=True, exist_ok=True)
    config = dict(subjects=subjects, windows=windows, models=[model_name], evaluation="loso",
                  smoke=False, candidates=candidates, seed=42, preprocessing_version="causal-v1", search=search,
                  feature_version="physical-v2", sklearn_version=importlib.metadata.version("scikit-learn"),
                  inner_score="macro_f1" if search == "macro" else "balanced_accuracy",
                  selection_policy=("three inner grouped folds select by mean subject macro F1; outer subjects never select settings"
                                    if search == "macro" else "exploratory follow-up; three inner grouped folds select by mean subject balanced accuracy"
                                    if search == "grouped" else "exploratory follow-up; one inner training subject selects by balanced accuracy; outer scores never select settings"),
                  script_sha256=checksum(__file__))
    manifest = dict(experiment_id=eid, config=config, dataset=dataset, class_names=DIRECTION_LABELS_8,
                    class_order=list(range(8)), timestamp=datetime.now(timezone.utc).isoformat(), status="running",
                    versions={name: importlib.metadata.version(name) for name in ["numpy", "scipy", "scikit-learn", "joblib"]})
    manifest_path = folder / "manifest.json"
    if manifest_path.exists():
        old = json.loads(manifest_path.read_text())
        if old["config"] != config or old["dataset"] != dataset:
            raise ValueError("Resume provenance mismatch")
        if old["status"] == "complete":
            return old
        manifest = old
    write_json(manifest_path, manifest)
    print(f"Experiment: {eid}; {len(candidates)} candidates; {search}; budgets {windows}; 14 outer subjects", flush=True)
    data = prepare_data(subjects, windows if search == "macro" else WINDOWS, dataset["fingerprint"])
    counts = {sid: len(segment_trials(loader, sid)) for sid in subjects}
    exclusions = [item for item in data["exclusions"] if item["window_ms"] in windows]
    write_json(folder / "exclusions.json", exclusions)
    results = []
    started = perf_counter()
    with threadpool_limits(limits=1):
        for ms in windows:
            row = data["windows"][str(ms)]
            folds = []
            for index, sid in enumerate(subjects):
                path = folder / f"{model_name}_{ms}_fold{index}.json"
                if path.exists():
                    fold = json.loads(path.read_text())
                else:
                    test = row["groups"] == sid
                    train = ~test
                    selected, selection = select_candidate(row["X"][train], row["y"][train], row["groups"][train], search)
                    fit_start = perf_counter()
                    model = create_candidate(selected).fit(row["X"][train], row["y"][train])
                    fit_seconds = perf_counter() - fit_start
                    prediction = model.predict(row["X"][test])
                    fold = dict(test_subjects=[sid], train_subjects=sorted(set(row["groups"][train])),
                                trial_ids=row["ids"][test].tolist(), y_true=row["y"][test].tolist(),
                                y_pred=prediction.tolist(), n_train=int(train.sum()), n_test=int(test.sum()),
                                metrics=metrics(row["y"][test], prediction), inner_selection=selection,
                                fit_seconds=fit_seconds)
                    write_json(path, fold)
                folds.append(fold)
                print(f"{ms}ms fold {index+1}/14 {sid}: {fold['metrics']['accuracy']:.4f}; {fold['inner_selection']['selected']}", flush=True)
            true = np.array([v for fold in folds for v in fold["y_true"]])
            predicted = np.array([v for fold in folds for v in fold["y_pred"]])
            result = dict(model_name=model_name, window_ms=ms, n_samples=int(np.ceil(ms*256/1000)),
                          metrics=metrics(true, predicted), folds=folds, n_predictions=len(true),
                          eligible_trials=len(true), source_test_trials=sum(counts.values()),
                          coverage=len(true)/sum(counts.values()), subject_accuracy_interval=subject_interval(folds))
            results.append(result)
            print(f"RESULT {ms}ms accuracy={result['metrics']['accuracy']:.6f} F1={result['metrics']['macro_f1']:.6f}", flush=True)
    manifest.update(status="complete", results=results, total_source_trials=sum(counts.values()),
                    exclusion_count=len(exclusions), runtime_seconds=perf_counter()-started,
                    serving_policy="exploratory comparison only; active serving model unchanged")
    write_json(manifest_path, manifest)
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--windows", default="100,200,400")
    parser.add_argument("--resume")
    parser.add_argument("--search", choices=["single", "grouped", "macro"], default="single")
    args = parser.parse_args()
    run([int(value) for value in args.windows.split(",")], args.resume, args.search)

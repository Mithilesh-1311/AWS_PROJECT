"""Only project-produced causal models with compatible metadata are served."""
import json
import os
import re
import pickle
from functools import lru_cache
from time import perf_counter
import importlib.metadata
import joblib
import numpy as np
from app.core.config import EXPERIMENTS_DIR, STATE_DIR
from app.evaluation.reproducible import checksum, write_json
from app.signal_processing.causal import VERSION, causal_window
from app.features.feature_extractor import FeatureConfig, extract_features
from app.data.dataset_loader import get_loader
from app.data.trial_segmenter import segment_trials, get_trial_eog


def model_records():
    records = []
    for path in sorted(EXPERIMENTS_DIR.glob("*/model.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if not {"model_id", "experiment_id", "window_ms", "alignment", "preprocessing_version", "feature_version", "class_names", "class_order", "score_semantics"} <= data.keys():
                continue
            try:
                load_model(data["model_id"])
                data["ready"] = True
            except ValueError:
                data["ready"] = False
            records.append(data)
        except (ValueError, OSError):
            continue
    return records


def active_model_id():
    configured = os.environ.get("EOG_ACTIVE_MODEL")
    if configured:
        return configured
    try:
        return json.loads((STATE_DIR / "active_model.json").read_text())["model_id"]
    except (OSError, ValueError, KeyError):
        return None


def activate(model_id):
    load_model(model_id)
    write_json(STATE_DIR / "active_model.json", {"model_id": model_id})


@lru_cache(maxsize=4)
def load_model(model_id):
    if not re.fullmatch(r"[a-f0-9]{32}_logistic_100", model_id or ""):
        raise ValueError("Invalid or unsupported model ID")
    folder = EXPERIMENTS_DIR / model_id.split("_")[0]
    try:
        metadata = json.loads((folder / "model.json").read_text())
        if (metadata["model_id"] != model_id or metadata["preprocessing_version"] != VERSION
                or metadata["feature_version"] != "physical-v2" or metadata["n_features"] != 212
                or metadata["window_ms"] != 100 or metadata["alignment"] != "onset"
                or len(metadata["class_names"]) != 8 or metadata["class_order"] != list(range(8))
                or metadata["versions"]["scikit-learn"] != importlib.metadata.version("scikit-learn")
                or metadata["sha256"] != checksum(folder / "serving.joblib")):
            raise ValueError("Incompatible model metadata, dependency version or checksum")
        model = joblib.load(folder / "serving.joblib")
        if model.n_features_in_ != 212 or model.classes_.tolist() != metadata["class_order"]:
            raise ValueError("Incompatible model feature schema or classes")
        return model, metadata
    except (OSError, KeyError, json.JSONDecodeError, EOFError, pickle.UnpicklingError, AttributeError, TypeError) as error:
        raise ValueError("Model unavailable or corrupt") from error


def recorded_trial(subject_id, trial_id):
    loader = get_loader()
    if subject_id not in loader.subject_ids:
        raise ValueError("Subject not found")
    trials = segment_trials(loader, subject_id)
    if not 0 <= trial_id < len(trials):
        raise ValueError("Trial not found")
    trial = trials[trial_id]
    return get_trial_eog(loader, trial, "outward"), trial


def predict_window(result, model_id):
    model, metadata = load_model(model_id)
    start = perf_counter()
    features = extract_features(result["window"], FeatureConfig(version=metadata["feature_version"]))
    if not np.isfinite(features).all():
        raise ValueError("Nonfinite features; prediction withheld")
    feature_ms = (perf_counter() - start) * 1000
    start = perf_counter()
    scores = model.predict_proba(features[None, :])[0]
    inference_ms = (perf_counter() - start) * 1000
    predicted = int(model.classes_[np.argmax(scores)])
    window = {k: v for k, v in result.items() if k != "window"}
    return {"state": "predicted", "model_id": model_id, "experiment_id": metadata["experiment_id"],
            "predicted_class": predicted, "predicted_direction": metadata["class_names"][predicted],
            "scores": scores.tolist(), "score_semantics": metadata["score_semantics"],
            "class_names": metadata["class_names"], "window": window,
            "feature_ms": feature_ms, "inference_ms": inference_ms,
            "warnings": [metadata["warning"], "Recorded-data research; calibration and cue-trigger assumptions apply"]}


def predict_trial(subject_id, trial_id, model_id=None):
    selected = model_id or active_model_id()
    if not selected:
        raise ValueError("No active model; train a serving model and activate it")
    _, metadata = load_model(selected)
    raw, trial = recorded_trial(subject_id, trial_id)
    start = perf_counter()
    result = causal_window(raw, metadata["window_ms"], metadata["alignment"])
    if result is None:
        return {"state": "abstained", "reason": "No confirmed onset or insufficient window",
                "model_id": selected, "subject_id": subject_id, "trial_id": trial_id}
    prediction = predict_window(result, selected)
    prediction.update(subject_id=subject_id, trial_id=trial_id,
                      server_total_ms=(perf_counter() - start) * 1000,
                      evaluation={"target_class": trial.direction_label_8, "target_angle_deg": trial.target_angle_deg})
    return prediction

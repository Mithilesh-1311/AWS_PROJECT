"""
Run Baseline Experiment
=======================
End-to-end experiment: load → segment → preprocess → window → features → train → evaluate.

Trains/evaluates baseline models separately for each observation window duration.
Generates the core latency-vs-accuracy results for Review 1.

Usage:
    python -m scripts.run_baseline [--subjects S1,S2,...] [--n-classes 8] [--model logistic_regression]
"""
import sys
import os
import numpy as np
import json
import logging
from pathlib import Path
from datetime import datetime
from sklearn.model_selection import GroupKFold
import joblib

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import (
    RANDOM_SEED, SAMPLING_RATE, MODELS_DIR, REPORTS_DIR, CACHE_DIR,
    DEFAULT_WINDOW_DURATIONS_MS, DIRECTION_LABELS_8, DIRECTION_LABELS_4,
)
from app.data.dataset_loader import DatasetLoader, get_loader
from app.data.trial_segmenter import segment_trials, get_trial_eog, get_direction_label_name
from app.signal_processing.preprocessor import PreprocessingConfig, preprocess_trial
from app.signal_processing.onset_detector import OnsetConfig, detect_onset
from app.features.window_generator import get_window_specs, extract_early_window
from app.features.feature_extractor import extract_features, FeatureConfig
from app.models.baseline_models import create_model, PhysicsBaseline
from app.evaluation.evaluator import (
    evaluate_predictions, WindowResult, ExperimentResult, save_experiment_result
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

np.random.seed(RANDOM_SEED)


def run_experiment(
    subjects: list = None,
    n_classes: int = 8,
    model_name: str = "logistic_regression",
    alignment: str = "onset",
    test_ratio: float = 0.3,
):
    """Run the full latency-vs-accuracy experiment.

    Split strategy: Group by subject. Use ~70% subjects for train, ~30% for test.
    This is a preliminary split — not final LOSO evaluation.
    """
    loader = get_loader()

    if subjects is None:
        subjects = loader.subject_ids

    logger.info(f"Experiment: model={model_name}, n_classes={n_classes}, "
                f"alignment={alignment}, subjects={subjects}")

    # --- Phase 1: Segment all trials ---
    logger.info("Phase 1: Segmenting trials...")
    all_trials = []
    for sid in subjects:
        trials = segment_trials(loader, sid)
        all_trials.extend(trials)
        logger.info(f"  {sid}: {len(trials)} trials")

    logger.info(f"Total trials: {len(all_trials)}")

    # --- Phase 2: Detect saccade onsets ---
    logger.info("Phase 2: Detecting saccade onsets...")
    onset_config = OnsetConfig()
    preprocess_config = PreprocessingConfig(
        baseline_correction=True,
        detrend=False,
        highpass_filter=False,
        normalize=False,
    )

    trial_onsets = {}  # trial index -> onset_sample
    onset_stats = {"reliable": 0, "unreliable": 0, "failed": 0}

    for i, trial in enumerate(all_trials):
        eog_out = get_trial_eog(loader, trial, phase="outward")
        # Preprocess for onset detection
        eog_proc = preprocess_trial(eog_out, preprocess_config)
        result = detect_onset(eog_proc, onset_config)

        if result.onset_sample is not None and result.reliable:
            trial_onsets[i] = result.onset_sample
            onset_stats["reliable"] += 1
        elif result.onset_sample is not None:
            # Use it but mark as unreliable
            trial_onsets[i] = result.onset_sample
            onset_stats["unreliable"] += 1
        else:
            # Fall back to cue-aligned (sample 0)
            trial_onsets[i] = 0
            onset_stats["failed"] += 1

    logger.info(f"Onset detection: {onset_stats}")

    # --- Phase 3: Subject-based train/test split ---
    logger.info("Phase 3: Train/test split (subject-level)...")
    unique_subjects = sorted(set(t.subject_id for t in all_trials))
    n_test = max(1, int(len(unique_subjects) * test_ratio))
    rng = np.random.RandomState(RANDOM_SEED)
    rng.shuffle(unique_subjects)
    test_subjects = set(unique_subjects[:n_test])
    train_subjects = set(unique_subjects[n_test:])

    logger.info(f"  Train subjects ({len(train_subjects)}): {sorted(train_subjects)}")
    logger.info(f"  Test subjects ({len(test_subjects)}): {sorted(test_subjects)}")

    train_indices = [i for i, t in enumerate(all_trials) if t.subject_id in train_subjects]
    test_indices = [i for i, t in enumerate(all_trials) if t.subject_id in test_subjects]

    # --- Phase 4: For each window, extract features and train/evaluate ---
    logger.info("Phase 4: Running per-window experiments...")
    window_specs = get_window_specs()
    # Add full reference window (use ~250 samples ≈ 977ms, approx outward phase length)
    from app.features.window_generator import WindowSpec
    window_specs.append(WindowSpec(requested_ms=1000, n_samples=256, effective_ms=1000.0))

    feature_config = FeatureConfig(channels=None, include_cross_channel=True)
    window_results = []

    for spec in window_specs:
        logger.info(f"  Window: {spec.requested_ms}ms ({spec.n_samples} samples, "
                     f"effective {spec.effective_ms:.1f}ms)...")

        # Extract features for all trials at this window duration
        X_all = []
        y_all = []
        valid_indices = []

        for i, trial in enumerate(all_trials):
            eog_out = get_trial_eog(loader, trial, phase="outward")
            eog_proc = preprocess_trial(eog_out, preprocess_config)

            onset = trial_onsets.get(i, 0)
            if alignment == "onset":
                window = extract_early_window(eog_proc, onset, spec.n_samples, "onset")
            else:
                window = extract_early_window(eog_proc, 0, spec.n_samples, "cue")

            if window is None:
                continue

            features = extract_features(window, feature_config)

            # Check for NaN/Inf features
            if np.any(np.isnan(features)) or np.any(np.isinf(features)):
                features = np.nan_to_num(features, nan=0.0, posinf=0.0, neginf=0.0)

            X_all.append(features)
            if n_classes == 8:
                y_all.append(trial.direction_label_8)
            elif n_classes == 4:
                y_all.append(trial.direction_label_4)
            else:
                y_all.append(trial.direction_label_36)
            valid_indices.append(i)

        X_all = np.array(X_all)
        y_all = np.array(y_all)

        # Split
        train_mask = np.isin(valid_indices, train_indices)
        test_mask = np.isin(valid_indices, test_indices)

        X_train = X_all[train_mask]
        y_train = y_all[train_mask]
        X_test = X_all[test_mask]
        y_test = y_all[test_mask]

        if len(X_train) == 0 or len(X_test) == 0:
            logger.warning(f"  Skipping {spec.requested_ms}ms: insufficient data")
            continue

        # Train
        model = create_model(model_name)
        model.fit(X_train, y_train)

        # Predict
        y_pred = model.predict(X_test)

        # Evaluate
        metrics = evaluate_predictions(y_test, y_pred, n_classes)

        wr = WindowResult(
            window_ms=spec.requested_ms,
            effective_ms=spec.effective_ms,
            n_samples=spec.n_samples,
            accuracy=metrics["accuracy"],
            macro_f1=metrics["macro_f1"],
            per_class_precision=metrics["per_class_precision"],
            per_class_recall=metrics["per_class_recall"],
            per_class_f1=metrics["per_class_f1"],
            confusion_matrix=metrics["confusion_matrix"],
            n_train=len(X_train),
            n_test=len(X_test),
        )
        window_results.append(wr)

        logger.info(f"    Accuracy: {wr.accuracy:.4f}, Macro F1: {wr.macro_f1:.4f} "
                     f"(train={wr.n_train}, test={wr.n_test})")

        # Save model for this window
        model_path = MODELS_DIR / f"{model_name}_{n_classes}class_{int(spec.requested_ms)}ms.joblib"
        joblib.dump(model, model_path)

    # --- Phase 5: Save results ---
    if n_classes == 8:
        class_names = DIRECTION_LABELS_8
    elif n_classes == 4:
        class_names = DIRECTION_LABELS_4
    else:
        class_names = [f"Dir_{i*10}" for i in range(36)]

    experiment = ExperimentResult(
        experiment_id=f"baseline_{model_name}_{n_classes}c_{alignment}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        model_name=model_name,
        n_classes=n_classes,
        class_names=class_names,
        alignment=alignment,
        preprocessing=preprocess_config.to_dict(),
        subjects_train=sorted(train_subjects),
        subjects_test=sorted(test_subjects),
        split_method="subject_split_70_30",
        window_results=window_results,
        timestamp=datetime.now().isoformat(),
        notes="Review 1 preliminary baseline. Subject-level 70/30 split. NOT final LOSO evaluation.",
    )

    filepath = save_experiment_result(experiment)
    logger.info(f"\nExperiment saved: {filepath}")

    # Print summary table
    print("\n" + "=" * 90)
    print(f"  RESULTS: {model_name} | {n_classes} classes | {alignment}-aligned")
    print("=" * 90)
    print(f"  {'Window':>8} | {'Samples':>7} | {'Eff. ms':>8} | {'Accuracy':>8} | {'Macro F1':>8} | {'Train':>5} | {'Test':>5}")
    print("-" * 90)
    for wr in window_results:
        print(f"  {wr.window_ms:>6.0f}ms | {wr.n_samples:>7} | {wr.effective_ms:>7.1f}ms | "
              f"{wr.accuracy:>8.4f} | {wr.macro_f1:>8.4f} | {wr.n_train:>5} | {wr.n_test:>5}")
    print("=" * 90)

    return experiment


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run baseline latency-vs-accuracy experiment")
    parser.add_argument("--subjects", type=str, default=None,
                        help="Comma-separated subject IDs (e.g., S1,S2,S3)")
    parser.add_argument("--n-classes", type=int, default=8, choices=[4, 8, 36])
    parser.add_argument("--model", type=str, default="logistic_regression",
                        choices=["logistic_regression", "linear_svm", "random_forest"])
    parser.add_argument("--alignment", type=str, default="onset",
                        choices=["onset", "cue"])
    args = parser.parse_args()

    subjects = args.subjects.split(",") if args.subjects else None

    run_experiment(
        subjects=subjects,
        n_classes=args.n_classes,
        model_name=args.model,
        alignment=args.alignment,
    )

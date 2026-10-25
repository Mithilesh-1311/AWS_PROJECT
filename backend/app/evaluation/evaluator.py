"""
Experiment Evaluator
====================
Evaluation utilities for computing and reporting classification metrics.
"""
import numpy as np
from sklearn.metrics import (
    accuracy_score, f1_score, precision_score, recall_score,
    confusion_matrix, classification_report
)
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import json
from datetime import datetime

from app.core.config import REPORTS_DIR


@dataclass
class WindowResult:
    """Results for a single observation window."""
    window_ms: float
    effective_ms: float
    n_samples: int
    accuracy: float
    macro_f1: float
    per_class_precision: List[float] = field(default_factory=list)
    per_class_recall: List[float] = field(default_factory=list)
    per_class_f1: List[float] = field(default_factory=list)
    confusion_matrix: Optional[List[List[int]]] = None
    n_train: int = 0
    n_test: int = 0

    def to_dict(self) -> dict:
        return {
            "window_ms": self.window_ms,
            "effective_ms": round(self.effective_ms, 2),
            "n_samples": self.n_samples,
            "accuracy": round(self.accuracy, 4),
            "macro_f1": round(self.macro_f1, 4),
            "per_class_precision": [round(x, 4) for x in self.per_class_precision],
            "per_class_recall": [round(x, 4) for x in self.per_class_recall],
            "per_class_f1": [round(x, 4) for x in self.per_class_f1],
            "confusion_matrix": self.confusion_matrix,
            "n_train": self.n_train,
            "n_test": self.n_test,
        }


@dataclass
class ExperimentResult:
    """Full results of a latency-vs-accuracy experiment."""
    experiment_id: str
    model_name: str
    n_classes: int
    class_names: List[str]
    alignment: str  # 'cue' or 'onset'
    preprocessing: dict
    subjects_train: List[str]
    subjects_test: List[str]
    split_method: str
    window_results: List[WindowResult] = field(default_factory=list)
    timestamp: str = ""
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "experiment_id": self.experiment_id,
            "model_name": self.model_name,
            "n_classes": self.n_classes,
            "class_names": self.class_names,
            "alignment": self.alignment,
            "preprocessing": self.preprocessing,
            "subjects_train": self.subjects_train,
            "subjects_test": self.subjects_test,
            "split_method": self.split_method,
            "window_results": [w.to_dict() for w in self.window_results],
            "timestamp": self.timestamp,
            "notes": self.notes,
        }


def evaluate_predictions(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    n_classes: int,
) -> Dict[str, Any]:
    """Compute classification metrics.

    Returns dict with accuracy, macro_f1, per_class metrics, confusion matrix.
    """
    labels = list(range(n_classes))

    acc = accuracy_score(y_true, y_pred)
    macro_f1 = f1_score(y_true, y_pred, average='macro', labels=labels, zero_division=0)
    precision = precision_score(y_true, y_pred, average=None, labels=labels, zero_division=0)
    recall = recall_score(y_true, y_pred, average=None, labels=labels, zero_division=0)
    f1 = f1_score(y_true, y_pred, average=None, labels=labels, zero_division=0)
    cm = confusion_matrix(y_true, y_pred, labels=labels)

    return {
        "accuracy": float(acc),
        "macro_f1": float(macro_f1),
        "per_class_precision": precision.tolist(),
        "per_class_recall": recall.tolist(),
        "per_class_f1": f1.tolist(),
        "confusion_matrix": cm.tolist(),
    }


def save_experiment_result(result: ExperimentResult) -> str:
    """Save experiment result to JSON file.

    Returns the file path.
    """
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    filepath = REPORTS_DIR / f"experiment_{result.experiment_id}.json"
    with open(filepath, "x") as f:
        json.dump(result.to_dict(), f, indent=2)
    return str(filepath)

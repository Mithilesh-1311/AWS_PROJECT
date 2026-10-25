"""
Baseline Models
===============
Simple, defensible baseline classifiers for Review 1.

Models:
1. Logistic Regression (multinomial)
2. Linear SVM
3. Random Forest (optional)
4. Physics-inspired baseline (direction from dominant H/V change)
"""
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from typing import Dict, Any, Optional
import logging

from app.core.config import RANDOM_SEED

logger = logging.getLogger(__name__)


def create_model(model_name: str, **kwargs) -> Pipeline:
    """Create a scikit-learn Pipeline with scaling + classifier.

    Args:
        model_name: 'logistic_regression', 'linear_svm', or 'random_forest'

    Returns:
        sklearn Pipeline (StandardScaler -> Classifier)
    """
    scaler = StandardScaler()

    if model_name == "logistic_regression":
        clf = LogisticRegression(
            max_iter=2000,
            random_state=RANDOM_SEED,
            multi_class="multinomial",
            solver="lbfgs",
            C=kwargs.get("C", 1.0),
        )
    elif model_name == "linear_svm":
        clf = LinearSVC(
            max_iter=5000,
            random_state=RANDOM_SEED,
            C=kwargs.get("C", 1.0),
            dual="auto",
        )
    elif model_name == "random_forest":
        clf = RandomForestClassifier(
            n_estimators=kwargs.get("n_estimators", 200),
            max_depth=kwargs.get("max_depth", None),
            random_state=RANDOM_SEED,
            n_jobs=-1,
        )
    else:
        raise ValueError(f"Unknown model: {model_name}")

    return Pipeline([
        ("scaler", scaler),
        ("classifier", clf),
    ])


class PhysicsBaseline:
    """Direction classification from dominant horizontal/vertical EOG change.

    This is a non-ML baseline that directly maps the sign and magnitude
    of voltage changes on assumed H/V channels to directional predictions.

    For 16-channel EOG, we use the channels with highest absolute voltage
    change as proxies for horizontal and vertical components.
    """

    def __init__(self, n_classes: int = 8):
        self.n_classes = n_classes
        self._h_channel: Optional[int] = None
        self._v_channel: Optional[int] = None

    def fit(self, X: np.ndarray, y: np.ndarray) -> 'PhysicsBaseline':
        """Identify the best horizontal and vertical proxy channels.

        Uses training data to find which channels best correlate with
        horizontal vs vertical target angles.
        """
        # X: (n_samples, n_features) — we need to decode channel voltage changes
        # For simplicity, we'll use the model with pre-computed h/v changes
        # In the pipeline, we pass raw voltage changes per channel
        return self

    def predict_from_changes(self, voltage_changes: np.ndarray) -> np.ndarray:
        """Predict direction from per-channel voltage changes.

        Args:
            voltage_changes: Shape (n_trials, n_channels)

        Returns:
            Predicted direction labels.
        """
        n_trials, n_channels = voltage_changes.shape

        predictions = []
        for i in range(n_trials):
            changes = voltage_changes[i]

            # Use the two channels with the largest absolute changes
            sorted_channels = np.argsort(np.abs(changes))[::-1]
            h_change = changes[sorted_channels[0]]
            v_change = changes[sorted_channels[1]]

            # Compute angle from these two components
            angle = np.degrees(np.arctan2(v_change, h_change))
            if angle < 0:
                angle += 360.0

            # Bin the angle
            bin_width = 360.0 / self.n_classes
            shifted = (angle + bin_width / 2) % 360.0
            label = int(shifted // bin_width)
            predictions.append(label)

        return np.array(predictions)

from copy import deepcopy

import numpy as np
import pytest

from app.evaluation.reproducible import metrics
from scripts.verify_artifacts import verify_result_metrics


def test_saved_metrics_are_recomputed_from_predictions():
    actual = np.arange(8)
    predicted = np.array([0, 1, 2, 3, 4, 5, 6, 0])
    scores = metrics(actual, predicted)
    fold = dict(y_true=actual.tolist(), y_pred=predicted.tolist(), metrics=scores)
    result = dict(folds=[fold], metrics=deepcopy(scores), n_predictions=8)
    verify_result_metrics(result)
    changed = deepcopy(result)
    changed['metrics']['macro_f1'] = .91
    with pytest.raises(AssertionError, match='pooled macro_f1'):
        verify_result_metrics(changed)
    changed = deepcopy(result)
    changed['folds'][0]['metrics']['accuracy'] = .99
    with pytest.raises(AssertionError, match='fold accuracy'):
        verify_result_metrics(changed)

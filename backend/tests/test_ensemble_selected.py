import numpy as np
import pytest
from scripts.ensemble_selected import majority_vote, select_members


def test_majority_and_ties_preserve_inner_selection_priority():
    predictions = [[7, 6, 3, 4], [2, 2, 3, 1], [2, 3, 5, 4]]
    assert np.array_equal(majority_vote(predictions), [2, 6, 3, 4])
    with pytest.raises(ValueError, match='three ordered'):
        majority_vote(predictions[:2])


def test_members_use_inner_scores_and_distinct_representations():
    candidates = [
        {'config': {'family':'rbf_svm', 'C':1}, 'balanced_accuracy':.8},
        {'config': {'family':'rbf_svm', 'C':10, 'features':'all'}, 'balanced_accuracy':.85},
        {'config': {'family':'rbf_svm', 'features':'normalized_all'}, 'balanced_accuracy':.9},
        {'config': {'family':'rbf_svm', 'features':'normalized_spatial'}, 'balanced_accuracy':.7},
    ]
    assert select_members(candidates) == [candidates[2]['config'], candidates[1]['config'], candidates[3]['config']]
    with pytest.raises(ValueError, match='distinct'):
        select_members(candidates[:3])


def test_members_rank_macro_f1_when_requested():
    candidates = [dict(config=dict(features=features), macro_f1=f1, balanced_accuracy=balanced)
                  for features, f1, balanced in [('all', .7, .95), ('normalized_all', .9, .8),
                                                 ('normalized_spatial', .8, .85), ('normalized_directional', .6, .99)]]
    assert select_members(candidates, 'macro_f1') == [candidates[i]['config'] for i in [1, 2, 0]]

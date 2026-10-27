# Macro-F1 search — 27 October 2026

## Results

**The best new result is 88.7931% accuracy and 0.886998 macro F1 at 400 ms. The 0.90 macro-F1 target was not reached.** Compared with the previous 400 ms ensemble, this is +0.2781 percentage points accuracy and +0.2873 points macro F1, with the same 3,596 eligible trials. It yields 3,193 correct predictions versus 3,183 previously.

The active 100 ms logistic model remains unchanged: 77.8393% evaluated accuracy and 0.779398 macro F1. The new 100 ms search/vote did not outperform that model by accuracy or macro F1.

| Method | Window | Accuracy | Macro F1 | Eligible trials |
|---|---:|---:|---:|---:|
| Macro-F1 search | 100 ms | 77.1745% | 0.772856 | 3,610 |
| Inner-selected vote | 100 ms | 77.6731% | 0.778929 | 3,610 |
| Macro-F1 search | 200 ms | 83.7119% | 0.836531 | 3,610 |
| **Inner-selected vote** | **200 ms** | **84.1828%** | **0.841217** | **3,610** |
| Macro-F1 search | 400 ms | 88.2369% | 0.881379 | 3,596 |
| **Inner-selected vote** | **400 ms** | **88.7931%** | **0.886998** | **3,596** |
| Macro-F1 search | 600 ms | 87.7419% | 0.876730 | 3,255 |
| Inner-selected vote | 600 ms | 88.4485% | 0.883734 | 3,255 |
| Macro-F1 search | 800 ms | 86.3254% | 0.863195 | 1,426 |
| Inner-selected vote | 800 ms | 87.6578% | 0.875941 | 1,426 |
| Waveform search | 400 ms | 88.1257% | 0.880537 | 3,596 |
| Waveform vote | 400 ms | 87.9032% | 0.878120 | 3,596 |

Longer windows did not improve the pooled result, and the waveform representation did not beat the existing feature representation. More tuning alone did not establish that 90% is attainable on this dataset under the same held-out-subject protocol.

Saved evidence: [search](../backend/published/fb687e11e37148b6982aba8640fc3fd3.json), [ensemble](../backend/published/e8d2423168ef498dbf52c2eb57c6a573.json), [waveform study](../backend/published/3be75a315229475b83d35b49fa488052.json), and [metric/selection audit with matched-cohort comparisons](results/macro_f1_verification.json).

## Method

The target is macro F1 of at least 0.90 across all eight directions, evaluated with all 14 leave-one-subject-out folds. The original serving model and its published 100 ms result are preserved.

The fixed search contains 20 configurations from six families: RBF SVM, polynomial SVM, logistic regression, shrinkage LDA, distance-weighted nearest neighbors, and Extra Trees. Feature representations include the original 212 features and per-trial normalized full, spatial and directional subsets. No dependencies were added.

Within each outer fold, three grouped inner folds evaluate every candidate. Selection maximizes the mean of the 13 training subjects' macro F1 scores. StandardScaler is fitted only on each corresponding training partition. The selected candidate is then refitted on all outer-training subjects. Outer-test subjects do not select candidates or ensemble members. The fixed ensemble takes the three highest-ranked distinct feature representations and resolves three-way ties using the highest inner-ranked member.

Requested observation budgets are 100, 200, 400, 600 and 800 ms. These are measured after the detected onset; they are not total cue-to-decision latency. Every result reports its own eligible-trial count and coverage. Longer windows must fit inside the same recorded outward phase, so they can exclude additional trials.

| Requested window | Eligible / source trials | Coverage | Median cue-to-decision readiness |
|---|---:|---:|---:|
| 100 ms | 3,610 / 4,032 | 89.53% | 332.03 ms |
| 200 ms | 3,610 / 4,032 | 89.53% | 433.59 ms |
| 400 ms | 3,596 / 4,032 | 89.19% | 632.81 ms |
| 600 ms | 3,255 / 4,032 | 80.73% | 824.22 ms |
| 800 ms | 1,426 / 4,032 | 35.37% | 980.47 ms |

There are 4,200 inner fits and 70 selected-model outer refits in the complete search; the three-member ensemble adds 210 outer refits. Earlier published results remain available for comparison.

The waveform study adds 16 fixed candidates on the same eligible 400 ms trials. It averages each observed channel into 16 time bins and compares raw, amplitude-normalized, common-reference-contrast, and hybrid waveform/physical features. It uses the same three-inner-fold macro-F1 selection procedure and separately evaluates a three-view vote. Its 672 inner fits and 42 shared selected/vote-member outer refits bring this session to **5,194 model fits**. The waveform cache checks exact trial-ID and target alignment against the original physical-feature cache.

## Dashboard and verification

The dashboard formats the saved macro-F1 fraction as a percentage and lets the user select the model/window row. A value of 0.779398 displays as 77.94%. The value comes directly from the selected experiment's recorded metrics.

`python -m scripts.verify_artifacts` now recomputes every fold and pooled metric from its saved predictions and compares saved targets against the original dataset's trial labels. Tests cover changed-metric rejection, train/test subject separation, candidate construction, macro-F1 selection, vote/tie behavior, and dashboard percentage selection.

## Reproduction

From `backend`, in the pinned clean environment with the dataset installed:

```powershell
python -m scripts.tune_classical --search macro --windows 100,200,400,600,800
python -m scripts.ensemble_selected <completed-search-experiment-id>
python -m scripts.tune_waveform
python -m scripts.verify_artifacts
```

Each experiment records source data hashes, code hashes, candidate scores, selected settings, held-out predictions, and eligibility counts. The nested-CV procedure follows the separation described in [scikit-learn's model-selection documentation](https://scikit-learn.org/stable/auto_examples/model_selection/plot_nested_cross_validation_iris.html).

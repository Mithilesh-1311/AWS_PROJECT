# Additional accuracy experiments — 26 October 2026

**This document records the first follow-up.** A later round improved the best 400 ms accuracy to **88.52%** and 200 ms accuracy to **83.99%**. See [round 2 results](ACCURACY_ROUND_2_RESULTS.md) for the current comparison and checks. The original results below are preserved.

## Outcome

**Best observed result: 88.0701% accuracy at a 400 ms requested observation budget**, using a nested classical-model search and 14-subject leave-one-subject-out (LOSO) evaluation. This exceeds 85% on the evaluated eligible trials. **90% pooled accuracy was not achieved.** The best existing 100 ms result remains 77.8393%; extra TCN epochs did not improve it.

The active 100 ms serving model was not replaced. The new model-search result is an evaluated selection procedure whose selected estimator can differ by fold, not a newly deployable single serving binary. The 400 ms observation budget is not total cue-to-decision latency.

## What was actually run

| Experiment | Actual work | Runtime for recorded training/evaluation loop |
|---|---|---:|
| Nested classical search | Nine candidates × 14 outer folds × three budgets; 378 inner candidate fits plus 42 selected-model refits | 139.43 seconds |
| TCN epoch-ceiling experiment | All 14 outer subjects; increase maximum epochs from 30 to 100; retain training-subject early stopping and outer-training refit | 51.66 seconds |
| Clean-runtime backend tests | Full backend suite including the new selection test | 48 passed, 1 optional Torch test skipped; 12.23 seconds |
| Torch-enabled backend tests | Full backend suite with Torch imported first | 49 passed; 13.31 seconds |

Recorded experiment runtimes exclude startup/fingerprinting/cache loading before the timed loop. No hardware or internet latency benchmark was rerun.

## Evaluation safeguards

All models use the existing validated recordings and causal `physical-v2` feature pipeline. The search evaluates 100, 200, and 400 ms separately. Every outer fold holds out an entire subject. Only the remaining subjects enter candidate selection. The last lexicographically sorted training subject supplies inner validation; candidate ranking uses balanced accuracy. The selected pipeline is then refitted on all outer training subjects before predicting the outer test subject.

Every candidate includes a training-fitted StandardScaler. The held-out subject does not fit scaling or select candidate settings. The search suite was fixed before its outer results were inspected. The candidate family/configuration and all inner scores are preserved in each fold. All 14 outer subjects are included; difficult subjects and failed comparisons are retained.

This is an **exploratory follow-up on a previously studied dataset**, not an untouched external confirmation set. One inner validation subject is a relatively limited selection procedure. The new results should be reported alongside the original declared primary, not silently substituted for it.

## Candidate configurations

| Family | Fixed candidate settings |
|---|---|
| Logistic regression | C=0.1 and C=1.0; maximum 2,000 solver iterations |
| Shrinkage linear discriminant analysis | `solver=lsqr`, automatic shrinkage |
| RBF support-vector classifier | C in {1, 10, 100}, crossed with gamma in {scale, 0.001} |

This makes nine candidates. Random seed 42 and a one-thread numerical-library limit are used. The search runs in scikit-learn 1.5.2. It reuses existing feature caches; no dependency was added. Training labels and evaluation targets are not inputs to prediction.

## Full results, including unsuccessful comparisons

| Method | Requested budget | Accuracy | Balanced accuracy | Macro F1 | Eligible / source trials |
|---|---:|---:|---:|---:|---:|
| Existing primary logistic with inner C selection | 100 ms | **77.8393%** | 77.6625% | 0.779398 | 3,610 / 4,032 |
| New nested classical search | 100 ms | 76.1496% | 76.1322% | 0.764161 | 3,610 / 4,032 |
| TCN, original 30-epoch ceiling | 100 ms | 76.2327% | 76.0093% | 0.762474 | 3,610 / 4,032 |
| TCN, new 100-epoch ceiling | 100 ms | 76.2327% | 76.0093% | 0.762474 | 3,610 / 4,032 |
| Existing fixed logistic, identical-cohort comparison | 200 ms | 83.2592% | See original JSON | 0.831228 | 3,596 / 4,032 |
| New nested classical search | 200 ms | 82.2161% | 82.3652% | 0.822675 | 3,610 / 4,032 |
| Existing fixed logistic, identical-cohort comparison | 400 ms | 87.1524% | See original JSON | 0.870592 | 3,596 / 4,032 |
| **New nested classical search** | **400 ms** | **88.0701%** | **87.9912%** | **0.880046** | **3,596 / 4,032** |

The two 400 ms rows have exactly the same eligible trial IDs, so their pooled accuracy difference is **0.9177 percentage points**, or **33 additional correct classifications**. On paired trials, the new procedure corrects 139 baseline errors and introduces 106 errors where the baseline was correct. No subject-cluster-aware significance claim is made.

The 200 ms rows above have different eligible pools, so their score difference is descriptive rather than a fully matched comparison. The separate existing fixed-classical experiment reports 83.4072% random-forest accuracy at 200 ms on 3,610 eligible trials, also above the new 200 ms search result.

## Best result: coverage and subject variation

At 400 ms, 3,596 of 4,032 trials are eligible: **89.19% coverage**, with 436 excluded trials. Of the eligible predictions, 3,167 are correct and 429 incorrect. Accuracy is conditional on eligible windows and does not count excluded cues as correct predictions.

| Held-out subject | Eligible trials | New 400 ms accuracy |
|---|---:|---:|
| S1 | 282 | 88.65% |
| S2 | 246 | 92.68% |
| S3 | 241 | 89.21% |
| S4 | 218 | 83.94% |
| S5 | 281 | 91.46% |
| S6 | 263 | 93.16% |
| S7 | 185 | 79.46% |
| S8 | 192 | 82.29% |
| S9 | 284 | 88.73% |
| S10 | 279 | 88.53% |
| S11 | 286 | 93.01% |
| S12 | 285 | 90.18% |
| S13 | 287 | 90.24% |
| S14 | 267 | 76.03% |

Six individual subject folds exceed 90%, but the complete pooled result is 88.07%. Reporting only those six would misrepresent full-cohort performance. RBF SVM is selected in 12 folds, logistic regression in one, and shrinkage LDA in one.

The saved 2,000-resample subject-bootstrap interval for **mean subject accuracy** is **84.90%–90.15%**. This is a different statistic from pooled trial accuracy and not an independent-validation interval. Its upper bound is not evidence that 90% accuracy was achieved, and its lower bound does not establish a population accuracy floor above 85%.

## Why more epochs did not help

The original TCN already selected epochs using a training subject and stopped after five epochs without validation-loss improvement. Increasing the ceiling to 100 retained those safeguards. Selected epochs across S1–S14 were:

```text
7, 17, 15, 9, 10, 3, 5, 2, 2, 23, 13, 9, 3, 4
```

All selected epochs remained below the old ceiling. The new run exactly reproduced the original per-fold prediction arrays, accuracy, and macro F1. It did not train every fold for 100 epochs: 100 was the maximum allowed during inner selection, and early stopping/refit used fewer epochs. More epochs alone therefore provide no measured improvement for this architecture/configuration.

## Saved evidence and reproduction

| File | Content |
|---|---|
| [Nested search experiment](../backend/published/3777b650b8cd46da84c1408ea92eb9aa.json) | All 42 outer folds, inner candidate scores/settings, predictions, metrics, coverage, source hashes |
| [100-epoch-ceiling TCN experiment](../backend/published/0e7aaf024f1e4afdab6a2f3bc13cda48.json) | All 14 folds, selected epochs, checkpoint hashes, predictions, metrics |
| [Search runner](../backend/scripts/tune_classical.py) | Fixed candidate suite, nested selection, immutable experiment output, resume |
| [Selection test](../backend/tests/test_tune_classical.py) | Disjoint inner subject selection, candidate records, fit behavior, invalid subject-count rejection |
| [Original primary result](../backend/published/46c8ad758f244c698eaceb90f161219a.json) | Original 100 ms result, retained as the serving/evaluation primary |

From `backend`, reproduce the classical search using the clean environment:

```powershell
.\.venv-clean\Scripts\python.exe -m scripts.tune_classical
```

Reproduce the epoch experiment in the existing Torch-capable environment:

```powershell
.\.venv\Scripts\python.exe -m scripts.train_tcn --max-epochs 100
```

Both commands produce a new experiment ID. The classical runner also supports `--windows 100,200,400` and `--resume <incomplete-id>` with matching configuration/source/script hash. Full recordings are required. Generated checkpoints/cache remain local and excluded from Git; published JSON contains derived results rather than raw recordings.

Before publishing these results, fold counts, subject separation, prediction counts, accuracy/F1 recomputation, selected-inner-score maxima, identical 400 ms trial IDs, and exact TCN prediction reproduction were checked. The project artifact verifier checks the published source/split invariants as well.

## Report wording

> An exploratory nested model-selection experiment achieved 88.07% pooled accuracy and 0.8800 macro F1 at a requested 400 ms observation budget under 14-subject LOSO evaluation, with 89.19% trial coverage. The original 100 ms primary remained 77.84%. Increasing the TCN epoch ceiling from 30 to 100 did not improve its 76.23% result under early stopping. A pooled 90% result was not obtained.

Next report action: add this paragraph as a follow-up experiment, retaining the observation budget, coverage, and exploratory qualification.

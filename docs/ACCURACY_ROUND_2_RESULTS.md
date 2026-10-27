# Accuracy follow-up, round 2 — 26 October 2026

## Result

**Best observed accuracy increased from 88.07% to 88.52% at a 400 ms requested observation budget.** The best 200 ms accuracy increased from 83.41% to **83.99%**. The original 100 ms primary remains best by accuracy at **77.84%**. Pooled 90% accuracy was not achieved.

| Observation budget | Best before this round | Best after this round | Change |
|---|---:|---:|---:|
| 100 ms | 77.8393% | 77.8393% | No improvement |
| 200 ms | 83.4072% | 83.9889% | +0.5817 percentage points |
| 400 ms | 88.0701% | 88.5150% | +0.4449 percentage points |

These are recorded-data, eight-class, 14-subject LOSO results. The 100/200 ms experiments include 3,610 eligible trials (89.53% coverage). The 400 ms experiments include 3,596 eligible trials (89.19% coverage). Observation budget is distinct from total cue-to-decision latency. The active serving model remains the original declared 100 ms logistic model; the new results are comparison experiments.

## Experiments executed

| Experiment | Work performed | Measured training/evaluation loop time |
|---|---|---:|
| Grouped feature search | 16 candidates, three inner grouped folds, 14 outer subjects, three budgets; 2,016 inner fits and 42 outer refits | 743.01 seconds |
| Diverse three-member ensemble | Reuse recorded inner-validation scores, choose three different feature representations, refit three models per outer fold; 126 additional fits | 41.01 seconds |
| Full-window causal TCN | Four convolutional layers, 32 hidden channels, maximum 100 epochs with training-only early stopping; 14 outer folds | 88.99 seconds |

The classical experiments therefore performed **2,184 fits**. Runtime values exclude preprocessing/startup outside each runner's timer. Some work ran concurrently, so these durations should not be summed as an exact wall-clock session duration.

## 1. Stronger training-only model selection

The first follow-up chose settings using one validation subject. This round uses three `GroupKFold` splits inside every outer training set. For each outer held-out subject, the other 13 subjects are divided into inner training/validation sets. Every outer-training subject appears in inner validation exactly once, and no inner split contains the outer test subject.

Candidate scores are calculated separately for each inner-validation subject using balanced accuracy, then averaged equally over the 13 subjects. This reduces the influence of one validation subject or unequal eligible trial counts on selection. Each pipeline fits its own StandardScaler on its inner training rows. After selection, the pipeline is refitted on all 13 outer-training subjects.

The fixed candidate suite contains:

| Candidate group | Settings | Number |
|---|---|---:|
| RBF SVM on each of four feature representations | C in {0.1, 1, 10}; gamma=`scale` | 12 |
| RBF SVM on original features | C in {1, 10}; gamma=0.001 | 2 |
| Logistic regression on original features | C=0.1 | 1 |
| Shrinkage LDA on original features | LSQR solver, automatic shrinkage | 1 |

Settings are selected from inner scores; outer scores do not select a candidate within a fold. This remains an exploratory follow-up on an already studied cohort, not a new external confirmation set.

## 2. Per-trial normalization and feature choices

The experiment reuses the 212 `physical-v2` features extracted from each eligible causal window. It tests four representations:

| Representation | Dimensions | Contents |
|---|---:|---|
| Original | 212 | Existing per-channel and cross-channel features |
| Normalized full | 212 | All features with per-trial amplitude scaling |
| Normalized spatial | 96 | Per-channel change, mean, standard deviation, minimum, maximum, range |
| Normalized directional | 64 | Per-channel change, mean, slope, mean derivative |

The scale is the root mean square of the 16 channel ranges within the observed window, with a numerical floor of 1e-12. Amplitude-linear features are divided by this scale; signal and derivative energy features are divided by its square. Cross-channel index and correlation remain unchanged. No other trial, label, or future sample estimates this scale.

This tests whether removing overall amplitude differences makes the direction pattern more transferable across subjects. The following StandardScaler is still fitted exclusively on the relevant training partition. A new test confirms that multiplying a synthetic raw window by seven leaves its normalized representations unchanged, that input arrays are not mutated, and that zero-valued inputs remain finite.

## 3. Diverse ensemble

The ensemble uses the completed grouped-search inner scores. It first ranks candidates by their mean subject balanced accuracy, then keeps the highest-ranked candidate for each feature representation. The top three distinct representations become the three members. Each member is refitted on all outer-training subjects.

Prediction uses an unweighted majority vote. If all three predict different classes, the highest inner-validation-ranked member resolves the tie. This rule was fixed before the ensemble's outer predictions were evaluated. No held-out label chooses the members or resolves the vote.

The experiment records its parent experiment ID, the parent's manifest SHA256, all inner candidate scores, selected member configurations, outer predictions, and metrics. The parent selection scores and trial IDs are verified unchanged. The selected members may differ by outer fold, so this is evaluation of a selection-and-ensemble procedure rather than one deployed model file.

## 4. Larger causal TCN

The original TCN has three kernel-size-three layers with dilations 1, 2, and 4. Its final encoded output has a direct receptive field of:

```text
1 + 2 × (1 + 2 + 4) = 15 input samples
```

The 100 ms input contains 26 samples. The new variant uses four layers with dilations 1, 2, 4, and 8, giving a 31-sample direct receptive field, and increases hidden channels from 24 to 32. It has **11,144 parameters**, compared with the original 4,880. Earlier causal preprocessing has its own state; the receptive-field statement concerns direct access to the model's input tensor.

The larger model retains left padding, last-valid-sample selection, training-fitted normalization, and the existing inner-subject early-stopping procedure. Maximum epochs are 100; patience remains five. Selected epochs for S1–S14 were:

```text
7, 3, 15, 22, 13, 9, 22, 3, 2, 6, 10, 9, 3, 6
```

Its accuracy was **75.2355%**, below the original TCN's 76.2327%. A larger receptive field and more parameters did not improve this evaluation. The result is retained rather than discarded.

The default TCN remains compatible with old checkpoints. A separate check loaded all 14 original checkpoints and exactly reproduced all 3,610 original predictions. Tests also confirm that the new architecture can respond to the first of 26 input samples while preserving future-prefix and padded-tail invariance.

## Complete new results

| Method | Window | Accuracy | Balanced accuracy | Macro F1 | Eligible trials |
|---|---:|---:|---:|---:|---:|
| Grouped feature search | 100 ms | 77.6731% | 77.4736% | 0.778162 | 3,610 |
| Diverse ensemble | 100 ms | 77.7562% | 77.5371% | 0.779640 | 3,610 |
| Full-window TCN | 100 ms | 75.2355% | 74.9334% | 0.754667 | 3,610 |
| Grouped feature search | 200 ms | 83.7396% | 83.5018% | 0.837036 | 3,610 |
| **Diverse ensemble** | **200 ms** | **83.9889%** | **83.7305%** | **0.839300** | **3,610** |
| Grouped feature search | 400 ms | 87.8476% | 87.6935% | 0.877499 | 3,596 |
| **Diverse ensemble** | **400 ms** | **88.5150%** | **88.3461%** | **0.884124** | **3,596** |

At 100 ms the ensemble's macro F1 is slightly higher than the original primary's 0.779398, but its accuracy is lower: 2,807 correct predictions versus 2,810. The accuracy and F1 objectives should not be conflated.

At 200 ms, the ensemble gets 3,032 eligible trials correct, compared with 3,011 for the earlier fixed random forest. At 400 ms it gets 3,183 correct, compared with 3,167 for the previous 88.07% search result. The 400 ms trial IDs are identical for that comparison.

## Best result by held-out subject

| Subject | Eligible 400 ms trials | Ensemble accuracy |
|---|---:|---:|
| S1 | 282 | 88.65% |
| S2 | 246 | 94.31% |
| S3 | 241 | 87.55% |
| S4 | 218 | 83.94% |
| S5 | 281 | 92.17% |
| S6 | 263 | 95.06% |
| S7 | 185 | 79.46% |
| S8 | 192 | 86.46% |
| S9 | 284 | 88.73% |
| S10 | 279 | 88.53% |
| S11 | 286 | 93.71% |
| S12 | 285 | 92.28% |
| S13 | 287 | 88.50% |
| S14 | 267 | 75.28% |

Some subjects exceed 90%, but complete-cohort pooled accuracy is 88.52%. Reporting only those subjects would misrepresent the complete result. The 436 ineligible source trials remain excluded; they are not treated as successful classifications.

## Uncertainty and interpretation

The 400 ms ensemble's 2,000-resample subject-bootstrap interval for **mean subject accuracy** is 85.25%–90.87%. This is a different statistic from pooled accuracy and not an external-validation interval. An interval containing 90% does not mean a 90% point result was achieved.

A paired subject-bootstrap comparison with the previous 88.07% procedure estimates a mean subject-accuracy change of **+0.50 percentage points**, with a bootstrap interval of **−0.22 to +1.33 percentage points**. Because that interval includes zero, this small observed improvement should not be presented as a reliably established population-level gain. The pooled improvement is +0.4449 percentage points.

Repeated experiments on the same 14 subjects provide exploratory evidence. Independent recordings or a prospectively reserved dataset are still needed to confirm performance. More epochs, more parameters, or repeated search cannot guarantee 90% generalization.

## Verification performed

| Check | Result |
|---|---|
| Torch-capable full backend suite | **55 passed**, 10.99 seconds |
| Clean runtime full backend suite | **52 passed, 1 optional Torch module skipped**, 10.74 seconds |
| Original TCN checkpoint compatibility | All 14 checkpoints reproduce all 3,610 original predictions |
| Dataset/experiment artifact verifier | **PASS** for all 10 published experiments and the 4,032-trial source |
| Actual label and metric audit | **PASS** for 50 result rows and 180,290 prediction records |
| Grouped selection and ensemble lineage | Disjoint subjects, complete inner-validation coverage, member selection, parent scores/IDs, and code/parent checksums verified |

The 180,290 count includes repeated predictions across experiments and windows; it is not a new dataset of independent trials. Each saved true label was compared with the actual segmented source trial, and accuracy, balanced accuracy, macro F1, and confusion matrices were recomputed.

The machine-readable audit is [accuracy_round2_verification.json](results/accuracy_round2_verification.json). Existing dependency deprecation warnings remain. Frontend/browser, cloud, connected-sensor, and latency benchmarks were not rerun for these offline training changes.

## Evidence and reproduction

| Artifact | Contents |
|---|---|
| [Grouped feature search](../backend/published/ec81293dc3054ee5892c8c0a9f091855.json) | 42 outer folds, inner scores for all 16 candidates, predictions, source fingerprint, versions |
| [Diverse ensemble](../backend/published/28e22af2c66946d49dccc40de67946c4.json) | 42 outer folds, selected members, parent provenance, predictions, metrics |
| [Full-window TCN](../backend/published/2d640404ae4f4c85a2df293472607f57.json) | 14 folds, epoch selection, checkpoint hashes, predictions, metrics |
| [Classical runner](../backend/scripts/tune_classical.py), [ensemble runner](../backend/scripts/ensemble_selected.py) | Reproducible searches and fixed voting rule |
| [TCN runner](../backend/scripts/train_tcn.py), [artifact verifier](../backend/scripts/verify_artifacts.py) | Architecture experiment and source/split verification |

Run from `backend` with recordings installed:

```powershell
.\.venv-clean\Scripts\python.exe -m scripts.tune_classical --search grouped
```

After that run completes, substitute its new experiment ID:

```powershell
.\.venv-clean\Scripts\python.exe -m scripts.ensemble_selected <completed-grouped-experiment-id>
```

The Torch environment is required for the neural comparison:

```powershell
.\.venv\Scripts\python.exe -m scripts.train_tcn --architecture full_window --max-epochs 100
```

Raw data and generated checkpoints remain local. New JSON reports preserve both improvements and failed experiments. No new serving artifact was activated.

## Suggested report text

> A second exploratory study used three grouped inner-validation folds, per-trial amplitude-normalized feature representations, and an inner-selected three-member ensemble. The ensemble achieved 88.52% pooled accuracy and 0.8841 macro F1 at a requested 400 ms observation budget under 14-subject LOSO evaluation, with 89.19% coverage. At 200 ms it achieved 83.99%. The original 100 ms primary retained the highest accuracy at 77.84%. A larger causal TCN did not improve the result, and no 90% pooled accuracy was obtained. The small 400 ms gain remains uncertain under paired subject resampling.

Next report action: use the paragraph above as the latest follow-up result and retain the latency, coverage, and uncertainty qualifications.

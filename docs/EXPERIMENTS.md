# Reproducing the experiments

Run commands from `backend` with the environment's Python. Raw data is required for training; published reports remain readable without it. Generated artifacts go to `artifacts/experiments/<UUID>/`, not historical filenames. Manifests record source hashes, versions, configuration, feature order, splits, predictions, exclusions and timing. Completed experiments are not overwritten. Resume requires matching configuration and data; current runs also include the scikit-learn version in their configuration hash.

```powershell
python -m scripts.train_causal --evaluation loso
python -m scripts.train_causal --models logistic_regression --windows 100 --evaluation loso --serve
python -m scripts.train_causal --models logistic_regression --evaluation loso --matched-reference
python -m scripts.train_causal --evaluation loso --resume <incomplete-experiment-id>
```

Activate a newly trained model explicitly using the ID printed in its `model.json`:

```powershell
python -c "from app.models.registry import activate; activate('<experiment-id>_logistic_100')"
```

| Published evidence | Scope |
|---|---|
| `783d80f8dca64182ac9936824151069a` | Three fixed classical families, nine budgets including 400 ms, 14 outer subjects; 378 folds; sklearn 1.3.2 |
| `e8b21ac2bcc24329ab2dc1423841f1fe` | Logistic C=1; nine budgets; identical 3,596 eligible training/test trial pool; 126 folds; sklearn 1.5.2 |
| `46c8ad758f244c698eaceb90f161219a` | Final 100 ms logistic; training-only C selection; 14 LOSO folds; sklearn 1.5.2 |
| `5a9624aabedc4f5e9a61f79c05cf5777` | Causal TCN at 100 ms; 14 LOSO folds; 4,880 parameters; Torch 2.14.1+cpu |
| `6d6bad267e7a4ebeab04d33f279fc493` | Earlier nested logistic run under sklearn 1.3.2; preserved for version provenance |

All source fingerprints match. The eight short budgets are 20,40,60,80,100,120,160,200 ms. Classifiers use scaling fitted inside each training fold. RF settings are 80 trees/depth 12; linear SVM and fixed logistic use C=1. Full classical fixed-hyperparameter comparisons have 3,610 eligible trials up to 200 ms and 3,596 at 400 ms. Their `matched_metrics` intersect test IDs with the longer window; their training pools still differ. Use the separate matched-cohort experiment for comparisons with identical training pools.

| Fixed classical LOSO | 20 ms accuracy | 100 ms | 200 ms | 400 ms |
|---|---:|---:|---:|---:|
| Logistic | 68.37% | 76.81% | 83.24% | 87.12% |
| Linear SVM | 66.79% | 76.37% | 81.83% | 84.98% |
| Random forest | 67.84% | 76.70% | 83.41% | 86.90% |

Identical-cohort logistic (sklearn 1.5.2): 67.99%, 77.20%, 83.26%, 87.15% respectively. These comparison models have fixed C; they are distinct from the 77.84% nested primary result. Do not compare smoke jobs as if they were full evaluation.

Historical reproduction under sklearn 1.3.2 exactly matched the saved logistic subject holdout (test S1,S5,S7,S8): 64.50% at 20 ms and 75.87% at 200 ms. Its 1,000 ms point has only 98 test trials and is not a matched long-window comparison. Historical channel selection/onset are retrospective. Existing reports and model binaries were preserved. The supplied presentation's 210-feature count conflicts with the actual 212; its old 44.2/82.4 scores and broad causality/head-motion claims are not current verified results.

TCN is optional at installation time:

```powershell
python -m pip install -r requirements-tcn.txt
python -m scripts.train_tcn
python -m scripts.train_tcn --resume <incomplete-tcn-id>
```

TCN uses three left-padded convolutions (24 hidden channels; dilations 1,2,4), last-valid-sample pooling and training-only channel normalization. One inner training subject selects epochs (maximum 30, patience 5), followed by refitting all outer training subjects. Padded tails cannot alter an earlier output. Checkpoints and fold records permit resume. No GPU or external dataset was used.

Published JSONs contain derived predictions, not raw EOG. Older published copies explicitly correct an erroneous coverage denominator in their original manifests; original local manifests remain immutable and their SHA256 is recorded. Model binaries/cache/state remain excluded from new Git commits. `python -m scripts.verify_artifacts` checks real source hashes, split separation, prediction counts and matched IDs.

GRU/LSTM, spatial-temporal CNN, circular angle regression, channel selection, personalized adaptation and confidence-based stopping remain research extensions. They have not been trained or claimed complete.

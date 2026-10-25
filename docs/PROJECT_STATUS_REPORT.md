# Project status: everything completed so far

**Project:** Low-Latency EOG-Based Early Intent Detection for Eye Movements  
**Analyzed:** 25 October 2026  
**Scope:** Backend, frontend, tests, configuration, scripts, saved experiments, model artifacts, dataset structure, and existing project documentation.

## 1. Current answer

The project has a working **local research prototype** for loading recorded EOG signals, identifying trials, estimating eye-movement onset, extracting short observation windows, training baseline classifiers, and exploring signals and saved results through a web dashboard.

The strongest verified milestone is an end-to-end classical machine-learning baseline using all 14 subjects, with **64.50% accuracy at a requested 20 ms window** and **75.87% at 200 ms**, on four held-out subjects. These are saved experiment results, not newly retrained results from this audit.

The backend's **27 tests pass**, the frontend **production build passes**, and a fresh data-quality API run confirms **4,032 trials with no NaN or Inf values**. There are **seven routed dashboard pages**, plus an About page component that is not connected to navigation.

Existing documents call this the Review 1 or approximately 50% milestone. That is a planning label, not a measured completion percentage. Advanced models, LOSO validation, streaming, live model-serving predictions, and AWS deployment remain unimplemented in the inspected source.

## 2. Completion at a glance

| Area | What is done | Evidence/status |
|---|---|---|
| Dataset access | MATLAB loading, subject discovery, metadata, cached reads | Implemented; real data exercised |
| Dataset validation | Shapes, trial counts, NaN/Inf checks, channel statistics | Fresh quality check passed for 14 subjects |
| Trial segmentation | Outward, return, blink boundaries and direction labels | Implemented and tested |
| Preprocessing | Baseline correction, optional detrending, high-pass filtering, normalization | Implemented and tested; causality depends on settings |
| Onset estimation | RMS aggregation, smoothing, derivative threshold, MAD noise estimate | Implemented and tested; retrospective channel selection remains |
| Early windows | Cue/onset alignment, exact sample conversion, reject insufficient data | Implemented and tested |
| Features | 13 per channel plus four cross-channel features | 212 features with all 16 channels |
| Classifiers | Logistic regression, linear SVM, random forest factories | Implemented; only logistic regression has saved result evidence |
| Training/evaluation | Subject split, per-window models, metrics, JSON output | Two saved logistic-regression experiments |
| REST backend | Dataset, subject, signal, onset, processing, window, results, quality APIs | Tests and additional successful API smoke checks |
| Dashboard | Seven connected pages with charts and controls | Source inspected; production build passed |
| About page | Capability and roadmap component | Exists but is not routed |
| Automated verification | Seven backend test modules | 27 passed; no frontend test suite found |
| Documentation | README, methodology, dataset report, review guide, roadmap, analysis | Present; some claims need correction |
| Deployment | Local development and production frontend build | No AWS or container deployment implementation found |

## 3. Repository and architecture

```text
AWS project/
  backend/
    app/
      api/                 REST route handlers
      core/                Paths, constants, class names, random seed
      data/                MATLAB loader and trial segmentation
      signal_processing/   Preprocessing and onset estimation
      features/            Window conversion/extraction and features
      models/              Classical classifier factories and physics sketch
      evaluation/          Metrics and experiment serialization
      schemas/             Package scaffold
      main.py              FastAPI application
    scripts/               Inspection, investigation, reporting, training
    tests/                 Seven pytest modules
    artifacts/
      models/              Nine saved .joblib models
      reports/             Two experiments and one inspection report
  frontend/
    src/pages/             Eight page components; seven routed
    src/hooks/             Shared useFetch hook
    src/services/          Shared API client
    dist/                  Production build output
  Dataset_Isotropic/
    Dataset_Isotropic/     S1-S14 and dataset description PDF
  docs/                    Existing research documents and this report
  Dataset_Isotropic.zip
  Low-Latency-EOG-Based-Early-Intent-Detection-for-Eye-Movements.pptx
  README.md
```

The training path is:

```text
Recorded MATLAB data -> phase segmentation -> baseline correction
  -> estimated onset -> early window -> 212 features
  -> training-only StandardScaler -> classifier -> saved model and metrics
```

The dashboard calls FastAPI to explore recordings and read experiment JSON files. It does not currently execute the saved models to produce live predictions.

## 4. Dataset work completed

### 4.1 Files and recording structure

The extracted dataset contains **14 subject directories and 70 MATLAB files**, five per subject.

| File per subject | How the project uses it |
|---|---|
| `EOG.mat` | Multichannel eye-movement voltage recordings |
| `ControlSignal.mat` | Experimental phase segmentation |
| `Target_GA_stream.mat` | Horizontal/vertical targets and derived direction labels |
| `PD.mat` | Inter-pupillary-distance metadata |
| `Dist_screen.mat` | Screen-distance metadata |

| Property | Current evidence |
|---|---|
| Subjects | S1 through S14 |
| Channels | 16 |
| Sampling rate | Configured as 256 Hz |
| Sampling period | 3.90625 ms |
| Samples per subject | 299,819-299,825 in the fresh quality response |
| Recording length | Approximately 1,171 seconds per subject |
| Trials per subject | 288 |
| Total segmented trials | 4,032 |
| Fine target directions | 36, approximately 10-degree spacing |
| Target magnitude | 12 degrees, as documented/configured |
| Recorded EOG NaNs/Infs | Zero in the fresh full-data quality response |

The existing dataset report describes eight repetitions per fine direction and acquisition filtering at 30 Hz low-pass and 50 Hz notch. These acquisition details were read from project documentation; the original dataset PDF was not independently audited here.

### 4.2 Loading and memory management

Implemented in [`dataset_loader.py`](../backend/app/data/dataset_loader.py): on-demand `scipy.io.loadmat` reads; dictionary caching keyed by subject/file; typed subject/trial metadata; channel-preserving signal access; and explicit subject/all-data release methods.

The loader is a module singleton. Its cache is a normal dictionary, not an LRU cache. Subject metadata currently loads the EOG array, despite the method comment describing lightweight metadata. No memory ceiling is enforced or measured by this audit.

Dataset discovery tries project-relative locations and then a legacy absolute Windows path. The current extracted directory is discovered successfully. There is no implemented environment-variable override.

### 4.3 ControlSignal anomaly handling

| Value | Meaning used by the project | Handling |
|---|---|---|
| 1 | Outward eye movement | Creates outward trial segments |
| 2 | Return to center | Creates return segments |
| 3 | Blink/rest interval | Creates blink segments |
| 30 | Recording termination marker | Excluded from experimental phase segmentation |

The fresh quality response contains **14 termination samples in total**. Existing investigation documentation identifies one at the end of each recording. The quality endpoint still lists these expected markers as anomalies while allowing subjects to pass.

## 5. Trial segmentation and labels

[`trial_segmenter.py`](../backend/app/data/trial_segmenter.py) finds contiguous segments, pairs the outward/return/blink phases, and records absolute sample boundaries using exclusive end indices. It reads the target coordinates at outward start and computes direction using `atan2(vertical, horizontal)`.

| Label scheme | Implemented mapping | Experiment evidence |
|---|---|---|
| Four classes | Right, Up, Left, Down | Code/CLI support; no saved four-class run |
| Eight classes | Cardinal and diagonal directions | Both saved experiments use this |
| 36 classes | Nearest 10-degree-center bin | Code/CLI support; no saved 36-class run |

Signal extraction supports outward, return, blink, and full-trial phases, with optional channel selection. Segmentation warns about count/order mismatches but does not reject all malformed phase sequences; it pairs phase lists by position and uses the minimum available count.

## 6. Signal-processing work completed

### 6.1 Preprocessing

[`preprocessor.py`](../backend/app/signal_processing/preprocessor.py) exposes these operations:

| Operation | Implementation | Saved baseline configuration |
|---|---|---|
| Baseline correction | Subtract each channel's initial-sample mean | Enabled, first 25 samples |
| Detrending | SciPy linear/constant detrend | Disabled |
| High-pass filter | Butterworth; forward `lfilter` or offline `filtfilt` | Disabled |
| Signal normalization | Per-channel z-score; optional supplied training parameters | Disabled |
| Feature scaling | StandardScaler inside classifier pipeline | Fitted with training features |

The first 25 samples represent 97.65625 ms of sample budget. Baseline correction assumes this initial period is suitable for calibration. A very short cue-aligned window can therefore depend on baseline samples beyond its requested observation duration.

`causal_mode=True` changes the high-pass filtering branch to forward filtering. It does not automatically make detrending or full-trial normalization causal. The saved experiment sets `causal_mode=False`, but high-pass filtering is disabled, so its active filter path does not use `filtfilt`.

### 6.2 Onset detection

[`onset_detector.py`](../backend/app/signal_processing/onset_detector.py) is implemented as an estimated physiological onset detector, separate from the experimental cue.

| Stage | Current default behavior |
|---|---|
| Channel selection | Four channels with highest variance over the full outward phase |
| Movement signal | RMS across selected channels |
| Smoothing | Three-sample causal moving average |
| Movement derivative | Absolute first difference |
| Baseline noise | First 20 samples; MAD scaled by 1.4826, with standard-deviation fallback |
| Threshold | Baseline median plus five times noise estimate |
| Persistence | Three consecutive above-threshold samples |
| Search cap | Before sample 200 from cue |
| Reliability | Flag detections before 50 ms or after 500 ms as unreliable |

The detector returns the onset sample/time, reliability, reason, threshold, selected channels, aggregate signal, and derivative trace. Tests cover a synthetic saccade, a no-movement signal, and a short signal.

**Research limitation:** automatic channel selection inspects the entire outward phase. This is future information relative to an early streaming decision. Persistence confirmation also requires later samples than the reported first crossing. The current implementation is useful for retrospective alignment, but does not prove end-to-end real-time causality or latency.

The training runner keeps detected but unreliable onsets; failed detections fall back to cue sample zero. Counts are logged during training but are not preserved as structured onset-quality statistics in the saved experiment result.

## 7. Early observation windows

[`window_generator.py`](../backend/app/features/window_generator.py) converts requested milliseconds to integer samples with `ceil(duration_ms * 256 / 1000)`. It supports cue and detected-onset alignment, returns copies, and returns `None` when the requested end exceeds available samples. It does not pad insufficient windows.

| Requested window | Samples | Effective sample budget |
|---|---:|---:|
| 20 ms | 6 | 23.44 ms |
| 40 ms | 11 | 42.97 ms |
| 60 ms | 16 | 62.50 ms |
| 80 ms | 21 | 82.03 ms |
| 100 ms | 26 | 101.56 ms |
| 120 ms | 31 | 121.09 ms |
| 160 ms | 41 | 160.16 ms |
| 200 ms | 52 | 203.12 ms |

The runner adds a 1,000 ms / 256-sample reference. In onset alignment this requires 256 samples *after* onset, so most roughly one-second outward phases cannot provide it. That reference is evaluated on far fewer trials and is not a like-for-like full-trial comparison.

Reported milliseconds describe an observation budget, not measured cue-to-prediction latency. Reaction time, onset-confirmation delay, processing time, transport, and rendering are not included.

## 8. Feature extraction

[`feature_extractor.py`](../backend/app/features/feature_extractor.py) computes the following features for each channel:

| Group | Features |
|---|---|
| Displacement | End-minus-start voltage change |
| Statistics | Mean, standard deviation, minimum, maximum, range |
| Trend | Least-squares slope |
| First differences | Mean derivative, maximum positive derivative, maximum negative derivative, derivative energy |
| Energy/integral | Signal energy, trapezoidal area |

Four additional cross-channel values describe the dominant-change channel index, its voltage change, global range, and average adjacent-channel correlation. The default vector contains **16 x 13 + 4 = 212 features**.

Channel selection and the cross-channel toggle are implemented. `include_voltage`, `include_stats`, `include_derivative`, and `include_energy` exist in the configuration but are not used to select feature groups. Derivatives, slope, and integration use sample indices rather than explicit seconds. The experiment runner replaces nonfinite feature values with zero.

## 9. Models, training, and evaluation

### 9.1 Available models

| Model | Implementation | Evidence of completed runs |
|---|---|---|
| Logistic regression | Multinomial LBFGS, max 2,000 iterations, seed 42 | Two JSON reports and nine saved models |
| Linear SVM | LinearSVC, max 5,000 iterations | Factory/CLI support only |
| Random forest | Default 200 trees, parallel jobs, seed 42 | Factory/CLI support only |
| PhysicsBaseline | Direction heuristic from two dominant channel changes | Partial sketch; `fit()` is a no-op and CLI does not select it |

The three factory-created classifiers use a StandardScaler pipeline. No neural-network implementation or deep-learning dependency appears in the inspected project.

### 9.2 Experiment runner

[`run_baseline.py`](../backend/scripts/run_baseline.py) completes loading, segmentation, onset estimation, subject splitting, per-window feature extraction, training, prediction, metric calculation, model saving, and JSON reporting.

CLI options select subject IDs, 4/8/36 classes, one of the three classical models, and cue/onset alignment. The split shuffles unique subjects with seed 42 and holds out `max(1, int(subject_count * 0.3))` subjects. It is **one random subject-level holdout**, not stratified K-fold, GroupKFold, repeated validation, or LOSO. Importing GroupKFold does not mean it is executed.

Metrics include accuracy, macro F1, per-class precision/recall/F1, confusion matrix, train/test counts, and effective window duration. JSON metadata records model, classes, alignment, preprocessing, subject lists, split label, timestamp, and notes.

Model filenames encode model/classes/window but not experiment timestamp or alignment; rerunning can overwrite earlier models. Saved files are evidence of artifacts, not a verified version-to-experiment lineage.

### 9.3 Saved experiment inventory

| Saved run, 15 September 2026 | Subjects | Training/testing trials for 20-200 ms |
|---|---|---|
| `baseline_logistic_regression_8c_onset_20260915_225511` | Train S1/S3/S4/S5; test S2 | 1,152 / 288 |
| `baseline_logistic_regression_8c_onset_20260915_230013` | Ten train subjects; four test subjects | 2,880 / 1,152 |

The full-data run trains on **S2, S3, S4, S6, S9, S10, S11, S12, S13, S14** and tests on **S1, S5, S7, S8**. This is approximately 71.4%/28.6% of subjects, despite the nominal `subject_split_70_30` label.

### 9.4 Full-data saved results

Source: [`experiment_baseline_logistic_regression_8c_onset_20260915_230013.json`](../backend/artifacts/reports/experiment_baseline_logistic_regression_8c_onset_20260915_230013.json).

| Requested ms | Effective ms | Accuracy | Macro F1 | Train trials | Test trials |
|---:|---:|---:|---:|---:|---:|
| 20 | 23.44 | 64.50% | 0.6429 | 2,880 | 1,152 |
| 40 | 42.97 | 70.49% | 0.7059 | 2,880 | 1,152 |
| 60 | 62.50 | 71.96% | 0.7209 | 2,880 | 1,152 |
| 80 | 82.03 | 72.66% | 0.7277 | 2,880 | 1,152 |
| 100 | 101.56 | 71.61% | 0.7186 | 2,880 | 1,152 |
| 120 | 121.09 | 71.88% | 0.7208 | 2,880 | 1,152 |
| 160 | 160.16 | 74.48% | 0.7452 | 2,880 | 1,152 |
| 200 | 203.12 | 75.87% | 0.7602 | 2,880 | 1,152 |
| 1,000 reference | 1,000.00 | 62.24% | 0.6112 | 138 | 98 |

Accuracy generally improves with longer windows, but is not monotonic. The 1,000 ms row has only 236 total eligible trials and must not be used to claim that early windows outperform full observation on the same population. No confidence intervals, repeated splits, or statistical significance results are saved.

### 9.5 Persisted output

`backend/artifacts/models/` contains nine logistic-regression `.joblib` files for 20, 40, 60, 80, 100, 120, 160, 200, and 1,000 ms. `backend/artifacts/reports/` contains the two experiments and a dataset inspection JSON generated on 15 September 2026. Results retain full per-class metrics and confusion matrices beyond the summary above.

## 10. Backend/API implementation

[`main.py`](../backend/app/main.py) registers FastAPI version `0.1.0`, logging, five route modules, and localhost CORS origins for development. FastAPI supplies interactive OpenAPI documentation at `/docs`.

| Method | Endpoint | Implemented behavior |
|---|---|---|
| GET | `/api/health` | Service status and detected dataset path |
| GET | `/api/dataset/summary` | Dataset constants, discovered subjects, window specs |
| GET | `/api/subjects` | Subject metadata |
| GET | `/api/subjects/{subject_id}/summary` | Detailed subject summary |
| GET | `/api/subjects/{subject_id}/trials` | Trial boundaries, targets, labels |
| GET | `/api/subjects/{subject_id}/trials/{trial_id}/signal` | Requested channels/phase and optional preprocessing |
| GET | `/api/subjects/{subject_id}/trials/{trial_id}/onset` | Onset estimate and diagnostics |
| GET | `/api/subjects/{subject_id}/trials/{trial_id}/early-window` | Window samples, context, metadata, feature count |
| GET | `/api/subjects/{subject_id}/trials/{trial_id}/processing` | Raw/processed comparison and onset diagnostics |
| GET | `/api/experiments` | Saved experiment listing |
| GET | `/api/experiments/{experiment_id}` | One saved experiment |
| GET | `/api/experiments/latest/results` | Experiment selected by file modification time |
| POST | `/api/experiments/run-baseline` | Returns CLI instructions; does not launch training |
| GET | `/api/data-quality` | Live all-subject quality assessment |

Signal payloads are capped using stride-based subsampling for visualization; this is not peak-preserving decimation. Processing and early-window responses expose selected channels for presentation, while features use all channels by default.

The early-window API does **not** return model predictions or confidence. No model-serving endpoint, WebSocket stream, database, authentication, or authorization layer is implemented. The APIs are suitable for the current local prototype; a public deployment would need deliberate access and input-validation work.

## 11. Frontend implementation

The frontend uses React, TypeScript, Vite, React Router, Recharts, and shared CSS for a dark dashboard. Installed dependency declarations are in [`package.json`](../frontend/package.json). The API service centralizes requests, checks HTTP status, and throws failures. Its responses mostly use `any`, rather than defined domain response interfaces.

| Route | Component | What is implemented |
|---|---|---|
| `/` | `OverviewPage.tsx` | Six dataset metrics, pipeline display, observation-window table |
| `/dataset` | `DatasetPage.tsx` | Subject/trial controls, channel input, outward waveform, target metadata, direction compass |
| `/signal` | `SignalPage.tsx` | Baseline/detrend/filter/normalize controls, channel-0 raw/processed overlay, derivative threshold and onset display |
| `/early-window` | `EarlyWindowPage.tsx` | Subject/trial selection, cue/onset selection, window controls and highlighted signal region |
| `/experiments` | `ExperimentsPage.tsx` | Latest result curve, per-window table, selected confusion matrix, per-class metrics, subject split |
| `/quality` | `QualityPage.tsx` | Subject validation table, direction counts, expected CS=30 explanation |
| `/methodology` | `MethodologyPage.tsx` | Pipeline explanation, implemented concepts, planned extensions |
| None | `AboutPage.tsx` | Capability/roadmap component exists but is not imported or routed |

The application includes sidebar navigation, a route-aware top bar, loading skeletons, and a backend status check every ten seconds. Backend status represents health-request success; it does not establish that every dataset/model operation is ready.

The shared `useFetch` hook tracks data/loading/error and prevents obsolete effect responses from updating state. Several pages do not display its returned error, so failures can appear as empty charts or missing values. It ignores stale responses rather than aborting their network requests.

Current UI limits include a dataset trial dropdown restricted to the first 50 trials, eight-class names hardcoded in experiment rendering, and a hardcoded API URL of `http://localhost:8000/api`. Four-class labels would be misleading and 36-class labeling incomplete without UI changes. No browser interaction, accessibility, or mobile-layout audit was performed.

## 12. Scripts and supporting documents

| Item | Completed purpose | Current limitation |
|---|---|---|
| `backend/scripts/inspect_dataset.py` | Inspect MATLAB structure, statistics, phase counts, per-subject/channel results; save JSON | Its validation flag does not consistently incorporate every anomaly |
| `backend/scripts/investigate_details.py` | Investigate CS=30 and target-angle structure | Legacy absolute dataset path; selected subjects rather than general CLI |
| `backend/scripts/summarize_report.py` | Print information from saved inspection JSON | Expects execution from project root |
| `backend/scripts/run_baseline.py` | Train/evaluate/save per-window baseline experiments | Single holdout; overwritable model filenames |
| `README.md` | Project explanation, architecture and run commands | Overstates connected page count and some validation/model evidence |
| `docs/DATASET_REPORT.md` | Dataset structure, subject table, anomaly explanation | Historical report; fresh quality check is recorded separately here |
| `docs/METHODOLOGY.md` | Scientific formulation and processing explanations | Describes stronger validation/causality than executed code supports |
| `docs/REVIEW_1_NOTES.md` | Presentation walkthrough and defense guide | Group-K-fold claim is not supported by runner |
| `docs/PHASE_2_PLAN.md` | Advanced models, angle regression, LOSO, streaming roadmap | Planned work, not implementation evidence |
| `docs/COMPREHENSIVE_PROJECT_ANALYSIS.md` | Existing extensive conceptual/project analysis | Includes claims such as LRU caching and performance guarantees not verified by source |
| Project `.pptx` | Presentation artifact exists | Slide contents not inspected in this audit |
| Dataset `DataDescription.pdf` | Original dataset reference exists | PDF contents not independently inspected in this audit |

## 13. Verification performed on 25 October 2026

| Check | Outcome | Meaning |
|---|---|---|
| `python -m pytest tests/ -q` in `backend` | **27 passed**, one PendingDeprecationWarning, 11.14 seconds | Existing backend tests pass in current environment |
| Additional TestClient GET checks | **Seven routes returned HTTP 200** | Subject summary, trials, signal, onset, 20 ms early window, processing, experiment list exercised |
| Fresh `/api/data-quality` response | **All 14 passed** | 4,032 trials; zero NaN/Inf values; 14 expected termination samples |
| `npm run build` in `frontend` | **Passed** | TypeScript build and Vite production bundle complete |
| `npm run lint` in `frontend` | **Completed with three warnings** | Warnings concern synchronous effect state and dependency analysis in `useFetch.ts` |

The initial frontend build hit a sandbox `spawn EPERM` while loading Vite configuration. The same build passed when run with the required process permissions; no source change was needed. Vite reports a large-bundle warning: the main minified JavaScript is approximately **670.44 kB**, or **197.49 kB gzip**.

| Backend test module | Test count | Coverage provided |
|---|---:|---|
| `test_api.py` | 5 | Health, summary, subjects, latest results, quality response |
| `test_dataset_loader.py` | 4 | Subject discovery, S1 metadata, control and target streams |
| `test_feature_extractor.py` | 3 | Known single-channel values, multichannel extraction, subset selection |
| `test_onset_detector.py` | 3 | Synthetic movement, quiet signal, short input |
| `test_preprocessor.py` | 3 | Baseline centering, supplied normalization parameters, filter modes |
| `test_trial_segmenter.py` | 5 | Segment boundaries, four/eight bins, names, real S1 trials |
| `test_window_generator.py` | 4 | Sample conversions, specs, extraction, insufficient length |

Passing these tests does not establish exhaustive edge-case coverage, clinical onset accuracy, strict streaming causality, model quality across all subjects, or production readiness. Some tests use random synthetic data without a local seed. No automated frontend interaction suite or dedicated model/evaluator test module was found.

## 14. Corrections and remaining technical gaps

These are analysis findings; application code was not changed as part of generating this report.

### 14.1 Claims to correct before a presentation

| Existing claim | What the inspected project supports |
|---|---|
| Eight working dashboard pages | Seven routed pages and one unconnected About component |
| Stratified Group-K-fold or completed LOSO evaluation | One seeded subject-level train/test holdout |
| Logistic regression and SVM benchmark results | Saved results are logistic regression only |
| Strict zero-look-ahead end-to-end processing | Full-phase onset channel selection and conditional preprocessing undermine that claim |
| Dashboard displays live predictions | Dashboard displays signals, metadata, features count, and saved experiment metrics |
| 1,000 ms is a comparable full reference | Most trials are discarded after onset alignment; population differs |
| LRU cache, bounded memory, guaranteed rendering speed | Dictionary cache and explicit release; no corresponding performance measurements |
| AWS project is deployed in the cloud | Folder name only; no deployment implementation found |

### 14.2 Validation and robustness gaps

| Location | Cause/limit | Bounded fix or next verification |
|---|---|---|
| `api/signals.py` | Channel strings, indices, phase/alignment, and positive window duration lack complete boundary validation | Validate before slicing/feature extraction and return explicit 4xx responses |
| `features/window_generator.py` | Zero/negative sample lengths are not rejected | Require a positive duration/sample count |
| `signal_processing/onset_detector.py` | Channel variance selection uses the whole phase | Use preset channels or past-only calibration and measure detection delay |
| `signal_processing/preprocessor.py` | First-25-sample baseline can extend past short cue windows; other optional modes use full-trial statistics | Define calibration availability and enforce causal operations for streaming experiments |
| `api/quality.py` | `passed = len(anomalies) <= 1` permits any lone anomaly, not specifically CS=30 | Explicitly exclude only the expected termination condition from failure checks |
| `scripts/inspect_dataset.py` | Some shape/data anomalies are appended without updating `validation_passed` | Derive pass/fail from explicit validated conditions |
| `api/dataset.py` | Summary trials are subjects x expected count, not a live segmented count | Use quality/segmentation output when claiming measured totals |
| `data/trial_segmenter.py` | Mismatched phase lists are paired by index with warnings | Validate sequence and completeness before accepting a trial |
| `scripts/run_baseline.py` | Very small subject subsets can leave no training subjects; split label is fixed | Validate selected subject count and record actual split configuration |
| `frontend/src/hooks/useFetch.ts` and pages | Lint warnings and inconsistent error display | Resolve dependency/state design and render actionable request failures |
| `frontend/src/services/api.ts` | Localhost API URL is hardcoded | Configure deployment API location when hosting |
| `frontend/src/pages/ExperimentsPage.tsx` | Labels assume eight classes; text implies stronger evaluation | Use result class names and accurate split descriptions |
| Saved model naming | Experiment/alignment absent from filenames | Preserve experiment lineage before comparing model artifacts |

These findings do not invalidate the verified local dataset exploration or existing saved holdout results. They limit stronger causality, generalization, and deployment claims.

## 15. What remains planned

| Workstream | Not yet implemented/verified |
|---|---|
| Stronger evaluation | LOSO over 14 subjects, repeated splits, uncertainty estimates, matched-trial full-window comparison |
| Broader baseline evidence | Saved SVM/random-forest, four-class, 36-class and cue-aligned comparisons |
| Advanced learning | TCN, spatial-temporal CNN, GRU/LSTM, continuous angle regression |
| Adaptation and efficiency | Subject personalization, domain adaptation, channel reduction, confidence-based early stopping |
| Real-time system | Stateful causal stream processing, ring buffer, WebSocket feed, actual model-serving endpoint and wall-clock latency measurements |
| Product/deployment | About route, robust input/error handling, deployment configuration, access controls where needed, CI/CD and AWS infrastructure |

No AWS SDK usage, S3/EC2/Lambda/SageMaker integration, Dockerfile, Terraform/CloudFormation configuration, or CI workflow was found in the inspected application/configuration files. Raw data, results, and models currently live on the local filesystem.

## 16. Running the completed work

### 16.1 Start the backend

From the project root:

```powershell
cd backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

Open `http://localhost:8000/docs` for the API or `http://localhost:8000/api/health` for a basic health response. The existing requirements pin runtime dependencies; `pytest` and the TestClient HTTP dependency are not separately declared as a development requirements set. They were available in the audited environment. A clean dependency installation was not tested.

### 16.2 Start the dashboard

In a second terminal, from the project root:

```powershell
cd frontend
npm install
npm run dev
```

Use the URL Vite prints, normally `http://localhost:5173`. Both frontend and backend must run for data pages to populate.

### 16.3 Run existing verification

```powershell
# From backend/
python -m pytest tests/ -q
```

```powershell
# From frontend/
npm run build
npm run lint
```

### 16.4 Reproduce training when needed

```powershell
# From backend/; this writes new reports and can overwrite matching model files.
python -m scripts.run_baseline --n-classes 8 --model logistic_regression --alignment onset
```

This training command was inspected, not rerun during the audit. The report's accuracy table comes directly from the existing full-data JSON experiment.

## 17. Practical handoff

The completed deliverable is a tested local EOG research foundation: real-data ingestion and validation, short-window feature/classification experiments, persisted results, REST exploration, and a buildable dashboard. The next research milestone is stronger causal onset handling and subject-independent evaluation; the next application milestone is serving an actual model prediction.

**Next action, under two minutes:** use the completion table in section 2 to choose which verified capabilities to demonstrate, and use section 14 to avoid unsupported presentation claims.

**Audit limits:** no model retraining, browser walkthrough, clean-environment installation, original PDF/slide review, or cloud deployment was performed. No Git repository metadata was present, so historical authorship, commits, and change chronology could not be reconstructed. Saved results establish one historical holdout experiment, not final clinical or real-time performance.

# EOG Intent — final Codex master implementation prompt

## How to use

Open the `AWS_PROJECT` repository in Codex. Provide this file, `PROJECT_STATUS_REPORT(1).md` or the repository's `docs/PROJECT_STATUS_REPORT.md`, and the real dataset at its existing local location. Then paste:

> Read EOG_CODEX_MASTER_PROMPT.md completely. Follow its build specification in the existing AWS_PROJECT repository. Inspect first, write implementation_plan.md and action_plan.md, then implement and verify the complete EOG project. Continue through every executable phase; do not stop after planning. Preserve existing work and report blockers honestly.

## Verified repository handoff — 25 October 2026

Repository: https://github.com/Mithilesh-1311/AWS_PROJECT

Inspected branch: `main`. Inspected commit: `d65e1a5fdab959d3520474dca8dac4f65fcc7916`.

The repository was successfully cloned and these facts were checked directly:

| Area | Verified repository state |
| --- | --- |
| Application identity | Existing sidebar title is **EOG Intent**; the entire project is about EOG early eye-movement intent detection. |
| Frontend | React 19, TypeScript, Vite 8, React Router 7, Recharts 3, Lucide; existing CSS; no animation framework declared. Exact versions are in package manifests/lockfile. |
| Routes | `/`, `/dataset`, `/signal`, `/early-window`, `/experiments`, `/quality`, `/methodology`; About component exists but is not routed. |
| Backend | FastAPI; MATLAB loader and trial segmenter; preprocessing/onset/window/features modules; classifier factories and experiment evaluator. |
| Training | `backend/scripts/run_baseline.py` executes one seeded subject holdout. Importing GroupKFold does not execute cross-validation. |
| Saved artifacts | Nine logistic-regression `.joblib` files, two experiment JSON reports, one dataset inspection JSON. These were inventoried; serialized models were not deserialized or inference-tested in this inspection. |
| Historical full-data results | The stored report confirms 64.50% accuracy at requested 20 ms and 75.87% at requested 200 ms, with held-out S1/S5/S7/S8. These are saved historical results, not newly reproduced scores. |
| Dataset availability | No raw `.mat` recordings, dataset archive or original dataset-description PDF are present in the tracked checkout. `.gitignore` excludes `Dataset_Isotropic/` and `Dataset_Isotropic.zip`. A local dataset must be supplied to Codex for retraining and real replay. |
| Inference and jobs | No model-serving endpoint found. POST `/api/experiments/run-baseline` returns instructions only; it does not launch training. |
| Deployment/replay | No implemented AWS infrastructure, container deployment or stateful streaming service found in the inspected tree. |
| Confirmed fixes needed | Hardcoded localhost API URL; `any` API contracts; full-outward-phase onset channel variance; 25-sample baseline; overly permissive quality pass condition; model paths overwritten across reruns. |

Source files inspected included `README.md`, package manifests, `.gitignore`, the configuration/loader, baseline model factory, baseline runner, evaluator, experiment API, processing/quality code references, frontend route shell/overview/API client/fetch hook, phase-two roadmap, and both saved experiment JSON files. The attached status report was also read. This is a source-and-artifact audit, not a fresh runtime certification. The checked environment lacks FastAPI, pytest and httpx and has different NumPy/SciPy/scikit-learn versions from the project requirements; application tests, browser checks, model inference and retraining were not run during prompt preparation.

**Scope:** Complete and improve this existing EOG application. Retain only the supplied reference's visual style: dense engineering dashboard, compact panels, dark palette, readable charts and purposeful motion. Every project name, technical concept, diagram, route label and dataset must be EOG-specific. The original source and verified EOG work are the product authority. Proposed features below are remaining implementation tasks, not claims about work already completed.

The three requested upstream repositories were consulted for the earlier prompt: Emil Kowalski's design/animation skills, Impeccable's Codex skill, and ECC's verification loop. Resolve their current versions when implementing; do not assume installers or slash commands exist unchanged.

---

## Build specification

You are the implementation owner for an existing research application: **Low-Latency EOG-Based Early Intent Detection for Eye Movements**, intended as an AWS course project. Complete it end to end using its real dataset and existing code. Deliver a working application, reproducible ML experiments, genuine model inference, recorded-data streaming replay, an engineering dashboard, and reproducible AWS deployment infrastructure.

Preserve the existing **EOG Intent** identity, with subtitle **EARLY EYE-MOVEMENT INTELLIGENCE**. The full scientific project title remains **Low-Latency EOG-Based Early Intent Detection for Eye Movements**. Do not include personal names, registration numbers, or institution details in the UI.

Work autonomously on reversible implementation decisions. Record material assumptions in `decisions_log.md`. Preserve user changes, raw recordings, original reports, and historical model artifacts. Do not replace this project with a starter template, migrate frameworks without evidence, or stop at a design mockup. If an input or external credential is missing, finish all independent work, identify the exact blocker, and give the next executable action. Never fabricate data, scores, cloud resources, or verification.

### 1. Inspect inputs and requested skills before editing

1. Use the existing `AWS_PROJECT` checkout. If absent, clone `https://github.com/Mithilesh-1311/AWS_PROJECT.git`. Check its branch, commit, instructions and working-tree changes before editing. Locate the real dataset separately: the inspected commit excludes it from Git. Support local `Dataset_Isotropic/S1` and nested `Dataset_Isotropic/Dataset_Isotropic/S1` layouts and an explicit environment override. If a dataset archive is supplied, safely extract it without path traversal or duplicate expansion. Missing data blocks real-data training/evaluation/replay verification, not independent source, UI, infrastructure, or synthetic unit-test work. Do not fabricate recordings or infer that historical reports substitute for raw data.
2. Read project instructions, the attached status report, README, methodology, phase-two roadmap, package manifests, routes, API clients, tests, training scripts, experiment JSON, and model metadata. Inspect the original dataset description PDF and relevant presentation content if available. Source/data inspection takes precedence over stale documentation. Explain inconsistencies.
3. Inventory routes, APIs, model artifacts, dataset files, installed dependencies, compute capacity, AWS configuration, and existing CI. Run the current backend tests and frontend checks to establish a baseline. Distinguish pre-existing failures from regressions.
4. Retrieve and read the applicable skills from these exact upstream repositories, recording the resolved commit and selected paths in `docs/SKILL_SOURCES.md`:
   - https://github.com/emilkowalski/skills — `skills/emil-design-eng/SKILL.md`, `skills/animate/SKILL.md`, plus relevant motion review/performance recipes as needed.
   - https://github.com/pbakaus/impeccable — discover the current Codex-compatible skill location. At prompt preparation, `.agents/skills/impeccable/SKILL.md` existed. Apply its Operate-mode design approach, applicable planning/context instructions, accessibility audit, and final polish. Read its referenced craft guidance before UI edits.
   - https://github.com/affaan-m/ECC — use applicable planning, Python/backend, testing, deployment, and `skills/verification-loop/SKILL.md` guidance. Discover paths from the repository rather than assuming every historical command exists.
5. Use these as engineering guidance, not application runtime dependencies. Do not globally install hooks, overwrite user configuration, enable unrelated MCP services, or run uninspected bootstrap scripts. Prefer reading the relevant files or project-scoped setup. The user’s scientific and visual requirements override generic skill preferences. An upstream outage must not block independent project work; document the unavailable reference.
6. Use an existing read-only reviewer if one is already available. Do not create additional reviewer agents or rely on multi-agent execution to finish this task.

### 2. Establish the implementation plan and action plan

Before feature changes, create:

- `implementation_plan.md`: current architecture, evidence-backed gap analysis, target architecture, data and model lifecycle, API changes, frontend route map, AWS architecture, risks, acceptance criteria, and verification strategy.
- `action_plan.md`: ordered tasks with dependencies, affected files/modules, expected outputs, verification commands, and status (`pending`, `active`, `complete`, `blocked`). Include concrete requirements for every phase below.
- `progress.md`: completed work, exact verification results, current blockers, and the next task. No invented completion percentages.
- `decisions_log.md`: material choices, rationale, and alternatives only where they affect implementation.

Execute in this order: baseline audit → data/scientific fixes → reproducible baselines → real inference/jobs → replay → dashboard → advanced comparison → AWS/containerization/CI → integrated verification/documentation. Keep the application runnable between phases. Implement the smallest complete vertical slice early: real trial → validated early window → saved model → prediction API → displayed prediction.

### 3. Historical baseline to verify

Direct inspection of the repository confirms FastAPI/Python with NumPy/SciPy/scikit-learn and React/TypeScript/Vite/React Router/Recharts. Keep these foundations unless source inspection justifies a change.

Reported dataset: S1–S14, five MATLAB files per subject (`EOG.mat`, `ControlSignal.mat`, `Target_GA_stream.mat`, `PD.mat`, `Dist_screen.mat`), 16 EOG channels, 256 Hz, 288 trials per subject, 4,032 trials, 36 fine target directions. Verify actual schemas, units, orientation, sampling metadata, license, and permitted use. Do not label voltages as microvolts until the source establishes the scale.

Repository inspection confirms seven routed pages, logistic regression/linear SVM/random forest factories, one seeded subject holdout strategy, nine saved logistic models, no genuine inference endpoint, no implemented AWS deployment, and no stateful streaming system. The report describes 212 classical features with 16 channels; verify feature count against the selected configuration.

Historical eight-class onset-aligned logistic holdout: requested 20 ms → 6 samples → approximately 23.44 ms sample budget, 64.50% accuracy; requested 200 ms → 52 samples → approximately 203.12 ms, 75.87% accuracy. Historical test subjects: S1/S5/S7/S8. These are NOT acceptance targets, freshly measured results, or evidence of causal real-time performance. The 1,000 ms historical reference used far fewer eligible trials and is not a matched comparison. The report records 27 passing backend tests and a passing frontend build, which must be rerun.

### 4. Correct data access and scientific validity

Implement and verify these items against the source:

- Configurable dataset/artifact roots through environment variables, without personal Windows paths; explicit missing-data states; bounded cache or documented measured limits; deterministic discovery and file validation.
- Validated phase sequences and exclusive boundaries. Reject or quarantine incomplete/misordered trials with recorded reasons. Treat control value 30 as an expected termination marker only at the documented position; do not pass arbitrary single anomalies.
- Actual segmented counts in quality/summary results, with expected counts identified separately. Report missing files, shape mismatches, nonfinite data, and exclusions explicitly.
- Strict input validation for subject/trial/channel identifiers, channel bounds, phase, alignment, positive finite durations, supported class schemes, model IDs, and resource limits. Return consistent typed 4xx responses rather than silent slicing or 500 errors.
- Implement feature-group flags correctly. Version feature order, units, sampling rate, selected channels, preprocessing, and nonfinite handling. If correcting slope/derivative/integration to physical time changes features, create a new feature version; preserve legacy-model compatibility.
- Separate **retrospective research** and **causal replay** modes. Preserve the old methodology as a labeled legacy path where useful; corrected results become new experiments.
- No full-trial variance channel selection in causal mode. Use fixed channels or calibration available before the prediction, with any learned choice fitted inside training folds.
- Baseline statistics must be available before the decision. Never let a 20 ms cue window depend on the first 25 post-cue samples. Use genuinely available pre-cue/calibration samples, or explicitly delay readiness and include that time in latency. Missing calibration must produce a visible state.
- Causal filters must carry state across chunks; avoid `filtfilt`, whole-trial detrending, or future-derived normalization in causal mode. Fit trainable preprocessing only on training subjects/folds.
- Record onset first-crossing sample and confirmation sample separately, including persistence delay, reliability, fallback policy, failures, and exclusions. Do not train causal models using future samples to backdate a prediction opportunity. Any buffered window anchored at crossing can only be emitted after confirmation and required samples are available.
- Explicitly distinguish requested milliseconds, integer sample count, sample-budget duration `N/fs`, and first-to-last sample span `(N-1)/fs`. Preserve the existing `ceil` rule where intended.
- Observation-window duration is not cue-to-decision latency. Record cue-to-onset, confirmation delay, window readiness, preprocessing/feature extraction/inference time, and transport/render timing where measurable. Do not add overlapping components twice. Use monotonic timing and documented clock boundaries.
- Target coordinates/control streams may supply evaluation labels and documented cues, but must not leak direction into model features or causal channel selection. Identify cue-triggered replay assumptions; do not imply autonomous continuous onset detection unless implemented and evaluated.

### 5. Build the real, reproducible ML workflow

Use eight-class prediction as the primary validated product path. Preserve four/36-class support where already implemented; expose a scheme only with truthful model and evaluation availability.

1. Preserve historical models/reports unchanged. Create immutable experiment IDs, dataset fingerprints, split manifests, configuration hashes, dependency versions, seeds, class order, feature schema, preprocessing settings, and checksums. Store models under experiment-specific directories. Never infer lineage from a filename alone.
2. Reproduce the legacy logistic holdout when compatible with the available environment; record any score differences. Then create corrected-causality runs separately. Do not silently apply new preprocessing to old models.
3. Benchmark logistic regression, linear SVM, and random forest on real recordings, across the reported 20/40/60/80/100/120/160/200 ms windows. Cache reusable valid intermediate data keyed by preprocessing and dataset versions. Include actual runtime/resource measurements.
4. Implement reproducible subject-independent evaluation. Use LOSO over all available subjects for the primary selected model/configuration, with training-only group validation for selection and tuning. Do not use held-out subjects to choose channels, scalers, hyperparameters, thresholds, calibrators, architectures, or the winning configuration. Preserve the historical holdout as historical if it already influenced prior development; LOSO is not a newly untouched external test.
5. Define hyperparameter/model selection before inspecting outer test performance. Keep search bounded. Report per-subject and aggregate accuracy, balanced accuracy, macro F1, class support, confusion matrices, and prediction counts. Include uncertainty using subject-aware resampling and state its limitations with only 14 subjects. Do not bootstrap correlated windows as independent subjects.
6. Build a matched-trial reference using an explicitly valid longer/full observation policy. Compare short and long models on the same eligible held-out trial IDs, disclose exclusions and coverage, and also show per-window all-eligible metrics separately. Do not reuse the historical unmatched 1,000 ms figure as proof of early-window superiority.
7. Train one compact sequence model, preferably a causal 1D TCN, using an existing deep-learning framework if present; otherwise select one supported framework and document the choice. Give it the same allowed observation/calibration budget and subject splits. Mask/pad variable windows explicitly and prevent future look-ahead. Use training-subject validation, early stopping, fixed seeds, and bounded epochs. Report real comparison results even if it loses to classical models. Full deep-model LOSO may be a separately resumable benchmark if compute is limiting; never imply an unfinished benchmark passed.
8. Distinguish calibrated probabilities, uncalibrated probabilities, and decision scores. For LinearSVC use a training-only subject-aware calibrator if probabilities are required, otherwise expose scores honestly. Do not manufacture confidence by normalizing arbitrary scores.
9. Provide explicit CLI/config commands for small real-data smoke runs, primary full classical evaluation, advanced-model comparison, resuming interrupted folds, and training a final serving model. Smoke-mode results must remain visibly distinct from full evaluation.
10. Select the serving model using a predeclared accuracy/latency tradeoff and training-only validation. Preserve outer-fold evaluation evidence separately from a final model retrained on all subjects. Do not call final all-subject training performance held-out accuracy. Never promise a target percentage.

Prioritize the existing project and its actual `docs/PHASE_2_PLAN.md`. The roadmap also names spatial-temporal CNN, GRU/LSTM, continuous angular regression and domain adaptation: record these in the action plan as separate research extensions, implement only after the primary classical/TCN path and serving/replay are working, and do not label them complete without experiments. For angular regression use a normalized circular representation and wrapped angular error; any subject adaptation must use a clearly separated calibration protocol and must not be mixed with zero-calibration LOSO. Finish primary real-data training and evaluation when resources allow. Save checkpoints/fold outputs incrementally. If runtime prevents full completion, report completed folds/trials, unexecuted commands, and exact remaining work instead of marking ML complete.

### 6. Implement backend inference and real job execution

Extend the existing API/service structure. Reuse clients and route behavior; add backward-compatible versioned contracts where semantics change.

- Typed request/response schemas and generated/shared frontend domain types. Make units, source, experiment/model ID, alignment, window length, readiness time, calibration state, and prediction state explicit.
- Separate service liveness from readiness for dataset, model, storage, and worker. Public health responses must not leak absolute filesystem paths or credentials.
- Model registry lists metadata, compatible feature/preprocessing versions, class order, evaluation reference, and readiness. Use an explicit active model ID, not file modification time.
- Genuine inference endpoint for a validated recorded trial/window, plus bounded sample-based inference only if needed. Enforce identical training/serving preprocessing. Ground-truth direction belongs in evaluation metadata, never prediction inputs.
- Responses include predicted class, probability/score semantics, window metadata, measured inference timings, model provenance, and warnings or abstention when data is insufficient. Detect incompatible/corrupt models and fail clearly. Load only trusted project-produced serialized artifacts.
- Replace the current run-baseline instructions-only behavior with a real bounded job interface while preserving compatibility if clients need it. Support create/list/status/result and cancellation where reliable. Track queued/running/succeeded/failed/cancelled states, persisted progress, structured errors, timestamps, and actual fold/window counters.
- Execute training outside request handlers. Use a durable job store and separate worker with bounded concurrency, restart recovery, atomic claims/leases, and artifact writes. For a single-host course deployment, SQLite on a persistent local volume is acceptable if locking/recovery is tested; do not pretend it is a distributed queue. Explain migration boundaries rather than adding unnecessary services.
- Report percentages only from known work counts; otherwise use indeterminate status. No fake timers or cosmetic progress.
- Configured origins/API URLs, request timeouts, abortable fetches, pagination, safe artifact identifiers, bounded payloads, rate/resource limits, structured logs, and authenticated authorization for protected cloud actions.
- Experiment/report exports in JSON/CSV and printable HTML using real stored results and configuration. Empty model/results states remain usable and actionable.

### 7. Stateful streaming replay

Implement real recorded-data replay over WebSocket, or a justified equivalent that supports the required behavior.

- Explicitly label it **RECORDED DATA REPLAY**. No sensor hardware or live acquisition claim without actual integration.
- Stream raw EOG chunks in sample order; run the stateful causal processor on the server. Keep filter state, calibration state, ring buffer, onset/persistence state, and model inference consistent with the tested causal pipeline.
- Support subject/trial or continuous-recording selection as actually implemented, play/pause/reset, bounded playback speed, channel selection, session cleanup, disconnect/reconnect, and backpressure. Speed changes scheduling only, never sampling metadata or scientific latency calculations.
- Transmit sequence numbers, sample indexes, source timestamps, processing timestamps, and versioned metadata. Bound server/client buffers and release resources on disconnect. Reconnect resets or resumes explicitly; never silently stitch incompatible state.
- Validate chunk continuity and report gaps/out-of-order samples. Test that different valid chunk sizes yield equivalent processing and predictions.
- Show cue, onset estimate, confirmation, observation cutoff, prediction emission, class/scores, and latency components when available. Continuous data needs a documented event/reset policy; cue boundaries available from a dataset are an experimental assumption.
- Ground truth may be overlaid after/beside predictions for research comparison with clear labeling, never used by the serving model.
- A real-data replay must produce actual model predictions, not prerecorded probability animations.

### 8. Frontend design: adapt the engineering reference to EOG

Inspect every existing page before changing it. Preserve working routes, controls, API integrations, and scientific calculations. This phase changes presentation; scientific/backend changes belong to the explicit phases above and retain versioned provenance.

Use the requested dense command-centre aesthetic:

```css
--background: #070B0E;
--panel: #0C1117;
--selected: #111920;
--border: #23313B;
--text: #E4ECF2;
--muted: #9AAAB7;
--green: #37C991;
--cyan: #36BCE3;
--amber: #E5AD38;
--red: #F16D70;
```

Near-black background, subtle engineering grid, thin borders, mostly square corners, minimal shadows. Cyan for selection/signals, green for ready/success, amber for warnings/pending, red for errors. Status always includes text/icons. Avoid oversized cards, excessive gradients, decorative empty space, glowing chart clutter, and a generic marketing landing page.

Typography: Inter or comparable sans-serif for navigation/body, IBM Plex Mono or JetBrains Mono for values/units/technical labels; compact uppercase panel headings; 12–14 px body; 26–34 px primary metrics; tabular numerals and readable contrast. Honor these pinned choices despite generic upstream font preferences.

Shell: desktop sidebar about 200 px, top bar about 52 px, content padding 14–20 px, compact reusable panels. Top bar: EOG Intent / EARLY EYE-MOVEMENT INTELLIGENCE, actual service/dataset/model/worker status. Footer: actual connection status and build/version metadata; no invented status.

Recommended navigation mapped to existing functionality:

| Label | Existing/new behavior |
| --- | --- |
| Overview | Preserve `/`; EOG command centre |
| Dataset Explorer | Preserve `/dataset`; all subjects/trials, pagination or search |
| Signal Processing | Preserve `/signal`; raw/processed/onset diagnostics |
| Early Windows | Preserve `/early-window`; calibration, cue/onset, sample budget |
| Predictions | New real inference workflow |
| Live Replay | New recorded-data replay workflow |
| Model Evaluation | Preserve `/experiments`; actual model/window/split comparisons |
| Data Quality | Preserve `/quality`; actual validation and exclusions |
| Methodology | Preserve `/methodology`; verified scientific explanation |
| Reports | New real exports and experiment provenance |

Do not remove existing routes to force this map. Route About only if useful, with accurate content. Use EOG comparison screens for models, observation windows, and causal versus retrospective settings.

Overview layout:

1. `EOG INTENT COMMAND CENTRE` heading and compact source/mode badge.
2. Metric strip from the selected dataset/experiment/model only: subject/trial/channel counts, sampling rate, requested/effective observation budget, accuracy/macro F1 with split context, measured inference timing where available. Each card links to its evidence. Missing values show unavailable, never zero or invented numbers.
3. Experiment/model selector and provenance strip: dataset fingerprint, subject split, class scheme, channel set, preprocessing version, alignment, evaluation timestamp.
4. Real processing/job panel with log/status detail and genuine counters.
5. About 60/40 analytical row: EOG waveform/prediction panel plus functional pipeline diagram.
6. Secondary panels: accuracy versus observation budget, subject results, confusion matrix, direction compass, and compact comparison tables as supported by selected results.

Create an EOG-specific clean SVG labeled **System pipeline**:

`Recorded EOG channels → calibration/causal preprocessing → onset and window manager → features or sequence encoder → model → predicted direction and timings`.

Place the target/control-label branch separately as evaluation metadata. Explicitly say functional pipeline; never imply a physical electrode layout or transistor schematic. All diagram content, icons, labels, loading states and navigation must describe the actual EOG workflow.

Charts: dark surfaces, fine grid, compact legends, consistent channel/signal colors, readable axes with verified units, hover crosshairs, tooltips, zoom/reset and relevant event markers. Distinguish raw/processed, actual target/predicted direction, retrospective/causal, and historical/current experiment through labels and line styles. Avoid connecting categorical classes as continuous measurements. Keep accessible data tables and export controls. Visualization downsampling must preserve salient extrema where practical and never change model input data.

Fix the report’s known UI gaps if confirmed: first-50-trial restriction, hardcoded eight-class names, localhost API URL, untyped `any` responses, inconsistent request errors, stale request races, and hook lint warnings. Display dynamic class order from model/report metadata. Persist/share relevant selection through URL or appropriate state and prevent cross-experiment metric mixing.

Motion using Emil guidance:

- Purposeful brief entrances for occasional panels, subtle pointer navigation transitions, readable loading changes, and smooth replacement of chart datasets only when it does not hide events or change scientific interpretation. Frequent sampling/keyboard navigation and numerical values should update directly.
- CSS transitions first; reuse existing Motion/GSAP only where warranted. Do not install both for basic fades. Animate explicit transform/opacity properties rather than `transition: all`; no scale-from-zero or slow `ease-in` entrances.
- Share easing tokens: `cubic-bezier(0.23,1,0.32,1)` for entering/exiting, `cubic-bezier(0.77,0,0.175,1)` for spatial movement; use roughly 150–250 ms where appropriate, 100–160 ms press feedback, minimal or no repeated chart animation.
- A short EOG signal-trace loading introduction may run during real startup work and end immediately on readiness. Never introduce a minimum delay or replay a full intro on every route.
- Animate active pipeline stages only when backend state supports activity. Indeterminate loaders when progress is unknown. No fluctuating mock metrics, fake terminal logs, or decorative sensor activity.
- Respect `prefers-reduced-motion` from the first render, gate hover motion to fine pointers, preserve normal cursor/native scrolling, and avoid chart panning effects or animated number counters.

Responsive/accessibility requirements: collapsible navigation drawer on small screens, progressively fewer metric columns, stacked chart rows, intentional table scrolling, no page-wide overflow, visible focus, complete keyboard operation, accessible drawer focus/escape behavior, form labels/errors, loading announcements that do not spam screen readers, sufficient contrast, readable units, and touch-friendly targets. Use established accessible primitives where needed.

### 9. Containers, AWS infrastructure, and operations

Build local Docker Compose and one reproducible AWS deployment path. Prefer a simple single-host course deployment over an unnecessarily expensive platform. Verify current AWS service capabilities and configuration against official documentation at implementation time; do not rely on this prompt for current prices or service limits.

Default architecture unless existing code/constraints suggest a better supported option:

- Frontend built to static assets served by a reverse proxy; FastAPI and a separate worker run in containers on a configurable EC2 host.
- Reverse proxy routes same-origin API and WebSocket traffic and provides HTTPS through a documented valid domain/certificate path. With no domain, finish local/container verification and disclose what is required for secure cloud access.
- S3 private versioned buckets/prefixes for authorized dataset storage, immutable model artifacts, experiment outputs, and backups; verify data licensing/permission before raw-data upload. Stage required data to persistent host storage using checksums rather than repeatedly downloading whole recordings per request.
- Persistent host volume for validated local dataset/cache and SQLite/job state if selected. Document single-host availability limits and backup/recovery.
- Instance IAM role and least-privilege access to required S3 prefixes and telemetry; no access keys baked into source, frontend, images, or Terraform state.
- CloudWatch logs/metrics with explicit retention. Configurable region/instance/storage sizes; no claimed free-tier guarantee. Separate training resource needs from lightweight serving needs.
- Security groups restrict management; prefer SSM instead of exposed SSH where supported. Keep buckets private and databases internal. Protect cloud training, exports, model activation, and data access with a real tested auth approach; do not embed a shared frontend secret. Local development mode must not silently weaken deployed access controls.
- One infrastructure-as-code implementation, preferably Terraform if none exists. Include validation, variable examples, outputs, resource tags, IAM, storage, networking, bootstrapping, deployment/update commands, rollback, backup/restore, and teardown instructions. Never auto-run destroy.
- CI for backend tests, frontend type/lint/build, relevant integration tests, and container build. Configure AWS deployment via OIDC if supported, not stored long-lived keys; deployment runs only with configured environment credentials/authorization.

Prepare and validate infrastructure locally even without credentials. Before any cost-incurring apply, produce the concrete plan, resources, region, and cost assumptions and respect the user’s actual deployment authorization. If AWS access, region, account approval, dataset permission, domain, or budget is missing, do not create resources or claim deployment. Complete the deployable code, plan where possible, and exact commands/configuration needed. Distinguish IaC validation from an applied deployment and cloud smoke verification.

### 10. Verification and acceptance gates

Use ECC’s build → types → lint → meaningful tests → security checks → diff review workflow, adapted to the actual tools. Do not introduce superficial tests solely for a coverage number.

Scientific/backend tests must cover:

- Real dataset discovery/schema checks, expected termination handling, malformed phase rejection, invalid duration/channel/alignment input, and actual trial counts.
- Correct sample conversion and insufficient-window handling; versioned feature order and preprocessing compatibility; legacy artifacts never silently loaded under corrected semantics.
- No subject overlap, training-only preprocessing/calibration/channel selection, deterministic splits, and matched trial IDs for window comparisons.
- A causal no-future-dependence test: modify samples after a decision cutoff and show all pre-cutoff causal outputs remain unchanged. Compare streaming chunks and whole-prefix processing, including filter state and onset confirmation timing.
- Real model save/load/predict round trip, meaningful probability/score semantics, missing/corrupt models, insufficient calibration/data, and zero prediction use of target direction.
- Job failure/cancellation/restart behavior and authenticated authorization; WebSocket continuity, buffer limits and disconnect cleanup.

Frontend/integration verification:

- Type check, lint, production build, and meaningful route/control interactions using the actual API. Include trial → window → inference → displayed provenance, a real training job, results selection, and recorded replay.
- Desktop and mobile visual checks, approximately 1440×900 and 390×844. Inspect rendered screenshots against the supplied screenshot if available and otherwise the written tokens/layout. Verify every existing route and new route.
- Loading, empty dataset, missing model, failed request/job, disconnected backend, reconnect, reduced-motion, keyboard navigation, dense table overflow, and dynamic class-scheme states.
- Same model/config/window yields compatible CLI/API predictions. Compare latency only within documented timing boundaries.
- Clean-install and container smoke test; reproducible dependency manifests; backend readiness, actual inference and replay through the production reverse proxy. Validate infrastructure and CI syntax; run cloud smoke checks only if deployed.

Do not mark end to end complete until the real-data path, model serving, replay, and application tests run successfully. Label each unrun check `NOT RUN` with its reason; no replacing full evaluation with a smoke result. No fabricated screenshots, benchmarks, passing tests, or deployment URLs.

### 11. Final deliverables and handoff

Commit-ready application changes, meaningful tests, immutable new experiment artifacts, model registry, replay, dashboard, Docker/Compose, one AWS IaC implementation, CI, and updated README are required outputs. Exclude raw data, environments, credentials, disposable builds, and large models from ordinary Git history; document permitted artifact storage and checksums.

Update these documents with actual final state:

- `implementation_plan.md`, `action_plan.md`, `progress.md`, `decisions_log.md`.
- `docs/DATASET_CARD.md`: source/license, schema/units, validation, subjects, exclusions and limits.
- `docs/MODEL_CARD.md`: target, intended research use, model/configuration, splits, actual results, uncertainty, calibration and latency definitions, limitations; no clinical or hardware-validation claim.
- `docs/EXPERIMENTS.md`: commands, manifests, provenance and comparisons, including historical versus corrected results.
- `docs/ARCHITECTURE.md`, `docs/API.md`, `docs/AWS_DEPLOYMENT.md`, `docs/VERIFICATION_REPORT.md`, `docs/DEMO_SCRIPT.md`, `docs/SKILL_SOURCES.md`.
- `PRODUCT.md` and `DESIGN.md` if required by the selected Impeccable workflow, recording the actual EOG product and requested visual system.

The final response must state: what works; actual measured ML results and evaluation scope; exact verification commands/results; local launch commands and URLs; AWS status (`prepared`, `validated`, `deployed`, `cloud-verified` as independently evidenced); files changed; and remaining blockers. Include a short demonstration flow: dataset → processing → early window → real prediction → replay → evaluation/report.

Start now with source/data/skill inspection and the two plans, then continue building until all executable acceptance gates are satisfied. Do not finish with only recommendations or a claim that implementation can begin later.

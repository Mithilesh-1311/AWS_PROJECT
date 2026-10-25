# EOG Intent implementation plan

## Inspected baseline (2026-10-25)
Main starts at d65e1a5. User-supplied docs/EOG_CODEX_MASTER_PROMPT.md is preserved. FastAPI + scipy/sklearn, React 19/TypeScript/Vite 8, seven routes, 27 passing backend tests. Frontend type check passes; bundled build needs process permission; three existing hook lint warnings. Real nested dataset has 14 subjects and 70 MATLAB files. Historical reports/models remain immutable. At audit time Docker, Terraform, AWS CLI and torch were absent. Terraform, Caddy and Torch were subsequently installed project-locally for verification; Docker and AWS CLI remain absent.

## Gaps and target architecture
Keep the current application. Fix configuration/discovery, phase validation, quality counts, API bounds and feature flags at their shared implementations. Keep legacy preprocessing explicitly retrospective. Add a versioned causal processor with fixed channels, an explicit 25-sample post-cue calibration delay, stateful filtering and separate onset crossing/confirmation. The initial calibration is part of cue-to-decision latency; early onset before calibration is not observable and is a limitation. Cue-triggered replay is a research assumption.

Build one shared data-to-window pipeline used by reproducible training, inference and replay. Immutable experiment directories hold manifests, dataset SHA256 fingerprint, dependencies, split IDs, metrics, checksum-verified model files and feature order. Use fold-fitted scalers and fixed model settings. Classical models evaluate eight windows and a matched 400 ms reference; primary evaluation is subject LOSO. The logistic family and 100 ms budget are predeclared; bounded training-only inner validation selects regularization. A compact causal TCN is a separate benchmark with training-subject validation. Never repurpose legacy model names for corrected data.

FastAPI adds registry/readiness, predictions, durable SQLite jobs, separate single-worker execution, exports and recorded WebSocket replay. Job claims use a transaction, heartbeat lease and explicit recovery; cancellation is checked between bounded work units. Replay and inference share processing and trusted model loading. Authentication in deployed mode uses reverse-proxy basic authentication (server secret hash, HTTPS), with API job authorization fail-closed unless trusted proxy configuration is enabled. Local mode remains loopback only.

Preserve all routes. Add Predictions, Live Replay, Reports; redesign the shell/overview using pinned engineering tokens. Typed API contracts, abortable requests and stale-response protection apply across pages. Navigation and controls must work with keyboard/mobile. Provenance stays adjacent to results; no invented readiness or accuracy.

Deployment: Docker Compose with Caddy static frontend/reverse proxy, API and worker; persistent local data/artifacts/SQLite; EC2 + SSM + private versioned S3 + CloudWatch via Terraform. HTTPS domain and bcrypt password hash are deployment inputs. No apply or raw-data upload without separate cloud configuration and dataset permission. CI runs synthetic backend tests plus optional real-data tests, types/lint/build and container builds.

## Scope of changes
Backend config/data/processing/features, baseline runner/evaluator, API and tests; new shared causal/experiment/registry/job/replay modules. Frontend services/hooks/pages/shell/CSS and contract types. Root plans/cards/docs, dependency manifests, containers, CI and infrastructure. Existing caller behavior stays compatible where scientific semantics are unchanged.

## Acceptance and verification
Run existing baseline; then malformed-input, phase, feature schema, no-future-dependence, chunk equivalence, save/load/inference, job failure/recovery/cancel/auth and WebSocket tests. Run real dataset validation and real classical evaluation incrementally; record scope, exclusions, balanced accuracy/F1/support/subject uncertainty and matched IDs. Run CLI/API/replay equivalence. Type check, lint, production build, desktop/mobile route checks and failure states. Validate clean dependency resolution, Compose/container/IaC when tools permit. Each NOT RUN result must name a reason. Preserve measured historical scores as historical. No final E2E certification without actual real prediction/replay and application checks.

## Risks
Scientific scores can change; no acceptance accuracy target. Only 14 subjects limits uncertainty and does not establish external/clinical validity. Calibration hides the first 97.66 ms; report it. SQLite supports one persistent host, not distributed workers. Dataset license/voltage units remain unverified. Missing Docker/Terraform/domain/account blocks runtime cloud verification, not source work.

## Executed final state (2026-10-26)
Scientific fixes, classical/TCN/matched evaluations, inference/jobs/replay, ten dashboard routes, deployment source and documentation are implemented. Final acceptance evidence and explicit environment blockers are in docs/VERIFICATION_REPORT.md. Fixed classical comparison: 378 folds; matched logistic: 126; nested primary: 14; TCN: 14. No AWS apply or raw-data upload occurred.

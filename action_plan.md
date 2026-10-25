# Action plan

| Phase | Dependencies / affected areas | Expected output / verification | Status |
|---|---|---|---|
| 1 Baseline audit | all source, dataset PDF, skills, tests | 27 tests; dependency/tool inventory; skill commits | complete |
| 2 Plans | audit; root plans and decision log | architecture, sequence, acceptance gates | complete |
| 3 Scientific fixes | config/data/processing/features/APIs/tests | data validation; input bounds; causal prefix/chunk tests; legacy isolation | complete |
| 4 Reproducible ML | shared processor, experiments, CLI | immutable manifests; three classical families/eight windows; LOSO; matched reference; training-only selection; uncertainty; legacy reproduction | complete |
| 5 Inference/jobs | registry/services/API/worker/SQLite/tests | real prediction; saved model round trip; durable bounded queue; recovery/auth/cancel | complete |
| 6 Replay | causal processor/inference/WebSocket/tests | ordered chunks, controls, bounded state, cleanup; CLI/API equivalence | complete |
| 7 Dashboard | all routes, API types/hooks/CSS | pinned Operate UI; predictions/replay/reports; URL state; accessible responsive checks | complete |
| 8 Advanced comparison | versioned dataset/splits, optional torch | bounded causal TCN; training-only validation; real holdout comparison; resumable LOSO | complete |
| 9 Operations | Docker/Compose/Caddy/Terraform/CI | source + Terraform/mock validation + native auth proxy passed; Linux container health/auth passed remotely; full real-data container/cloud runtime remains blocked | prepared / locally validated |
| 10 Integrated verification | all phases/docs | backend/types/lint/build/browser/real job/prediction/replay/proxy passed; screenshots/docs complete; real-data container/cloud NOT RUN | complete with recorded blockers |
| Research extensions | primary path complete | ST-CNN, GRU/LSTM, circular regression, calibrated adaptation need separate experiments; never claim completion without evidence | not implemented; optional research |

Commands and measured results are recorded in progress.md and docs/VERIFICATION_REPORT.md as execution proceeds. Full training must not be replaced by smoke claims. AWS applies and dataset cloud transfer require concrete inputs and authorization.

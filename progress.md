# Progress

2026-10-26: Steps 1-10 application/source work complete, with explicit environment blockers for Docker/cloud execution. See docs/VERIFICATION_REPORT.md for commands, results and unrun gates.

1. Audit/plans: real source/PDF/presentation inspected; pinned upstream skill references read; no extra agents/global hooks. Existing source and historical artifacts preserved.
2. Scientific/ML: shared causal-v1/physical-v2; 4032 actual trials/14 subjects verified. Fixed classical 378 folds, matched logistic 126, final nested primary 14 and TCN 14 completed. Primary 77.8393% accuracy / 0.779398 F1 on 3610 eligible trials; TCN 76.2327% / 0.762474. Published derived manifests carry original hashes and explicit coverage corrections where needed.
3. Application: real inference/registry, durable SQLite jobs/separate worker, bounded recorded WS replay, typed/provenance dashboard with all ten routes, exports, mobile/keyboard/error states. Actual CLI/API/proxy replay scores match. Source units and retrospective diagnostics are labeled accurately.
4. Verification: clean runtime 47 passed/1 optional skip; dedicated Torch 48 passed; no-data simulation 39 passed/9 explicit skips; browser 10 passed; lint/type/build/audits pass; Terraform schema + one mocked security plan pass; native authenticated Caddy smoke passes. Screenshots inspected. Original twelve model/report artifacts unchanged; raw data/environments/tools/credentials excluded.
5. Operations: Docker/Compose, Terraform EC2/S3/SSM/IAM/CloudWatch, CI/OIDC release configuration and complete docs prepared. Docker unavailable, cloud/domain/budget/data permission absent: no container execution, actual-account plan/apply, cloud smoke or raw-data upload. Optional research extensions are not implemented.

Local application: http://localhost:5173, API http://127.0.0.1:8000. API, separate worker and frontend remain running for review. New clones must install the local data and train/activate or restore compatible serving weights. Published reports are included in Git; generated model binaries are retained locally.

Next action (under 2 minutes): open /predictions?subject=S1&trial=0 and select Predict direction.

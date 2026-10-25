# Decisions

2026-10-25

- Preserve legacy reports and `.joblib` files byte-for-byte. Corrected work uses `causal-v1`, fixed channels and experiment-specific directories; legacy evaluation remains retrospective.
- No guaranteed pre-cue quiet period for trial 0. Use 25 initial cue samples for calibration, emit nothing until ready, include delay in latency, and disclose missed early events. No claim of zero-calibration continuous detection.
- Fixed all-channel processor avoids future-variance channel selection. Train-only standardization stays inside sklearn pipelines.
- Immutable dataset checksums and matching trial IDs are required for new comparisons. Historical 1000 ms results remain unmatched historical context.
- Single persistent SQLite worker is sufficient for a course deployment; no distributed queue or new infrastructure service solely for jobs.
- Keep existing frontend framework, chart package and CSS; no animation dependency. Impeccable Operate mode and the user's pinned palette/font/motion requirements control presentation.
- No extra agents. Upstream references are read locally without global installation/hooks. Cloud costs/data upload are outside current execution until explicit configuration and authorization exist.

2026-10-26

- Keep the serving family/window predeclared (logistic/100 ms); select C using only inner training subjects, then refit outer training subjects. Do not select the serving policy by outer scores.
- Run a separate 3596-trial matched-cohort experiment so longer-window comparisons have identical eligible training and test pools. Keep earlier all-eligible comparison results and exact dependency versions.
- Upgrade vulnerable FastAPI/Starlette/sklearn dependencies in an isolated environment; remove unused multipart/pandas/h5py runtime dependencies. Retrain/re-evaluate final serving weights under sklearn 1.5.2; older binaries are incompatible and shown disabled.
- Publish derived manifest copies with original hashes. Correct the old coverage denominator only in explicitly labeled published copies; never overwrite completed original manifests. Original model binaries/report content are unchanged.
- Native Caddy is sufficient to verify actual proxy auth/HTTP/WS behavior when Docker is absent; it does not establish container or cloud readiness. Terraform JSON avoids fragile generated compact HCL; provider validation and a mocked plan pass without AWS access.
- Keep cloud training single-host, with one durable worker and explicit backup/restore. No apply, raw-data upload, domain provisioning or cost claim is authorized by missing configuration.
- PyTorch and sklearn DLL initialization conflict in this Windows environment when torch loads late; preload torch before pytest for optional sequence tests. Serving has no torch dependency.

- Remote CI found the worker inheriting the API HTTP health check. Override it with worker heartbeat health; all four jobs then passed at 264d72c. Record container build/health/auth separately from unrun real-data container/cloud inference.

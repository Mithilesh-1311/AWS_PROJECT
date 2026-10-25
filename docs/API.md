# API

Base path `/api`; typed frontend contracts are in `frontend/src/services/types.ts`, and prediction/registry/job response schemas are in `backend/app/api/schemas.py`. `/docs` on the local API exposes the complete generated schema. The current API version is 0.2.0.

| Endpoint | Purpose |
|---|---|
| GET `/health`, `/ready` | Process liveness; dataset/model/worker/storage readiness |
| GET `/dataset/summary`, `/subjects`, `/subjects/{id}/trials` | Actual source metadata/trials |
| GET `/subjects/{id}/trials/{n}/signal`, `/processing`, `/onset`, `/early-window` | Raw waveform and explicitly retrospective diagnostics |
| GET `/data-quality` | Live schema, finite-data, phase/count checks |
| GET `/v1/models`; POST `/v1/models/{id}/activate` | Compatible model metadata; explicit activation |
| POST `/v1/predictions` | Real recorded trial inference or abstention |
| POST/GET `/v1/jobs`; GET `/v1/jobs/{id}`; POST `/v1/jobs/{id}/cancel` | Durable bounded training jobs |
| GET `/v1/experiments`, `/v1/experiments/{id}` | Live or published provenance/results |
| GET `/v1/experiments/{id}/export?format=json|csv|html` | JSON/CSV or printable HTML report |
| WS `/v1/replay` | Real recorded-data chunks and shared causal inference |

Prediction body:

```json
{"subject_id":"S1","trial_id":0,"model_id":null}
```

`model_id:null` uses explicit active selection. Predictions return class order, uncalibrated probabilities, model/experiment IDs, window/calibration/crossing/confirmation/readiness metadata and feature/model/processing timing. Evaluation target metadata is separate. Missing or incompatible models return a bounded validation error; absent eligible windows return `state:abstained`.

Job body:

```json
{"subjects":["S1","S2","S3"],"models":["logistic_regression"],"windows":[100],"evaluation":"holdout","smoke":true}
```

Jobs return HTTP 202 and an ID. States are queued, running, succeeded, failed or cancelled. Poll the returned ID; do not infer completion from another latest job. Supported families: logistic_regression, linear_svm, random_forest. Budgets: 20,40,60,80,100,120,160,200,400 ms. Full LOSO is separate from the dashboard's explicitly labeled S1-S3 smoke job. Worker errors expose a category and safe message; details remain in server logs.

Replay first message:

```json
{"subject_id":"S1","trial_id":0,"model_id":null,"channels":[0,1,2,3],"chunk_size":16,"speed":1}
```

The server emits metadata, ordered chunks, a prediction once available and a completion state/target. Chunk messages include sequence, start/end sample, source time and processing timestamp. Display channels do not change the model's fixed 16-channel input. Speed is 0.25 through 8; chunks are 1 through 128 samples. Send `{"action":"pause"}`, `{"action":"play"}`, `{"action":"reset"}` or `{"action":"speed","value":2}`. Reset/reconnect restarts cue calibration. A reset preserves the paused state. Disconnect frees the session; no resume-from-midstream state is promised.

Cloud access requires HTTPS basic auth at Caddy for static pages, data, exports, activation and jobs. Do not expose API port 8000. The proxy token belongs only in server environment configuration. Local training/activation/replay authorization is loopback-only; deployed mode does not inherit that exception. HTTP 422 means invalid inputs/configuration, 503 means required source/artifact unavailable, 403 means backend authentication missing, and 429 means the configured resource limit was reached.

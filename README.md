# EOG Intent

Recorded EOG research workspace: validated dataset exploration, causal early-window inference, recorded WebSocket replay, reproducible subject-held-out evaluation, durable training jobs and provenance exports.

Final logistic 100 ms result: **77.84% accuracy / 0.7794 macro F1**, 14-subject LOSO, 3,610 eligible trials out of 4,032. The 25-sample calibration delay and onset-confirmation delay are included in decision readiness. Observation budget is not total latency. See [model card](docs/MODEL_CARD.md) and [experiment evidence](docs/EXPERIMENTS.md).

## Local launch (PowerShell)

Use Python 3.10 and Node 22. Raw data is deliberately excluded. Place the supplied archive under `Dataset_Isotropic/Dataset_Isotropic/S1...S14`, or set `EOG_DATASET_ROOT` to a folder containing S1...S14. Published reports can be viewed without raw data; training/prediction/replay require it.

```powershell
cd backend
python -m venv .venv-local
.\.venv-local\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv-local\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

In a second terminal, from `backend`:

```powershell
.\.venv-local\Scripts\python.exe -m scripts.worker
```

In a third terminal:

```powershell
cd frontend
npm ci
npm run dev
```

Open **http://localhost:5173**. API health: **http://127.0.0.1:8000/api/health**; interactive API schema: **http://127.0.0.1:8000/docs**. Local launch binds loopback. Frontend API and WebSocket requests use the same-origin `/api` proxy.

New clones contain published experiment reports, not generated serving binaries. With the data installed, train and activate a compatible model:

```powershell
cd backend
.\.venv-local\Scripts\python.exe -m scripts.train_causal --models logistic_regression --windows 100 --evaluation loso --serve
# Read the experiment ID from the output, then substitute it below:
.\.venv-local\Scripts\python.exe -c "from app.models.registry import activate; activate('<experiment-id>_logistic_100')"
```

## Verification

```powershell
cd backend
python -m pytest -q
python -m scripts.verify_artifacts
# From frontend, with API + worker running:
npm run lint
npm run build
npx playwright install chromium
npm run test:e2e
```

The clean runtime passed 47 tests with one optional TCN test skipped; the dedicated Torch environment passed all 48 tests including the TCN. Ten browser tests passed at desktop and mobile sizes. Authenticated Caddy inference and replay passed. Exact commands, test scopes and unrun gates are in [VERIFICATION_REPORT.md](docs/VERIFICATION_REPORT.md).

## Deployment and demonstration

Docker Compose provides Caddy/static frontend, API and a separate worker. Copy `.env.example` to `.env`, generate the required bcrypt hash/token, then use `docker compose up -d --build`. [AWS_DEPLOYMENT.md](docs/AWS_DEPLOYMENT.md) gives the complete configuration and rollback/backup path.

AWS status: **prepared; Terraform schema and mocked security plan validated; not deployed; not cloud-verified**. No AWS resources or raw-data uploads were performed. Docker/container execution was not run locally because Docker is unavailable; CI contains that gate.

Demo: Dataset Explorer → Signal Processing (retrospective diagnostics) → Early Windows → Predictions (causal) → Live Replay (recorded data) → Model Evaluation → Reports. Follow the [demo script](docs/DEMO_SCRIPT.md).

Read [DATASET_CARD](docs/DATASET_CARD.md), [ARCHITECTURE](docs/ARCHITECTURE.md), [API](docs/API.md) and [EXPERIMENTS](docs/EXPERIMENTS.md) for scientific and operational limits. Research extensions are explicitly unimplemented. No clinical or connected-hardware validation is claimed.

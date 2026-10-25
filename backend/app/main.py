"""
FastAPI Backend — EOG Early Intent Detection
=============================================
Main application entry point.

Run with:
    uvicorn app.main:app --reload --port 8000
"""
import logging
import os
import time
from collections import defaultdict, deque
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.api.dataset import router as dataset_router
from app.api.subjects import router as subjects_router
from app.api.signals import router as signals_router
from app.api.experiments import router as experiments_router
from app.api.quality import router as quality_router
from app.api.research import router as research_router, authorized

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')

app = FastAPI(
    title="EOG Early Intent Detection API",
    description="Backend for Low-Latency EOG-Based Early Saccade Direction Prediction",
    version="0.2.0",
)

# CORS for frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("EOG_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(dataset_router, prefix="/api", tags=["Dataset"])
app.include_router(subjects_router, prefix="/api", tags=["Subjects"])
app.include_router(signals_router, prefix="/api", tags=["Signals"])
app.include_router(experiments_router, prefix="/api", tags=["Experiments"])
app.include_router(quality_router, prefix="/api", tags=["Quality"])
app.include_router(research_router, prefix="/api", tags=["Research v1"])

_requests = defaultdict(deque)


@app.middleware("http")
async def access_limits(request: Request, call_next):
    if request.url.path != "/api/health" and os.environ.get("EOG_DEPLOYED") == "1":
        if not authorized(request.headers, request.client.host if request.client else ""):
            return JSONResponse({"detail": "Authenticated access required"}, status_code=403)
    length = request.headers.get("content-length", "0")
    if not length.isdecimal():
        return JSONResponse({"detail": "Invalid Content-Length"}, status_code=400)
    if int(length) > 65536:
        return JSONResponse({"detail": "Payload exceeds 64 KiB"}, status_code=413)
    if request.method in {"POST", "PUT", "PATCH"}:
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > 65536:
                return JSONResponse({"detail": "Payload exceeds 64 KiB"}, status_code=413)
        request._body = bytes(body)
    key = request.client.host if request.client else "unknown"
    now = time.monotonic()
    for stale in [host for host, timestamps in _requests.items() if not timestamps or timestamps[-1] < now - 60]:
        del _requests[stale]
    if key not in _requests and len(_requests) >= 1024:
        return JSONResponse({"detail": "Server client limit reached"}, status_code=429)
    queue = _requests[key]
    while queue and queue[0] < now - 60:
        queue.popleft()
    if len(queue) >= 240:
        return JSONResponse({"detail": "Request rate exceeded"}, status_code=429, headers={"Retry-After": "60"})
    queue.append(now)
    return await call_next(request)


@app.exception_handler(ValueError)
async def invalid_input(request: Request, error: ValueError):
    return JSONResponse({"detail": str(error)}, status_code=422)


@app.exception_handler(FileNotFoundError)
async def unavailable(request: Request, error: FileNotFoundError):
    return JSONResponse({"detail": "Required dataset or artifact unavailable"}, status_code=503)


@app.get("/api/ready")
def readiness():
    from app.core.config import DATASET_ROOT, STATE_DIR
    from app.models.registry import active_model_id, load_model
    from app.evaluation.jobs import worker_ready
    from app.data.dataset_loader import get_loader
    dataset_ready = False
    if DATASET_ROOT is not None:
        try:
            loader = get_loader()
            dataset_ready = bool(loader.subject_ids) and all(
                loader.get_subject_metadata(sid).n_channels == 16 and loader.get_subject_metadata(sid).n_trials == 288
                for sid in loader.subject_ids)
        except (ValueError, OSError):
            pass
    selected = active_model_id()
    model_ready = False
    if selected:
        try:
            load_model(selected)
            model_ready = True
        except ValueError:
            pass
    return {"dataset": dataset_ready, "model": model_ready,
            "active_model_id": selected, "worker": worker_ready(), "storage": STATE_DIR.exists(), "version": "0.2.0"}


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    from app.core.config import DATASET_ROOT
    return {
        "status": "ok",
        "version": "0.2.0",
        "dataset_loaded": DATASET_ROOT is not None and DATASET_ROOT.exists(),
    }

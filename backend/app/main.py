"""
FastAPI Backend — EOG Early Intent Detection
=============================================
Main application entry point.

Run with:
    uvicorn app.main:app --reload --port 8000
"""
import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.dataset import router as dataset_router
from app.api.subjects import router as subjects_router
from app.api.signals import router as signals_router
from app.api.experiments import router as experiments_router
from app.api.quality import router as quality_router

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')

app = FastAPI(
    title="EOG Early Intent Detection API",
    description="Backend for Low-Latency EOG-Based Early Saccade Direction Prediction",
    version="0.1.0",
)

# CORS for frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
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


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    from app.core.config import DATASET_ROOT
    return {
        "status": "ok",
        "version": "0.1.0",
        "dataset_loaded": DATASET_ROOT is not None and DATASET_ROOT.exists(),
        "dataset_path": str(DATASET_ROOT) if DATASET_ROOT else None,
    }

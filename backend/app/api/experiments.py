"""Experiment results API routes."""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pathlib import Path
import json
import glob
from app.core.config import REPORTS_DIR

router = APIRouter()


@router.get("/experiments")
async def list_experiments():
    """List all saved experiment results."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    experiments = []
    for f in sorted(REPORTS_DIR.glob("experiment_*.json")):
        try:
            with open(f) as fp:
                data = json.load(fp)
            experiments.append({
                "experiment_id": data.get("experiment_id"),
                "model_name": data.get("model_name"),
                "n_classes": data.get("n_classes"),
                "alignment": data.get("alignment"),
                "split_method": data.get("split_method"),
                "timestamp": data.get("timestamp"),
                "n_windows": len(data.get("window_results", [])),
                "notes": data.get("notes"),
            })
        except Exception:
            continue
    return {"experiments": experiments}


@router.get("/experiments/{experiment_id}")
async def get_experiment(experiment_id: str):
    """Get detailed results for a specific experiment."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    # Search for the experiment file
    for f in REPORTS_DIR.glob("experiment_*.json"):
        try:
            with open(f) as fp:
                data = json.load(fp)
            if data.get("experiment_id") == experiment_id:
                return data
        except Exception:
            continue
    raise HTTPException(404, f"Experiment {experiment_id} not found")


@router.get("/experiments/latest/results")
async def get_latest_results():
    """Get the most recent experiment results (convenience endpoint)."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(REPORTS_DIR.glob("experiment_*.json"), key=lambda f: f.stat().st_mtime)
    if not files:
        raise HTTPException(404, "No experiments found. Run a baseline experiment first.")
    with open(files[-1]) as f:
        return json.load(f)


@router.post("/experiments/legacy-instructions")
async def trigger_baseline(background_tasks: BackgroundTasks):
    """Trigger a baseline experiment run in the background.

    Note: For Review 1, experiments are run via the CLI script.
    This endpoint exists for future use.
    """
    return {
        "status": "Use CLI for Review 1",
        "command": "python -m scripts.run_baseline --n-classes 8 --model logistic_regression",
        "note": "Background experiment execution planned for Phase 2."
    }

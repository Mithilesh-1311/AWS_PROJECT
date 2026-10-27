"""Versioned model inference, durable jobs, provenance exports and recorded replay."""
import asyncio
import csv
import hmac
import html
import io
import json
import os
import time
from typing import Literal
from fastapi import APIRouter, HTTPException, Request, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field, ConfigDict
from app.core.config import EXPERIMENTS_DIR, PUBLISHED_DIR
from app.models.registry import model_records, active_model_id, activate, predict_trial, recorded_trial, load_model, predict_window
from app.evaluation import jobs
from app.signal_processing.causal import CausalProcessor

from app.api.schemas import RegistryResponse, PredictedResponse, AbstainedResponse, JobResponse, JobsResponse

router = APIRouter()


def authorized(headers, host):
    if os.environ.get("EOG_DEPLOYED") == "1":
        access_token = os.environ.get("EOG_ACCESS_TOKEN", "")
        if len(access_token) >= 32 and hmac.compare_digest(
                headers.get("authorization", "").encode(), f"Bearer {access_token}".encode()):
            return True
        token = os.environ.get("EOG_PROXY_TOKEN", "")
        return len(token) >= 32 and hmac.compare_digest(headers.get("x-eog-proxy-token", "").encode(), token.encode()) and bool(headers.get("x-eog-user"))
    return host in {"127.0.0.1", "::1", "localhost", "testclient"}


def protect(request):
    if not authorized(request.headers, request.client.host if request.client else ""):
        raise HTTPException(403, "Authenticated access required")


class PredictionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    subject_id: str = Field(pattern=r"^S(?:[1-9]|1[0-4])$")
    trial_id: int = Field(ge=0, le=287)
    model_id: str | None = Field(default=None, max_length=100)


class JobRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    subjects: list[str] | None = Field(default=None, min_length=3, max_length=14)
    models: list[Literal["logistic_regression", "linear_svm", "random_forest"]] = Field(default=["logistic_regression"], min_length=1, max_length=3)
    windows: list[Literal[20, 40, 60, 80, 100, 120, 160, 200, 400]] = Field(default=[100], min_length=1, max_length=9)
    evaluation: Literal["holdout", "loso"] = "holdout"
    smoke: bool = True


@router.get("/v1/models", response_model=RegistryResponse)
def models():
    return {"models": model_records(), "active_model_id": active_model_id()}


@router.post("/v1/models/{model_id}/activate")
def activate_model(model_id: str, request: Request):
    protect(request)
    activate(model_id)
    return {"active_model_id": model_id}


@router.post("/v1/predictions", response_model=PredictedResponse | AbstainedResponse)
def prediction(body: PredictionRequest):
    return predict_trial(body.subject_id, body.trial_id, body.model_id)


@router.post("/v1/jobs", status_code=202, response_model=JobResponse)
@router.post("/experiments/run-baseline", status_code=202, response_model=JobResponse)
def create_job(body: JobRequest, request: Request):
    protect(request)
    from app.data.dataset_loader import get_loader
    available = get_loader().subject_ids
    selected = body.subjects or available
    if len(selected) < 3 or len(set(body.models)) != len(body.models) or len(set(body.windows)) != len(body.windows) or len(set(selected)) != len(selected) or not set(selected) <= set(available):
        raise HTTPException(422, "Select distinct available subject IDs")
    return jobs.create_job(body.model_dump())


@router.get("/v1/jobs", response_model=JobsResponse)
def list_jobs():
    return {"jobs": jobs.list_jobs(), "worker_ready": jobs.worker_ready()}


@router.get("/v1/jobs/{job_id}", response_model=JobResponse)
def job_status(job_id: str):
    return jobs.get_job(job_id)


@router.post("/v1/jobs/{job_id}/cancel", response_model=JobResponse)
def cancel_job(job_id: str, request: Request):
    protect(request)
    return jobs.cancel_job(job_id)


def report(experiment_id):
    if not experiment_id.isalnum() or len(experiment_id) > 64:
        raise HTTPException(422, "Invalid experiment ID")
    path = PUBLISHED_DIR / f"{experiment_id}.json"
    if not path.exists():
        path = EXPERIMENTS_DIR / experiment_id / "manifest.json"
    if not path.exists():
        raise HTTPException(404, "Experiment not found")
    return json.loads(path.read_text())


@router.get("/v1/experiments")
def experiments():
    records = []
    live = list(EXPERIMENTS_DIR.glob("*/manifest.json"))
    live_ids = {p.parent.name for p in live}
    paths = live + [p for p in PUBLISHED_DIR.glob("*.json") if p.stem not in live_ids]
    for path in sorted(paths):
        try:
            item = json.loads(path.read_text())
            records.append({k: item[k] for k in ["experiment_id", "config", "timestamp", "status"]})
        except (ValueError, KeyError):
            continue
    return {"experiments": records[-100:]}


@router.get("/v1/experiments/{experiment_id}")
def experiment(experiment_id: str):
    return report(experiment_id)


@router.get("/v1/experiments/{experiment_id}/export")
def export_report(experiment_id: str, format: Literal["json", "csv", "html"] = "json"):
    data = report(experiment_id)
    if format == "json":
        return Response(json.dumps(data, indent=2), media_type="application/json",
                        headers={"Content-Disposition": f'attachment; filename="{experiment_id}.json"'})
    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["experiment_id", "model", "requested_ms", "samples", "accuracy", "balanced_accuracy", "macro_f1", "n_predictions"])
        for r in data.get("results", []):
            writer.writerow([experiment_id, r["model_name"], r["window_ms"], r["n_samples"],
                             r["metrics"]["accuracy"], r["metrics"]["balanced_accuracy"], r["metrics"]["macro_f1"], r["n_predictions"]])
        return Response(output.getvalue(), media_type="text/csv",
                        headers={"Content-Disposition": f'attachment; filename="{experiment_id}.csv"'})
    content = html.escape(json.dumps(data, indent=2))
    return Response(f'<!doctype html><html lang="en"><meta charset="utf-8"><title>EOG experiment {experiment_id}</title><style>body{{font:14px monospace;margin:2rem}}pre{{white-space:pre-wrap;overflow-wrap:anywhere}}@media print{{button{{display:none}}}}</style><h1>EOG Intent research report</h1><button onclick="window.print()">Print</button><pre>{content}</pre></html>', media_type="text/html")


async def replay_message(socket):
    raw = await socket.receive_text()
    if len(raw.encode("utf-8")) > 65536:
        raise ValueError("Replay message exceeds 64 KiB")
    message = json.loads(raw)
    if not isinstance(message, dict):
        raise ValueError("Replay messages must be objects")
    return message


_sessions = set()


@router.websocket("/v1/replay")
async def replay(socket: WebSocket):
    origin = socket.headers.get("origin")
    origins = os.environ.get("EOG_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    protocols = [value.strip() for value in socket.headers.get("sec-websocket-protocol", "").split(",")]
    headers = dict(socket.headers)
    for protocol in protocols:
        if protocol.startswith("eog-token."):
            headers["authorization"] = "Bearer " + protocol.removeprefix("eog-token.")
    if (origin and origin not in origins) or not authorized(headers, socket.client.host if socket.client else "") or len(_sessions) >= 4:
        await socket.close(code=1008)
        return
    await socket.accept(subprotocol="eog-replay" if "eog-replay" in protocols else None)
    session_id = id(socket)
    _sessions.add(session_id)
    try:
        config = await asyncio.wait_for(replay_message(socket), timeout=15)
        request = PredictionRequest.model_validate({k: config[k] for k in ["subject_id", "trial_id", "model_id"] if k in config})
        selected = request.model_id or active_model_id()
        _, metadata = load_model(selected)
        raw, trial = recorded_trial(request.subject_id, request.trial_id)
        speed = float(config.get("speed", 1))
        chunk_size = int(config.get("chunk_size", 16))
        channels = config.get("channels", [0, 1, 2, 3])
        if not isinstance(channels, list):
            raise ValueError("Channels must be an array")
        if not 0.25 <= speed <= 8 or not 1 <= chunk_size <= 128 or not channels or len(channels) > 16 or any(type(c) is not int or c < 0 or c >= 16 for c in channels) or len(set(channels)) != len(channels):
            raise ValueError("Invalid replay speed/chunk/channels")
        processor = CausalProcessor(metadata["window_ms"], metadata["alignment"])
        position, sequence, paused, emitted = 0, 0, False, False
        await socket.send_json({"type": "metadata", "version": 1, "source": "RECORDED DATA REPLAY", "model_id": selected,
                                "sampling_rate_hz": 256, "n_samples": raw.shape[1], "channels": channels,
                                "reset_policy": "reconnect and reset restart the cue-triggered trial", "units": "recorded units (scale unverified)"})
        last_command = time.monotonic()
        while True:
            if (paused or position == raw.shape[1]) and time.monotonic() - last_command > 300:
                await socket.close(code=1000)
                break
            if not paused and position < raw.shape[1]:
                end = min(position + chunk_size, raw.shape[1])
                result = processor.push(raw[:, position:end], position)
                event = {"type": "chunk", "sequence": sequence, "start_sample": position, "end_sample": end,
                         "source_time_ms": position / 256 * 1000, "processed_monotonic_ns": time.perf_counter_ns(),
                         "state": processor.status(), "data": {str(c): raw[c, position:end].tolist() for c in channels}}
                if result and not emitted:
                    event["prediction"] = predict_window(result, selected)
                    emitted = True
                await asyncio.wait_for(socket.send_json(event), timeout=5)
                position, sequence = end, sequence + 1
                if position == raw.shape[1]:
                    await socket.send_json({"type": "complete", "state": "predicted" if emitted else "abstained",
                                            "evaluation": {"target_class": trial.direction_label_8, "target_angle_deg": trial.target_angle_deg}})
            try:
                delay = chunk_size / 256 / speed if not paused and position < raw.shape[1] else 30
                command = await asyncio.wait_for(replay_message(socket), timeout=delay)
            except asyncio.TimeoutError:
                if paused or position == raw.shape[1]:
                    await socket.send_json({"type": "idle", "state": "paused" if paused else "complete"})
                continue
            last_command = time.monotonic()
            action = command.get("action")
            if action == "pause":
                paused = True
            elif action == "play":
                paused = False
            elif action == "reset":
                processor = CausalProcessor(metadata["window_ms"], metadata["alignment"])
                position, sequence, emitted = 0, 0, False
                await socket.send_json({"type": "reset"})
            elif action == "speed":
                candidate = float(command.get("value", 0))
                if not 0.25 <= candidate <= 8:
                    raise ValueError("Invalid speed")
                speed = candidate
            else:
                raise ValueError("Unsupported replay command")
    except WebSocketDisconnect:
        pass
    except (ValueError, KeyError, asyncio.TimeoutError):
        try:
            await socket.send_json({"type": "error", "message": "Invalid replay configuration, missing model/data or stalled client"})
            await socket.close(code=1008)
        except (RuntimeError, WebSocketDisconnect):
            pass
    finally:
        _sessions.discard(session_id)

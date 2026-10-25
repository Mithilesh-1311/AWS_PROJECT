import json
import time
from types import SimpleNamespace
import importlib.metadata
import joblib
import numpy as np
import pytest
from fastapi.testclient import TestClient
from app.main import app, _requests
from app.evaluation import jobs
from app.models import registry
from app.api import research
from app.models.baseline_models import create_model
from app.evaluation.reproducible import checksum, write_json


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(jobs, "STATE_DIR", tmp_path / "state")
    monkeypatch.setattr(registry, "STATE_DIR", tmp_path / "state")
    monkeypatch.setattr(registry, "EXPERIMENTS_DIR", tmp_path / "experiments")
    monkeypatch.delenv("EOG_DEPLOYED", raising=False)
    monkeypatch.delenv("EOG_ACTIVE_MODEL", raising=False)
    registry.load_model.cache_clear()
    _requests.clear()
    yield tmp_path
    registry.load_model.cache_clear()


@pytest.fixture
def serving(isolated, monkeypatch):
    identifier = "a" * 32
    folder = isolated / "experiments" / identifier
    folder.mkdir(parents=True)
    rng = np.random.default_rng(2)
    model = create_model("logistic_regression").fit(rng.normal(size=(80, 212)), np.tile(np.arange(8), 10))
    joblib.dump(model, folder / "serving.joblib")
    model_id = identifier + "_logistic_100"
    write_json(folder / "model.json", {"model_id": model_id, "experiment_id": identifier, "window_ms": 100,
               "alignment": "onset", "preprocessing_version": "causal-v1", "feature_version": "physical-v2",
               "n_features": 212, "class_names": [str(i) for i in range(8)], "class_order": list(range(8)),
               "score_semantics": "uncalibrated_probability", "warning": "synthetic test fixture",
               "versions": {"scikit-learn": importlib.metadata.version("scikit-learn")},
               "sha256": checksum(folder / "serving.joblib")})
    raw = rng.normal(0, .001, (16, 140))
    raw[:, 40:] += np.arange(100) * 10
    trial = SimpleNamespace(direction_label_8=3, target_angle_deg=135)
    monkeypatch.setattr(registry, "recorded_trial", lambda *a: (raw, trial))
    monkeypatch.setattr(research, "recorded_trial", lambda *a: (raw, trial))
    registry.activate(model_id)
    return model_id, folder, raw, trial


def test_registry_predict_and_target_independence(serving):
    mid, folder, raw, trial = serving
    first = registry.predict_trial("S1", 0)
    trial.direction_label_8 = 7
    second = registry.predict_trial("S1", 0)
    assert first["scores"] == second["scores"]
    assert sum(first["scores"]) == pytest.approx(1)
    assert first["model_id"] == mid and first["window"]["n_samples"] == 26
    registry.load_model.cache_clear()
    (folder / "serving.joblib").write_bytes(b"corrupt")
    with pytest.raises(ValueError, match="checksum"):
        registry.load_model(mid)


def test_api_and_replay_match(serving):
    with TestClient(app) as client:
        response = client.post("/api/v1/predictions", json={"subject_id": "S1", "trial_id": 0})
        assert response.status_code == 200
        expected = response.json()
        for chunk_size in [1, 17, 128]:
            with client.websocket_connect("/api/v1/replay") as socket:
                socket.send_json({"subject_id": "S1", "trial_id": 0, "chunk_size": chunk_size, "speed": 8})
                assert socket.receive_json()["source"] == "RECORDED DATA REPLAY"
                next_sample = 0
                prediction = None
                while True:
                    event = socket.receive_json()
                    if event["type"] == "complete":
                        break
                    assert event["start_sample"] == next_sample
                    next_sample = event["end_sample"]
                    prediction = event.get("prediction", prediction)
                assert prediction["scores"] == pytest.approx(expected["scores"])
                assert prediction["window"]["ready_sample"] == expected["window"]["ready_sample"]
        deadline = time.monotonic() + 1
        while research._sessions and time.monotonic() < deadline:
            time.sleep(.01)
        assert not research._sessions


def test_input_limits_and_deployed_auth(isolated, monkeypatch):
    with TestClient(app) as client:
        assert client.post("/api/v1/predictions", json={"subject_id": "../S1", "trial_id": -1}).status_code == 422
        assert client.post("/api/v1/predictions", content=b"x" * 65537).status_code == 413
        for query in ["channels=-1", "channels=16", "channels=one", "phase=bad"]:
            assert client.get("/api/subjects/S1/trials/0/signal?" + query).status_code in {422, 503}
        monkeypatch.setenv("EOG_DEPLOYED", "1")
        monkeypatch.setenv("EOG_PROXY_TOKEN", "t" * 32)
        assert client.get("/api/v1/models").status_code == 403
        assert client.get("/api/v1/models", headers={"x-eog-user": "researcher", "x-eog-proxy-token": "t" * 32}).status_code == 200
        assert "dataset_path" not in client.get("/api/health").json()


def test_job_claim_cancel_recovery_and_failure(isolated, monkeypatch):
    queued = jobs.create_job({"subjects": ["S1", "S2", "S3"]})
    assert jobs.claim("first")["id"] == queued["id"]
    assert jobs.claim("second") is None
    jobs.cancel_job(queued["id"])
    with pytest.raises(jobs.Cancelled):
        jobs.update_progress(queued["id"], "first", stage="features")
    jobs.finish(queued["id"], "first", "cancelled")
    assert jobs.get_job(queued["id"])["state"] == "cancelled"
    failed = jobs.create_job({})
    jobs.claim("lost")
    with jobs.database() as con:
        con.execute("UPDATE jobs SET updated=? WHERE id=?", (time.time() - 200, failed["id"]))
    assert jobs.claim("new") is None
    assert jobs.get_job(failed["id"])["error"]["code"] == "worker_lost"
    from scripts import worker
    job = jobs.create_job({})
    monkeypatch.setattr(worker, "run_causal", lambda **kw: (_ for _ in ()).throw(ValueError("bad training")))
    assert worker.run_once("worker")
    assert jobs.get_job(job["id"])["state"] == "failed"


def test_queue_bound_and_model_missing(isolated):
    for _ in range(4):
        jobs.create_job({})
    with pytest.raises(ValueError, match="limit"):
        jobs.create_job({})
    with pytest.raises(ValueError, match="No active model"):
        registry.predict_trial("S1", 0)


def test_invalid_replay_messages_fail_closed(serving):
    with TestClient(app) as client:
        for body in [[], {'subject_id':'S1','trial_id':0,'channels':[[1]]},
                     {'subject_id':'S1','trial_id':0,'speed':9}]:
            with client.websocket_connect('/api/v1/replay') as socket:
                socket.send_json(body)
                assert socket.receive_json()['type'] == 'error'
    assert not research._sessions


def test_readiness_requires_validated_data(isolated, monkeypatch):
    from app.data import dataset_loader
    from app.core import config
    monkeypatch.setattr(config, 'DATASET_ROOT', isolated)
    fake = SimpleNamespace(subject_ids=['S1'], get_subject_metadata=lambda sid: (_ for _ in ()).throw(ValueError('invalid shape')))
    monkeypatch.setattr(dataset_loader, 'get_loader', lambda: fake)
    with TestClient(app) as client:
        response = client.get('/api/ready')
        assert response.status_code == 200
        assert response.json()['dataset'] is False
        assert response.json()['model'] is False

"""
Integration tests for FastAPI endpoints
"""
import pytest
from starlette.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["dataset_loaded"] is True

def test_dataset_summary(client):
    res = client.get("/api/dataset/summary")
    assert res.status_code == 200
    data = res.json()
    assert data["n_subjects"] == 14
    assert data["sampling_rate_hz"] == 256
    assert data["n_channels"] == 16

def test_subjects_list(client):
    res = client.get("/api/subjects")
    assert res.status_code == 200
    data = res.json()
    assert "subjects" in data
    assert len(data["subjects"]) == 14

def test_latest_experiment(client):
    res = client.get("/api/experiments/latest/results")
    assert res.status_code == 200
    data = res.json()
    assert "window_results" in data
    assert len(data["window_results"]) > 0

def test_quality_summary(client):
    res = client.get("/api/data-quality")
    assert res.status_code == 200
    data = res.json()
    assert "all_passed" in data
    assert data["n_subjects"] == 14

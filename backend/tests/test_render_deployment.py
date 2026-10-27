from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.api import research
from app.main import app, _requests
from scripts import serve_render


@pytest.fixture
def deployed(monkeypatch):
    monkeypatch.setenv("EOG_DEPLOYED", "1")
    monkeypatch.setenv("EOG_ACCESS_TOKEN", "a" * 64)
    monkeypatch.delenv("EOG_PROXY_TOKEN", raising=False)
    monkeypatch.setenv("EOG_ALLOWED_ORIGINS", "http://localhost:5173")
    monkeypatch.setattr(research, "model_records", lambda: [])
    _requests.clear()


def test_bearer_auth_and_cors(deployed):
    with TestClient(app) as client:
        assert client.get("/api/health").status_code == 200
        for headers in [{}, {"authorization": "Bearer wrong"}, {"x-eog-user": "forged"}]:
            assert client.get("/api/v1/models", headers=headers).status_code == 403
        response = client.get("/api/v1/models", headers={"authorization": "Bearer " + "a" * 64,
                                                           "origin": "http://localhost:5173"})
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
        denied = client.get("/api/v1/models", headers={"origin": "http://localhost:5173"})
        assert denied.status_code == 403
        assert denied.headers["access-control-allow-origin"] == "http://localhost:5173"
        preflight = {"origin": "http://localhost:5173", "access-control-request-method": "POST",
                     "access-control-request-headers": "authorization,content-type"}
        assert client.options("/api/v1/predictions", headers=preflight).status_code == 200
        preflight["origin"] = "https://untrusted.example"
        assert client.options("/api/v1/predictions", headers=preflight).status_code == 400


def test_replay_auth_before_loading_data(deployed, monkeypatch):
    load_model = Mock(side_effect=ValueError("No model installed"))
    monkeypatch.setattr(research, "load_model", load_model)
    with TestClient(app) as client:
        for protocols, origin in [([], "http://localhost:5173"), (["eog-token.wrong"], "http://localhost:5173"),
                                  (["eog-token." + "a" * 64], "https://untrusted.example")]:
            with pytest.raises(WebSocketDisconnect):
                with client.websocket_connect("/api/v1/replay", subprotocols=protocols, headers={"origin": origin}):
                    pass
        load_model.assert_not_called()
        with client.websocket_connect("/api/v1/replay", subprotocols=["eog-replay", "eog-token." + "a" * 64],
                                      headers={"origin": "http://localhost:5173"}) as socket:
            assert socket.accepted_subprotocol == "eog-replay"
            socket.send_json({"subject_id": "S1", "trial_id": 0, "model_id": "missing"})
            assert socket.receive_json()["type"] == "error"
        load_model.assert_called_once_with("missing")


@pytest.mark.parametrize("child_failed", [False, True])
def test_launcher_stops_both_children(monkeypatch, child_failed):
    monkeypatch.setenv("EOG_DEPLOYED", "1")
    monkeypatch.setenv("EOG_ACCESS_TOKEN", "a" * 64)
    monkeypatch.setenv("EOG_ALLOWED_ORIGINS", "https://frontend.example")
    monkeypatch.setenv("PORT", "12345")
    monkeypatch.setattr(serve_render.signal, "signal", Mock())
    event = Mock()
    event.wait.return_value = not child_failed
    monkeypatch.setattr(serve_render.threading, "Event", lambda: event)
    children = [Mock(), Mock()]
    children[0].poll.return_value = 1 if child_failed else None
    children[1].poll.return_value = None
    launch = Mock(side_effect=children)
    monkeypatch.setattr(serve_render.subprocess, "Popen", launch)
    if child_failed:
        with pytest.raises(RuntimeError, match="API or worker exited"):
            serve_render.main()
    else:
        serve_render.main()
        children[0].terminate.assert_called_once()
    children[1].terminate.assert_called_once()
    for child in children:
        child.wait.assert_called_once_with(timeout=20)
    assert "12345" in launch.call_args_list[1].args[0]


def test_launcher_rejects_missing_auth_and_wildcard_origins(monkeypatch):
    monkeypatch.setenv("EOG_DEPLOYED", "1")
    monkeypatch.delenv("EOG_ACCESS_TOKEN", raising=False)
    with pytest.raises(ValueError, match="EOG_ACCESS_TOKEN"):
        serve_render.main()
    monkeypatch.setenv("EOG_ACCESS_TOKEN", "a" * 64)
    monkeypatch.setenv("EOG_ALLOWED_ORIGINS", "https://*.vercel.app")
    with pytest.raises(ValueError, match="exact HTTPS"):
        serve_render.main()

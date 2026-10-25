"""Exercise the production Caddy config with real dataset/model; no cloud resources."""
import base64
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import time
import httpx
from websockets.sync.client import connect


def main():
    root = Path(__file__).resolve().parents[1]
    caddy = os.environ.get('CADDY_BIN', str(root / '.tools/caddy/caddy.exe'))
    password = secrets.token_urlsafe(24)
    hashed = subprocess.run([caddy, 'hash-password', '--plaintext', password], capture_output=True, text=True, check=True).stdout.strip()
    env = dict(os.environ, EOG_DEPLOYED='1', EOG_PROXY_TOKEN=secrets.token_hex(32),
               EOG_ALLOWED_ORIGINS='http://127.0.0.1:8080', EOG_SITE='http://127.0.0.1:8080',
               EOG_UPSTREAM='127.0.0.1:8001', EOG_STATIC_ROOT=str(root / 'frontend/dist'),
               EOG_USER='proxy-test', EOG_PASSWORD_HASH=hashed)
    flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
    folder = root / 'backend/artifacts/cache'
    folder.mkdir(parents=True, exist_ok=True)
    processes = []
    with open(folder / 'proxy_smoke.log', 'w', encoding='utf-8') as log:
        try:
            subprocess.run([caddy, 'validate', '--config', str(root / 'frontend/Caddyfile'), '--adapter', 'caddyfile'], env=env, stdout=log, stderr=log, check=True)
            processes.append(subprocess.Popen([sys.executable, '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8001'], cwd=root / 'backend', env=env, stdout=log, stderr=log, creationflags=flags))
            processes.append(subprocess.Popen([caddy, 'run', '--config', str(root / 'frontend/Caddyfile'), '--adapter', 'caddyfile'], env=env, stdout=log, stderr=log, creationflags=flags))
            with httpx.Client(base_url='http://127.0.0.1:8080', auth=('proxy-test', password), timeout=30) as client:
                deadline = time.monotonic() + 30
                while True:
                    try:
                        if client.get('/api/health').status_code == 200:
                            break
                    except httpx.TransportError:
                        pass
                    if time.monotonic() > deadline:
                        raise RuntimeError('Production proxy did not become healthy; inspect proxy_smoke.log')
                    time.sleep(.1)
                assert httpx.get('http://127.0.0.1:8080/api/v1/models').status_code == 401
                assert httpx.get('http://127.0.0.1:8080/api/v1/models', headers={'X-EOG-User':'forged', 'X-EOG-Proxy-Token':env['EOG_PROXY_TOKEN']}).status_code == 401
                assert client.get('/predictions').status_code == 200
                ready = client.get('/api/ready').json()
                assert ready['model'] and ready['dataset']
                prediction = client.post('/api/v1/predictions', json={'subject_id':'S1','trial_id':0}).json()
                assert prediction['state'] == 'predicted'
                eid = prediction['experiment_id']
                assert client.get(f'/api/v1/experiments/{eid}/export?format=csv').status_code == 200
                auth = base64.b64encode(f'proxy-test:{password}'.encode()).decode()
                with connect('ws://127.0.0.1:8080/api/v1/replay', origin='http://127.0.0.1:8080', additional_headers={'Authorization':'Basic '+auth}, open_timeout=10) as socket:
                    socket.send(json.dumps({'subject_id':'S1','trial_id':0,'speed':8,'chunk_size':17}))
                    assert json.loads(socket.recv(timeout=10))['type'] == 'metadata'
                    next_sample = 0
                    output = None
                    while True:
                        event = json.loads(socket.recv(timeout=10))
                        if event['type'] == 'complete':
                            break
                        assert event['start_sample'] == next_sample
                        next_sample = event['end_sample']
                        output = event.get('prediction', output)
                    assert output['scores'] == prediction['scores']
                    assert output['window']['ready_sample'] == prediction['window']['ready_sample']
                print('PASS: authenticated static route, API readiness/inference/export, forged-header rejection, real WebSocket continuity and matching scores')
        finally:
            for process in reversed(processes):
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()


if __name__ == '__main__':
    main()

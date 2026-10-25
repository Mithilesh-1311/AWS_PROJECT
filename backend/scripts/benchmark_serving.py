"""Local warm API/CLI compatibility and timing; does not measure physical hardware latency."""
import json
from time import perf_counter
import httpx
import numpy as np
from app.models.registry import predict_trial, active_model_id


def main():
    measurements = []
    with httpx.Client(base_url='http://127.0.0.1:8000', timeout=30) as client:
        warm = client.post('/api/v1/predictions', json={'subject_id':'S1','trial_id':0})
        warm.raise_for_status()
        for trial in range(20):
            started = perf_counter()
            response = client.post('/api/v1/predictions', json={'subject_id':'S1','trial_id':trial})
            response.raise_for_status()
            elapsed = (perf_counter() - started) * 1000
            api = response.json()
            cli = predict_trial('S1', trial)
            assert cli['state'] == api['state']
            if api['state'] != 'predicted':
                continue
            np.testing.assert_allclose(cli['scores'], api['scores'], rtol=1e-12, atol=1e-12)
            assert cli['window']['ready_sample'] == api['window']['ready_sample']
            measurements.append(dict(http_roundtrip_ms=elapsed, feature_ms=api['feature_ms'], model_ms=api['inference_ms'],
                                     causal_and_inference_ms=api['server_total_ms'], cue_to_decision_ms=api['window']['cue_to_decision_ms']))
    summary = {key:{'median':float(np.median([m[key] for m in measurements])),
                    'p95':float(np.quantile([m[key] for m in measurements],.95))} for key in measurements[0]}
    print(json.dumps(dict(model_id=active_model_id(), attempts=20, predictions=len(measurements),
                         scope='S1 trials 0..19; one warm-up; local sequential HTTP; raw data may be cached; no physical acquisition or internet latency',
                         metrics_ms=summary), indent=2))


if __name__ == '__main__':
    main()

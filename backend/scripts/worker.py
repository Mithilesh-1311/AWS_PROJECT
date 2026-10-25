"""Run one bounded training job at a time, outside the web server."""
import argparse
import logging
import threading
import time
import uuid
from app.evaluation import jobs
from app.evaluation.reproducible import run_causal


def run_once(owner):
    jobs.heartbeat(owner)
    job = jobs.claim(owner)
    if job is None:
        return False
    stop = threading.Event()

    def keep_alive():
        while not stop.wait(10):
            jobs.heartbeat(owner)
            # Do not renew the job lease here: progress checkpoints own that lease.

    thread = threading.Thread(target=keep_alive, daemon=True)
    thread.start()
    try:
        result = run_causal(**job["config"], experiment_id=job["id"],
                            progress=lambda **kw: jobs.update_progress(job["id"], owner, **kw))
        jobs.finish(job["id"], owner, "succeeded", result={"experiment_id": result["experiment_id"]})
    except jobs.Cancelled as error:
        jobs.finish(job["id"], owner, "cancelled", error={"code": "cancelled", "message": str(error)})
    except Exception as error:
        logging.exception("Training job failed: %s", job["id"])
        jobs.finish(job["id"], owner, "failed", error={"code": type(error).__name__, "message": "Training failed; inspect worker logs"})
    finally:
        stop.set()
        thread.join(timeout=1)
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    owner = uuid.uuid4().hex
    while True:
        jobs.heartbeat(owner)
        ran = run_once(owner)
        if args.once:
            return
        if not ran:
            time.sleep(2)


if __name__ == "__main__":
    main()

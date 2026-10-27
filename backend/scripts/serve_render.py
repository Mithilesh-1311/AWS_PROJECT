"""Keep the API and SQLite worker on the same Render service and disk."""
import os
import signal
import subprocess
import sys
import threading


def main():
    if os.environ.get("EOG_DEPLOYED") != "1" or len(os.environ.get("EOG_ACCESS_TOKEN", "")) < 32:
        raise ValueError("Set EOG_DEPLOYED=1 and EOG_ACCESS_TOKEN to at least 32 characters")
    origins = os.environ.get("EOG_ALLOWED_ORIGINS", "").split(",")
    if not origins or any(not origin.startswith("https://") or origin.endswith("/") or "*" in origin for origin in origins):
        raise ValueError("Set EOG_ALLOWED_ORIGINS to exact HTTPS frontend origins without trailing slashes")
    port = int(os.environ.get("PORT", "10000"))
    if not 1 <= port <= 65535:
        raise ValueError("PORT must be between 1 and 65535")
    # shortcut: one service shares SQLite; move to a shared queue before scaling out.
    stopped = threading.Event()
    signal.signal(signal.SIGTERM, lambda *_: stopped.set())
    signal.signal(signal.SIGINT, lambda *_: stopped.set())
    children = []
    try:
        children.append(subprocess.Popen([sys.executable, "-m", "scripts.worker"]))
        children.append(subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app",
                                         "--host", "0.0.0.0", "--port", str(port),
                                         "--workers", "1", "--no-proxy-headers"]))
        while not stopped.wait(1):
            if any(child.poll() is not None for child in children):
                raise RuntimeError("API or worker exited; stopping service so Render can restart it")
    finally:
        for child in children:
            if child.poll() is None:
                child.terminate()
        for child in children:
            try:
                child.wait(timeout=20)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()


if __name__ == "__main__":
    main()

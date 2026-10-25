"""Single-host SQLite queue; claims and terminal states are transactional."""
import json
import sqlite3
import time
import uuid
from contextlib import contextmanager
from app.core.config import STATE_DIR


@contextmanager
def database():
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(STATE_DIR / "jobs.sqlite3", timeout=10)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, state TEXT NOT NULL, config TEXT NOT NULL, progress TEXT NOT NULL DEFAULT '{}', result TEXT, error TEXT, created REAL NOT NULL, updated REAL NOT NULL, owner TEXT, cancel INTEGER NOT NULL DEFAULT 0)")
    con.execute("CREATE TABLE IF NOT EXISTS workers (id TEXT PRIMARY KEY, heartbeat REAL NOT NULL)")
    try:
        yield con
        con.commit()
    finally:
        con.close()


def decode(row):
    result = dict(row)
    for key in ["config", "progress", "result", "error"]:
        result[key] = json.loads(result[key]) if result[key] else None
    return result


def create_job(config):
    now = time.time()
    job_id = uuid.uuid4().hex
    with database() as con:
        con.execute("BEGIN IMMEDIATE")
        if con.execute("SELECT count(*) FROM jobs WHERE state IN ('queued','running')").fetchone()[0] >= 4:
            raise ValueError("Queue limit reached (4 jobs)")
        con.execute("INSERT INTO jobs(id,state,config,created,updated) VALUES(?,?,?,?,?)",
                    (job_id, "queued", json.dumps(config), now, now))
    return get_job(job_id)


def get_job(job_id):
    with database() as con:
        row = con.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    if row is None:
        raise ValueError("Job not found")
    return decode(row)


def list_jobs():
    with database() as con:
        return [decode(row) for row in con.execute("SELECT * FROM jobs ORDER BY created DESC LIMIT 50")]


def cancel_job(job_id):
    with database() as con:
        con.execute("UPDATE jobs SET cancel=1, state=CASE WHEN state='queued' THEN 'cancelled' ELSE state END, updated=? WHERE id=? AND state IN ('queued','running')", (time.time(), job_id))
    return get_job(job_id)


def heartbeat(owner):
    with database() as con:
        con.execute("INSERT OR REPLACE INTO workers VALUES(?,?)", (owner, time.time()))


def worker_ready():
    with database() as con:
        return bool(con.execute("SELECT 1 FROM workers WHERE heartbeat>? LIMIT 1", (time.time() - 30,)).fetchone())


def claim(owner):
    now = time.time()
    with database() as con:
        con.execute("BEGIN IMMEDIATE")
        # Expired jobs fail explicitly; immutable experiment checkpoints remain resumable.
        con.execute("UPDATE jobs SET state='failed', error=?, updated=? WHERE state='running' AND updated<? AND owner NOT IN (SELECT id FROM workers WHERE heartbeat>?)",
                    (json.dumps({"code": "worker_lost", "message": "Lease expired; resume the experiment explicitly"}), now, now - 120, now - 30))
        if con.execute("SELECT 1 FROM jobs WHERE state='running'").fetchone():
            return None
        row = con.execute("SELECT id FROM jobs WHERE state='queued' ORDER BY created LIMIT 1").fetchone()
        if row is None:
            return None
        con.execute("UPDATE jobs SET state='running',owner=?,updated=? WHERE id=? AND state='queued'", (owner, now, row["id"]))
    return get_job(row["id"])


class Cancelled(Exception):
    pass


def update_progress(job_id, owner, **progress):
    with database() as con:
        row = con.execute("SELECT cancel,state,owner FROM jobs WHERE id=?", (job_id,)).fetchone()
        if not row or row["owner"] != owner or row["state"] != "running":
            raise Cancelled("Worker lease no longer belongs to this process")
        if row["cancel"]:
            raise Cancelled("Cancellation requested")
        con.execute("UPDATE jobs SET progress=?,updated=? WHERE id=? AND owner=?", (json.dumps(progress), time.time(), job_id, owner))


def finish(job_id, owner, state, result=None, error=None):
    with database() as con:
        con.execute("UPDATE jobs SET state=CASE WHEN cancel=1 THEN 'cancelled' ELSE ? END,result=?,error=?,updated=? WHERE id=? AND owner=? AND state='running'",
                    (state, json.dumps(result), json.dumps(error), time.time(), job_id, owner))

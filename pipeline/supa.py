"""Tiny Supabase client (REST + Storage) using the service key from the environment.

Needs SUPABASE_URL and SUPABASE_SERVICE_KEY (GitHub repo secrets). Never put the service key in the site.
"""
import os
import requests

URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")


def _h(extra=None):
    if not URL or not KEY:
        raise SystemExit("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
    h = {"apikey": KEY, "Authorization": f"Bearer {KEY}"}
    h.update(extra or {})
    return h


def select(table, params=None, page=1000):
    """All rows of a table (pages through PostgREST's limit)."""
    rows, start = [], 0
    while True:
        r = requests.get(f"{URL}/rest/v1/{table}", params=params or {"select": "*"},
                         headers=_h({"Range-Unit": "items", "Range": f"{start}-{start + page - 1}"}), timeout=60)
        r.raise_for_status()
        batch = r.json()
        rows += batch
        if len(batch) < page:
            return rows
        start += page


def insert(table, rows, ignore_duplicates=False, returning=True):
    prefer = ["return=representation" if returning else "return=minimal"]
    if ignore_duplicates:
        prefer.append("resolution=ignore-duplicates")
    r = requests.post(f"{URL}/rest/v1/{table}", json=rows,
                      headers=_h({"Prefer": ",".join(prefer), "Content-Type": "application/json"}), timeout=60)
    r.raise_for_status()
    return r.json() if returning and r.text else []


def update(table, match, values):
    r = requests.patch(f"{URL}/rest/v1/{table}", params={k: f"eq.{v}" for k, v in match.items()}, json=values,
                       headers=_h({"Content-Type": "application/json", "Prefer": "return=minimal"}), timeout=60)
    r.raise_for_status()


def upload(bucket, path, data, content_type="image/jpeg"):
    r = requests.post(f"{URL}/storage/v1/object/{bucket}/{path}", data=data,
                      headers=_h({"Content-Type": content_type, "x-upsert": "true"}), timeout=120)
    r.raise_for_status()


def public_url(bucket, path):
    return f"{URL}/storage/v1/object/public/{bucket}/{path}"


class Run:
    """Logs a job to pipeline_runs: `with Run('export') as run: run.stats['x'] = 1`."""

    def __init__(self, job):
        self.job, self.stats, self.id = job, {}, None

    def __enter__(self):
        try:
            self.id = insert("pipeline_runs", [{"job": self.job}])[0]["id"]
        except Exception as e:  # logging must never stop the job
            print("could not log run:", e)
        return self

    def __exit__(self, et, ev, tb):
        if self.id:
            try:
                update("pipeline_runs", {"id": self.id},
                       {"finished_at": "now()", "stats": self.stats, "error": repr(ev) if ev else None})
            except Exception as e:
                print("could not finish run log:", e)
        return False

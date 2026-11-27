"""Cloudflare R2 (the jonin-scans bucket, public at https://img.jonin.cards) for site images.

Card scans and grid thumbnails live here instead of in the site repo (audit fix 2026-11-27): Cloudflare Pages allows
20,000 files per site and every scan added two files to the repo. Keys:
    site/scans/<storage path>     card scans (copied from Supabase Storage by mirror_images.py)
    site/t/<16-hex>.webp          grid thumbnails (thumbs.py)

What's been uploaded is recorded in pipeline/r2_site.json (committed), so export_cards.py and build_pages.py can build
URLs without R2 credentials. Only add a key there after its upload succeeded.

Env: R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_ENDPOINT, R2_BUCKET (default jonin-scans).
"""
import json
import os
from pathlib import Path

PUBLIC = "https://img.jonin.cards/"
MANIFEST = Path(__file__).resolve().parent / "r2_site.json"
IMMUTABLE = "public, max-age=31536000, immutable"


_cache = {}


def manifest():
    """{"scans": storage paths, "t": thumbnail file names} already in R2, read-only (cached until the file changes).
    Scripts that upload use manifest_copy() and save_manifest()."""
    try:
        mt = MANIFEST.stat().st_mtime_ns
    except FileNotFoundError:
        return {"scans": set(), "t": set()}
    if _cache.get("mt") != mt:
        d = json.loads(MANIFEST.read_text())
        _cache.update(mt=mt, m={"scans": frozenset(d.get("scans", [])), "t": frozenset(d.get("t", []))})
    return _cache["m"]


def manifest_copy():
    """A changeable copy of the manifest, for scripts that upload and then save_manifest()."""
    m = manifest()
    return {"scans": set(m["scans"]), "t": set(m["t"])}


def save_manifest(m):
    MANIFEST.write_text(json.dumps({"scans": sorted(m["scans"]), "t": sorted(m["t"])}, indent=0) + "\n")


def scan_url(path):
    return PUBLIC + "site/scans/" + path


def thumb_url(name):
    return PUBLIC + "site/t/" + name


_client = None


def client():
    global _client
    if _client is None:
        import boto3
        _client = boto3.client("s3", endpoint_url=os.environ["R2_ENDPOINT"], region_name="auto",
                               aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
                               aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"])
    return _client


def bucket():
    return os.environ.get("R2_BUCKET", "jonin-scans")


def configured():
    return all(os.environ.get(k) for k in ("R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_ENDPOINT"))


def put(key, data, content_type):
    client().put_object(Bucket=bucket(), Key=key, Body=data, ContentType=content_type, CacheControl=IMMUTABLE)


def existing(prefix):
    """Every key under a prefix (used to double-check the manifest)."""
    out, token = set(), None
    while True:
        kw = {"Bucket": bucket(), "Prefix": prefix, "MaxKeys": 1000}
        if token:
            kw["ContinuationToken"] = token
        r = client().list_objects_v2(**kw)
        out.update(o["Key"] for o in r.get("Contents", []))
        if not r.get("IsTruncated"):
            return out
        token = r["NextContinuationToken"]


def content_type(name):
    n = name.lower()
    return "image/webp" if n.endswith(".webp") else "image/png" if n.endswith(".png") else "image/jpeg"

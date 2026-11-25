"""Copy every public card scan from Supabase Storage into the site (public/img/scans/...), so jonin.cards
serves the images from Cloudflare Pages instead of Supabase. Supabase's free plan only includes 5 GB of
egress a month, and card images are by far the biggest part of a visit.

    python pipeline/mirror_images.py           # download any public scan not mirrored yet

export_cards.py then points each card's "img" at https://jonin.cards/img/scans/<path> when the file is here,
and falls back to the Supabase URL when it isn't (yet). Runs in the "Sync card list" workflow before the export.
"""
import concurrent.futures as cf
from pathlib import Path

import requests

import supa

ROOT = Path(__file__).resolve().parent.parent / "public" / "img" / "scans"
MAX_PER_RUN = 6000          # first run copies everything (~4,300 files); later runs only new scans


def local_path(storage_path):
    p = (ROOT / storage_path).resolve()
    if ROOT.resolve() not in p.parents:
        raise ValueError(f"bad path {storage_path!r}")
    return p


def fetch(path):
    dest = local_path(path)
    r = requests.get(f"{supa.URL}/storage/v1/object/scans/{path}", headers=supa._h(), timeout=60)
    r.raise_for_status()
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    tmp.write_bytes(r.content)
    tmp.rename(dest)
    return len(r.content)


def main():
    with supa.Run("mirror_images") as run:
        rows = supa.select("scans", {"select": "image_url", "public": "eq.true", "image_url": "like.storage:scans/*"})
        paths = sorted({r["image_url"][len("storage:scans/"):] for r in rows})
        todo = [p for p in paths if not local_path(p).exists()][:MAX_PER_RUN]
        done, failed, size = 0, 0, 0
        with cf.ThreadPoolExecutor(8) as ex:
            for fut in cf.as_completed({ex.submit(fetch, p): p for p in todo}):
                try:
                    size += fut.result()
                    done += 1
                except Exception as e:
                    failed += 1
                    print("failed:", e)
        run.stats = {"public_scans": len(paths), "new": done, "failed": failed, "mb": round(size / 1e6, 1)}
        print(run.stats)


if __name__ == "__main__":
    main()

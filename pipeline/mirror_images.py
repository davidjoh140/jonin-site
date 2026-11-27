"""Copy every public card scan from Supabase Storage into R2 (img.jonin.cards/site/scans/..., audit fix 2026-11-27:
was public/img/scans in the repo, which counted against Cloudflare Pages' 20,000-file limit), so the site serves
images from Cloudflare instead of Supabase. Supabase's free plan only includes 5 GB of
egress a month, and card images are by far the biggest part of a visit.

    python pipeline/mirror_images.py           # download any public scan not mirrored yet

export_cards.py then points each card's "img" at https://img.jonin.cards/site/scans/<path> once it's in R2 (r2_site.json),
and falls back to the Supabase URL when it isn't (yet). Runs in the "Sync card list" workflow before the export.
"""
import concurrent.futures as cf
from pathlib import Path

import requests

import r2
import supa

MAX_PER_RUN = 6000          # first run copies everything (~4,300 files); later runs only new scans


def fetch(path):
    r = requests.get(f"{supa.URL}/storage/v1/object/scans/{path}", headers=supa._h(), timeout=60)
    r.raise_for_status()
    r2.put("site/scans/" + path, r.content, r2.content_type(path))
    return path, len(r.content)


def main():
    with supa.Run("mirror_images") as run:
        m = r2.manifest_copy()
        rows = supa.select("scans", {"select": "image_url", "public": "eq.true", "image_url": "like.storage:scans/*"})
        paths = sorted({r["image_url"][len("storage:scans/"):] for r in rows})
        todo = [p for p in paths if p not in m["scans"]][:MAX_PER_RUN]
        done, failed, size = 0, 0, 0
        if todo and not r2.configured():
            print("R2 not configured; skipping", len(todo), "new scans")
            todo = []
        with cf.ThreadPoolExecutor(8) as ex:
            for fut in cf.as_completed({ex.submit(fetch, p): p for p in todo}):
                try:
                    path, n = fut.result()
                    m["scans"].add(path)
                    size += n
                    done += 1
                except Exception as e:
                    failed += 1
                    print("failed:", e)
        if done:
            r2.save_manifest(m)
        run.stats = {"public_scans": len(paths), "new": done, "failed": failed, "mb": round(size / 1e6, 1)}
        print(run.stats)


if __name__ == "__main__":
    main()

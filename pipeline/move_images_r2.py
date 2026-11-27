"""One-time move of the site's card scans and grid thumbnails from the repo into R2 (audit fix 2026-11-27).

    python pipeline/move_images_r2.py

Uploads public/img/scans/** to site/scans/... and each card's thumbnail to site/t/<name> (thumbnails are renamed to
the stable naming in thumbs.py, so a scan keeps its thumbnail when its URL moves to img.jonin.cards). Skips anything
already in R2, records every successful upload in pipeline/r2_site.json, and can be re-run safely.
Run by the "Move site images to R2" workflow (manual).
"""
import concurrent.futures as cf
import json
from pathlib import Path

import r2
import thumbs

ROOT = Path(__file__).resolve().parent.parent / "public"
SCANS = ROOT / "img" / "scans"
OLD_T = ROOT / "img" / "t"
LOCAL = "https://jonin.cards/img/scans/"


def main():
    m = r2.manifest_copy()
    have = r2.existing("site/")
    m["scans"] |= {k[len("site/scans/"):] for k in have if k.startswith("site/scans/")}
    m["t"] |= {k[len("site/t/"):] for k in have if k.startswith("site/t/")}

    jobs = []
    for f in sorted(SCANS.rglob("*")):
        if f.is_file() and not f.name.endswith(".part"):
            rel = f.relative_to(SCANS).as_posix()
            if rel not in m["scans"]:
                jobs.append(("scans", rel, "site/scans/" + rel, f))
    cards = json.loads((ROOT / "cards.json").read_text())["cards"]
    for c in cards:
        img = c.get("img") or ""
        if not img.startswith(LOCAL):
            continue
        old = OLD_T / (thumbs.key(img) + ".webp")
        new = thumbs.key(img) + ".webp"
        if old.exists() and new not in m["t"]:
            jobs.append(("t", new, "site/t/" + new, old))
    print(f"{len(jobs)} files to upload ({sum(1 for j in jobs if j[0] == 'scans')} scans, "
          f"{sum(1 for j in jobs if j[0] == 't')} thumbnails)", flush=True)

    def up(j):
        kind, name, key, f = j
        r2.put(key, f.read_bytes(), r2.content_type(f.name))
        return kind, name

    done = failed = 0
    with cf.ThreadPoolExecutor(16) as ex:
        for fut in cf.as_completed([ex.submit(up, j) for j in jobs]):
            try:
                kind, name = fut.result()
                m[kind].add(name)
                done += 1
                if done % 500 == 0:
                    print(done, "uploaded", flush=True)
                    r2.save_manifest(m)
            except Exception as e:
                failed += 1
                print("failed:", e, flush=True)
    r2.save_manifest(m)
    print(json.dumps({"uploaded": done, "failed": failed, "scans_in_r2": len(m["scans"]), "thumbs_in_r2": len(m["t"])}))


if __name__ == "__main__":
    main()

"""Small grid images (audit fix 2026-11-27).

Grids (homepage, set, character and list pages) show cards about 165-250px wide but used to download the full
500x700 scan (~50 KB each). This makes a 250x350 copy (~10 KB) of each card's current image and adds it to
cards.json as "th". Card pages keep the full image.

    python pipeline/thumbs.py            # make missing thumbnails, drop unused ones, add "th" to cards.json

Thumbnails are stored in R2 (img.jonin.cards/site/t/, recorded in pipeline/r2_site.json; audit fix 2026-11-27, they
used to be public/img/t in the repo) and named after a hash of the source image, so a new scan gets a new thumbnail
automatically and browsers can keep each file forever. Without R2 credentials (e.g. a local run) it only refreshes
"th" for thumbnails already in R2. export_cards.py also adds "th" for any
card whose thumbnail already exists, so cards.json stays the same between runs.
Runs in the "Sync card list" workflow right after the export.
"""
import concurrent.futures as cf
import hashlib
import io
import json
import sys
from pathlib import Path

import r2

ROOT = Path(__file__).resolve().parent.parent / "public"
CARDS = ROOT / "cards.json"
SITE = "https://jonin.cards/"
SIZE = (250, 350)        # PLACEHOLDER: 250px wide covers the widest grid tile on a 2x phone screen
QUALITY = 78             # PLACEHOLDER: webp quality


SCAN_PREFIXES = ("https://jonin.cards/img/scans/", "https://img.jonin.cards/site/scans/")


def source_id(img_url):
    """Stable id for a card image: a mirrored scan keeps the same id whether it's served from jonin.cards or R2."""
    for p in SCAN_PREFIXES:
        if img_url.startswith(p):
            return "scan:" + img_url[len(p):]
    return img_url


def key(img_url):
    return hashlib.sha1(source_id(img_url).encode("utf-8")).hexdigest()[:16]


def legacy_key(img_url):
    """Thumbnail name before the move to R2 (hash of the full URL)."""
    return hashlib.sha1(img_url.encode("utf-8")).hexdigest()[:16]


def thumb_name(img_url):
    return key(img_url) + ".webp"


def thumb_url(img_url, m=None):
    """The thumbnail URL for a card image, or None if it hasn't been made yet."""
    if not img_url or not img_url.startswith("https://"):
        return None
    n = thumb_name(img_url)
    return r2.thumb_url(n) if n in (m or r2.manifest())["t"] else None


def source_bytes(img_url):
    if img_url.startswith(SITE):
        p = (ROOT / img_url[len(SITE):]).resolve()
        if ROOT.resolve() in p.parents and p.exists():
            return p.read_bytes()
    import requests
    r = requests.get(img_url, timeout=60)
    r.raise_for_status()
    return r.content


def make(img_url):
    from PIL import Image
    im = Image.open(io.BytesIO(source_bytes(img_url))).convert("RGB")
    im = im.resize(SIZE, Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=QUALITY, method=6)
    r2.put("site/t/" + thumb_name(img_url), buf.getvalue(), "image/webp")
    return "made"


def main():
    data = json.loads(CARDS.read_text())
    m = r2.manifest_copy()
    urls = sorted({c["img"] for c in data["cards"] if (c.get("img") or "").startswith("https://")})
    todo = [u for u in urls if thumb_name(u) not in m["t"]]
    made = failed = 0
    if todo and not r2.configured():
        print(f"R2 not configured; {len(todo)} thumbnails not made")
        todo = []
    with cf.ThreadPoolExecutor(8) as ex:
        for u, res in zip(todo, ex.map(lambda u: _safe(make, u), todo)):
            if res == "made":
                m["t"].add(thumb_name(u))
                made += 1
            else:
                failed += 1
    if made:
        r2.save_manifest(m)
    # Add/refresh "th" in cards.json, written exactly the way export_cards.py writes it.
    changed = 0
    for c in data["cards"]:
        t = thumb_url(c.get("img") or "", m)
        if t and c.get("th") != t:
            c["th"] = t
            changed += 1
        elif not t and "th" in c:
            del c["th"]
            changed += 1
    if changed:
        CARDS.write_text(json.dumps(data, ensure_ascii=True, separators=(",", ":")))
    print(json.dumps({"images": len(urls), "made": made, "failed": failed, "cards_json_changed": changed}))


def _safe(fn, u):
    try:
        return fn(u)
    except Exception as e:  # one bad image shouldn't stop the run; it falls back to the full image
        print("thumb failed", u, e, file=sys.stderr)
        return None


if __name__ == "__main__":
    main()

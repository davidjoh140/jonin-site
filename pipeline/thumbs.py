"""Small grid images (audit fix 2026-11-27).

Grids (homepage, set, character and list pages) show cards about 165-250px wide but used to download the full
500x700 scan (~50 KB each). This makes a 250x350 copy (~10 KB) of each card's current image and adds it to
cards.json as "th". Card pages keep the full image.

    python pipeline/thumbs.py            # make missing thumbnails, drop unused ones, add "th" to cards.json

Thumbnails are named after a hash of the source image URL, so a new scan (on jonin.cards or img.jonin.cards in R2)
gets a new thumbnail automatically and browsers can keep each file forever. export_cards.py also adds "th" for any
card whose thumbnail already exists, so cards.json stays the same between runs.
Runs in the "Sync card list" workflow right after the export.
"""
import concurrent.futures as cf
import hashlib
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "public"
DIR = ROOT / "img" / "t"
CARDS = ROOT / "cards.json"
SITE = "https://jonin.cards/"
SIZE = (250, 350)        # PLACEHOLDER: 250px wide covers the widest grid tile on a 2x phone screen
QUALITY = 78             # PLACEHOLDER: webp quality


def key(img_url):
    return hashlib.sha1(img_url.encode("utf-8")).hexdigest()[:16]


def thumb_path(img_url):
    return DIR / (key(img_url) + ".webp")


def thumb_url(img_url):
    """The thumbnail URL for a card image, or None if it hasn't been made yet."""
    if not img_url or not img_url.startswith("https://"):
        return None
    return SITE + "img/t/" + key(img_url) + ".webp" if thumb_path(img_url).exists() else None


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
    dest = thumb_path(img_url)
    if dest.exists():
        return "kept"
    im = Image.open(io.BytesIO(source_bytes(img_url))).convert("RGB")
    im = im.resize(SIZE, Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=QUALITY, method=6)
    dest.write_bytes(buf.getvalue())
    return "made"


def main():
    DIR.mkdir(parents=True, exist_ok=True)
    text = CARDS.read_text()
    data = json.loads(text)
    urls = sorted({c["img"] for c in data["cards"] if (c.get("img") or "").startswith("https://")})
    made = failed = 0
    with cf.ThreadPoolExecutor(8) as ex:
        for u, res in zip(urls, ex.map(lambda u: _safe(make, u), urls)):
            if res == "made":
                made += 1
            elif res is None:
                failed += 1
    # Drop thumbnails no card uses any more.
    keep = {thumb_path(u).name for u in urls}
    removed = 0
    for f in DIR.glob("*.webp"):
        if f.name not in keep:
            f.unlink()
            removed += 1
    # Add/refresh "th" in cards.json, written exactly the way export_cards.py writes it.
    changed = 0
    for c in data["cards"]:
        t = thumb_url(c.get("img") or "")
        if t and c.get("th") != t:
            c["th"] = t
            changed += 1
        elif not t and "th" in c:
            del c["th"]
            changed += 1
    if changed:
        CARDS.write_text(json.dumps(data, ensure_ascii=True, separators=(",", ":")))
    print(json.dumps({"images": len(urls), "made": made, "failed": failed, "removed": removed, "cards_json_changed": changed}))


def _safe(fn, u):
    try:
        return fn(u)
    except Exception as e:  # one bad image shouldn't stop the run; it falls back to the full image
        print("thumb failed", u, e, file=sys.stderr)
        return None


if __name__ == "__main__":
    main()

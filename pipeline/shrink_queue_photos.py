"""Re-save sold-listing photos waiting to be cut (sale_scan_queue) at a smaller file size (audit fix 2026-11-27).

The Hub can't load images from other sites, so these photos are stored in the database as base64 while they wait.
eBay's full-size JPEGs average ~430 KB; re-saving at JPEG quality 82 (same pixel size, max 1600px) makes them
~40% smaller with no visible difference at cutting size (the cut scan is 750x1050).

    python pipeline/shrink_queue_photos.py      # up to 40 photos per run

Runs in the "Sync card list" workflow. Each photo is done once (photo_small = true); a re-fetched photo resets it.
"""
import base64
import io

from PIL import Image

import supa

MAX_SIDE = 1600    # PLACEHOLDER
QUALITY = 82       # PLACEHOLDER
PER_RUN = 40


def shrink(b64):
    raw = base64.b64decode(b64)
    im = Image.open(io.BytesIO(raw))
    im = im.convert("RGB")
    im.thumbnail((MAX_SIDE, MAX_SIDE))
    out = io.BytesIO()
    im.save(out, "JPEG", quality=QUALITY, optimize=True, progressive=True)
    new = out.getvalue()
    return base64.b64encode(new).decode() if len(new) < len(raw) else b64, len(raw), len(new)


def main():
    rows = supa.select("sale_scan_queue", {"select": "sale_id,photo_b64", "status": "eq.fetched",
                                            "photo_small": "eq.false", "photo_b64": "not.is.null",
                                            "limit": str(PER_RUN)})
    before = after = 0
    for r in rows:
        try:
            b64, a, b = shrink(r["photo_b64"])
        except Exception as e:
            print("skip", r["sale_id"], e)
            b64, a, b = r["photo_b64"], 0, 0
        supa.update("sale_scan_queue", {"sale_id": r["sale_id"], "status": "fetched"},
                    {"photo_b64": b64, "photo_small": True})
        before += a
        after += min(a, b) if b else a
    print(f"shrank {len(rows)} photos: {before // 1024} KB -> {after // 1024} KB")


if __name__ == "__main__":
    main()

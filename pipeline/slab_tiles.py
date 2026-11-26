"""Uniform slab photos for the most-valuable lists (David, 2026-11-26: "cropped and flattened nicely,
uniform and clean"). Every sold-slab photo in public/img/sales is turned, once, into a straight-on tile:
  1. find the whole slab (edge maps + background-removal mask; largest quad with a slab's shape),
  2. warp it flat to a fixed slab shape, centred on one dark canvas (same size for every photo),
  3. blur the cert number (and the PSA barcode, which encodes it).
The eBay original is kept in pipeline/sale_photos_raw/. Results go to pipeline/slab_tiles.json:
  ok      tile made, cert found and blurred
  check   tile made, but we couldn't place the cert for sure: David looks first. Until he sets it to "ok"
          the lists show the card scan (PLACEHOLDER rule, 2026-11-26)
  noslab  no clean slab crop: the lists show the card scan instead of this photo (build_pages.sale_photo)
Usage: python slab_tiles.py            process new slab photos
       python slab_tiles.py --pending  print how many are waiting (the workflow skips heavy installs at 0)
       python slab_tiles.py --redo X   reprocess one file name from its original"""
import json, re, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SALES = ROOT.parent / "public" / "img" / "sales"
RAW = ROOT / "sale_photos_raw"
MANIFEST = ROOT / "slab_tiles.json"

# PLACEHOLDERS for David (2026-11-26): tile size/shape and background.
CANVAS_W, CANVAS_H = 600, 1000          # matches the 3:5 frame the pages already use
SLAB_W, SLAB_H = 560, 952               # PSA/BGS/CGC slabs are ~3.1 x 5.3 in (0.59)
BG = (20, 17, 17)                       # BGR, near-black like the list background (#0b0b0d-ish)
SLAB_RATIO = (0.54, 0.66)               # width/height range accepted as "a slab"
SLAB_FILE = re.compile(r"-(psa|bgs|cgc|sgc|tag)-[0-9-]+\.jpg$")


def load():
    return json.loads(MANIFEST.read_text()) if MANIFEST.is_file() else {}


def pending(man):
    return sorted(p.name for p in SALES.glob("*.jpg") if SLAB_FILE.search(p.name) and p.name not in man)


# ------------------------------------------------------------------ geometry
def _order(p):
    import numpy as np
    s = p.sum(1); d = np.diff(p, axis=1).ravel()
    return np.array([p[s.argmin()], p[d.argmin()], p[s.argmax()], p[d.argmax()]], np.float32)


def _dims(q):
    import numpy as np
    tl, tr, br, bl = q
    return (np.linalg.norm(tr - tl) + np.linalg.norm(br - bl)) / 2, (np.linalg.norm(bl - tl) + np.linalg.norm(br - tr)) / 2


def _quads(binary):
    import cv2
    out = []
    cnts, _ = cv2.findContours(binary, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    for c in cnts:
        if cv2.contourArea(c) < 500:
            continue
        hull = cv2.convexHull(c); peri = cv2.arcLength(hull, True)
        for eps in (0.02, 0.03, 0.04, 0.06):
            ap = cv2.approxPolyDP(hull, eps * peri, True)
            if len(ap) == 4:
                out.append((_order(ap.reshape(4, 2).astype("float32")), cv2.contourArea(c) / max(cv2.contourArea(ap), 1)))
                break
    return out


_SESSION = None


def _edge_candidates(img):
    import cv2, numpy as np
    g = cv2.GaussianBlur(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), (5, 5), 0)
    for lo, hi in ((20, 60), (40, 120), (80, 200)):
        e = cv2.dilate(cv2.Canny(g, lo, hi), np.ones((5, 5), np.uint8))
        e = cv2.morphologyEx(e, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
        for q, f in _quads(e):
            yield q, f, f"edge{lo}"


def _mask_candidates(path):
    import cv2, numpy as np
    from PIL import Image
    global _SESSION
    from rembg import remove, new_session
    _SESSION = _SESSION or new_session("isnet-general-use")
    a = np.array(remove(Image.open(path).convert("RGB"), session=_SESSION))[:, :, 3]
    for cut in (8, 40, 128):
        m = cv2.morphologyEx(((a > cut) * 255).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((21, 21), np.uint8))
        for q, f in _quads(m):
            yield q, f, f"mask{cut}"


def _warp(img, q):
    import cv2, numpy as np
    M = cv2.getPerspectiveTransform(q, np.array([[0, 0], [SLAB_W, 0], [SLAB_W, SLAB_H], [0, SLAB_H]], np.float32))
    return cv2.warpPerspective(img, M, (SLAB_W, SLAB_H), flags=cv2.INTER_CUBIC)


def has_label(slab):
    """A real slab crop has the grader's label across the top: a wide, short rectangle in the top fifth
    (PSA's red frame, Beckett/CGC's label). Crops of just the card, or of the wrong thing, don't."""
    import cv2, numpy as np
    H, W = slab.shape[:2]
    top = slab[: int(H * 0.30)]
    if _psa_label(top, W):
        return True
    g = cv2.GaussianBlur(cv2.cvtColor(top, cv2.COLOR_BGR2GRAY), (3, 3), 0)
    for lo, hi in ((30, 90), (60, 160)):
        e = cv2.morphologyEx(cv2.Canny(g, lo, hi), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
        cnts, _ = cv2.findContours(e, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        for c in cnts:
            x, y, w, h = cv2.boundingRect(c)
            if w > 0.60 * W and 0.07 * H < h < 0.22 * H and y < 0.16 * H and cv2.contourArea(c) > 0.5 * w * h:
                return True
    return False


def flatten(path):
    """(tile or None, note). Tries the largest slab-shaped outlines first and keeps the first one whose
    flattened crop shows a label on top; edge outlines first, background-removal outlines only if needed."""
    import cv2, numpy as np
    img = cv2.imread(str(path)); h, w = img.shape[:2]

    def pick(cands):
        ok = []
        for q, fill, src in cands:
            qw, qh = _dims(q)
            if qw > qh:
                q = np.array([q[3], q[0], q[1], q[2]], np.float32); qw, qh = qh, qw
            r = qw / qh; area = cv2.contourArea(q) / (w * h)
            if SLAB_RATIO[0] <= r <= SLAB_RATIO[1] and 0.10 <= area <= 0.985 and fill >= 0.85:
                ok.append((area, r, src, q))
        for area, r, src, q in sorted(ok, key=lambda t: -t[0]):
            slab = _warp(img, q)
            if has_label(slab):
                return slab, f"{src} ratio {r:.2f} area {area:.2f}"
        return None, None

    slab, note = pick(_edge_candidates(img))
    if slab is None:   # photo already cropped tight to the slab: use the whole frame
        r = w / h
        whole = np.array([[0, 0], [w, 0], [w, h], [0, h]], np.float32)
        if SLAB_RATIO[0] <= r <= SLAB_RATIO[1] and has_label(_warp(img, whole)):
            slab, note = _warp(img, whole), f"whole photo ratio {r:.2f}"
    if slab is None:
        slab, note = pick(_mask_candidates(path))
    if slab is None:
        return None, "no clean slab crop (no label found on top)"
    canvas = np.full((CANVAS_H, CANVAS_W, 3), BG, np.uint8)
    ox, oy = (CANVAS_W - SLAB_W) // 2, (CANVAS_H - SLAB_H) // 2
    canvas[oy:oy + SLAB_H, ox:ox + SLAB_W] = slab
    return canvas, note


# ------------------------------------------------------------------ cert blur
def _blur(img, x, y, w, h):
    import cv2
    x, y = max(int(x), 0), max(int(y), 0)
    roi = img[y:y + int(h), x:x + int(w)]
    if roi.size:
        img[y:y + int(h), x:x + int(w)] = cv2.GaussianBlur(roi, (0, 0), 9)


def _psa_label(top, W=None):
    import cv2
    hsv = cv2.cvtColor(top, cv2.COLOR_BGR2HSV)
    red = cv2.inRange(hsv, (0, 90, 90), (10, 255, 255)) | cv2.inRange(hsv, (170, 90, 90), (180, 255, 255))
    cnts, _ = cv2.findContours(red, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return None
    x, y, w, h = cv2.boundingRect(max(cnts, key=cv2.contourArea))
    W = W or top.shape[1]
    return (x, y, w, h) if w > 0.58 * W and h > 0.09 * W else None


def blur_cert(tile):
    """Blur the cert number (any 7+ digit run on the label) and the PSA barcode. True if we know where the cert
    was: read off the label, or the red PSA label was found (its cert line is always in the same place; most
    sale photos arrive with the cert already blurred, so there is often nothing left to read)."""
    import cv2, pytesseract
    top = tile[:300]
    label = _psa_label(top)
    hits = []
    big = cv2.resize(top, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(big, cv2.COLOR_BGR2GRAY)
    for im in (big, cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]):
        d = pytesseract.image_to_data(im, output_type=pytesseract.Output.DICT, config="--psm 11")
        hits = [(d["left"][k] // 3, d["top"][k] // 3, d["width"][k] // 3, d["height"][k] // 3)
                for k, t in enumerate(d["text"]) if sum(ch.isdigit() for ch in t) >= 7]
        if hits:
            break
    if not hits:
        if label:   # cert is the bottom-right line of the red PSA label, barcode bottom-left
            x, y, w, h = label
            _blur(tile, x + w * 0.62, y + h * 0.75, w * 0.36, h * 0.2)
            _blur(tile, x + w * 0.04, y + h * 0.75, w * 0.36, h * 0.2)
            return True
        _blur(tile, 370, 130, 190, 80)
        return False
    for x, y, w, h in hits:
        _blur(tile, x - 8, y - 6, w + 16, h + 12)
        if label:
            lx, ly, lw, lh = label
            _blur(tile, lx + lw * 0.03, y - 8, lw * 0.38, h + 22)
    return True


# ------------------------------------------------------------------ run
def process(name, man):
    import cv2
    src = SALES / name
    raw = RAW / name
    if not raw.is_file():
        RAW.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, raw)
    tile, note = flatten(raw)
    if tile is None:
        man[name] = {"status": "noslab", "note": note}
        return
    read = blur_cert(tile)
    cv2.imwrite(str(src), tile, [cv2.IMWRITE_JPEG_QUALITY, 88, cv2.IMWRITE_JPEG_PROGRESSIVE, 1])
    man[name] = {"status": "ok" if read else "check", "note": note + ("" if read else "; cert not found on a non-PSA label, default spot blurred")}


def main(argv):
    man = load()
    if "--pending" in argv:
        print(len(pending(man))); return 0
    names = [argv[argv.index("--redo") + 1]] if "--redo" in argv else pending(man)
    for n in names:
        try:
            process(n, man)
        except Exception as err:   # one bad photo must not stop the sync
            man[n] = {"status": "noslab", "note": f"error: {err}"}
        print(n, man[n]["status"], man[n]["note"])
    MANIFEST.write_text(json.dumps(man, indent=1, sort_keys=True) + "\n")
    print(f"{len(names)} slab photos processed; {sum(v['status'] == 'check' for v in man.values())} to check, "
          f"{sum(v['status'] == 'noslab' for v in man.values())} showing the card scan")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

"""Cleans a sealed-product photo for the site.

David 2026-11-27: keep it simple. If an item can't be cut and angled smoothly, leave it the best it can be without
doing too much.

clean(img) / split(img, n) -> RGBA images, one per item:
  1. rembg finds the item(s).
  2. Each item is straightened (only a small tilt, up to MAX_TILT degrees).
  3. Its outline becomes a simple straight-edged polygon (packs, blisters, boxes and decks are flat-sided), so there
     are no jagged edges, bites or slivers of the item next to it.
  4. If the cut-out doesn't look like a clean flat-sided item, the photo is just cropped around the item instead,
     background kept.
Two items side by side are separated at the gap between them (the emptiest column), never by guessing at artwork.
Needs: pip install "rembg[cpu]" opencv-python-headless
"""
import io

import cv2
import numpy as np
from PIL import Image, ImageOps

MAX_TILT = 12          # PLACEHOLDER: degrees of tilt we straighten; more than that is left as photographed
MIN_FILL = 0.88        # PLACEHOLDER: cut-out must fill this much of its outline, or we fall back to a plain crop
_SESSIONS = {}


def _raw_mask(img, model):
    from rembg import new_session, remove
    if model not in _SESSIONS:
        _SESSIONS[model] = new_session(model)
    a = np.array(remove(img, session=_SESSIONS[model], only_mask=True, post_process_mask=True))
    return (a > 128).astype(np.uint8) * 255


def _edges_touched(m, pad=3):
    return sum(bool(x.any()) for x in (m[:pad], m[-pad:], m[:, :pad], m[:, -pad:]))


def _mask(img):
    m = _raw_mask(img, "isnet-general-use")
    if _edges_touched(m) >= 3:
        alt = _raw_mask(img, "u2net")
        if _edges_touched(alt) < _edges_touched(m):
            m = alt
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (21, 21)))
    return cv2.morphologyEx(m, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))


def _trim_stand(m):
    """Drop a display stand or hand under the item: bottom rows much narrower than the item."""
    w = (m > 0).sum(1)
    rows = np.nonzero(w)[0]
    if len(rows) < 20:
        return m
    body = np.median(w[rows])
    last = rows[-1]
    while last > rows[0] and w[last] < 0.75 * body:
        last -= 1
    if rows[-1] - last > 4:
        m = m.copy()
        m[last + 1:] = 0
    return m


def _largest(m):
    n, lab, st, _ = cv2.connectedComponentsWithStats((m > 0).astype(np.uint8))
    if n <= 1:
        return m
    k = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    return ((lab == k) * 255).astype(np.uint8)


def _item_masks(m, n):
    """n item masks, left to right, separated at the emptiest columns."""
    if n == 1:
        return [_largest(m)]
    cols = (m > 0).sum(0).astype(float)
    xs = np.nonzero(cols)[0]
    l, r = xs[0], xs[-1]
    cuts = []
    for k in range(1, n):
        c, w = l + (r - l) * k // n, (r - l) // (4 * n)
        win = np.convolve(cols[c - w:c + w], np.ones(5) / 5, "same")
        cuts.append(c - w + int(np.argmin(win)))
    edges, out = [0] + cuts + [m.shape[1]], []
    for i in range(n):
        a = np.zeros_like(m)
        a[:, edges[i]:edges[i + 1]] = m[:, edges[i]:edges[i + 1]]
        out.append(_largest(a))
    return out


def _cut(rgb, m, size, crop=False, tight_x=False):
    m = _trim_stand(m)
    cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    c = max(cs, key=cv2.contourArea)
    (cx, cy), (rw, rh), ang = cv2.minAreaRect(c)
    if ang > 45:
        ang -= 90
    # straighten a small tilt; leave bigger ones as photographed
    if 0.5 < abs(ang) <= MAX_TILT:
        H, W = m.shape
        R = cv2.getRotationMatrix2D((cx, cy), ang, 1.0)
        rgb = cv2.warpAffine(rgb, R, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        m = cv2.warpAffine(m, R, (W, H), flags=cv2.INTER_NEAREST)
        cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        c = max(cs, key=cv2.contourArea)
    hull = cv2.convexHull(c)
    poly = cv2.approxPolyDP(hull, 0.008 * cv2.arcLength(hull, True), True)
    x, y, w, h = cv2.boundingRect(poly)
    fill = cv2.contourArea(c) / max(cv2.contourArea(poly), 1)
    img = Image.fromarray(rgb)
    plain = crop or fill < MIN_FILL or len(poly) > 12
    if plain:
        # not a clean flat-sided cut-out: plain crop around the item, background kept
        p = int(0.03 * max(w, h))
        px = 0 if tight_x else p                     # two items side by side: don't take in the neighbor
        out = img.crop((max(x - px, 0), max(y - p, 0), min(x + w + px, img.width), min(y + h + p, img.height)))
        out = ImageOps.autocontrast(out, cutoff=0.3).convert("RGBA")
    else:
        # anti-aliased straight-edged outline, drawn at 4x and scaled down
        S = 4
        big = np.zeros((h * S, w * S), np.uint8)
        cv2.fillPoly(big, [((poly.reshape(-1, 2) - [x, y]) * S).astype(np.int32)], 255, lineType=cv2.LINE_AA)
        alpha = Image.fromarray(big).resize((w, h), Image.LANCZOS)
        out = ImageOps.autocontrast(img.crop((x, y, x + w, y + h)), cutoff=0.3).convert("RGBA")
        out.putalpha(alpha)
    out.thumbnail((size, size), Image.LANCZOS)
    return out, ("crop" if plain else "cut")


def split(img, n, size=1200, info=False, crop=False):
    """n items side by side -> n cleaned images, left to right. crop=True: plain crop, no cut-out (for photos that
    can't be cut cleanly, like boxes shot at an angle)."""
    img = img.convert("RGB")
    rgb, m = np.array(img), _mask(img)
    res = [_cut(rgb, a, size, crop, n > 1) for a in _item_masks(m, n)]
    return res if info else [r[0] for r in res]


def clean(img, size=1200, crop=False):
    return split(img, 1, size, crop=crop)[0]


def webp(rgba, quality=88):
    buf = io.BytesIO()
    rgba.save(buf, "WEBP", quality=quality, method=6)
    return buf.getvalue()

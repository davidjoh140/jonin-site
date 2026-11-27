"""Cleans a sealed-product photo for the site (David 2026-11-27: cut out and clean every sealed photo).

clean(PIL image) -> RGBA image on a transparent background:
  1. rembg (isnet-general-use) finds the item.
  2. Every hole inside the item's outer edge is filled: pack art often has white areas that look like background.
  3. The item is filled to its outer outline (packs, boxes and decks have no inward corners), which keeps edges that
     blend into a white background, like silver crimps.
  4. Cropped to the item, mild auto-contrast and sharpen, max 1200px.
Several items in one photo (e.g. both pack arts side by side) are split by hand, not here: split(img, n) is there for
that, cutting at the strongest vertical edge between them, left to right.
Needs: pip install "rembg[cpu]" opencv-python-headless (installed by the Sync workflow only when a photo is waiting).
"""
import numpy as np
import cv2
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

_SESSION = None


def _mask(img):
    global _SESSION
    from rembg import new_session, remove
    _SESSION = _SESSION or new_session("isnet-general-use")
    a = np.array(remove(img, session=_SESSION, only_mask=True, post_process_mask=True))
    m = (a > 128).astype(np.uint8) * 255
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25)))
    cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    filled = np.zeros_like(m)
    cv2.drawContours(filled, [c for c in cs if cv2.contourArea(c) > 0.02 * m.size], -1, 255, thickness=cv2.FILLED)
    return cv2.morphologyEx(filled, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))


def _hull(alpha):
    cs, _ = cv2.findContours((alpha > 128).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not cs:
        return alpha
    h = np.zeros_like(alpha)
    cv2.fillPoly(h, [cv2.convexHull(max(cs, key=cv2.contourArea))], 255)
    return cv2.GaussianBlur(h, (3, 3), 0)


def _finish(rgb, alpha, size=1200):
    im = ImageOps.autocontrast(Image.fromarray(rgb), cutoff=0.5)
    im = ImageEnhance.Color(im).enhance(1.05).filter(ImageFilter.UnsharpMask(radius=1.6, percent=60, threshold=3))
    out = im.convert("RGBA")
    out.putalpha(Image.fromarray(_hull(alpha)))
    out = out.crop(out.getbbox())
    out.thumbnail((size, size), Image.LANCZOS)
    return out


def clean(img):
    img = img.convert("RGB")
    return _finish(np.array(img), _mask(img))


def split(img, n):
    """n items side by side -> n cleaned images, left to right."""
    img = img.convert("RGB")
    rgb, alpha = np.array(img), _mask(img)
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(float)
    score = (np.abs(cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)) * (alpha > 128)).sum(0)
    l, r = np.nonzero((alpha > 128).sum(0))[0][[0, -1]]
    xs = []
    for k in range(1, n):
        c, w = l + (r - l) * k // n, (r - l) // (5 * n)
        xs.append(c - w + int(np.argmax(np.convolve(score[c - w:c + w], np.ones(3) / 3, "same"))))
    edges, out = [0] + xs + [rgb.shape[1]], []
    for i in range(n):
        a = alpha.copy()
        a[:, :edges[i]] = 0
        a[:, edges[i + 1]:] = 0
        out.append(_finish(rgb, a))
    return out


def webp(rgba, quality=88):
    import io
    buf = io.BytesIO()
    rgba.save(buf, "WEBP", quality=quality, method=6)
    return buf.getvalue()

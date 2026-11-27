"""Hybrid enhance: AI upscale for art and big titles, plain sharpened resize where there's small text.

text_mask() finds lines of small text on the original 350x490 scan (morphological gradient -> threshold ->
join letters into lines -> keep line-shaped boxes whose height is small-text sized), then the mask is
scaled up and feathered. Final = AI * (1 - mask) + sharpened * mask.
"""
import cv2
import numpy as np
from PIL import Image, ImageFilter

OUT = (750, 1050)
# PLACEHOLDER tuning (at the original 350x490 scale): text this tall or shorter counts as "small text"
MIN_H, MAX_H = 3, 13
PAD = 2          # px around each text box (original scale)
FEATHER = 6      # blur radius of the mask edge (output scale)
ZONE_TOP = 0.58  # PLACEHOLDER: where the card's text area starts (fraction of height)


def text_mask(src_rgb):
    g = cv2.cvtColor(src_rgb, cv2.COLOR_RGB2GRAY)
    H, W = g.shape
    grad = cv2.morphologyEx(g, cv2.MORPH_GRADIENT, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
    bw = cv2.adaptiveThreshold(grad, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 15, -12)
    m = np.zeros(g.shape, np.uint8)
    # 1) lines of small text anywhere (letters joined into lines)
    lines = cv2.morphologyEx(bw, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (9, 1)))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(lines, 8)
    for i in range(1, n):
        x, y, w, h, area = stats[i]
        if MIN_H <= h <= MAX_H and w >= 3 * h and w >= 14 and area / float(w * h) > 0.25:
            cv2.rectangle(m, (max(0, x - PAD), max(0, y - PAD)), (x + w + PAD, y + h + PAD), 255, -1)
    # 2) text zone (flavor line down to the bottom edge): faithful by default; only big shapes
    #    (card name, cost circles, stat numbers) go back to the AI art version
    top = int(H * ZONE_TOP)
    m[top:, :] = 255
    n, lab, stats, _ = cv2.connectedComponentsWithStats(bw[top:], 8)
    for i in range(1, n):
        x, y, w, h, area = stats[i]
        if MAX_H < h <= int(H * 0.12) and w <= int(W * 0.9):
            cv2.rectangle(m, (max(0, x - 1), top + max(0, y - 1)), (x + w + 1, top + y + h + 1), 0, -1)
    # small text that sits inside a big shape's box still needs to stay faithful
    n2, lab2, stats2, _ = cv2.connectedComponentsWithStats(lines[top:], 8)
    for i in range(1, n2):
        x, y, w, h, area = stats2[i]
        if MIN_H <= h <= MAX_H and w >= 3 * h:
            cv2.rectangle(m, (max(0, x - PAD), top + max(0, y - PAD)), (x + w + PAD, top + y + h + PAD), 255, -1)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (7, 3)))
    m = cv2.resize(m, OUT, interpolation=cv2.INTER_LINEAR)
    m = cv2.GaussianBlur(m, (0, 0), FEATHER)
    return m.astype(np.float32) / 255.0


def sharpened(src_img):
    return src_img.convert("RGB").resize(OUT, Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=1.6, percent=120, threshold=2))


def blend(src_img, ai_img):
    src = np.asarray(src_img.convert("RGB"))
    m = text_mask(src)[..., None]
    a = np.asarray(ai_img.convert("RGB").resize(OUT, Image.LANCZOS), np.float32)
    b = np.asarray(sharpened(src_img), np.float32)
    out = a * (1 - m) + b * m
    return Image.fromarray(np.clip(out + 0.5, 0, 255).astype(np.uint8)), m


def overlay(img, m):
    a = np.asarray(img, np.float32)
    tint = np.array([255, 60, 140], np.float32)
    o = a * (1 - 0.45 * m[..., None]) + tint * 0.45 * m[..., None]
    return Image.fromarray(o.astype(np.uint8))

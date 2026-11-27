"""Enhance one original 350x490 card scan into a 1400x1960 master.

Art, card name and big numbers: Real-ESRGAN x4plus_anime_6B (crisp, stylized).
Small text: RealESRNet_x4plus (faithful, keeps letters correct), chosen by hybrid.text_mask().
No extra sharpening, so letters stay clean and full.
"""
import os, sys, time
import numpy as np
import cv2
import torch
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import esr
import hybrid

MASTER = (1400, 1960)


def load_models(d):
    anime = esr.load(os.path.join(d, "anime6b.pth"))
    net = esr.RRDBNet(nb=23)
    sd = torch.load(os.path.join(d, "esrnet.pth"), map_location="cpu", weights_only=True)
    net.load_state_dict(sd.get("params_ema", sd.get("params", sd)))
    net.eval()
    return anime, net


def enhance(src, anime, net):
    src = src.convert("RGB")
    if src.size != (350, 490):
        src = src.resize((350, 490), Image.LANCZOS)
    a = np.asarray(esr.upscale(anime, src).resize(MASTER, Image.LANCZOS), np.float32)
    b = np.asarray(esr.upscale(net, src).resize(MASTER, Image.LANCZOS), np.float32)
    hybrid.OUT = MASTER
    hybrid.FEATHER = 10
    m = hybrid.text_mask(np.asarray(src))[..., None]
    out = a * (1 - m) + b * m
    return Image.fromarray(np.clip(out + 0.5, 0, 255).astype(np.uint8))


if __name__ == "__main__":
    d = os.path.dirname(os.path.abspath(__file__))
    anime, net = load_models(d)
    outdir = sys.argv[1]
    os.makedirs(outdir, exist_ok=True)
    for p in sys.argv[2:]:
        t = time.time()
        img = enhance(Image.open(p), anime, net)
        name = os.path.basename(os.path.dirname(p)).split(" - ")[0].replace(" ", "") + "_" + os.path.splitext(os.path.basename(p))[0]
        img.save(os.path.join(outdir, name + ".webp"), "WEBP", quality=90, method=5)
        print(name, round(time.time() - t, 1), "s", flush=True)

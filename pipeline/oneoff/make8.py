import sys
from PIL import Image, ImageOps
# make8.py src out x6a x6b ytop ymid ybot looptop dx  (all in the image's own pixels)
src, out = sys.argv[1], sys.argv[2]
x6a, x6b, ytop, ymid, ybot, looptop, dx = map(int, sys.argv[3:10])
im = Image.open(src).convert("RGB")
w = x6b - x6a
glyph = im.crop((x6a, ytop, x6b, ybot))                      # the 6 with its background
loop = im.crop((x6a, looptop, x6b, ybot))                     # closed bottom loop of the 6
top = ImageOps.flip(loop).resize((w, ymid - ytop), Image.LANCZOS)
glyph.paste(top, (0, 0))
glyph.paste(loop.resize((w, ybot - ymid), Image.LANCZOS), (0, ymid - ytop))
im.paste(glyph, (x6a + dx, ytop))
im.save(out, "WEBP", quality=95)

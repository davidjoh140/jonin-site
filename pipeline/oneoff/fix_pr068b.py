"""One-off (2026-11-27): the Hebi Sasuke promo is really PR068 (shares the number with Killer Bee), filed as P:PR068B.
Its scans showed "PR 067". Uploads the corrected Card Index scan to Storage and writes a corrected enhanced master
(masters/P/PR068B.webp) built from masters/P/PR067.webp, with the 7 rebuilt as an 8 from the card's own 6."""
import hashlib, io, os, subprocess, sys
import boto3
from PIL import Image
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import supa  # noqa: E402

here = os.path.dirname(os.path.abspath(__file__))
os.makedirs("out", exist_ok=True)
ci = open(os.path.join(here, "pr068b_ci.webp"), "rb").read()
path = f"ci/p/pr068b_promo--{hashlib.sha256(ci).hexdigest()[:8]}.webp"
supa.upload("scans", path, ci, "image/webp")
print("storage", path)

s3 = boto3.client("s3", endpoint_url=os.environ["R2_ENDPOINT"], region_name="auto",
                  aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"], aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"])
B = os.environ.get("R2_BUCKET", "jonin-scans")
open("out/m067.webp", "wb").write(s3.get_object(Bucket=B, Key="masters/P/PR067.webp")["Body"].read())
open("out/m068.webp", "wb").write(s3.get_object(Bucket=B, Key="masters/P/PR068.webp")["Body"].read())
im = Image.open("out/m067.webp"); W, H = im.size; k = W / 750
print("master size", W, H)
c = [round(v * k) for v in (93, 103, 1030, 1036, 1043, 1034, 9)]
subprocess.run([sys.executable, os.path.join(here, "make8.py"), "out/m067.webp", "out/m068b.webp", *map(str, c)], check=True)
fixed = open("out/m068b.webp", "rb").read()
if os.environ.get("WRITE_MASTER") == "1":
    s3.put_object(Bucket=B, Key="masters/P/PR068B.webp", Body=fixed, ContentType="image/webp")
    print("wrote masters/P/PR068B.webp")
    import base64
    th = io.BytesIO(); Image.open(io.BytesIO(fixed)).convert("RGB").resize((200, 280), Image.LANCZOS).save(th, "WEBP", quality=80)
    supa.update("enhanced_scans", {"card_id": "P:PR068B"}, {"r2_key": "masters/P/PR068B.webp",
                "thumb_b64": base64.b64encode(th.getvalue()).decode()})
    print("enhanced row updated")
for n in ("m067", "m068b", "m068"):
    x = Image.open(f"out/{n}.webp").convert("RGB")
    x.crop((0, int(H * 0.95), int(W * 0.4), H)).save(f"out/{n}_strip.png")

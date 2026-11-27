"""Publish enhanced scans David approved in the Buying Desk.

For each enhanced_scans row with status 'approved' and no published_at:
  - read the 1400x1960 master from R2 (masters/...), save a 500x700 site version (web/...)
  - add a public `scans` row (quality 'clean', printing 'Normal', source 'enhanced') pointing at the
    site version on img.jonin.cards, so it becomes the card's image (newest clean scan wins)
  - stamp published_at / scan_id
A skipped row that was published earlier is taken down again (its scans row is made non-public).

Env: SUPABASE_URL, SUPABASE_SERVICE_KEY, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_ENDPOINT, R2_BUCKET.
"""
import io, os, sys
from datetime import datetime, timezone
import boto3
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import supa  # noqa: E402

PUBLIC = "https://img.jonin.cards/"
WEB = (500, 700)


def main():
    s3 = boto3.client("s3", endpoint_url=os.environ["R2_ENDPOINT"], region_name="auto",
                      aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
                      aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"])
    bucket = os.environ.get("R2_BUCKET", "jonin-scans")
    now = datetime.now(timezone.utc).isoformat()

    rows = supa.select("enhanced_scans", {"select": "src_path,card_id,r2_key", "status": "eq.approved",
                                           "published_at": "is.null", "order": "src_path"})
    print(f"{len(rows)} approved scans to publish", flush=True)
    ok = 0
    for r in rows:
        try:
            body = s3.get_object(Bucket=bucket, Key=r["r2_key"])["Body"].read()
            img = Image.open(io.BytesIO(body)).convert("RGB").resize(WEB, Image.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, "WEBP", quality=86, method=5)
            web_key = "web/" + r["r2_key"].split("/", 1)[1]
            s3.put_object(Bucket=bucket, Key=web_key, Body=buf.getvalue(), ContentType="image/webp",
                          CacheControl="public, max-age=31536000")
            ins = supa.insert("scans", [{"card_id": r["card_id"], "printing": "Normal", "image_url": PUBLIC + web_key,
                                         "source": "enhanced", "credit": "master:" + PUBLIC + r["r2_key"],
                                         "public": True, "quality": "clean"}])
            supa.update("enhanced_scans", {"src_path": r["src_path"]},
                        {"published_at": now, "scan_id": ins[0]["id"] if ins else None})
            ok += 1
        except Exception as e:
            print("error", r["src_path"], e, flush=True)

    gone = supa.select("enhanced_scans", {"select": "src_path,scan_id", "status": "eq.skipped",
                                           "published_at": "not.is.null"})
    for g in gone:
        if g.get("scan_id"):
            supa.update("scans", {"id": g["scan_id"]}, {"public": False})
        supa.update("enhanced_scans", {"src_path": g["src_path"]}, {"published_at": None})
    print(f"published {ok}, took down {len(gone)}", flush=True)


if __name__ == "__main__":
    main()

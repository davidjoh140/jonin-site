"""Readable copies of the enhanced scans for the card-text scheduled tasks (2026-11-27).

The scheduled Claude sessions that type out card text can reach GitHub but not R2, so this puts a 1000x1400 JPEG of each
enhanced master (R2 masters/...) on the `text-scans` branch as text-scans/<set>/<number>[_tag].jpg, plus index.json
mapping card id -> file. Only cards that still need text are kept (BATCH at a time), and the branch is rebuilt as a
single fresh commit every run, so it never grows: once a card's text is in public.card_text its picture drops off.

Env: SUPABASE_URL, SUPABASE_SERVICE_KEY, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_ENDPOINT, R2_BUCKET. Writes ./out/.
"""
import io, json, os, sys
import boto3
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import supa

BATCH = int(os.environ.get("TEXT_SCANS_BATCH", "500"))
OUT = "out"


def main():
    done = {r["card_id"] for r in supa.select("card_text", {"select": "card_id"})}
    rows = supa.select("enhanced_scans", {"select": "card_id,tag,r2_key", "r2_key": "not.is.null", "order": "card_id"})
    pick = {}
    for r in rows:   # one master per card: prefer the untagged (normal) one
        cid = r["card_id"]
        if not cid or cid in done:
            continue
        if cid not in pick or (pick[cid]["tag"] and not r["tag"]):
            pick[cid] = r
    todo = list(pick.values())[:BATCH]
    print(f"{len(done)} cards have text, {len(pick)} enhanced cards waiting, exporting {len(todo)}", flush=True)
    s3 = boto3.client("s3", endpoint_url=os.environ["R2_ENDPOINT"], region_name="auto",
                      aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
                      aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"])
    bucket = os.environ.get("R2_BUCKET", "jonin-scans")
    index = {}
    for r in todo:
        try:
            img = Image.open(io.BytesIO(s3.get_object(Bucket=bucket, Key=r["r2_key"])["Body"].read())).convert("RGB")
            rel = r["r2_key"].split("/", 1)[1].rsplit(".", 1)[0] + ".jpg"
            path = os.path.join(OUT, "text-scans", rel)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            img.resize((1000, 1400), Image.LANCZOS).save(path, "JPEG", quality=84, optimize=True)
            index[r["card_id"]] = "text-scans/" + rel
        except Exception as ex:
            print("skip", r["r2_key"], ex, flush=True)
    os.makedirs(OUT, exist_ok=True)
    json.dump({"waiting_total": len(pick), "cards": index}, open(os.path.join(OUT, "index.json"), "w"), indent=0)
    open(os.path.join(OUT, "README.md"), "w").write(
        "Temporary card pictures for the card-text tasks. Rebuilt by .github/workflows/text-scans.yml on main. Not the site.\n")


if __name__ == "__main__":
    main()

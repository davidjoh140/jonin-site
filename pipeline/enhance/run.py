"""Enhance the original 350x490 card scans into 1400x1960 masters (see process.py) for one shard.

  python run.py <originals dir> <shard> <shards>

For every scan in this shard that isn't in `enhanced_scans` yet:
  - match it to a card (set folder + file name, e.g. "Set 3 - .../n133.jpg" -> 3:N-133)
  - enhance it, upload the master to R2 (bucket jonin-scans, masters/<set>/<number>[_tag].webp)
  - save a row in `enhanced_scans` with a small thumbnail for review (status 'pending')
Unmatched scans are recorded with status 'unmatched' (not enhanced) so they can be mapped by hand.
Nothing reaches the site until David approves it in the Buying Desk.

Env: SUPABASE_URL, SUPABASE_SERVICE_KEY, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_ENDPOINT, R2_BUCKET.
"""
import base64, io, os, re, sys, time
import boto3
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import supa       # noqa: E402
import process    # noqa: E402

TINS = {"Fierce Ambitions": "T1", "Untouchables": "T2", "Ultimate Battle": "T3", "Rebirth": "T4"}
TP = {"17.5": "TP1", "19.5": "TP2", "21.5": "TP3", "23.5": "TP4"}
NAME_RX = re.compile(r"^([A-Za-z]+?)(US)?([0-9]+)([a-z]?)((?: \[[^\]]+\])*)\.(?:jpe?g|png|webp)$")


def set_for(folder):
    parts = folder.split("/")
    top = parts[0]
    if top == "Promos":
        if len(parts) > 1:
            for k, v in TINS.items():
                if parts[1].startswith(k):
                    return v
        return "P"
    m = re.match(r"^Set ([0-9.]+) ", top)
    if not m:
        return None
    return TP.get(m.group(1), m.group(1))


def number_for(name):
    """Possible card numbers for a file name, most likely first: n133 -> N-133; pr018b -> PR-018b, PR018B."""
    m = NAME_RX.match(name)
    if not m:
        return [], None
    p, us, d, sfx = m.group(1).upper(), m.group(2), m.group(3), m.group(4)
    tag = (m.group(5) or "").strip() or None
    dashed = f"{p}-{'US-' if us else ''}{d}{sfx}"
    plain = f"{p}{'US' if us else ''}{d}{sfx.upper()}"      # promo style: EX001, PR018B, PRUS001, M621
    return [dashed, plain, f"{p}-{'US' if us else ''}{d}{sfx.upper()}"], tag


def resolve(cards, by_number, set_id, nums):
    for n in nums:
        if (set_id, n) in cards:
            return cards[(set_id, n)], n
    if set_id == "P":                        # promos filed in another set (e.g. tin promos PR-069): only if unique
        for n in nums:
            ids = by_number.get(n, [])
            if len(ids) == 1:
                return ids[0], n
    return None, (nums[0] if nums else None)


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")


def main():
    root, shard, shards = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    files = sorted(os.path.relpath(os.path.join(d, f), root) for d, _, fs in os.walk(root) for f in fs
                   if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp")))
    mine = [f for i, f in enumerate(files) if i % shards == shard]
    done = {r["src_path"] for r in supa.select("enhanced_scans", {"select": "src_path", "status": "neq.unmatched"})}
    allc = supa.select("cards", {"select": "id,set_id,number"})
    cards = {(c["set_id"], c["number"]): c["id"] for c in allc}
    by_number = {}
    for c in allc:
        by_number.setdefault(c["number"], []).append(c["id"])
    todo = [f for f in mine if f not in done]
    if os.environ.get("ENHANCE_LIMIT"):
        todo = todo[:int(os.environ["ENHANCE_LIMIT"])]
    print(f"shard {shard}/{shards}: {len(mine)} scans, {len(todo)} to do", flush=True)

    s3 = boto3.client("s3", endpoint_url=os.environ["R2_ENDPOINT"], region_name="auto",
                      aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
                      aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"])
    bucket = os.environ.get("R2_BUCKET", "jonin-scans")
    anime, net = process.load_models(HERE)
    ok = bad = 0
    for i, rel in enumerate(todo):
        folder, name = os.path.split(rel)
        set_id = set_for(folder)
        nums, tag = number_for(name)
        card_id, num = resolve(cards, by_number, set_id, nums) if set_id and nums else (None, None)
        if card_id:
            num = card_id.split(":", 1)[1]
        if not card_id:
            supa.upsert("enhanced_scans", [{"src_path": rel, "status": "unmatched",
                                            "note": f"no card {set_id}:{num}" if num else "file name not understood"}], "src_path")
            continue
        try:
            t = time.time()
            img = process.enhance(Image.open(os.path.join(root, rel)), anime, net)
            buf = io.BytesIO()
            img.save(buf, "WEBP", quality=90, method=5)
            key = f"masters/{set_id}/{num}{'_' + slug(tag) if tag else ''}.webp"
            s3.put_object(Bucket=bucket, Key=key, Body=buf.getvalue(), ContentType="image/webp",
                          CacheControl="public, max-age=31536000")
            th = io.BytesIO()
            img.resize((200, 280), Image.LANCZOS).save(th, "WEBP", quality=72)
            supa.upsert("enhanced_scans", [{"src_path": rel, "card_id": card_id, "tag": tag, "r2_key": key,
                                            "status": "pending", "thumb_b64": base64.b64encode(th.getvalue()).decode()}], "src_path")
            ok += 1
            if ok % 10 == 0 or i < 3:
                print(f"{i + 1}/{len(todo)} {rel} -> {key} ({time.time() - t:.0f}s)", flush=True)
        except Exception as e:
            bad += 1
            supa.upsert("enhanced_scans", [{"src_path": rel, "card_id": card_id, "status": "error", "note": str(e)[:300]}], "src_path")
            print("error", rel, e, flush=True)
    print(f"shard {shard} finished: {ok} enhanced, {bad} errors", flush=True)


if __name__ == "__main__":
    main()

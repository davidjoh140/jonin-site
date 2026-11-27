"""Find product photos for sealed items on eBay and queue them for David in Jonin Hub → Review → Sealed → Photos.

Two jobs:
  python find_sealed_images.py          search eBay for every sealed product with no photo yet (Find sealed photos workflow)
  python find_sealed_images.py --mirror copy photos David picked into R2 (img.jonin.cards) and set products.image_url
                                        (runs in the Sync workflow every ~15 minutes)

Nothing shows on jonin.cards until David picks a photo. PLACEHOLDERS for David: 4 photos per product, listings must
match the product by title (opened/empty items allowed for photos), 1 eBay page per product.
"""
import hashlib
import io
import os
import sys

import requests
from PIL import Image

import sealed
import supa
from find_scans import EBAY, Budget, OutOfCalls, big, ebay_token, fetch_image

PER_PRODUCT = 4        # PLACEHOLDER: photos queued per product
MAX_CALLS = 150        # PLACEHOLDER: eBay calls per run (one per product, then the broad searches)
BROAD = ["naruto ccg theme deck", "naruto ccg starter deck", "naruto card game theme deck bandai",
         "naruto ccg booster box", "naruto ccg booster pack", "naruto ccg tin"]   # PLACEHOLDER
BROAD_PAGES = 3


def query(p):
    name = p["name"].replace(":", " ")
    return f"naruto ccg {name}" + ("" if p["kind"] == "tournament_pack" else " sealed")


def search(tok, q, budget):
    budget.spend()
    r = requests.get(f"{EBAY}/buy/browse/v1/item_summary/search", params={"q": q, "limit": 100},
                     headers={"Authorization": f"Bearer {tok}", "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"}, timeout=60)
    r.raise_for_status()
    return r.json().get("itemSummaries", [])


def find():
    with supa.Run("find_sealed_images") as run:
        products = [p for p in supa.select("products") if p.get("public", True)]
        sets = supa.select("sets")
        have, seen = {}, set()
        for c in supa.select("sealed_image_candidates", {"select": "product_id,status,image_url"}):
            have.setdefault(c["product_id"], []).append(c["status"])
            seen.add((c["product_id"], c["image_url"]))

        def add(row):
            """Queue one photo; False if we already have it."""
            k = (row["product_id"], row["image_url"])
            if k in seen:
                return False
            seen.add(k)
            try:
                supa.insert("sealed_image_candidates", [row], returning=False)
                return True
            except Exception as e:
                print("could not queue", k, e)
                return False
        todo = [p for p in products if not p.get("image_url") and "approved" not in have.get(p["id"], [])
                and have.get(p["id"], []).count("pending") < PER_PRODUCT]
        only = os.environ.get("PRODUCT_FILTER")
        if only:
            todo = [p for p in todo if p["id"] == only or p["set_id"] == only]
        tok, budget = ebay_token(), Budget(MAX_CALLS)
        stats = run.stats = {"products": len(todo), "queued": 0, "none_found": [], "calls_left": MAX_CALLS}
        try:
            for p in todo:
                want = PER_PRODUCT - have.get(p["id"], []).count("pending")
                got = 0
                for it in search(tok, query(p), budget):
                    if got >= want:
                        break
                    hit = sealed.match(it.get("title", ""), products, sets, photo=True)
                    url = big((it.get("image") or {}).get("imageUrl"))
                    if not hit or hit[0]["id"] != p["id"] or not url or (p["id"], url) in seen:
                        continue
                    strict = sealed.match(it.get("title", ""), products, sets)
                    note = "" if strict and strict[0]["id"] == p["id"] else "title says opened, empty or similar: photo may show an opened item"
                    try:
                        _, thumb = fetch_image(url)
                    except Exception as e:
                        print("photo failed", url, e)
                        continue
                    if add({"product_id": p["id"], "image_url": url, "source_url": it.get("itemWebUrl"),
                            "title": it.get("title"), "note": note, "thumb_b64": thumb}):
                        got += 1
                        stats["queued"] += 1
                if not got and not have.get(p["id"]):
                    stats["none_found"].append(p["id"])
            # 2. broad searches for whatever is still missing (rare decks are rarely titled the way we search)
            missing = {pid for pid in stats["none_found"]}
            per = {}
            for q in BROAD:
                if not missing:
                    break
                for page in range(BROAD_PAGES):
                    budget.spend()
                    r = requests.get(f"{EBAY}/buy/browse/v1/item_summary/search",
                                     params={"q": q, "limit": 200, "offset": page * 200},
                                     headers={"Authorization": f"Bearer {tok}", "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"}, timeout=60)
                    r.raise_for_status()
                    items = r.json().get("itemSummaries", [])
                    for it in items:
                        hit = sealed.match(it.get("title", ""), products, sets, photo=True)
                        url = big((it.get("image") or {}).get("imageUrl"))
                        if not hit or hit[0]["id"] not in missing or not url or per.get(hit[0]["id"], 0) >= PER_PRODUCT \
                                or (hit[0]["id"], url) in seen:
                            continue
                        try:
                            _, thumb = fetch_image(url)
                        except Exception:
                            continue
                        if add({"product_id": hit[0]["id"], "image_url": url, "source_url": it.get("itemWebUrl"),
                                "title": it.get("title"), "note": "", "thumb_b64": thumb}):
                            per[hit[0]["id"]] = per.get(hit[0]["id"], 0) + 1
                            stats["queued"] += 1
                    if len(items) < 200:
                        break
            stats["found_by_broad"] = sorted(per)
            stats["none_found"] = [x for x in stats["none_found"] if x not in per]
        except OutOfCalls:
            stats["stopped"] = "call budget used up"
        stats["calls_left"] = budget.left
        print(stats)


def mirror():
    """Photos David picked -> R2 site/sealed/<product>-<hash>.webp -> products.image_url."""
    import r2
    if not r2.configured():
        print("R2 not configured, skipping")
        return
    with supa.Run("mirror_sealed_images") as run:
        rows = supa.select("sealed_image_candidates", {"select": "id,product_id,image_url,r2_url",
                                                       "status": "eq.approved", "r2_url": "is.null"})
        done = 0
        for c in rows:
            try:
                r = requests.get(c["image_url"], timeout=60)
                r.raise_for_status()
                im = Image.open(io.BytesIO(r.content)).convert("RGB")
                try:                                # cut out and cleaned (sealed_photo.py) when rembg is installed
                    import sealed_photo
                    data, tag = sealed_photo.webp(sealed_photo.clean(im)), "c"
                except Exception as e:
                    print("photo cleanup skipped:", e)
                    im.thumbnail((1200, 1200))
                    buf = io.BytesIO()
                    im.save(buf, "WEBP", quality=86)
                    data, tag = buf.getvalue(), ""
                key = f"site/sealed/{c['product_id'].lower()}-{tag}{hashlib.sha1(c['image_url'].encode()).hexdigest()[:10]}.webp"
                r2.put(key, data, "image/webp")
                url = r2.PUBLIC + key
                supa.update("sealed_image_candidates", {"id": c["id"]}, {"r2_url": url})
                supa.update("products", {"id": c["product_id"]}, {"image_url": url, "updated_at": "now()"})
                done += 1
            except Exception as e:
                print("mirror failed", c["id"], e)
        run.stats = {"mirrored": done, "waiting": len(rows)}
        print(run.stats)


def pending():
    """How many picked photos are waiting to be copied (the Sync workflow installs rembg only when > 0)."""
    return len(supa.select("sealed_image_candidates", {"select": "id", "status": "eq.approved", "r2_url": "is.null"}))


if __name__ == "__main__":
    if "--pending" in sys.argv:
        print(pending())
    else:
        mirror() if "--mirror" in sys.argv else find()

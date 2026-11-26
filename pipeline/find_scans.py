"""Find card images on eBay and PSA and queue them in Supabase (scan_candidates) for David's yes / no.

Reads the card list from Supabase at the start of every run, so it can only attach images to cards
that exist there. Nothing goes public until it is approved.

Env: SUPABASE_URL, SUPABASE_SERVICE_KEY, EBAY_CLIENT_ID, EBAY_CLIENT_SECRET, PSA_TOKEN (optional),
     SET_FILTER (optional, overrides settings.SET_FILTER; "all" = every set).
"""
import base64
import io
import os
import re
import time

import requests
from PIL import Image

import settings as cfg
import supa
from match import Matcher, norm_num, words

EBAY = "https://api.ebay.com"
PSA = "https://api.psacard.com/publicapi"
QUALITY_RANK = {"placeholder": 1, "slab": 2, "clean": 3}


class OutOfCalls(Exception):
    pass


class Budget:
    def __init__(self, n):
        self.left = n

    def spend(self):
        if self.left <= 0:
            raise OutOfCalls
        self.left -= 1


class PsaBudget(Budget):
    """PSA calls also come out of the shared daily count in Supabase (psa_take), leaving
    PSA_MEMBER_RESERVE calls for jonin.cards members' cert lookups."""

    def spend(self):
        super().spend()
        try:
            ok = supa.rpc("psa_take", {"p_calls": 1, "p_reserve": cfg.PSA_MEMBER_RESERVE})
        except (Exception, SystemExit):
            ok = True   # counter unreachable: fall back to the per-run cap only
        if ok is False:
            self.left = 0
            raise OutOfCalls


def ebay_token():
    r = requests.post(f"{EBAY}/identity/v1/oauth2/token",
                      auth=(os.environ["EBAY_CLIENT_ID"], os.environ["EBAY_CLIENT_SECRET"]),
                      data={"grant_type": "client_credentials", "scope": "https://api.ebay.com/oauth/api_scope"},
                      timeout=30)
    r.raise_for_status()
    return r.json()["access_token"]


def ebay_search(tok, q, pages, budget):
    for p in range(pages):
        budget.spend()
        r = requests.get(f"{EBAY}/buy/browse/v1/item_summary/search",
                         params={"q": q, "limit": 200, "offset": p * 200},
                         headers={"Authorization": f"Bearer {tok}", "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"}, timeout=60)
        r.raise_for_status()
        items = r.json().get("itemSummaries", [])
        yield from items
        if len(items) < 200:
            return


def ebay_cert(tok, item_id, budget):
    """PSA cert number from a graded listing's item specifics, if the seller filled it in."""
    budget.spend()
    r = requests.get(f"{EBAY}/buy/browse/v1/item/{item_id}",
                     headers={"Authorization": f"Bearer {tok}", "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"}, timeout=60)
    if r.status_code != 200:
        return None
    asp = {a.get("name", "").lower(): a.get("value", "") for a in r.json().get("localizedAspects", [])}
    if "psa" not in asp.get("professional grader", "").lower():
        return None
    m = re.search(r"\d{8,10}", asp.get("certification number", ""))
    return m.group(0) if m else None


def psa_cert(cert, budget):
    """Card details and front image URL for a PSA cert (2 API calls)."""
    h = {"Authorization": f"bearer {os.environ['PSA_TOKEN']}"}
    budget.spend()
    r = requests.get(f"{PSA}/cert/GetByCertNumber/{cert}", headers=h, timeout=30)
    if r.status_code != 200:
        return None, None
    info = r.json().get("PSACert") or {}
    budget.spend()
    r = requests.get(f"{PSA}/cert/GetImagesByCertNumber/{cert}", headers=h, timeout=30)
    imgs = r.json() if r.status_code == 200 else []
    front = next((i.get("ImageURL") for i in imgs if i.get("IsFrontImage")), None)
    return info, front


def fetch_image(url):
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    im = Image.open(io.BytesIO(r.content)).convert("RGB")
    full = io.BytesIO()
    im.save(full, "JPEG", quality=90)
    th = im.copy()
    th.thumbnail((cfg.THUMB_WIDTH, cfg.THUMB_WIDTH * 2))
    small = io.BytesIO()
    th.save(small, "JPEG", quality=78)
    return full.getvalue(), base64.b64encode(small.getvalue()).decode()


def big(url):
    return re.sub(r"/s-l\d+\.", "/s-l1600.", url or "")


def main():
    set_filter = os.environ.get("SET_FILTER") or cfg.SET_FILTER
    set_filter = None if set_filter in (None, "", "all") else set_filter
    with supa.Run("find_scans") as run:
        sets = supa.select("sets")
        cards = supa.select("cards")
        if set_filter:
            cards = [c for c in cards if c["set_id"] == set_filter]
        matcher = Matcher(cards, sets)
        existing = supa.select("scan_candidates", {"select": "card_id,status,quality,source_ref"})
        approved = supa.select("scans", {"select": "card_id,quality", "public": "eq.true"})
        seen = {e["source_ref"] for e in existing}
        pending = {}
        for e in existing:
            if e["status"] == "pending":
                pending[e["card_id"]] = pending.get(e["card_id"], 0) + 1
        best = {}
        for a in approved:
            best[a["card_id"]] = max(best.get(a["card_id"], 0), QUALITY_RANK.get(a.get("quality") or "", 3))
        stats = run.stats = {"set": set_filter or "all", "listings": 0, "matched": 0, "queued": 0, "psa": 0,
                             "skipped_have_better": 0, "errors": 0}

        def wanted(card_id, quality):
            if best.get(card_id, 0) >= QUALITY_RANK[quality]:
                stats["skipped_have_better"] += 1
                return False
            return pending.get(card_id, 0) < cfg.MAX_PENDING_PER_CARD

        def queue(card, conf, reason, printing, edition, source, quality, ref, url, credit, img_url, folder):
            full, thumb = fetch_image(img_url)
            path = f"{folder}/{card['id'].replace(':', '_')}/{re.sub(r'[^A-Za-z0-9_-]', '_', ref)}.jpg"
            supa.upload("scans", path, full)
            row = {"card_id": card["id"], "printing": printing, "edition": edition, "source": source,
                   "quality": quality, "source_ref": ref, "source_url": url, "credit": credit, "image_path": path,
                   "thumb_b64": thumb, "confidence": conf, "match_reason": reason}
            supa.insert("scan_candidates", [row], ignore_duplicates=True, returning=False)
            if cfg.AUTO_APPROVE_CONFIDENCE is not None and conf >= cfg.AUTO_APPROVE_CONFIDENCE:
                supa.update("scan_candidates", {"source_ref": ref}, {"status": "approved"})
            seen.add(ref)
            pending[card["id"]] = pending.get(card["id"], 0) + 1
            stats["queued"] += 1

        tok = ebay_token()
        ebay_budget, psa_budget = Budget(cfg.EBAY_MAX_CALLS_PER_RUN), PsaBudget(cfg.PSA_MAX_CALLS_PER_RUN)
        set_name = next((s["name"] for s in sets if s["id"] == set_filter), "") if set_filter else ""
        try:
            for q in cfg.EBAY_QUERIES:
                for it in ebay_search(tok, f'{q} "{set_name}"' if set_name else q, cfg.EBAY_PAGES_PER_QUERY,
                                      ebay_budget):
                    stats["listings"] += 1
                    ref = f"ebay:{it['itemId']}"
                    if ref in seen:   # already queued from an earlier search or run
                        continue
                    title = it.get("title", "")
                    hit = matcher.match(title, cfg.LOT_WORDS)
                    if not hit or hit[1] < cfg.MIN_CONFIDENCE:
                        continue
                    card, conf, reason, printing, edition = hit
                    stats["matched"] += 1
                    try:
                        graded = re.search(r"\bPSA\s?(10|[1-9](\.5)?)\b", title.upper())
                        if graded and os.environ.get("PSA_TOKEN") and psa_budget.left >= 2:
                            cert = ebay_cert(tok, it["itemId"], ebay_budget)
                            pref = f"psa:{cert}:front" if cert else None
                            if cert and pref not in seen and wanted(card["id"], "slab"):
                                info, front = psa_cert(cert, psa_budget)
                                n = norm_num(info.get("CardNumber") or "") if info else None
                                same = n and n.replace("-", "") == card["number"].replace("-", "").upper() and \
                                    set(words(card["name"])) & set(words(info.get("Subject") or ""))
                                if front and same:
                                    queue(card, min(conf + 0.05, 0.99), reason + ", PSA cert agrees", printing, edition,
                                          "PSA", "slab", pref, f"https://www.psacard.com/cert/{cert}",
                                          f"PSA cert {cert}", front, "psa")
                                    stats["psa"] += 1
                                    seen.add(ref)
                                    continue
                        if not wanted(card["id"], "placeholder"):
                            continue
                        img = big((it.get("image") or {}).get("imageUrl"))
                        if not img:
                            continue
                        seller = (it.get("seller") or {}).get("username", "")
                        queue(card, conf, reason, printing, edition, "eBay listing", "placeholder", ref,
                              it.get("itemWebUrl"), f"eBay seller {seller}".strip(), img, "ebay")
                    except OutOfCalls:
                        raise
                    except Exception as e:
                        stats["errors"] += 1
                        print("error on", ref, e)
                    time.sleep(0.2)
        except OutOfCalls:
            stats["stopped"] = "call budget used up"
        print(stats)


if __name__ == "__main__":
    main()
